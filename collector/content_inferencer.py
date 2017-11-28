#!/usr/bin/env python3.4
#
# @file    content_inferencer.py
# @brief   Simple guesser for repository content_type values.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Code to normalize language names.
# List came from our first database approach to cataloging github repos.
lang_names = {
    # Lang name: is it for code?}
    "ABAP"                           : True,
    "ABC"                            : True,
    "AGS Script"                     : True,
    "AMPL"                           : True,
    "ANTLR"                          : True,
    "API Blueprint"                  : True,
    "APL"                            : True,
    "ASP"                            : True,
    "ATLAS"                          : True,
    "ATS"                            : True,
    "ActionScript"                   : True,
    "Ada"                            : True,
    "Agda"                           : True,
    "AgilentVEE"                     : True,
    "Algol"                          : True,
    "Alice"                          : True,
    "Alloy"                          : True,
    "Angelscript"                    : True,
    "Ant Build System"               : True,
    "ApacheConf"                     : True,
    "Apex"                           : True,
    "AppleScript"                    : True,
    "Arc"                            : True,
    "Arduino"                        : True,
    "AsciiDoc"                       : False,
    "AspectJ"                        : True,
    "Assembly"                       : True,
    "Augeas"                         : True,
    "AutoHotkey"                     : True,
    "AutoIt"                         : True,
    "AutoLISP"                       : True,
    "Automator"                      : True,
    "Avenue"                         : True,
    "Awk"                            : True,
    "BASIC"                          : True,
    "BCPL"                           : True,
    "BETA"                           : True,
    "Bash"                           : True,
    "Batchfile"                      : True,
    "BeanShell"                      : True,
    "Befunge"                        : True,
    "Bison"                          : True,
    "BitBake"                        : True,
    "BlitzBasic"                     : True,
    "BlitzMax"                       : True,
    "Bluespec"                       : True,
    "Boo"                            : True,
    "BourneShell"                    : True,
    "Brainfuck"                      : True,
    "Brightscript"                   : True,
    "Bro"                            : True,
    "C"                              : True,
    "C#"                             : True,
    "C++"                            : True,
    "C-ObjDump"                      : True,
    "C2hs Haskell"                   : True,
    "CFML"                           : True,
    "CHILL"                          : True,
    "CIL"                            : True,
    "CLIPS"                          : True,
    "CLU"                            : True,
    "CMake"                          : True,
    "COBOL"                          : True,
    "COMAL"                          : True,
    "COmega"                         : True,
    "CPL"                            : True,
    "CSS"                            : True,
    "CShell"                         : True,
    "Caml"                           : True,
    "Cap&#39;n Proto"                : True,
    "Cap'n Proto"                    : True,
    "CartoCSS"                       : True,
    "Ceylon"                         : True,
    "Ch"                             : True,
    "Chapel"                         : True,
    "Charity"                        : True,
    "Chef"                           : True,
    "ChucK"                          : True,
    "Cirru"                          : True,
    "Clarion"                        : True,
    "Clean"                          : True,
    "Clipper"                        : True,
    "Clojure"                        : True,
    "Cobra"                          : True,
    "CoffeeScript"                   : True,
    "ColdFusion CFC"                 : True,
    "ColdFusion"                     : True,
    "Common Lisp"                    : True,
    "Component Pascal"               : True,
    "Cool"                           : True,
    "Coq"                            : True,
    "Cpp-ObjDump"                    : True,
    "Creole"                         : True,
    "Crystal"                        : True,
    "Cucumber"                       : True,
    "Cuda"                           : True,
    "Curl"                           : True,
    "Cycript"                        : True,
    "Cython"                         : True,
    "D"                              : True,
    "D-ObjDump"                      : True,
    "DCL"                            : True,
    "DCPU-16 ASM"                    : True,
    "DCPU16ASM"                      : True,
    "DIGITAL Command Language"       : True,
    "DM"                             : True,
    "DNS Zone"                       : True,
    "DOT"                            : True,
    "DTrace"                         : True,
    "Darcs Patch"                    : True,
    "Dart"                           : True,
    "Delphi"                         : True,
    "DiBOL"                          : True,
    "Diff"                           : True,
    "Dockerfile"                     : True,
    "Dogescript"                     : True,
    "Dylan"                          : True,
    "E"                              : True,
    "ECL"                            : True,
    "ECLiPSe"                        : True,
    "ECMAScript"                     : True,
    "EGL"                            : True,
    "EPL"                            : True,
    "EXEC"                           : True,
    "Eagle"                          : True,
    "Ecere Projects"                 : True,
    "Ecl"                            : True,
    "Eiffel"                         : True,
    "Elixir"                         : True,
    "Elm"                            : True,
    "Emacs Lisp"                     : True,
    "EmberScript"                    : True,
    "Erlang"                         : True,
    "Escher"                         : True,
    "Etoys"                          : True,
    "Euclid"                         : True,
    "Euphoria"                       : True,
    "F#"                             : True,
    "FLUX"                           : True,
    "FORTRAN"                        : True,
    "Factor"                         : True,
    "Falcon"                         : True,
    "Fancy"                          : True,
    "Fantom"                         : True,
    "Felix"                          : True,
    "Filterscript"                   : True,
    "Formatted"                      : False,
    "Forth"                          : True,
    "Fortress"                       : True,
    "FourthDimension 4D"             : True,
    "FreeMarker"                     : True,
    "Frege"                          : True,
    "G-code"                         : True,
    "GAMS"                           : True,
    "GAP"                            : True,
    "GAS"                            : True,
    "GDScript"                       : True,
    "GLSL"                           : True,
    "GNU Octave"                     : True,
    "Gambas"                         : True,
    "Game Maker Language"            : True,
    "Genshi"                         : True,
    "Gentoo Ebuild"                  : True,
    "Gentoo Eclass"                  : True,
    "Gettext Catalog"                : True,
    "Glyph"                          : True,
    "Gnuplot"                        : True,
    "Go"                             : True,
    "Golo"                           : True,
    "GoogleAppsScript"               : True,
    "Gosu"                           : True,
    "Grace"                          : True,
    "Gradle"                         : True,
    "Grammatical Framework"          : False,
    "Graph Modeling Language"        : True,
    "Graphviz DOT"                   : True,
    "Groff"                          : False,
    "Groovy Server Pages"            : True,
    "Groovy"                         : True,
    "HCL"                            : True,
    "HPL"                            : True,
    "HTML"                           : False,
    "HTML+Django"                    : True,
    "HTML+EEX"                       : True,
    "HTML+ERB"                       : True,
    "HTML+PHP"                       : True,
    "HTTP"                           : True,
    "Hack"                           : True,
    "Haml"                           : True,
    "Handlebars"                     : True,
    "Harbour"                        : True,
    "Haskell"                        : True,
    "Haxe"                           : True,
    "Heron"                          : True,
    "Hy"                             : True,
    "HyPhy"                          : True,
    "HyperTalk"                      : True,
    "IDL"                            : True,
    "IGOR Pro"                       : True,
    "INI"                            : True,
    "INTERCAL"                       : True,
    "IRC log"                        : True,
    "Icon"                           : True,
    "Idris"                          : True,
    "Inform 7"                       : True,
    "Inform"                         : True,
    "Informix 4GL"                   : True,
    "Inno Setup"                     : True,
    "Io"                             : True,
    "Ioke"                           : True,
    "Isabelle ROOT"                  : True,
    "Isabelle"                       : True,
    "J"                              : True,
    "J#"                             : True,
    "JADE"                           : True,
    "JFlex"                          : True,
    "JSON"                           : False,
    "JSON5"                          : False,
    "JSONLD"                         : False,
    "JSONiq"                         : False,
    "JSX"                            : True,
    "JScript"                        : True,
    "JScript.NET"                    : True,
    "Jade"                           : True,
    "Jasmin"                         : True,
    "Java Server Pages"              : True,
    "Java"                           : True,
    "JavaFXScript"                   : True,
    "JavaScript"                     : True,
    "Julia"                          : True,
    "Jupyter Notebook"               : False,
    "KRL"                            : True,
    "KiCad"                          : True,
    "Kit"                            : True,
    "KornShell"                      : True,
    "Kotlin"                         : True,
    "LFE"                            : True,
    "LLVM"                           : True,
    "LOLCODE"                        : True,
    "LPC"                            : True,
    "LSL"                            : True,
    "LaTeX"                          : False,
    "LabVIEW"                        : True,
    "LadderLogic"                    : True,
    "Lasso"                          : True,
    "Latte"                          : True,
    "Lean"                           : True,
    "Less"                           : True,
    "Lex"                            : True,
    "LilyPond"                       : True,
    "Limbo"                          : True,
    "Lingo"                          : True,
    "Linker Script"                  : True,
    "Linux Kernel Module"            : True,
    "Liquid"                         : True,
    "Lisp"                           : True,
    "Literate Agda"                  : True,
    "Literate CoffeeScript"          : True,
    "Literate Haskell"               : True,
    "LiveScript"                     : True,
    "Logo"                           : True,
    "Logos"                          : True,
    "Logtalk"                        : True,
    "LookML"                         : True,
    "LoomScript"                     : True,
    "LotusScript"                    : True,
    "Lua"                            : True,
    "Lucid"                          : True,
    "Lustre"                         : True,
    "M"                              : True,
    "M4"                             : True,
    "MAD"                            : True,
    "MANTIS"                         : True,
    "MAXScript"                      : True,
    "MDL"                            : True,
    "MEL"                            : True,
    "ML"                             : True,
    "MOO"                            : True,
    "MSDOSBatch"                     : True,
    "MTML"                           : True,
    "MUF"                            : True,
    "MUMPS"                          : True,
    "Magic"                          : True,
    "Magik"                          : True,
    "Makefile"                       : True,
    "Mako"                           : True,
    "Malbolge"                       : True,
    "Maple"                          : True,
    "Markdown"                       : False,
    "Mask"                           : True,
    "Mathematica"                    : True,
    "Matlab"                         : True,
    "Maven POM"                      : True,
    "Max"                            : True,
    "MaxMSP"                         : True,
    "MediaWiki"                      : True,
    "Mercury"                        : True,
    "Metal"                          : True,
    "MiniD"                          : True,
    "Mirah"                          : True,
    "Miva"                           : True,
    "Modelica"                       : True,
    "Modula-2"                       : True,
    "Modula-3"                       : True,
    "Module Management System"       : True,
    "Monkey"                         : True,
    "Moocode"                        : True,
    "MoonScript"                     : True,
    "Moto"                           : True,
    "Myghty"                         : True,
    "NATURAL"                        : True,
    "NCL"                            : True,
    "NL"                             : True,
    "NQC"                            : True,
    "NSIS"                           : True,
    "NXTG"                           : True,
    "Nemerle"                        : True,
    "NetLinx"                        : True,
    "NetLinx+ERB"                    : True,
    "NetLogo"                        : True,
    "NewLisp"                        : True,
    "Nginx"                          : True,
    "Nimrod"                         : True,
    "Ninja"                          : True,
    "Nit"                            : True,
    "Nix"                            : True,
    "Nu"                             : True,
    "NumPy"                          : True,
    "OCaml"                          : True,
    "OPL"                            : True,
    "Oberon"                         : True,
    "ObjDump"                        : True,
    "Object Rexx"                    : True,
    "Objective-C"                    : True,
    "Objective-C++"                  : True,
    "Objective-J"                    : True,
    "Occam"                          : True,
    "Omgrofl"                        : True,
    "Opa"                            : True,
    "Opal"                           : True,
    "OpenCL"                         : True,
    "OpenEdge ABL"                   : True,
    "OpenEdgeABL"                    : True,
    "OpenSCAD"                       : True,
    "Org"                            : True,
    "Ox"                             : True,
    "Oxygene"                        : True,
    "Oz"                             : True,
    "PAWN"                           : True,
    "PHP"                            : True,
    "PILOT"                          : True,
    "PLI"                            : True,
    "PLSQL"                          : True,
    "PLpgSQL"                        : True,
    "POVRay"                         : True,
    "Pan"                            : True,
    "Papyrus"                        : True,
    "Paradox"                        : True,
    "Parrot Assembly"                : True,
    "Parrot Internal Representation" : True,
    "Parrot"                         : True,
    "Pascal"                         : True,
    "Perl"                           : True,
    "Perl6"                          : True,
    "PicoLisp"                       : True,
    "PigLatin"                       : True,
    "Pike"                           : True,
    "Pliant"                         : True,
    "Pod"                            : False,
    "PogoScript"                     : True,
    "PostScript"                     : False,
    "PowerBasic"                     : True,
    "PowerScript"                    : True,
    "PowerShell"                     : True,
    "Processing"                     : True,
    "Prolog"                         : True,
    "Propeller Spin"                 : True,
    "Protocol Buffer"                : True,
    "Public Key"                     : False,
    "Puppet"                         : True,
    "Pure Data"                      : True,
    "PureBasic"                      : True,
    "PureData"                       : True,
    "PureScript"                     : True,
    "Python traceback"               : True,
    "Python"                         : True,
    "Q"                              : True,
    "QML"                            : True,
    "QMake"                          : True,
    "R"                              : True,
    "RAML"                           : True,
    "RDoc"                           : False,
    "REALbasic"                      : True,
    "REALbasicDuplicate"             : True,
    "REBOL"                          : True,
    "REXX"                           : True,
    "RHTML"                          : True,
    "RMarkdown"                      : True,
    "RPGOS400"                       : True,
    "Racket"                         : True,
    "Ragel in Ruby Host"             : True,
    "Ratfor"                         : True,
    "Raw token data"                 : True,
    "Rebol"                          : True,
    "Red"                            : True,
    "Redcode"                        : True,
    "RenderScript"                   : True,
    "Revolution"                     : True,
    "RobotFramework"                 : True,
    "Rouge"                          : True,
    "Ruby"                           : True,
    "Rust"                           : True,
    "S"                              : True,
    "SAS"                            : True,
    "SCSS"                           : True,
    "SIGNAL"                         : True,
    "SMT"                            : True,
    "SPARK"                          : True,
    "SPARQL"                         : True,
    "SPLUS"                          : True,
    "SPSS"                           : True,
    "SQF"                            : True,
    "SQL"                            : True,
    "SQLPL"                          : True,
    "SQR"                            : True,
    "STON"                           : True,
    "SVG"                            : False,
    "Sage"                           : True,
    "SaltStack"                      : True,
    "Sass"                           : True,
    "Sather"                         : True,
    "Scala"                          : True,
    "Scaml"                          : True,
    "Scheme"                         : True,
    "Scilab"                         : True,
    "Scratch"                        : True,
    "Seed7"                          : True,
    "Self"                           : True,
    "Shell"                          : True,
    "ShellSession"                   : True,
    "Shen"                           : True,
    "Simula"                         : True,
    "Simulink"                       : True,
    "Slash"                          : True,
    "Slate"                          : True,
    "Slim"                           : True,
    "Smali"                          : True,
    "Smalltalk"                      : True,
    "Smarty"                         : True,
    "SourcePawn"                     : True,
    "Squeak"                         : True,
    "Squirrel"                       : True,
    "Standard ML"                    : True,
    "Stata"                          : True,
    "Stylus"                         : True,
    "Suneido"                        : True,
    "SuperCollider"                  : True,
    "Swift"                          : True,
    "SystemVerilog"                  : True,
    "TACL"                           : True,
    "TOM"                            : True,
    "TOML"                           : True,
    "TXL"                            : True,
    "Tcl"                            : True,
    "Tcsh"                           : True,
    "TeX"                            : False,
    "Tea"                            : True,
    "Text"                           : True,
    "Textile"                        : False,
    "Thrift"                         : True,
    "Transact-SQL"                   : True,
    "Turing"                         : True,
    "Turtle"                         : True,
    "Twig"                           : True,
    "TypeScript"                     : True,
    "Unified Parallel C"             : True,
    "Unity3D Asset"                  : True,
    "UnrealScript"                   : True,
    "VBScript"                       : True,
    "VCL"                            : True,
    "VHDL"                           : True,
    "Vala"                           : True,
    "Verilog"                        : True,
    "VimL"                           : True,
    "Visual Basic"                   : True,
    "Visual Basic.NET"               : True,
    "Visual Fortran"                 : True,
    "Visual FoxPro"                  : True,
    "Volt"                           : True,
    "Vue"                            : True,
    "Web Ontology Language"          : False,
    "WebDNA"                         : True,
    "WebIDL"                         : True,
    "Whitespace"                     : True,
    "Wolfram Language"               : True,
    "X10"                            : True,
    "XBase++"                        : True,
    "XC"                             : True,
    "XML"                            : True,
    "XPL"                            : True,
    "XPages"                         : True,
    "XProc"                          : True,
    "XQuery"                         : True,
    "XS"                             : True,
    "XSLT"                           : True,
    "Xen"                            : True,
    "Xojo"                           : True,
    "Xtend"                          : True,
    "YAML"                           : True,
    "Yacc"                           : True,
    "Yorick"                         : True,
    "Zephir"                         : True,
    "Zimpl"                          : True,
    "Zshell"                         : True,
    "bc"                             : True,
    "cT"                             : True,
    "cg"                             : True,
    "dBase"                          : True,
    "desktop"                        : True,
    "eC"                             : True,
    "edn"                            : True,
    "fish"                           : True,
    "haXe"                           : True,
    "ksh"                            : True,
    "mupad"                          : True,
    "nesC"                           : True,
    "ooc"                            : True,
    "reStructuredText"               : False,
    "sed"                            : True,
    "thinBasic"                      : True,
    "wisp"                           : True,
    "xBase"                          : True,
    "Other"                          : False,
}

lang_names_nocase = {k.lower():v for k,v in lang_names.items()}

def known_code_lang(lang):
    lang = lang.lower()
    if lang in lang_names_nocase:
        return lang_names_nocase[lang]
    else:
        return False


# code_files and noncode_files are taken literally, without file
# extensions of any kind, and matched in a case-insensitive way.
#
code_files = [
    'build.xml',
    'capfile',
    'gemfile',
    'makefile',
    'pom.xml',
    'rakefile',
]

noncode_files = [
    '.config',
    '.ds_store',
    '.editorconfig',
    '.gitattributes',
    '.gitconfig',
    '.gitignore',
    '.gitmodules',
    'license',
    'readme',
    'contributors',
    'authors'
]

# FIXME: this list is incomplete
#
# FIXME: The following purposefully omits some files like php because it's
# unclear whether we should take them as a sign of being about code or docs.
# (An html-based documentation set could have an index.php file, for example,
# and would probably be something we'd not want to classify as code.)  Needs
# resolving what really counts as code.
#
code_file_extensions = [
    'ac',
    'action',
    'ada',
    'agc',
    'ahk',
    'am',
    'as',
    'asc',
    'ascx',
    'asm',
    'aspx',
    'axd',
    'axs',
    'bal',
    'bas',
    'bash',
    'bat',
    'bpr',
    'bsc',
    'bsh',
    'c',
    'c++',
    'cbl',
    'cc',
    'cfm',
    'cgi',
    'cla',
    'class',
    'cls',
    'cmd',
    'coffee',
    'cp',
    'cpp',
    'cs',
    'csh',
    'ctl',
    'cxx',
    'dep',
    'dfn',
    'dlg',
    'dot',
    'dpk',
    'dpr',
    'ejs',
    'exp',
    'f',
    'f90',
    'f95',
    'fas',
    'for',
    'fs',
    'fsx',
    'gch',
    'gcl',
    'groovy',
    'gs',
    'h',
    'hs',
    'hx',
    'ino',
    'ins',
    'irc',
    'jav',
    'java',
    'jml',
    'js',
    'jsc',
    'jse',
    'jsp',
    'ksh',
    'l',
    'lap',
    'lib',
    'lisp',
    'lmv',
    'lsp',
    'lst',
    'lua',
    'luac',
    'm',
    'm4',
    'mak',
    'make',
    'matlab',
    'mcp',
    'mdp',
    'mf',
    'mk',
    'ml',
    'mod',
    'msvc',
    'o',
    'obj',
    'pas',
    'pdb',
    'perl',
    'ph',
    'pl',
    'pm',
    'pri',
    'prl',
    'pro',
    'properties',
    'ptx',
    'py',
    'pyc',
    'pyo',
    'pyw',
    'qs',
    'r',
    'rb',
    'rbw',
    'rc',
    'rh',
    'rpg',
    'rule',
    'run',
    'sbr',
    'scala',
    'sct',
    'sh',
    'ss',
    'swift',
    'swt',
    'tcl',
    'tru',
    'vb',
    'vba',
    'vbe',
    'vbi',
    'vbs',
    'vbx',
    'vcxproj/',
    'wbt',
    'ws',
    'wsdl',
    'wsf',
    'xcodeproj/',
    'xla',
    'xlm',
    'xsc',
    'xslt',
    'xul',
    'zero',
    'zsh',
]

# FIXME: this list is incomplete.
#
# This purposefully omits .html & .htm files because someone could put
# javascript inside HTML files.  Ditto for .xml and the possibility of XSLT.
#
noncode_file_extensions = [
    'ascii',
    'avi',
    'bbl',
    'bib',
    'bibtex',
    'bmp',
    'conf',
    'csv',
    'dbx',
    'doc',
    'docx',
    'dvi',
    'enex',
    'enw',
    'epdf',
    'epub',
    'fdf',
    'gif',
    'help',
    'jpeg',
    'jpg',
    'm4a',
    'm4p',
    'man',
    'markdown',
    'md',
    'mdown',
    'mdwn',
    'mkdn',
    'mov',
    'mp3',
    'mp4',
    'mp4a',
    'mpeg',
    'mpg',
    'nbib',
    'odc',
    'odp',
    'ods',
    'odt',
    'ogg',
    'opml',
    'opx',
    'oxps',
    'oxt',
    'pcl',
    'pdf',
    'pdfa',
    'pict',
    'plist',
    'pmd',
    'png',
    'pod',
    'ppdf',
    'ppsx',
    'ppt',
    'pptx',
    'ps',
    'pub',
    'raw',
    'roff',
    'rst',
    'rtf',
    'sgml',
    'snd',
    'tbl',
    'tex',
    'text',
    'textile',
    'tif',
    'tiff',
    'txt',
    'vcard',
    'vsd',
    'wav',
    'wma',
    'wps',
    'xgmml',
    'xml',
    'yml',
]


def has_code_extension(name):
    return name.split(".")[-1].lower() in code_file_extensions


def has_noncode_extension(name):
    return name.split(".")[-1].lower() in noncode_file_extensions


def has_code_file_name(name):
    return name.lower() in code_files


def has_noncode_file_name(name):
    return name.lower() in noncode_files


def is_code_file(file):
    return has_code_extension(file) or has_code_file_name(file)


def is_noncode_file(file):
    return has_noncode_extension(file) or has_noncode_file_name(file)