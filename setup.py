# setup.py
from distutils.core import setup
import py2exe, sys, os

game_includes = ['inputbox']
game_packages = ['MySQLdb']


def main():
    origIsSystemDLL = py2exe.build_exe.isSystemDLL

    def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in ["sdl_ttf.dll"]:
            return 0
        return origIsSystemDLL(pathname)

    py2exe.build_exe.isSystemDLL = isSystemDLL

    setup(windows=['ToD.py'],
          options={
              "py2exe": {
                  "excludes": ["AppKit", "Foundation", "_scproxy", "_sysconfigdata", "dummy.Process", "OpenGL.GL",
                               "Numeric", "copyreg", "numpy", "pkg_resources", "queue", "winreg", "pygame.sdlmain_osx"],
              }
          },
          name='Tides Of Darkness',
          version='0.0.1',
          author='Alex Stevens & Jim Clarke',
          includes=game_includes
          )


if __name__ == '__main__':
    main()
