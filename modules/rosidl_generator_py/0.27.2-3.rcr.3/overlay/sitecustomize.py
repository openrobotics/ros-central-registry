# Copyright 2025 Open Source Robotics Foundation, Inc.
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

"""
This is a global hook applies to the Python context that silently transforms
calls that look like this:

    from std_msgs.msg import String

into ones that look like this:
    
    from std_msgs.msg._string import String

We need this functionality because the Python IDL generator uses namespace
packages (PEP420) and therefore cannot put these remaps in __init__.py files.

This works because all message packages depend on rosidl_generator_py, and
so any code that relies on a message will have this injected into its context.
"""

import re
import sys
import importlib.abc
import importlib.util

INTERFACE_NAME_SUFFIXES = [
    '_Constants',
    '_Event',
    '_Feedback',
    '_FeedbackMessage',
    '_GetResult',
    '_Goal',
    '_Request',
    '_Response',
    '_Result',
    '_SendGoal',
    '.Constants',
]

def _convert_camel_case_to_lower_case_underscore(value: str) -> str:
    """Function to transform a capitalized message to a snake case message"""
    value = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    value = re.sub('([a-z0-9])([A-Z])', r'\1_\2', value)
    return value.lower()

def _get_code_from_name(name):
    code = name

    # Optimization: only strip suffixes if we see an underscore in the name
    if '_' in name:

        # Allow for at most two laters of suffix, eg. _SendGoal_Result.
        for suffix in INTERFACE_NAME_SUFFIXES:
            code = code.removesuffix(suffix)
        for suffix in INTERFACE_NAME_SUFFIXES:
            code = code.removesuffix(suffix)

    # This should now be the PEP-420 name of the python module.
    return _convert_camel_case_to_lower_case_underscore(code)

class NamespaceInterceptor(importlib.abc.Loader):
    """Class to handle and transform module load calls in Python"""

    def __init__(self, spec):
        self.spec = spec

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__path__ = self.spec.submodule_search_locations
        module.__package__ = self.spec.name
        def __getattr__(name):
            code = _get_code_from_name(name)
            try:
                target_submodule = f"{module.__name__}._{code}"
                impl_mod = importlib.import_module(target_submodule)
                return getattr(impl_mod, name)
            except (ImportError, AttributeError) as e:
                raise AttributeError(f"Could not resolve {name} via {target_submodule}") from e
            raise AttributeError(f"module {module.__name__} has no attribute {name}")
        module.__getattr__ = __getattr__

class InterceptingFinder(importlib.abc.MetaPathFinder):
    """Class to intercept module load calls in Python"""

    def find_spec(self, fullname, path, target=None):

        # We only want to intercept module calls that end in specific package
        # names, which are likely to be requests for ROS messages.
        if fullname.endswith((".msg", ".srv", ".action")):

            # Remove self to avoid recursion, and add it back once the correct
            # spec has been found using importlib.util.find_spec.
            meta_path = sys.meta_path[:]
            try:
                sys.meta_path.remove(self)
                spec = importlib.util.find_spec(fullname, path)
            finally:
                sys.meta_path[:] = meta_path

            # Namespaced modules have a spec.loader == None. We side-channel
            # these specs with our own namespaced finder that remaps the class.
            if spec is not None and spec.loader is None:
                spec.loader = NamespaceInterceptor(spec)
                return spec

        # If we hit this, then the traditional loader will be used.
        return None

# Register the hook
sys.meta_path.insert(0, InterceptingFinder())
