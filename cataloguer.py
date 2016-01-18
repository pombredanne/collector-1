#!/usr/bin/env python3.4
#
# @file    cataloguer.py
# @brief   Creates a database of all projects in repository hosts
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Basic principles
# ----------------
# This is a front-end interface to a simple system to gather data about
# repositories hosted in places like GitHub and store that data in a database.
# The code is more or less abstracted from the specifics of individual
# repositories as well as the database format.  The relevant pieces are:
#    host communications           => github_indexer.py
#    repository data record format => RepoData from common/reporecord.py
#    database interface            => Database from common/dbinterface.py
#
# The system is meant to be expandable to other hosting sites in addition to
# GitHub, but right now only GitHub is implemented.
#
# The basic catalog-building procedure goes like this:
#
#  1) Start the database server (using ../database/startserver.py)
#
#  2) Run this cataloguer with the "-c" flag to query hosting sites like
#     GitHub and store the results in the database.  This can take a very long
#     time.  (It took several days for 25 million entries in GitHub.)  The
#     command line is very simple:
#
#      ./cataloguer -c
#
#     But it's a good idea to capture the output of that as well as send it to
#     the background, so really you want to run it like this (using csh/tcsh
#     shell syntax):
#
#      ./cataloguer -c >& log-cataloguer.txt &
#
#  3) The cataloguing process invoked with "-c" only retrieves very basic
#     information about the repositories in the case of GitHub, because the
#     GitHub API is such that you can get the most basic info for 100 repos
#     at a time with a single API call, but to get more detailed information
#     such as the programming languages used in a given repository, you have
#     to query each repo at one API call per repo.  Since GitHub's rate limit
#     is 5000 API calls per hour, it means that getting the detailed info
#     proceeds at a 100 times slower rate.  Consequently, the procedure to
#     get programming language info is implemented as a separate step in this
#     program.  It is invoked with the "-l" flag.  To invoke it:
#
#      ./cataloguer -l >& log-languages.txt &
#
#  4) Once the cataloguer is finished, you can use this program
#     (cataloguer.py) to print some information in the database.  E.g.,
#     "cataloguer -p" will print a summary of every entry in the database.

import pdb
import sys
import os
import plac
from datetime import datetime
from time import sleep
from timeit import default_timer as timer

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
from dbinterface import *
from utils import *
from reporecord import *

from github_indexer import GitHubIndexer


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

def main(user_login=None, index_create=False, index_recreate=False,
         file=None, languages=None, index_forks=False, index_langs=False,
         index_readmes=False, print_details=False, print_index=False,
         summarize=False, print_ids=False, update=False, update_internal=False,
         list_deleted=False, delete=False, *repos):
    '''Generate or print index of projects found in repositories.'''

    def convert(arg):
        return int(arg) if (arg and arg.isdigit()) else arg

    if repos:
        repos = [convert(x) for x in repos]
    elif file:
        with open(file) as f:
            repos = f.read().splitlines()
            if len(repos) > 0 and repos[0].isdigit():
                repos = [int(x) for x in repos]

    if languages:
        languages = languages.split(',')

    if   summarize:       do_action("print_summary",     user_login)
    elif print_ids:       do_action("print_indexed_ids", user_login)
    elif print_index:     do_action("print_index",       user_login, repos, languages)
    elif print_details:   do_action("print_details",     user_login, repos)
    elif index_create:    do_action("create_index",      user_login, repos)
    elif index_recreate:  do_action("recreate_index",    user_login, repos)
    elif index_langs:     do_action("add_languages",     user_login, repos)
    elif index_forks:     do_action("add_fork_info",     user_login, repos)
    elif index_readmes:   do_action("add_readmes",       user_login, repos)
    elif delete:          do_action("mark_deleted",      user_login, repos)
    elif list_deleted:    do_action("list_deleted",      user_login, repos)
    elif update:          do_action("update_entries",    user_login, repos)
    elif update_internal: do_action("update_internal",   user_login)
    else:
        raise SystemExit('No action specified. Use -h for help.')


def do_action(action, user_login=None, targets=None, languages=None):
    msg('Started at ', datetime.now())
    started = timer()

    dbinterface = Database()
    db = dbinterface.open()

    # Do each host in turn.  (Currently only GitHub.)

    try:
        indexer = GitHubIndexer(user_login)
        method = getattr(indexer, action, None)
        if targets and languages:
            method(db, targets, languages)
        elif targets:
            method(db, targets)
        elif languages:
            method(db, None, languages)
        else:
            method(db)
    finally:
        transaction.commit()
        dbinterface.close()

    # We're done.  Print some messages and exit.

    stopped = timer()
    msg('Stopped at {}'.format(datetime.now()))
    msg('Time elapsed: {}'.format(stopped - started))


# Plac annotations for main function arguments
# .............................................................................
# Argument annotations are: (help, kind, abbrev, type, choices, metavar)
# Plac automatically adds a -h argument for help, so no need to do it here.

main.__annotations__ = dict(
    user_login      = ('use specified account login',                'option', 'a'),
    index_create    = ('gather basic index data',                    'flag',   'c'),
    index_recreate  = ('re-gather basic index data',                 'flag',   'C'),
    file            = ('get repo names or identifiers from file',    'option', 'f'),
    languages       = ('limit printing to specific languages',       'option', 'L'),
    index_forks     = ('gather repository copy/fork status',         'flag',   'k'),
    index_langs     = ('gather programming languages',               'flag',   'l'),
    index_readmes   = ('gather README files',                        'flag',   'r'),
    print_details   = ('print details about entries',                'flag',   'p'),
    print_ids       = ('print all known repository id numbers',      'flag',   'P'),
    print_index     = ('print summary of indexed repositories',      'flag',   's'),
    summarize       = ('summarize database statistics',              'flag',   'S'),
    update          = ('update specific entries by querying GitHub', 'flag',   'u'),
    update_internal = ('update internal database tables',            'flag',   'U'),
    list_deleted    = ('list deleted entries',                       'flag',   'x'),
    delete          = ('mark specific entries as deleted',           'flag',   'X'),
    repos           = 'repository identifiers or names',
)

# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
