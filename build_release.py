#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Copyright (c) 2020 Francesco Martini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import re
import sys
import zipfile
import argparse
import subprocess
from subprocess import SubprocessError


PROJECT_NAME = 'cssUndefinedClasses'
ROOT_PATH = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = os.path.join(ROOT_PATH, PROJECT_NAME)
ICONS_PATH = os.path.join(ROOT_PATH, 'images')
RELEASES_PATH = os.path.join(ROOT_PATH, 'Releases')

PROJECT_FILES = {
    os.path.join(SRC_PATH, f): f for f in os.listdir(SRC_PATH) if os.path.isfile(os.path.join(SRC_PATH, f))
}

ADD_TO_RELEASE = {
    os.path.join(ICONS_PATH, 'icon_clean_xhtml48x48.png'): 'plugin.png',
    os.path.join(ROOT_PATH, 'README.md'): 'README.md'
}

NOT_RELEASED = []


def add_dir_to_release(dir_name, add_to):
    for top_dir, dirs, files in os.walk(os.path.join(ROOT_PATH, dir_name)):
        for file in files:
            abspath = os.path.join(top_dir, file)
            add_to[abspath] = os.path.relpath(abspath, ROOT_PATH)
    return add_to


add_dir_to_release('clearlooks', ADD_TO_RELEASE)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--destination', default=os.path.join(RELEASES_PATH, PROJECT_NAME))
    parser.add_argument('-v', '--version', default='')
    return parser.parse_args()


def confirm_proceed(prompt='Shall I proceed? (y/n)'):
    """
    Prompts user for confirmation. Expects 'y' or 'n'.
    """
    confirm = ''
    while confirm not in ('y', 'Y', 'n', 'N'):
        confirm = input(prompt)
    if confirm in ('n', 'N'):
        return False
    return True


def set_version(version):
    """
    If the version number is not provided by the -v argument to the script,
    use git to get the latest tag used in the repository. As a last resort, ask the user.
    """
    if not version:
        try:
            proc = subprocess.run(
                'git describe --tags --abbrev=0',  # $(git rev-list --tags --max-count=1)',
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                shell=True, check=True, universal_newlines=True
            )
            version = proc.stdout.strip('\n')
        except SubprocessError as E:
            print(E, file=sys.stderr, end='\n\n')
    if not version:
        version = input(
            "I'm unable to find a usable tag to suffix the release. Which suffix do you want to use? "
            "(Press enter to use 'dev')"
        ) or 'dev'
    # add 'v' in front of version if it's like number.number.number
    if re.fullmatch(r'\d+\.\d+\.\d+', version):
        version = "v" + version
    return version


def check_files(files: dict) -> None:
    for file in files.keys():
        prompt = ''
        if not os.path.exists(file):
            prompt = f'{file} not found.'
        if not os.path.isfile(file):
            prompt = f'{file} is not a regular file.'
        if prompt:
            if not confirm_proceed(f'{prompt} Shall I proceed? (y/n) '):
                sys.exit(1)


def set_zip_path(path, version):
    zip_path = os.path.join(path + '_' + version + '.zip')
    zip_dirname = os.path.dirname(zip_path)
    if not os.path.isdir(zip_dirname):
        try:
            os.mkdir(zip_dirname)
        except FileExistsError:
            print(
                f'{zip_dirname} already exists and is not a directory.\n'
                f'Rename it or choose another path for the release.',
                file=sys.stderr
            )
            sys.exit(1)
    if os.path.isfile(zip_path):
        if not confirm_proceed(
            'Destination for the release already present. Shall I overwrite it? (y/n) '
        ):
            sys.exit(1)
    return zip_path


def set_project_files():
    files = {**PROJECT_FILES, **ADD_TO_RELEASE}
    for f in NOT_RELEASED:
        try:
            del files[f]
        except KeyError:
            pass
    return files


if __name__ == '__main__':
    args = parse_args()
    project_files = set_project_files()
    check_files(project_files)
    release_version = set_version(args.version)
    destination = set_zip_path(args.destination, release_version)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for orig, dest in project_files.items():
            z.write(orig, os.path.join(PROJECT_NAME, dest))
