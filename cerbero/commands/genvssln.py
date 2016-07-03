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

from cerbero.build import build
from cerbero.enums import Platform
from cerbero.commands import Command, register_command
from cerbero.utils import _, N_, shell, ArgparseArgument
from cerbero.utils import messages as m
from cerbero.build.cookbook import CookBook
from cerbero.errors import UsageError


class GenVSSolution(Command):
    doc = N_('Generate a Visual Studio Solution for the specified recipe using Meson')
    name = 'genvssln'

    def __init__(self):
        Command.__init__(self,
            [ArgparseArgument('recipe', nargs=1,
                help=_('recipe to generate solution for')),
            ArgparseArgument('-s', '--source-dir', default=None,
                help=_('source tree to use for generating the solution '
                       '(default: cerbero )')),
             ArgparseArgument('--open', default=False, action='store_true',
                 help=_('open the solution in Visual Studio when done '
                        '(default: print the path to the console)')),
            ])

    def run(self, config, args):
        self.runargs(config, args.recipe[0], args.source_dir, args.open)

    def runargs(self, config, recipe, src_dir, open_after):
        m.message(_('Generating VS solution for ' + recipe))
        # Get the recipe object from the cookbook (the recipe list)
        cookbook = CookBook(config)
        recipe = cookbook.get_recipe(recipe)
        # Check if the recipe uses Meson
        if not isinstance(recipe, build.Meson):
            raise UsageError('recipe does not support building with MSVC')
        # Compute the output directory
        if not src_dir:
            # Poorly-named attribute on the recipe
            src_dir = recipe.build_dir
        if not os.path.exists(src_dir):
            raise UsageError('Source directory "{0}" does not exist'.format(src_dir))
        output_dir = os.path.join(src_dir, "vs-build-dir")
        # Generate the solution
        self.create_vs_solution(recipe, output_dir)
        m.message('VS Solution was created in ' + os.path.abspath(output_dir))
        if open_after and config.platform == Platform.WINDOWS:
            shell.check_call(['explorer', '/root,' + output_dir.replace('/', '\\')])

    def create_vs_solution(self, recipe, output_dir):
        # XXX: Hard-coded vs2015 because we only support that right now
        recipe.meson_backend = 'vs2015'
        recipe.make_dir = output_dir
        # Append the includedir to CPPFLAGS so that Meson adds it to
        # AdditionalIncludeDirectories. This is needed because the Cerbero
        # environment is not available when Visual Studio runs, so our custom
        # `INCLUDE` env variable isn't available for cl.exe to look for headers.
        includedir = os.path.join(recipe.config.prefix, 'include')
        recipe.append_env['CPPFLAGS'] = '-I' + includedir
        recipe.configure()


register_command(GenVSSolution)
