#!/usr/bin/env python

#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Willow Garage, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#


'''
This script partially converts a CMakeLists.txt file from rosbuild to catkin.
'''

from __future__ import print_function
import re
import sys
import argparse

conversions = [
    ('rosbuild_add_gtest', 'catkin_add_gtest'),
    ('rosbuild_add_pyunit', 'catkin_add_nosetests'),
    ('rosbuild_', '')
]


def main(argv, outstream):
    """
    reads file and prints converted file to stdout
    """
    parser = argparse.ArgumentParser(description='Helper script to migrate rosbuild packages')
    parser.add_argument('project_name',
                        nargs=1,
                        help='The name of the package')
    parser.add_argument('cmakelists_path',
                        nargs=1,
                        help='path to the CMakeLists.txt')
    # Parse args
    args = parser.parse_args(argv)

    # Convert CMakeLists.txt
    print('Converting %s' % args.cmakelists_path, file=sys.stderr)
    with open(args.cmakelists_path[0], 'r') as f_in:
        lines = f_in.read().splitlines()
    for line in convert_cmakelists(args.project_name[0], lines):
        print(line, file=outstream)


def convert_cmakelists(project_name, lines):
    """
    Catkinize the lines of a file as much as we can without manual intervention.
    """
    lines = list(convert_boost(lines))
    lines = map(convert_line, lines)
    lines = add_header_if_needed(lines, make_header_lines(project_name))
    return lines


def add_header_if_needed(lines, header):
    if not [l for l in lines if 'catkin_package' in l]:
        return header + [''] + lines
    return lines


def make_header_lines(project_name):
    """
    Make top lines of CMakeLists file according to
    http://www.ros.org/doc/groovy/api/catkin/html/user_guide/standards.html
    """
    header = '''
# http://ros.org/doc/groovy/api/catkin/html/user_guide/supposed.html
cmake_minimum_required(VERSION 2.8.3)
project(%s)
# Load catkin and all dependencies required for this package
find_package(catkin REQUIRED)

# catkin_package(
#    INCLUDE_DIRS include
#    LIBRARIES ${PROJECT_NAME}
#    DEPENDS otherpkg)

# include_directories(include ${Boost_INCLUDE_DIR} ${catkin_INCLUDE_DIRS})
''' % project_name
    return header.strip().splitlines()


def convert_line(line):
    """
    Do all replacements that can be done for a single line without looking at
    anything else.
    """
    for a, b in conversions:
        line = line.replace(a, b)
    return line


COMMENT_RX = re.compile('#.*')
LINK_BOOST_RX = re.compile(r'[ ]*rosbuild_link_boost\(([^ ]+)\s+([^)]+)\)')


def convert_boost(lines):
    """
    convert_cmakelists Boost sections.
    """
    for count, line in enumerate(lines):
        line2 = COMMENT_RX.sub('', line)
        if 'rosbuild_add_boost_directories' in line2:
            # These lines are no longer needed.
            continue
        if 'rosbuild_init' in line2:
            # These lines are no longer needed.
            continue
        elif 'rosbuild_link_boost' in line2:
            # rosbuild_link_boost lines expand to multiple statements.
            m = LINK_BOOST_RX.match(line2)
            if not m:
                raise ValueError('Could not recognize rosbuild_link_boost statement starting at line %s (maybe multi-line?): \n%s' % (count+1, line))
            target = m.group(1)
            components = m.group(2)
            yield 'find_package(Boost REQUIRED COMPONENTS %s)' % components
            yield 'include_directories(${Boost_INCLUDE_DIRS})'
            yield 'target_link_libraries(%s ${Boost_LIBRARIES})' % target
        else:
            # All other lines pass through unchanged.
            yield line


if __name__ == '__main__':
    main(argv=sys.argv[1:], outstream=sys.stdout)

