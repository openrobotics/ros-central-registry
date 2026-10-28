#!/usr/bin/ruby
# Copyright (C) 2026 Open Source Robotics Foundation
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

require 'optparse'

SIM_USAGE =
  "Run and manage Gazebo simulations.\n\n"\
  "  gz sim [options] [file]\n\n"\
  "Options:\n"\
  "  -g, --gui                    Run only the GUI.\n"\
  "  -s, --server                 Run only the server (headless mode).\n"\
  "  -r                           Run simulation on start.\n"\
  "  -v, --verbose [level]        Adjust the level of console output (0~4).\n"\
  "  -h, --help                   Print this help message.\n"\
  "  --force-version <VERSION>    Use a specific library version.\n"\
  "  --versions                   Show the available versions.\n"

class Cmd
  def execute(args)
    if args.include?('-h') || args.include?('--help')
      puts SIM_USAGE
      exit(0)
    end

    sim_args = args[0] == 'sim' ? args[1..-1] : args

    server_only = (sim_args.include?('-s') || sim_args.include?('--server')) &&
                  !sim_args.include?('-g') && !sim_args.include?('--gui')
    gui_only = (sim_args.include?('-g') || sim_args.include?('--gui')) &&
               !sim_args.include?('-s') && !sim_args.include?('--server')

    value_flags = [
      '--force-version', '-v', '--verbose', '--iterations',
      '--network-role', '--network-secondaries', '--record-path',
      '--record-topic', '--record-period', '--playback', '--seed',
      '--gui-config', '--physics-engine', '--render-engine',
      '--render-engine-gui', '--render-engine-server',
      '--render-engine-api-backend', '--render-engine-gui-api-backend',
      '--render-engine-server-api-backend', '-z', '--initial-sim-time'
    ]
    world_file = ''
    gui_config = ''
    verbose_level = nil
    render_engine_gui = nil
    render_engine_gui_backend = nil
    i = 0
    while i < sim_args.length
      a = sim_args[i]
      if a == '-v' || a == '--verbose'
        if i + 1 < sim_args.length && !sim_args[i + 1].start_with?('-')
          verbose_level = sim_args[i + 1]
          i += 2
        else
          verbose_level = '3'
          i += 1
        end
        next
      elsif a == '--gui-config' && i + 1 < sim_args.length
        gui_config = sim_args[i + 1]
        i += 2
        next
      elsif (a == '--render-engine' || a == '--render-engine-gui') && i + 1 < sim_args.length
        render_engine_gui = sim_args[i + 1]
        i += 2
        next
      elsif a == '--render-engine-gui-api-backend' && i + 1 < sim_args.length
        render_engine_gui_backend = sim_args[i + 1]
        i += 2
        next
      elsif value_flags.include?(a)
        i += 2
        next
      end
      world_file = a unless a.start_with?('-')
      i += 1
    end

    run_gui_client = lambda do
      gui_client_bin = ENV['GZ_SIM_GUI_CLIENT_BIN']
      if !gui_client_bin.nil? && !gui_client_bin.empty? && File.executable?(gui_client_bin)
        client_cmd = [gui_client_bin]
        if !verbose_level.nil?
          client_cmd += ['--verbose', verbose_level]
        end
        cfg = gui_config
        if cfg.empty?
          cfg = ENV['GZ_SIM_DEFAULT_GUI_CONFIG'] || ''
        end
        if !cfg.empty? && File.file?(cfg)
          client_cmd += ['--gui-config', cfg]
        end
        if !render_engine_gui.nil?
          client_cmd += ['--render-engine-gui', render_engine_gui]
        end
        if !render_engine_gui_backend.nil?
          client_cmd += ['--render-engine-gui-api-backend', render_engine_gui_backend]
        end
        begin
          system(*client_cmd)
        rescue Interrupt
          nil
        end
      else
        require 'cmdgui'
        gui_args = ['gui']
        gui_args += ['-v', verbose_level] unless verbose_level.nil?
        cfg = gui_config
        if cfg.empty?
          default_cfg = File.expand_path('sim_gui.config', File.dirname(__FILE__))
          cfg = default_cfg if File.file?(default_cfg)
        end
        gui_args += ['-c', cfg] unless cfg.empty?
        ARGV.replace(gui_args.dup)
        Cmd.new.execute(gui_args)
      end
    end

    if gui_only
      run_gui_client.call
      exit(0)
    end

    gzserver_bin = ENV['GZ_SIM_SERVER_BIN']
    if gzserver_bin.nil? || gzserver_bin.empty? || !File.executable?(gzserver_bin)
      gzserver_bin = nil
      (ENV['PATH'] || '').split(File::PATH_SEPARATOR).each do |dir|
        candidate = File.join(dir, 'gzserver')
        if File.file?(candidate) && File.executable?(candidate)
          gzserver_bin = candidate
          break
        end
      end
      gzserver_bin ||= 'gzserver'
    end

    cmd = [gzserver_bin]
    if !world_file.empty?
      cmd += ['--ros-args', '-p', "world_sdf_file:=#{world_file}"]
    end
    if server_only
      exec(*cmd)
    else
      server_pid = Process.spawn(*cmd)
      at_exit do
        begin
          Process.kill('TERM', server_pid)
          sleep 0.5
          Process.kill('KILL', server_pid)
          Process.wait(server_pid)
        rescue StandardError
          nil
        end
      end
      run_gui_client.call
    end
  end
end
