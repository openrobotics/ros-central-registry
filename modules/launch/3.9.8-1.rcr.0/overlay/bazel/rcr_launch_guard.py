# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pre-/post-run process hygiene for Bazel launch targets.

Used by the entry points behind ``launch_binary``/``launch_test`` (and so by
``launch_ros_binary``/``launch_ros_test``, which wrap them).

Every launch invocation tags its own environment, and therefore every
process it spawns, with ``RCR_LAUNCH_OWNER_PID``. That lets a later
invocation recognise processes left behind by an earlier one even after
they have been re-parented to PID 1:

* **Pre-run**: tagged processes whose owning launch process is gone are
  *dangling*. Outside ``bazel test`` the launch aborts and lists them;
  under ``bazel test`` (``TEST_TMPDIR`` set) they are killed instead, so a
  flaky-test retry after a timeout can still run. Tagged processes whose
  owner is still alive belong to a concurrent launch and only produce a
  warning.
* **Post-run**: whatever this invocation spawned and is still alive after
  ``LaunchService`` returns (or after SIGHUP/SIGTERM) is terminated, then
  killed.

Environment overrides:

* ``RCR_LAUNCH_KILL_DANGLING=1`` -- kill dangling processes and proceed.
* ``RCR_LAUNCH_IGNORE_DANGLING=1`` -- skip the pre-run check entirely.

Only Bazel invocations go through this; ``ros2 launch`` is unaffected.
"""

import contextlib
import os
import signal
import sys
import threading
from typing import Dict, Iterator, List, Optional, Tuple

import psutil

OWNER_PID_ENV = 'RCR_LAUNCH_OWNER_PID'
TARGET_ENV = 'RCR_LAUNCH_TARGET'
KILL_DANGLING_ENV = 'RCR_LAUNCH_KILL_DANGLING'
IGNORE_DANGLING_ENV = 'RCR_LAUNCH_IGNORE_DANGLING'

ABORT_MESSAGE = (
    'Background dangling subprocesses detected from a previous launch '
    'invocation. Aborting.'
)

_TERMINATE_TIMEOUT_S = 5.0
_TRACK_INTERVAL_S = 1.0
_LOG_PREFIX = '[rcr_launch_guard]'


class _DescendantTracker:
    """Periodically record our descendants' (pid, create_time) while launch runs.

    Needed because by the time the post-run cleanup runs, grandchildren whose
    parent already exited have been re-parented to PID 1 and are no longer
    reachable via Process.children(); and on macOS the environment marker is
    unreadable for Apple platform binaries (/bin/sh, sleep, ...), so the
    marker scan can't find those either. Anything seen in our tree at least
    once is remembered and checked (by create time, to rule out PID reuse)
    at cleanup.
    """

    def __init__(self, interval: float = _TRACK_INTERVAL_S):
        self._interval = interval
        self._seen: Dict[int, float] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name='rcr_launch_guard_tracker', daemon=True
        )

    def start(self) -> None:
        self.snapshot()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.snapshot()

    def snapshot(self) -> None:
        try:
            children = psutil.Process(os.getpid()).children(recursive=True)
        except (psutil.Error, OSError):
            return
        with self._lock:
            for child in children:
                try:
                    self._seen[child.pid] = child.create_time()
                except (psutil.Error, OSError):
                    continue

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            self.snapshot()

    def survivors(self) -> List[psutil.Process]:
        """Remembered descendants that are still alive (same pid *and* create time)."""
        result = []
        with self._lock:
            seen = dict(self._seen)
        for pid, created in seen.items():
            try:
                proc = psutil.Process(pid)
                if proc.is_running() and abs(proc.create_time() - created) < 1e-3:
                    result.append(proc)
            except (psutil.Error, OSError):
                continue
        return result


def _log(msg: str) -> None:
    print(f'{_LOG_PREFIX} {msg}', file=sys.stderr, flush=True)


def _is_truthy(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in ('1', 'true', 'yes', 'on')


def _describe(proc: psutil.Process) -> str:
    try:
        cmd = proc.cmdline()
        name = os.path.basename(cmd[0]) if cmd else proc.name()
        tail = ' '.join(cmd[1:3])
        if len(cmd) > 3:
            tail += ' ...'
        return f'pid {proc.pid} ({name} {tail})'.rstrip()
    except (psutil.Error, OSError):
        return f'pid {proc.pid}'


def _tagged_processes() -> Iterator[Tuple[psutil.Process, int, Optional[str]]]:
    """Yield (process, owner_pid, target) for every process carrying our marker.

    Only the current user's processes are readable; others are skipped.
    """
    me = os.getpid()
    for proc in psutil.process_iter(attrs=['pid']):
        if proc.pid == me:
            continue
        try:
            env = proc.environ()
        except (psutil.Error, OSError):
            continue
        owner = env.get(OWNER_PID_ENV)
        if not owner:
            continue
        try:
            owner_pid = int(owner)
        except ValueError:
            continue
        yield proc, owner_pid, env.get(TARGET_ENV)


def _owner_alive(owner_pid: int, child: psutil.Process) -> bool:
    """True if owner_pid still refers to the launch process that spawned child."""
    try:
        owner = psutil.Process(owner_pid)
        # Guard against PID reuse: the owner must predate the child.
        return owner.is_running() and owner.create_time() <= child.create_time()
    except (psutil.Error, OSError):
        return False


def classify_leftovers() -> Tuple[List[Tuple[psutil.Process, Optional[str]]],
                                  Dict[int, Tuple[int, Optional[str]]]]:
    """Split tagged processes into dangling ones and live concurrent launches.

    Returns ``(dangling, live)`` where ``dangling`` is a list of
    ``(process, target)`` whose owner no longer exists, and ``live`` maps an
    alive owner PID to ``(number_of_processes, target)``.
    """
    dangling: List[Tuple[psutil.Process, Optional[str]]] = []
    live: Dict[int, Tuple[int, Optional[str]]] = {}
    for proc, owner_pid, target in _tagged_processes():
        if owner_pid == proc.pid or _owner_alive(owner_pid, proc):
            count, tgt = live.get(owner_pid, (0, target))
            live[owner_pid] = (count + 1, tgt or target)
        else:
            dangling.append((proc, target))
    return dangling, live


def terminate_processes(procs: List[psutil.Process],
                        timeout: float = _TERMINATE_TIMEOUT_S) -> int:
    """SIGTERM procs, wait up to timeout, SIGKILL survivors. Returns # handled."""
    alive = []
    for proc in procs:
        try:
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                proc.terminate()
                alive.append(proc)
        except (psutil.Error, OSError):
            pass
    if not alive:
        return 0
    _, still_alive = psutil.wait_procs(alive, timeout=timeout)
    for proc in still_alive:
        try:
            proc.kill()
        except (psutil.Error, OSError):
            pass
    if still_alive:
        psutil.wait_procs(still_alive, timeout=timeout)
    return len(alive)


def check_for_dangling_processes() -> None:
    """Pre-run check. Raises SystemExit(1) on dangling processes unless overridden."""
    if _is_truthy(IGNORE_DANGLING_ENV):
        return

    dangling, live = classify_leftovers()

    for owner_pid, (count, target) in sorted(live.items()):
        what = f"'{target}'" if target else 'another launch'
        _log(
            f'warning: {what} (pid {owner_pid}) is still running with '
            f'{count} process(es); it may interfere with this launch.'
        )

    if not dangling:
        return

    lines = [f'  - {_describe(proc)}' + (f'  [from {target}]' if target else '')
             for proc, target in dangling]
    in_test = bool(os.environ.get('TEST_TMPDIR'))
    if in_test or _is_truthy(KILL_DANGLING_ENV):
        _log(
            f'warning: killing {len(dangling)} dangling subprocess(es) left '
            'by a previous launch invocation:\n' + '\n'.join(lines)
        )
        terminate_processes([proc for proc, _ in dangling])
        return

    _log(
        f'error: {ABORT_MESSAGE}\n'
        + '\n'.join(lines)
        + '\n'
        + f'Kill them (e.g. `kill {" ".join(str(p.pid) for p, _ in dangling)}`), '
        f'or re-run with {KILL_DANGLING_ENV}=1 to have the launcher clean them '
        f'up, or {IGNORE_DANGLING_ENV}=1 to proceed anyway.'
    )
    raise SystemExit(1)


def cleanup_own_processes(tracker: Optional[_DescendantTracker] = None) -> None:
    """Post-run cleanup: terminate anything this invocation spawned that's still alive."""
    me = os.getpid()
    found: Dict[int, psutil.Process] = {}
    try:
        for child in psutil.Process(me).children(recursive=True):
            found[child.pid] = child
    except (psutil.Error, OSError):
        pass
    # Descendants that detached from our tree before we got here.
    if tracker is not None:
        for proc in tracker.survivors():
            found.setdefault(proc.pid, proc)
    # ... and anything else carrying our marker.
    for proc, owner_pid, _ in _tagged_processes():
        if owner_pid == me:
            found.setdefault(proc.pid, proc)
    if not found:
        return
    procs = list(found.values())
    _log(
        f'warning: {len(procs)} subprocess(es) still running after launch '
        'exit; terminating:\n' + '\n'.join(f'  - {_describe(p)}' for p in procs)
    )
    terminate_processes(procs)


@contextlib.contextmanager
def launch_process_guard(target: Optional[str] = None) -> Iterator[None]:
    """Wrap a launch run with the pre-run check and post-run cleanup.

    Also makes SIGHUP (e.g. the terminal closing) unwind through the normal
    exit path so the cleanup runs; SIGINT/SIGTERM are already handled by
    launch itself.
    """
    check_for_dangling_processes()

    os.environ[OWNER_PID_ENV] = str(os.getpid())
    if target:
        os.environ[TARGET_ENV] = target

    previous_hup = None
    if hasattr(signal, 'SIGHUP'):
        def _on_hup(signum, _frame):
            raise SystemExit(128 + signum)
        try:
            previous_hup = signal.signal(signal.SIGHUP, _on_hup)
        except (ValueError, OSError):  # not the main thread, etc.
            previous_hup = None

    tracker = _DescendantTracker()
    tracker.start()
    try:
        yield
    finally:
        tracker.stop()
        try:
            cleanup_own_processes(tracker)
        finally:
            if previous_hup is not None:
                try:
                    signal.signal(signal.SIGHUP, previous_hup)
                except (ValueError, OSError):
                    pass
