"""
    Driver for PDB2PQR

    This module takes a PDB file as input and performs optimizations
    before yielding a new PDB-style file as output.

    Ported to Python by Todd Dolinsky (todd@ccb.wustl.edu)
    Washington University in St. Louis

    Parsing utilities provided by Nathan A. Baker (Nathan.Baker@pnl.gov)
    Pacific Northwest National Laboratory

    Copyright (c) 2002-2011, Jens Erik Nielsen, University College Dublin;
    Nathan A. Baker, Battelle Memorial Institute, Developed at the Pacific
    Northwest National Laboratory, operated by Battelle Memorial Institute,
    Pacific Northwest Division for the U.S. Department Energy.;
    Paul Czodrowski & Gerhard Klebe, University of Marburg.

	All rights reserved.

	Redistribution and use in source and binary forms, with or without modification,
	are permitted provided that the following conditions are met:

		* Redistributions of source code must retain the above copyright notice,
		  this list of conditions and the following disclaimer.
		* Redistributions in binary form must reproduce the above copyright notice,
		  this list of conditions and the following disclaimer in the documentation
		  and/or other materials provided with the distribution.
        * Neither the names of University College Dublin, Battelle Memorial Institute,
          Pacific Northwest National Laboratory, US Department of Energy, or University
          of Marburg nor the names of its contributors may be used to endorse or promote
          products derived from this software without specific prior written permission.

	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
	ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
	WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
	IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
	INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
	BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
	LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
	OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
	OF THE POSSIBILITY OF SUCH DAMAGE.

"""

__date__  = "5 April 2010"
__author__ = "Todd Dolinsky, Nathan Baker, Jens Nielsen, Paul Czodrowski, Jan Jensen, Samir Unni, Yong Huang"

from optparse import OptionParser, OptionGroup

import time

from .src import utilities
from .src.errors import PDB2PQRError
from .src.hydrogens import *


__version__ = "FIXME"

from . import extensions

def getOldHeader(pdblist):
    oldHeader = StringIO()
    headerTypes = (HEADER, TITLE, COMPND, SOURCE,
                   KEYWDS, EXPDTA, AUTHOR, REVDAT,
                   JRNL, REMARK, SPRSDE, NUMMDL)
    for pdbObj in pdblist:
        if not isinstance(pdbObj,headerTypes):
            break

        oldHeader.write(str(pdbObj))
        oldHeader.write('\n')

    return oldHeader.getvalue()

def printPQRHeader(pdblist,
                   atomlist,
                   reslist,
                   charge,
                   ff,
                   warnings,
                   ph_calc_method,
                   pH,
                   ffout,
                   cl_args,
                   include_old_header = False):
    """
        Print the header for the PQR file

        Parameters:
            atomlist: A list of atoms that were unable to have
                      charges assigned (list)
            reslist:  A list of residues with non-integral charges
                      (list)
            charge:   The total charge on the protein (float)
            ff:       The forcefield name (string)
            warnings: A list of warnings generated from routines (list)
            pH :  pH value, if any. (float)
            ffout :  ff used for naming scheme (string)
            cl_args : the command line argument used when running pdb2pqr (string)
        Returns
            header:   The header for the PQR file (string)
    """
    if ff is None:
        ff = 'User force field'
    else:
        ff = ff.upper()
    header = "REMARK   1 PQR file generated by PDB2PQR (Version %s)\n" % __version__
    header = header + "REMARK   1\n"
    if cl_args is not None:
        header +=     "REMARK   1 Command line used to generate this file:\n"
        header +=     "REMARK   1 " + cl_args + "\n"
        header = header + "REMARK   1\n"
    header = header + "REMARK   1 Forcefield Used: %s\n" % ff
    if not ffout is None:
        header = header + "REMARK   1 Naming Scheme Used: %s\n" % ffout
    header = header + "REMARK   1\n"

    if ph_calc_method is not None:
        header = header + "REMARK   1 pKas calculated by %s and assigned using pH %.2f\n" % (ph_calc_method, pH)
        header = header + "REMARK   1\n"

    for warning in warnings:
        header = header + "REMARK   5 " + warning
    header = header + "REMARK   5\n"

    if len(atomlist) != 0:
        header += "REMARK   5 WARNING: PDB2PQR was unable to assign charges\n"
        header += "REMARK   5          to the following atoms (omitted below):\n"
        for atom in atomlist:
            header += "REMARK   5              %i %s in %s %i\n" % \
                      (atom.get("serial"), atom.get("name"), \
                       atom.get("residue").get("name"), \
                       atom.get("residue").get("resSeq"))
        header += "REMARK   5 This is usually due to the fact that this residue is not\n"
        header += "REMARK   5 an amino acid or nucleic acid; or, there are no parameters\n"
        header += "REMARK   5 available for the specific protonation state of this\n"
        header += "REMARK   5 residue in the selected forcefield.\n"
        header += "REMARK   5\n"
    if len(reslist) != 0:
        header += "REMARK   5 WARNING: Non-integral net charges were found in\n"
        header += "REMARK   5          the following residues:\n"
        for residue in reslist:
            header += "REMARK   5              %s - Residue Charge: %.4f\n" % \
                      (residue, residue.getCharge())
        header += "REMARK   5\n"
    header += "REMARK   6 Total charge on this protein: %.4f e\n" % charge
    header += "REMARK   6\n"

    if include_old_header:
        header += "REMARK   7 Original PDB header follows\n"
        header += "REMARK   7\n"

        header += getOldHeader(pdblist)

    return header

def runPDB2PQR(pdblist, ff,
               outname = "",
               ph = None,
               verbose = False,
               selectedExtensions = [],
               extensionOptions = utilities.ExtraOptions(),
               ph_calc_method = None,
               ph_calc_options = None,
               clean = False,
               neutraln = False,
               neutralc = False,
               ligand = None,
               assign_only = False,
               chain = False,
			   drop_water = False,
               debump = True,
               opt = True,
               typemap = False,
               userff = None,
               usernames = None,
               ffout = None,
               holdList = None,
               commandLine = None,
               include_old_header = False):
    """
        Run the PDB2PQR Suite

        Arguments:
            pdblist: The list of objects that was read from the PDB file
                     given as input (list)
            ff:      The name of the forcefield (string)

        Keyword Arguments:
            outname:       The name of the desired output file
            ph:            The desired ph of the system (float)
            verbose:       When True, script will print information to stdout
                             When False, no detailed information will be printed (float)
            extensions:      List of extensions to run
            extensionOptions:optionParser like option object that is passed to each object.
            ph_calc_method: pKa calculation method ("propka","propka31","pdb2pka")
            ph_calc_options: optionParser like option object for propka30.
            clean:         only return original PDB file in aligned format.
            neutraln:      Make the N-terminus of this protein neutral
            neutralc:      Make the C-terminus of this protein neutral
            ligand:        Calculate the parameters for the ligand in mol2 format at the given path.
            assign_only:   Only assign charges and radii - do not add atoms, debump, or optimize.
            chain:         Keep the chain ID in the output PQR file
            drop_water:    Remove water molecules from output
            debump:        When 1, debump heavy atoms (int)
            opt:           When 1, run hydrogen optimization (int)
            typemap:       Create Typemap output.
            userff:        The user created forcefield file to use. Overrides ff.
            usernames:     The user created names file to use. Required if using userff.
            ffout:         Instead of using the standard canonical naming scheme for residue and atom names,  +
                           use the names from the given forcefield
            commandLine:   command line used (if any) to launch the program. Included in output header.
            include_old_header: Include most of the PDB header in output.
            holdlist:      A list of residues not to be optimized, as [(resid, chain, icode)]
            pdb2pka_params: parameters for running pdb2pka.

        Returns
            header:  The PQR file header (string)
            lines:   The PQR file atoms (list)
            missedligandresidues:  A list of ligand residue names whose charges could
                     not be assigned (ligand)
            protein: The protein object
    """

    pkaname = ""
    lines = []
    Lig = None
    atomcount = 0   # Count the number of ATOM records in pdb

    outroot = utilities.getPQRBaseFileName(outname)

    if ph_calc_method == 'propka':
        pkaname = outroot + ".propka"
        #TODO: What? Shouldn't it be up to propka on how to handle this?
        if os.path.isfile(pkaname):
            os.remove(pkaname)

    start = time.time()

    if verbose:
        print("Beginning PDB2PQR...\n")

    myDefinition = Definition()
    if verbose:
        print("Parsed Amino Acid definition file.")

    if drop_water:
        # Remove the waters
        pdblist_new = []
        for record in pdblist:
            if isinstance(record, (HETATM, ATOM, SIGATM, SEQADV)):
                if record.resName in WAT.water_residue_names:
                    continue
            pdblist_new.append(record)

        pdblist = pdblist_new

    # Check for the presence of a ligand!  This code is taken from pdb2pka/pka.py

    if not ligand is None:
        from pdb2pka.ligandclean import ligff
        myProtein, myDefinition, Lig = ligff.initialize(myDefinition, ligand, pdblist, verbose)
        for atom in myProtein.getAtoms():
            if atom.type == "ATOM":
                atomcount += 1
    else:
        myProtein = Protein(pdblist, myDefinition)

    if verbose:
        print("Created protein object -")
        print("\tNumber of residues in protein: %s" % myProtein.numResidues())
        print("\tNumber of atoms in protein   : %s" % myProtein.numAtoms())

    myRoutines = Routines(myProtein, verbose)

    for residue in myProtein.getResidues():
        multoccupancy = 0
        for atom in residue.getAtoms():
            if atom.altLoc != "":
                multoccupancy = 1
                txt = "Warning: multiple occupancies found: %s in %s\n" % (atom.name, residue)
                sys.stderr.write(txt)
        if multoccupancy == 1:
            myRoutines.warnings.append("WARNING: multiple occupancies found in %s,\n" % (residue))
            myRoutines.warnings.append("         at least one of the instances is being ignored.\n")

    myRoutines.setTermini(neutraln, neutralc)
    myRoutines.updateBonds()

    if clean:
        header = ""
        lines = myProtein.printAtoms(myProtein.getAtoms(), chain)

        # Process the extensions
        for ext in selectedExtensions:
            module = extensions.extDict[ext]
            #TODO: figure out a way to do this without crashing...
            #tempRoutines = copy.deepcopy(myRoutines)
            module.run_extension(myRoutines, outroot, extensionOptions)

        if verbose:
            print("Total time taken: %.2f seconds\n" % (time.time() - start))

        #Be sure to include None for missed ligand residues
        return header, lines, None

    #remove any future need to convert to lower case
    if not ff is None:
        ff = ff.lower()
    if not ffout is None:
        ffout = ffout.lower()

    if not assign_only:
        # It is OK to process ligands with no ATOM records in the pdb
        if atomcount == 0 and Lig != None:
            pass
        else:
            myRoutines.findMissingHeavy()
        myRoutines.updateSSbridges()

        if debump:
            myRoutines.debumpProtein()

        if ph_calc_method == 'propka':
            myRoutines.runPROPKA(ph, ff, outroot, pkaname, ph_calc_options, version=30)
        elif ph_calc_method == 'propka31':
            myRoutines.runPROPKA(ph, ff, outroot, pkaname, ph_calc_options, version=31)
        elif ph_calc_method == 'pdb2pka':
            myRoutines.runPDB2PKA(ph, ff, pdblist, ligand, verbose, ph_calc_options)

        myRoutines.addHydrogens()

        myhydRoutines = hydrogenRoutines(myRoutines)

        if debump:
            myRoutines.debumpProtein()

        if opt:
            myhydRoutines.setOptimizeableHydrogens()
            # TONI fixing residues - myhydRoutines has a reference to myProtein, so i'm altering it in place
            myRoutines.holdResidues(holdList)
            myhydRoutines.initializeFullOptimization()
            myhydRoutines.optimizeHydrogens()
        else:
            myhydRoutines.initializeWaterOptimization()
            myhydRoutines.optimizeHydrogens()

        # Special for GLH/ASH, since both conformations were added
        myhydRoutines.cleanup()


    else:  # Special case for HIS if using assign-only
        for residue in myProtein.getResidues():
            if isinstance(residue, HIS):
                myRoutines.applyPatch("HIP", residue)

    myRoutines.setStates()

    myForcefield = Forcefield(ff, myDefinition, userff, usernames)
    hitlist, misslist = myRoutines.applyForcefield(myForcefield)

    ligsuccess = 0

    if not ligand is None:
        # If this is independent, we can assign charges and radii here
        for residue in myProtein.getResidues():
            if isinstance(residue, LIG):
                templist = []
                Lig.make_up2date(residue)
                for atom in residue.getAtoms():
                    atom.ffcharge = Lig.ligand_props[atom.name]["charge"]
                    atom.radius = Lig.ligand_props[atom.name]["radius"]
                    if atom in misslist:
                        misslist.pop(misslist.index(atom))
                        templist.append(atom)

                charge = residue.getCharge()
                if abs(charge - int(charge)) > 0.001:
                    # Ligand parameterization failed
                    myRoutines.warnings.append("WARNING: PDB2PQR could not successfully parameterize\n")
                    myRoutines.warnings.append("         the desired ligand; it has been left out of\n")
                    myRoutines.warnings.append("         the PQR file.\n")
                    myRoutines.warnings.append("\n")

                    # remove the ligand
                    myProtein.residues.remove(residue)
                    for myChain in myProtein.chains:
                        if residue in myChain.residues: myChain.residues.remove(residue)
                else:
                    ligsuccess = 1
                    # Mark these atoms as hits
                    hitlist = hitlist + templist

    # Temporary fix; if ligand was successful, pull all ligands from misslist
    if ligsuccess:
        templist = misslist[:]
        for atom in templist:
            if isinstance(atom.residue, (Amino, Nucleic)):
                continue
            misslist.remove(atom)

    # Create the Typemap
    if typemap:
        typemapname = "%s-typemap.html" % outroot
        myProtein.createHTMLTypeMap(myDefinition, typemapname)

    # Grab the protein charge
    reslist, charge = myProtein.getCharge()

    # If we want a different naming scheme, use that

    if not ffout is None:
        scheme = ffout
        userff = None # Currently not supported
        if scheme != ff:
            myNameScheme = Forcefield(scheme, myDefinition, userff)
        else:
            myNameScheme = myForcefield
        myRoutines.applyNameScheme(myNameScheme)

    header = printPQRHeader(pdblist, misslist, reslist, charge, ff,
                            myRoutines.getWarnings(), ph_calc_method, ph, ffout, commandLine,
                            include_old_header=include_old_header)
    lines = myProtein.printAtoms(hitlist, chain)

    # Determine if any of the atoms in misslist were ligands
    missedligandresidues = []
    for atom in misslist:
        if isinstance(atom.residue, (Amino, Nucleic)):
            continue
        if atom.resName not in missedligandresidues:
            missedligandresidues.append(atom.resName)

    # Process the extensions
    for ext in selectedExtensions:
        module = extensions.extDict[ext]
        #TODO: figure out a way to do this without crashing...
        #tempRoutines = copy.deepcopy(myRoutines)
        module.run_extension(myRoutines, outroot, extensionOptions)


    if verbose:
        print("Total time taken: %.2f seconds\n" % (time.time() - start))

    return header, lines, missedligandresidues, myProtein


def mainCommand(argv):
    """
        Main driver for running program from the command line.
    """

    fieldNames = ('amber','charmm','parse', 'tyl06','peoepb','swanson')

    validForcefields = []
    validForcefields.extend(fieldNames)
    validForcefields.extend((x.upper() for x in fieldNames))

    description = 'This module takes a PDB file as input and performs ' +\
                  'optimizations before yielding a new PQR-style file in PQR_OUTPUT_PATH.\n' +\
                  'If PDB_PATH is an ID it will automatically be obtained from the PDB archive.'

    usage = 'Usage: %prog [options] PDB_PATH PQR_OUTPUT_PATH'

    parser = OptionParser(description=description, usage=usage, version='%prog (Version ' + __version__ + ')')


    group = OptionGroup(parser,"Manditory options", "One of the following options must be used.")
    group.add_option('--ff', dest='ff', metavar='FIELD_NAME', choices=validForcefields,
                      help='The forcefield to use - currently amber, ' +
                           'charmm, parse, tyl06, peoepb and swanson ' +
                           'are supported.')

    group.add_option('--userff', dest='userff', metavar='USER_FIELD_FILE',
                      help='The user created forcefield file to use. Requires --usernames overrides --ff')

    group.add_option('--clean', dest='clean', action='store_true', default=False,
                      help='Do no optimization, atom addition, or parameter assignment, ' +
                           'just return the original PDB file in aligned format. ' +
                           'Overrides --ff and --userff')
    parser.add_option_group(group)


    group = OptionGroup(parser,"General options")
    group.add_option('--nodebump', dest='debump', action='store_false', default=True,
                      help='Do not perform the debumping operation')

    group.add_option('--noopt', dest='opt', action='store_false', default=True,
                      help='Do not perform hydrogen optimization')

    group.add_option('--chain', dest='chain', action='store_true', default=False,
                      help='Keep the chain ID in the output PQR file')

    group.add_option('--assign-only', dest='assign_only', action='store_true', default=False,
                      help='Only assign charges and radii - do not add atoms, debump, or optimize.')

    group.add_option('--ffout', dest='ffout', metavar='FIELD_NAME',choices=validForcefields,
                      help='Instead of using the standard canonical naming scheme for residue and atom names, ' +
                           'use the names from the given forcefield - currently amber, ' +
                           'charmm, parse, tyl06, peoepb and swanson are supported.')

    group.add_option('--usernames', dest='usernames', metavar='USER_NAME_FILE',
                      help='The user created names file to use. Required if using --userff')

    group.add_option('--apbs-input', dest='input', action='store_true', default=False,
                      help='Create a template APBS input file based on the generated PQR file.  Also creates a Python ' +
                           'pickle for using these parameters in other programs.')

    group.add_option('--ligand', dest='ligand',  metavar='PATH',
                      help='Calculate the parameters for the ligand in mol2 format at the given path. ' +
                           'Pdb2pka must be compiled.')

    group.add_option('--whitespace', dest='whitespace', action='store_true', default=False,
                      help='Insert whitespaces between atom name and residue name, between x and y, and between y and z.')

    group.add_option('--typemap', dest='typemap', action='store_true', default=False,
                      help='Create Typemap output.')

    group.add_option('--neutraln', dest='neutraln', action='store_true', default=False,
                      help='Make the N-terminus of this protein neutral (default is charged). '
                           'Requires PARSE force field.')

    group.add_option('--neutralc', dest='neutralc', action='store_true', default=False,
                      help='Make the C-terminus of this protein neutral (default is charged). '
                           'Requires PARSE force field.')

    group.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
                      help='Print information to stdout.')

    group.add_option('--drop-water', dest='drop_water', action='store_true', default=False,
                      help='Drop waters before processing protein. Currently recognized and deleted are the following water types:  %s' % ', '.join(WAT.water_residue_names))

    group.add_option('--include-header', dest='include_header', action='store_true', default=False,
                      help='Include pdb header in pqr file. '
                           'WARNING: The resulting PQR file will not work with APBS versions prior to 1.5')
    parser.add_option_group(group)

    pka_group = OptionGroup(parser,"pH options")

    pka_group.add_option('--ph-calc-method', dest='ph_calc_method', metavar='PH_METHOD', choices=('propka', 'propka31', 'pdb2pka'),
                      help='Method used to calculate ph values. If a pH calculation method is selected, for each'
                      ' titratable residue pH values will be calculated and the residue potentially modified'
                      ' after comparison with the pH value supplied by --with_ph. Valid options are: '
                      'propka - Use PROPKA to calculate pH values. Actual PROPKA results will be output to <output-path>.propka.\n'
                      'propka31 - Use PROPKA 3.1 to calculate pH values. Actual PROPKA results will be output to <output-path>.propka.\n'
                      'pdb2pka - (EXPERIMENTAL) Use PDB2PKA to calculate pH values. Requires the use of the PARSE force field.'
                      ' Warning: Larger residues can take a very long time to run using this method. ')

    pka_group.add_option('--with-ph', dest='ph', action='store', type='float', default=7.0,
                      help='pH values to use when applying the results of the selected pH calculation method.'
                      ' Defaults to %default')

    parser.add_option_group(pka_group)

    pdb2pka_group = OptionGroup(parser,"PDB2PKA method options")

    pdb2pka_group.add_option('--pdb2pka-out', dest='pdb2pka_out', action='store', default='pdb2pka_output',
                             help='Output directory for PDB2PKA results. Defaults to %default')
    pdb2pka_group.add_option('--pdb2pka-resume', dest='pdb2pka_resume', action="store_true", default=False,
                             help='Resume run from state saved in output directory.')

    pdb2pka_group.add_option('--pdie', dest='pdb2pka_pdie', default=8,type='int',
                             help='Protein dielectric constant. Defaults to %default')
    pdb2pka_group.add_option('--sdie', dest='pdb2pka_sdie', default=80, type='int',
                             help='Solvent dielectric constant. Defaults to %default')

#     pdb2pka_group.add_option('--maps', dest='maps', default=None, type='int',
#                              help='<1 for using provided 3D maps; 2 for genereting new maps>')
#     pdb2pka_group.add_option('--xdiel', dest='xdiel', default=None, type='str',
#                              help='<xdiel maps>')
#     pdb2pka_group.add_option('--ydiel', dest='ydiel', default=None, type='str',
#                              help='<ydiel maps>')
#     pdb2pka_group.add_option('--zdiel', dest='zdiel', default=None, type='str',
#                              help='<zdiel maps>')
#     pdb2pka_group.add_option('--kappa', dest='kappa', default=None, type='str',
#                              help='<ion-accessibility map>')
#     pdb2pka_group.add_option('--smooth', dest='sd', default=None, type='float',
#                              help='<st.dev [A] of Gaussian smooting of 3D maps at the boundary, bandthwith=3 st.dev>')
    #
    # Cut off energy for calculating non-charged-charged interaction energies
    #
    pdb2pka_group.add_option('--pairene',dest='pdb2pka_pairene',type='float',default=1.0,
                      help='Cutoff energy in kT for calculating non charged-charged interaction energies. Default: %default')

    parser.add_option_group(pdb2pka_group)

    propka_group = OptionGroup(parser,"PROPKA method options")

    propka_group.add_option("--propka-reference", dest="propka_reference", default="neutral", choices=('neutral','low-pH'),
           help="Setting which reference to use for stability calculations. See PROPKA 3.0 documentation.")

    propka_group.add_option('--propka-verbose', dest='propka_verbose', action='store_true', default=False,
                      help='Print extra proPKA information to stdout. '
                           'WARNING: This produces an incredible amount of output.')

    parser.add_option_group(propka_group)


    extensions.setupExtensionsOptions(parser)

    (options, args) = parser.parse_args(argv[1:])

    commandLine = ' '.join(argv[1:])

    if len(args) != 2:
        parser.error('Incorrect number (%d) of arguments!\nargs: %s' % (len(args), args))

    if options.assign_only or options.clean:
        options.debump = options.optflag = False

    userfffile = None
    usernamesfile = None

    if not options.clean:
        if not options.usernames is None:
            try:
                usernamesfile = open(options.usernames, 'rU')
            except IOError:
                parser.error('Unable to open user names file %s' % options.usernames)

        if not options.userff is None:
            try:
                userfffile = open(options.userff, 'rU')
            except IOError:
                parser.error('Unable to open user force field file %s' % options.userff)

            if options.usernames is None:
                parser.error('--usernames must be specified if using --userff')

        else:
            if options.ff is None:
                parser.error('One of the manditory options was not specified.\n' +
                             'Please specify either --ff, --userff, or --clean')

            if getFFfile(options.ff) == '':
                parser.error('Unable to find parameter files for forcefield %s!' % options.ff)

    if options.ph < 0.0 or options.ph > 14.0:
        parser.error('%i is not a valid pH!  Please choose a pH between 0.0 and 14.0.' % options.pH)

    ph_calc_options = None
    if options.ph_calc_method == 'propka':
        ph_calc_options = utilities.createPropkaOptions(options.ph,
                                                   verbose=options.propka_verbose,
                                                   reference=options.propka_reference)
    elif options.ph_calc_method == 'propka31':
        import propka.lib
        ph_calc_options, _ = propka.lib.loadOptions('--quiet')
    elif options.ph_calc_method == 'pdb2pka':
        if options.ff.lower() != 'parse':
            parser.error('PDB2PKA requires the PARSE force field.')
        ph_calc_options = {'output_dir': options.pdb2pka_out,
                          'clean_output': not options.pdb2pka_resume,
                          'pdie': options.pdb2pka_pdie,
                          'sdie': options.pdb2pka_sdie,
                          'pairene': options.pdb2pka_pairene}

    if options.ligand is not None:
        try:
            options.ligand = open(options.ligand, 'rU')
        except IOError:
            parser.error('Unable to find ligand file %s!' % options.ligand)

    if options.neutraln and (options.ff is None or options.ff.lower() != 'parse'):
        parser.error('--neutraln option only works with PARSE forcefield!')

    if options.neutralc and (options.ff is None or options.ff.lower() != 'parse'):
        parser.error('--neutralc option only works with PARSE forcefield!')

    text =  """
--------------------------
PDB2PQR - a Python-based structural conversion utility
--------------------------
Please cite your use of PDB2PQR as:
  Dolinsky TJ, Nielsen JE, McCammon JA, Baker NA.
  PDB2PQR: an automated pipeline for the setup, execution,
  and analysis of Poisson-Boltzmann electrostatics calculations.
  Nucleic Acids Research 32 W665-W667 (2004).

"""
    sys.stdout.write(text)

    path = args[0]
    pdbFile = getPDBFile(path)
    pdblist, errlist = readPDB(pdbFile)

    if len(pdblist) == 0 and len(errlist) == 0:
        parser.error("Unable to find file %s!" % path)

    if len(errlist) != 0 and options.verbose:
        print("Warning: %s is a non-standard PDB file.\n" % path)
        print(errlist)

    outpath = args[1]
    options.outname = outpath

    #In case no extensions were specified or no extensions exist.
    if not hasattr(options, 'active_extensions' ) or options.active_extensions is None:
        options.active_extensions = []

    #I see no point in hiding options from extensions.
    extensionOpts = options

    #TODO: The ideal would be to pass a file like object for the second
    # argument and add a third for names then
    # get rid of the userff and username arguments to this function.
    # This would also do away with the redundent checks and such in
    # the Forcefield constructor.
    try:
        header, lines, missedligands, _ = runPDB2PQR(pdblist,
                                                  options.ff,
                                                  outname = options.outname,
                                                  ph = options.ph,
                                                  verbose = options.verbose,
                                                  selectedExtensions = options.active_extensions,
                                                  ph_calc_method = options.ph_calc_method,
                                                  ph_calc_options = ph_calc_options,
                                                  extensionOptions = extensionOpts,
                                                  clean = options.clean,
                                                  neutraln = options.neutraln,
                                                  neutralc = options.neutralc,
                                                  ligand = options.ligand,
                                                  assign_only = options.assign_only,
                                                  chain = options.chain,
                                                  drop_water = options.drop_water,
                                                  debump = options.debump,
                                                  opt = options.opt,
                                                  typemap = options.typemap,
                                                  userff = userfffile,
                                                  usernames = usernamesfile,
                                                  ffout = options.ffout,
                                                  commandLine = commandLine,
                                                  include_old_header = options.include_header)
    except PDB2PQRError as er:
        print(er)
        sys.exit(2)

    # Print the PQR file
    outfile = open(outpath,"w")
    outfile.write(header)
    # Adding whitespaces if --whitespace is in the options
    for line in lines:
        if options.whitespace:
            if line[0:4] == 'ATOM':
                newline = line[0:6] + ' ' + line[6:16] + ' ' + line[16:38] + ' ' + line[38:46] + ' ' + line[46:]
                outfile.write(newline)
            elif line[0:6] == 'HETATM':
                newline = line[0:6] + ' ' + line[6:16] + ' ' + line[16:38] + ' ' + line[38:46] + ' ' + line[46:]
                outfile.write(newline)
        else:
            outfile.write(line)
    outfile.close()

    if options.input:
        from src import inputgen
        from src import psize
        method = "mg-auto"
        size = psize.Psize()
        size.parseInput(outpath)
        size.runPsize(outpath)
        async = 0 # No async files here!
        input = inputgen.Input(outpath, size, method, async, potdx=True)
        input.printInputFiles()
        input.dumpPickle()


if __name__ == "__main__":
    mainCommand(sys.argv)
