#!/usr/bin/env python3

# Copyright 2013 The Servo Project Developers.
# Copyright 2017 zerolib Developers.
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

from glob import glob
import gzip
import itertools
import locale
import os
from os import path
import contextlib

import sys
import tarfile

from argparse import ArgumentParser


@contextlib.contextmanager
def cd(new_path):
    """Context manager for changing the current working directory"""
    previous_path = os.getcwd()
    try:
        os.chdir(new_path)
        yield
    finally:
        os.chdir(previous_path)


@contextlib.contextmanager
def setlocale(name):
    """Context manager for changing the current locale"""
    saved_locale = locale.setlocale(locale.LC_ALL)
    try:
        yield locale.setlocale(locale.LC_ALL, name)
    finally:
        locale.setlocale(locale.LC_ALL, saved_locale)


def archive_deterministically(dir_to_archive, dest_archive, prepend_path=None):
    """Create a .tar.gz archive in a deterministic (reproducible) manner.

    See https://reproducible-builds.org/docs/archives/ for more details."""

    def reset(tarinfo):
        """Helper to reset owner/group and modification time for tar entries"""
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        tarinfo.mtime = 0
        return tarinfo

    dest_archive = os.path.abspath(dest_archive)
    with cd(dir_to_archive):
        current_dir = "."
        file_list = [current_dir]
        for root, dirs, files in os.walk(current_dir):
            for name in itertools.chain(dirs, files):
                file_list.append(os.path.join(root, name))

        # Sort file entries with the fixed locale
        with setlocale('C'):
            file_list.sort(key=locale.strxfrm)

        # Use a temporary file and atomic rename to avoid partially-formed
        # packaging (in case of exceptional situations like running out of disk space).
        # TODO do this in a temporary folder after #11983 is fixed
        temp_file = '{}.temp~'.format(dest_archive)
        with os.fdopen(os.open(temp_file, os.O_WRONLY | os.O_CREAT, 0o644), 'wb') as out_file:
            with gzip.GzipFile('wb', fileobj=out_file, mtime=0) as gzip_file:
                with tarfile.open(fileobj=gzip_file, mode='w:') as tar_file:
                    for entry in file_list:
                        arcname = entry
                        if prepend_path is not None:
                            arcname = os.path.normpath(os.path.join(prepend_path, arcname))
                        tar_file.add(entry, filter=reset, recursive=False, arcname=arcname)
        os.rename(temp_file, dest_archive)


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--dir', help='directory to archive')
    parser.add_argument('-o', '--out', help='archive destination')
    parser.add_argument('-p', '--prepend', help='prepend path')

    args = parser.parse_args()

    if not args.dir or not args.out:
        error = 'You should provide a directory to archive, ' + \
                'and the archive file name, ' + \
                'not %s' % repr((args.dir, args.out))
        raise ValueError(error)

    archive_deterministically(args.dir, args.out, args.prepend)


if __name__ == '__main__':
    main()
