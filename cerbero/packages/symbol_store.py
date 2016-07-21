# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2016 Nirbheek Chauhan <nirbheek@centricular.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import re
import shutil
import subprocess

from cerbero.errors import FatalError
from cerbero.enums import Architecture
from cerbero.packages import PackageType

# The tools are always run in 32-bit mode, so they're either in
# 'Program Files (x86)' (on 64-bit) or in 'Program Files' (on 32-bit)
PROG_FILE_PATH = ['C:/Program Files (x86)/',
                  'C:/Program Files/']
# FIXME: Add Windows 7 SDK debugger path
WINDBG_PATHS = ['Windows Kits/10/Debuggers/',
                'Windows Kits/8.1/Debuggers/',
                'Windows Kits/8.0/Debuggers/']
# The tool that uploads/stores debug files to a symbol server or store
SYMSTORE = 'symstore.exe'
# The tool used for stripping private symbols from PDB files for uploading to
# the 'public' section of a symbol server or store
PDBCOPY = 'pdbcopy.exe'

WINSDK_DL_PAGE = 'http://go.microsoft.com/fwlink/p?LinkID=271979'

class SymbolStoreProcessor(object):

    def __init__(self, config, package, path):
        self.config = config
        self.package = package
        self.store_path = path
        self._find_windbg_tools()
        self.workdir = os.path.join(self.config.home_dir, 'symbol-store')
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)

    def _find_windbg_tools(self):
        if self.config.target_arch == Architecture.X86:
            windbg_archp = 'x86/'
        elif self.config.target_arch == Architecture.X86_64:
            windbg_archp = 'x64/'
        else:
            raise FatalError("Unsupported target arch '{0}' for Windows Debugging Tools".format(self.config.target_arch))
        for progfp in PROG_FILE_PATH:
            for windbgp in WINDBG_PATHS:
                symstore = progfp + windbgp + windbg_archp + SYMSTORE
                if not os.path.exists(symstore):
                    print(symstore)
                    continue
                self.symstore = symstore
                self.pdbcopy = progfp + windbgp + windbg_archp + PDBCOPY
                if not os.path.exists(self.pdbcopy):
                    raise FatalError("SymStore found but PDBCopy not found?! "
                                     "You might have a corrupt installation!")
                return
        raise FatalError("Windows Debugging tools not found! "
                         "You can download them from " + WINSDK_DL_PAGE)

    def _create_workdir(self, workdir):
        path = os.path.join(self.workdir, workdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        return path

    def create_symbol_files_list(self):
        """
        Copy files with debugging symbols to a working directory
        """
        self.private_symbols_list = os.path.join(self.workdir, 'private.txt')
        with open(self.private_symbols_list, 'w') as flist:
            for f in self.symbol_files:
                flist.write(os.path.join(self.config.prefix, f) + '\n')

    def copy_stripped_private(self):
        """
        Strip private symbols and store in a working directory
        """
        self.public_symbols_dir = self._create_workdir('public')
        procs = {}
        for f in self.symbol_files:
            oldf = os.path.join(self.config.prefix, f)
            newf = os.path.join(self.public_symbols_dir, os.path.basename(f))
            # We don't wait for this to finish, so this will cause several
            # processes to be started in parallel, which is what we want.
            # It speeds this whole thing up quite a bit.
            procs[f] = subprocess.Popen([self.pdbcopy, oldf, newf, '-p'])
        for (f, proc) in procs.items():
            if proc.wait() != 0:
                raise FatalError('Running pdbcopy on {0} failed!'.format(f))

    def process(self, packager, force):
        all_files = packager.files_list(PackageType.DEVEL, True) + \
                    packager.files_list(PackageType.RUNTIME, True)
        # All our debugging information is in .pdb files
        self.symbol_files = [f for f in all_files if f.endswith('.pdb')]
        # Copy symbol files to working directories
        self.create_symbol_files_list()
        self.copy_stripped_private()

    def _check_symstore_success(self, num, output):
        p = '^SYMSTORE: Number of '
        # Check that all the files listed were stored
        if not re.search(p + 'files stored = {0}$'.format(num), output, re.MULTILINE):
            return False
        # No errors
        if not re.search(p + 'errors = 0$', output, re.MULTILINE):
            return False
        # All files were valid and were not ignored
        if not re.search(p + 'files ignored = 0$', output, re.MULTILINE):
            return False
        return True

    def store(self):
        """
        Store the public and private symbols on a local directory or a remote
        symbol server.
        We serialize the storing just in case there's some silly locking
        requirements when pushing to a symbol server.
        """
        # Store PDBs with private symbols (from a list)
        privp = subprocess.Popen([self.symstore, 'add',
                                  '/z', 'pri', '/t', 'book',
                                  '/s', self.store_path + '/private',
                                  '/f', '@' + self.private_symbols_list],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
        (privo, prive) = privp.communicate()
        if not self._check_symstore_success(len(self.symbol_files), privo):
            raise FatalError('Failed while storing private symbol PDBs:\n' + \
                             privo + prive)
        # Store PDBs with public symbols (from a dir, not recursive)
        pubp = subprocess.Popen([self.symstore, 'add',
                                 '/z', 'pub', '/t', 'book',
                                 '/s', self.store_path + '/public',
                                 '/f', self.public_symbols_dir],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
        (pubo, pube) = pubp.communicate()
        # Cleanup
        shutil.rmtree(self.public_symbols_dir)
        if not self._check_symstore_success(len(self.symbol_files), pubo):
            raise FatalError('Failed while storing public symbol PDBs:\n' + \
                             pubo + pube)
