from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
import os

class build_py(build_py):
   def byte_compile(self, files):
       super(build_py, self).byte_compile(files)
       for file in files:
           if file.endswith('.py'):
               tmp = os.path.split(file)
               if tmp[0]=="build/lib/pdb2pqr" and not tmp[1] in ['__init__.py','main.py']:
                   print(file + "<--- DELETED")
                   os.unlink(file)

setup(name='pdb2pqr',
      version='2.1.2a1',
      url='http://www.poissonboltzmann.org/',
      packages=['pdb2pqr',
                             'pdb2pqr.src',
                             'pdb2pqr.pdb2pka',
                             'pdb2pqr.propka30',
                             'pdb2pqr.extensions'
                             ],
      package_data={'pdb2pqr': ['dat/*']},
      cmdclass = dict(build_py=build_py),
      scripts = ["pdb2pqr_cli"]
      )

