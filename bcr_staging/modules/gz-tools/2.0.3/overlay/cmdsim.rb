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

    gui_only = (sim_args.include?('-g') || sim_args.include?('--gui')) &&
               !sim_args.include?('-s') && !sim_args.include?('--server')

    if gui_only
      require 'cmdgui'
      gui_args = ['gui']
      has_config = false
      i = 0
      while i < sim_args.length
        a = sim_args[i]
        if a == '-v' || a == '--verbose'
          gui_args << '-v'
          if i + 1 < sim_args.length && !sim_args[i + 1].start_with?('-')
            gui_args << sim_args[i + 1]
            i += 1
          end
        elsif a == '--gui-config' && i + 1 < sim_args.length
          gui_args << '-c' << sim_args[i + 1]
          has_config = true
          i += 1
        end
        i += 1
      end
      if !has_config
        default_cfg = File.expand_path('sim_gui.config', File.dirname(__FILE__))
        if File.file?(default_cfg)
          gui_args << '-c' << default_cfg
        end
      end
      ARGV.replace(gui_args.dup)
      Cmd.new.execute(gui_args)
      exit(0)
    end

    value_flags = [
      '--force-version', '-v', '--verbose', '--iterations',
      '--network-role', '--network-secondaries', '--record-path',
      '--playback', '--seed', '--gui-config', '--physics-engine',
      '--render-engine', '--render-engine-gui', '--render-engine-server'
    ]
    world_file = ''
    i = 0
    while i < sim_args.length
      a = sim_args[i]
      if value_flags.include?(a)
        i += 2
        next
      end
      world_file = a unless a.start_with?('-')
      i += 1
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
    exec(*cmd)
  end
end
