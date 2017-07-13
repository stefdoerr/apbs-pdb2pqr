Fixups to PDB2PQR for HTMD
============

This fork contains a patched version of pdb2pqr for use with HTMD.
The main changes are compatibility with Python 3, ability to use
PROPKA 3.1 instead of 3.0, use of relative imports, returning of
molecular structures as Python objects, plus occasional fixes.

The parts related to the web interface and SCons have been removed.
Other parts may be untested.

This repo is converted into a conda package by the
https://github.com/Acellera/conda-pdb2pqr repository, and uploaded to
Acellera's conda channel. Releases are named adding the local suffix
`+htmd.N` to the upstream version number.


Original README
============

Welcome to the home for the [APBS and PDB2PQR software](http://www.poissonboltzmann.org)!.  

Binary releases can be found here:
* [GitHub](https://github.com/Electrostatics/apbs-pdb2pqr/releases)
* [SourceForge](https://sourceforge.net/projects/apbs/). 

Souce code build instructions are here:
* [APBS](https://github.com/Electrostatics/apbs-pdb2pqr/blob/master/apbs/README.md).
* [pdb2pqr](https://github.com/Electrostatics/apbs-pdb2pqr/blob/master/pdb2pqr/README.md)

Support:
* [Mailing lists](http://www.poissonboltzmann.org/support/home/)
* [chat](https://gitter.im/Electrostatics/help)


