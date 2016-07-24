# Description

cerbero is a multi-platform build system for Open Source projects that builds
and creates native packages for different platforms, architectures and distributions.

Projects are defined using recipes files (.recipe), which provides a description
of the project being built such as name, version, licenses, sources and the way
it's built. It also provide listing of files, which is later used for the packaging.

Packages are defined using packages files (.package), describing the package name,
version, license, maintainer and other fields used to create the packages. A
package wraps a list of recipes, from which the list of files belonging to the
package will be extracted.

# Minimum Requirements

cerbero provides bootstrapping facilities for all platforms, but it still needs a
minimum base to bootstrap

## Linux

On linux, you will only need a distribution with python >= 2.7

## OSX

On OSX you will need to have install the following software:
  * XCode
  * CMake: http://www.cmake.org/cmake/resources/software.html

## Windows

The initial setup on Windows has a longer initial setup, but you only have to
do this once. Please follow the instructions here **carefully**.

  * Python 2.7: https://www.python.org/downloads/
   * IMPORTANT: Download 64-bit if you're running 64-bit Windows and 32-bit otherwise
   * Install it for all users
   * Don't select pip and don't register extensions
   * Inside `C:\Python27`, rename `python.exe` to `python2.exe`
    * This is needed to avoid a collision with Python 3

  * Python 3.5: https://www.python.org/downloads/
   * IMPORTANT: Download 64-bit if you're running 64-bit Windows and 32-bit otherwise
   * This is needed for building with Meson
   * Select options:
    * `Install launcher for all users`
    * `Add Python 3.5 to PATH`
   * Click `Customize installation`
   * Install at least everything, `for all users`, then Next
   * Advanced Options, `Install for all users`, `Add Python to environment variables`
    * Ensure that the installation directory is `C:\Python35`
    * If you use a different install path, make sure it doesn't have spaces 
   * Run `cmd.exe` as Administrator, `cd C:\Python35` and run `mklink python3.exe python.exe`
    * This creates a symlink from `python3` to `python` which is required because most scripts assume Python 3 is called `python3`

  * CMake: https://cmake.org/download/#latest
   * Select option `Add CMake to the system PATH for all users`
  * WiX 3.5: http://wix.codeplex.com/releases/view/60102
   * Needed for creating MSI installers

  * Git: https://github.com/git-for-windows/git/releases/latest
   * `Use Git from the Windows Command prompt`, next
   * `Checkout as-is, commit as-is`, next
   * `Use MinTTY`, next
   * `Enable file system caching`, install

  * MSYS/MinGW: http://sourceforge.net/projects/mingw/files/Installer/mingw-get-setup.exe/download
   * Install it with all the options enabled

Once the MSYS installation finishes, the MinGW Installation Manager will be
started. You must select only `mingw-developer-toolkit` and `msys-base`, and
then select `Installation > Apply Changes` from the menu. This will install the
MSYS shell and basic build tools such as Perl, Autotools, etc.

  * Visual Studio 2015 Community: http://go.microsoft.com/fwlink/?LinkID=626924&clcid=0x409
   * The only supported version is 2015
    * You can skip this if you already have Visual Studio 2015
   * Default options
   * Make sure to select 'C++' from Programming Languages support

Lastly, exclude `C:\MinGW` from your anti-virus scan list. If you don't do
this, the build will be slowed down massively because your anti-virus will keep
trying to scan all the temporary build files, and might even cause build
failures due to race conditions between the anti-virus locking a file for
scanning and the build system trying to open or delete it.

# Basic Usage

Despite the presence of `setup.py` this tool does not need installation. It is
usually invoked via the cerbero-uninstalled script, which should be invoked as
`./cerbero-uninstalled`, or you can add the cerbero directory in your `PATH`
and invoke it as `cerbero-uninstalled`.

#### Bootstrap

Before using cerbero for the first time, you will need to run the bootstrap
command. This command installs the missing parts of the build system using the
packages manager when available. Note that this can take a while since it
fetches tarballs over the network and then builds recipes using Autotools.

    $ ./cerbero-uninstalled bootstrap

If you want to cross-compile to 32-bit from 64-bit (or vice-versa), you also need
to bootstrap that.

    $ ./cerbero-uninstalled -c config/win32-mixed-msvc.cbc bootstrap

`config/win32-mixed-msvc.cbc` is the configuration that we use for providing
a mixed Autotools-and-MSVC toolchain. With this configuration, Cerbero recipes
that can use MSVC will be built with MSVC and those that can't will use MinGW.

In all the commands below, you should replace `win32-mixed-msvc.cbc` with
`win64-mixed-msvc.cbc` if you want to build for 64-bit.

#### Help

    $ ./cerbero-uninstalled --help

#### List available recipes

    $ ./cerbero-uninstalled list

#### List available packages

    $ ./cerbero-uninstalled list-packages

#### Build a recipe

    $ ./cerbero-uninstalled -c config/win32-mixed-msvc.cbc build gst-plugins-base-1.0

#### Rebuild a single recipe

    $ ./cerbero-uninstalled -c config/win32-mixed-msvc.cbc buildone gst-plugins-base-1.0

#### Clean a recipe

    $ ./cerbero-uninstalled -c config/win32-mixed-msvc.cbc cleanone gst-plugins-base-1.0

#### Create a package (this automatically invokes build)

    # This will build several recipes including gstreamer-1.0, gst-plugins-*-1.0, and more
    $ ./cerbero-uninstalled -c config/win32-mixed-msvc.cbc package gstreamer-1.0

# More Details

The following recipes are currently using Meson and are built with MSVC:

| Recipes using Meson + MSVC |
|---------------------------|
| bzip2.recipe |
| orc.recipe |
| libffi.recipe (only 32-bit) |
| glib.recipe |
| gstreamer-1.0.recipe |
| gst-plugins-base-1.0.recipe |
| gst-plugins-good-1.0.recipe |
| gst-plugins-bad-1.0.recipe |
| gst-plugins-ugly-1.0.recipe |

For more details on how to use Cerbero, especially for things like platform
support, recipe format, generating Visual Studio project files, and so on,
please refer to the [work-in-progress documentation](https://github.com/centricular/cerbero-docs/blob/master/start.md).

# License

cerbero is released under the GNU Lesser General Public License, Version 2.1 (LGPLv2.1)

# Dependencies

 * python >= 2.7
