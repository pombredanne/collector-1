#!/usr/bin/env python3.4
#
# @file    github-indexer.py
# @brief   Create a database of all GitHub repositories
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

import pdb
import sys
import os
import operator
import requests
import json
import http
import requests
import urllib
import github3
import zlib
import ZODB
import persistent
import transaction
from base64 import b64encode
from BTrees.IOBTree import TreeSet
from BTrees.OOBTree import Bucket
from datetime import datetime
from time import time, sleep

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
from utils import *
from reporecord import *


# Summary
# .............................................................................
# This uses the GitHub API to download basic information about every GitHub
# repository and stores it in a ZODB database.
#
# This code pays attention to the GitHub rate limit on API calls and pauses
# when it hits the 5000/hr limit, restarting again after the necessary time
# has elapsed to do another 5000 calls.  For basic information, each GitHub
# API call nets 100 records, so a rate of 5000/hr = 500,000/hr.  More detailed
# information such as programming languages only goes at 1 per API call, which
# means no more than 5000/hr.
#
# This uses the github3.py module (https://github.com/sigmavirus24/github3.py),
# for some things.  Unfortunately, github3.py turns out to be inefficient for
# getting detailed info such as languages because it causes 2 API calls to be
# used for each repo.  So, for some things, this code uses the GitHub API
# directly, via the Python httplib interface.


# Main class.
# .............................................................................

class GitHubIndexer():
    _max_failures   = 10

    def __init__(self, user_login=None):
        cfg = Config()
        section = Host.name(Host.GITHUB)

        try:
            if user_login:
                for name, value in cfg.items(section):
                    if name.startswith('login') and value == user_login:
                        self._login = user_login
                        index = name[len('login'):]
                        if index:
                            self._password = cfg.get(section, 'password' + index)
                        else:
                            # login entry doesn't have an index number.
                            # Might be a config file in the old format.
                            self._password = value
                        break
                # If we get here, we failed to find the requested login.
                msg('Cannot find "{}" in section {} of config.ini'.format(
                    user_login, section))
            else:
                try:
                    self._login = cfg.get(section, 'login1')
                    self._password = cfg.get(section, 'password1')
                except:
                    self._login = cfg.get(section, 'login')
                    self._password = cfg.get(section, 'password')
        except Exception as err:
            msg(err)
            text = 'Failed to read "login" and/or "password" for {}'.format(
                section)
            raise SystemExit(text)


    def github(self):
        '''Returns the github3.py connection object.  If no connection has
        been established yet, it connects to GitHub first.'''

        if hasattr(self, '_github') and self._github:
            return self._github

        msg('Connecting to GitHub as user {}'.format(self._login))
        try:
            self._github = github3.login(self._login, self._password)
            return self._github
        except Exception as err:
            msg(err)
            text = 'Failed to log into GitHub'
            raise SystemExit(text)

        if not self._github:
            msg('Unexpected failure in logging into GitHub')
            raise SystemExit()


    def api_calls_left(self):
        '''Returns an integer.'''
        try:
            rate_limit = self.github().rate_limit()
            return rate_limit['resources']['core']['remaining']
        except Exception as err:
            msg('Got exception asking about rate limit: {}'.format(err))
            raise err


    def api_reset_time(self):
        '''Returns a timestamp value, i.e., seconds since epoch.'''
        try:
            rate_limit = self.github().rate_limit()
            return rate_limit['resources']['core']['reset']
        except Exception as err:
            msg('Got exception asking about reset time: {}'.format(err))
            raise err


    def wait_for_reset(self):
        reset_time = datetime.fromtimestamp(self.api_reset_time())
        time_delta = reset_time - datetime.now()
        msg('Sleeping until ', reset_time)
        sleep(time_delta.total_seconds() + 1)  # Extra second to be safe.


    def get_repo_iterator(self, last_seen=None):
        try:
            if last_seen:
                return self.github().iter_all_repos(since=last_seen)
            else:
                return self.github().iter_all_repos()
        except Exception as err:
            msg('github.iter_all_repos() failed with {0}'.format(err))
            sys.exit(1)


    def get_search_iterator(self, query, last_seen=None):
        try:
            if last_seen:
                return self.github().search_repositories(query, since=last_seen)
            else:
                return self.github().search_repositories(query)
        except Exception as err:
            msg('github.search_repositories() failed with {0}'.format(err))
            sys.exit(1)


    def add_record_from_github3(self, repo, db, languages=None):
        # Match impedances between github3's record format and ours.  Our
        # database keys are the integer identifiers assigned to repos.  If
        # overwriting an existing entry, save content that needs separate calls.
        identifier = repo if isinstance(repo, int) else repo.id
        if identifier in db:
            old_entry = db[identifier]
            db[identifier] = RepoEntry(host=Host.GITHUB,
                                       id=identifier,
                                       path=repo.full_name,
                                       description=repo.description,
                                       readme=old_entry.readme,
                                       copy_of=repo.fork,   # Only a Boolean.
                                       deleted=old_entry.deleted,
                                       owner=repo.owner.login,
                                       owner_type=repo.owner.type,
                                       languages=old_entry.languages,
                                       topics=old_entry.topics,
                                       categories=old_entry.categories)
        else:
            db[identifier] = RepoEntry(host=Host.GITHUB,
                                       id=identifier,
                                       path=repo.full_name,
                                       description=repo.description,
                                       copy_of=repo.fork,   # Only a Boolean.
                                       owner=repo.owner.login,
                                       owner_type=repo.owner.type,
                                       languages=languages)


    def get_globals(self, db):
        # We keep globals at position 0 in the database, since there is no
        if 0 in db:
            return db[0]
        else:
            db[0] = Bucket()            # This needs to be an OOBucket.
            return db[0]


    def set_in_globals(self, var, value, db):
        globals = self.get_globals(db)
        globals[var] = value


    def from_globals(self, db, var):
        globals = self.get_globals(db)
        return globals[var] if var in globals else None


    def set_last_seen(self, id, db):
        self.set_in_globals('last seen id', id, db)


    def get_last_seen(self, db):
        return self.from_globals(db, 'last seen id')


    def set_highest_github_id(self, id, db):
        self.set_in_globals('highest id number', id, db)


    def get_highest_github_id(self, db):
        globals = self.get_globals(db)
        highest = self.from_globals(db, 'highest id number')
        if highest:
            return highest
        else:
            msg('Did not find a record of the highest id.  Searching now...')
            pdb.set_trace()


    def set_language_list(self, value, db):
        self.set_in_globals('entries with languages', value, db)


    def get_language_list(self, db):
        lang_list = self.from_globals(db, 'entries with languages')
        if lang_list:
            return lang_list
        else:
            msg('Did not find list of entries with languages. Creating it.')
            self.set_in_globals('entries with languages', TreeSet(), db)
            return self.from_globals(db, 'entries with languages')


    def set_readme_list(self, value, db):
        self.set_in_globals('entries with readmes', value, db)


    def get_readme_list(self, db):
        readme_list = self.from_globals(db, 'entries with readmes')
        if readme_list:
            return readme_list
        else:
            msg('Did not find list of entries with readmes. Creating it.')
            self.set_in_globals('entries with readmes', TreeSet(), db)
            return self.from_globals(db, 'entries with readmes')


    def set_total_entries(self, count, db):
        self.set_in_globals('total entries', count, db)


    def get_total_entries(self, db):
        globals = self.get_globals(db)
        if 'total entries' in globals:
            return globals['total entries']
        else:
            msg('Did not find a count of entries.  Counting now...')
            count = len(list(db.keys()))
            self.set_total_entries(count, db)
            return count


    def summarize_language_stats(self, db):
        msg('Gathering programming language statistics ...')
        entries_with_languages = self.get_language_list(db)
        entries = 0                     # Total number of entries seen.
        language_counts = {}            # Pairs of language:count.
        for name in entries_with_languages:
            entries += 1
            if (entries + 1) % 100000 == 0:
                print(entries + 1, '...', end='', flush=True)
            if name in db:
                entry = db[name]
            else:
                msg('Cannot find entry "{}" in database'.format(name))
                continue
            if not isinstance(entry, RepoEntry):
                msg('Entry "{}" is not a RepoEntry'.format(name))
                continue
            if entry.languages != None:
                for lang in entry.languages:
                    if lang in language_counts:
                        language_counts[lang] = language_counts[lang] + 1
                    else:
                        language_counts[lang] = 1
        msg('Language usage counts:')
        for key, value in sorted(language_counts.items(), key=operator.itemgetter(1),
                                 reverse=True):
            msg('  {0:<24s}: {1}'.format(Language.name(key), value))


    def update_internal(self, db):
        last_seen = 0
        num_entries = 0
        entries_with_languages = self.get_language_list(db)
        entries_with_readmes = self.get_readme_list(db)
        msg('Scanning every entry in the database ...')
        for key, entry in db.items():
            if not isinstance(entry, RepoEntry):
                continue
            num_entries += 1
            if entry.id > last_seen:
                last_seen = entry.id
            if entry.languages != None:
                entries_with_languages.add(key)
            if entry.readme and entry.readme != '' and entry.readme != -1:
                entries_with_readmes.add(key)
            if (num_entries + 1) % 100000 == 0:
                print(num_entries + 1, '...', end='', flush=True)
        msg('Done.')
        self.set_total_entries(num_entries, db)
        msg('Database has {} total GitHub entries.'.format(num_entries))
        self.set_last_seen(last_seen, db)
        self.set_highest_github_id(last_seen, db)
        msg('Last seen GitHub repository id: {}'.format(last_seen))
        self.set_language_list(entries_with_languages, db)
        msg('Number of entries with language info: {}'.format(entries_with_languages.__len__()))
        self.set_readme_list(entries_with_readmes, db)
        msg('Number of entries with README files: {}'.format(entries_with_readmes.__len__()))
        transaction.commit()


    def print_index(self, db):
        '''Print the database contents.'''
        last_seen = self.get_last_seen(db)
        if last_seen:
            msg('Last seen id: {}'.format(last_seen))
        else:
            msg('No record of last seen id.')
        for key, entry in db.items():
            if not isinstance(entry, RepoEntry):
                continue
            print(entry)
            if entry.description:
                msg(' ', entry.description.encode('ascii', 'ignore').decode('ascii'))
            else:
                msg('  -- no description --')


    def print_indexed_ids(self, db):
        '''Print the known repository identifiers in the database.'''
        total_recorded = self.get_total_entries(db)
        msg('total count: ', total_recorded)
        count = 0
        for key in db.keys():
            if key == 0: continue
            msg(key)
            count += 1
        if count != total_recorded:
            msg('Error: {} expected in database, but counted {}'.format(
                total_recorded, count))


    def print_summary(self, db):
        '''Print a summary of the database, without listing every entry.'''
        total = self.get_total_entries(db)
        if total:
            msg('Database has {} total GitHub entries.'.format(total))
            last_seen = self.get_last_seen(db)
            if last_seen:
                msg('Last seen GitHub id: {}.'.format(last_seen))
            else:
                msg('No "last_seen" marker found.')
            entries_with_readmes = self.get_readme_list(db)
            if entries_with_readmes:
                msg('Database has {} entries with README files.'.format(entries_with_readmes.__len__()))
            else:
                msg('No entries recorded with README files.')
            entries_with_languages = self.get_language_list(db)
            if entries_with_languages:
                msg('Database has {} entries with language info.'.format(entries_with_languages.__len__()))
                self.summarize_language_stats(db)
            else:
                msg('No entries recorded with language info.')
        else:
            msg('Database has not been updated to include counts. Doing it now...')
            self.update_internal(db)
            total = self.get_total_entries(db)
            msg('Database has {} total GitHub entries'.format(total))


    def direct_api_call(self, url):
        auth = '{0}:{1}'.format(self._login, self._password)
        headers = {
            'User-Agent': self._login,
            'Authorization': 'Basic ' + b64encode(bytes(auth, 'ascii')).decode('ascii'),
            'Accept': 'application/vnd.github.v3.raw',
        }
        conn = http.client.HTTPSConnection("api.github.com")
        conn.request("GET", url, {}, headers)
        response = conn.getresponse()
        if response.status == 200:
            content = response.readall()
            return content.decode('utf-8')
        else:
            return None


    def extract_languages_from_html(self, html, entry):
        marker = 'class="lang">'
        marker_len = len(marker)
        languages = []
        startpoint = html.find(marker)
        while startpoint > 0:
            endpoint = html.find('<', startpoint)
            languages.append(html[startpoint+marker_len : endpoint])
            startpoint = html.find(marker, endpoint)
        # Minor cleanup.
        if 'Other' in languages:
            languages.remove('Other')
        return languages


    def get_languages(self, entry):
        # First try to get it by scraping the HTTP web page for the project.
        # This saves an API call.

        r = requests.get('http://github.com/' + entry.path)
        if r.status_code == 200:
            return ('http', self.extract_languages_from_html(r.text, entry))

        # Failed to get it by scraping.  Try the GitHub API.
        # Using github3.py would need 2 api calls per repo to get this info.
        # Here we do direct access to bring it to 1 api call.
        url = 'https://api.github.com/repos/{}/languages'.format(entry.path)
        response = self.direct_api_call(url)
        if response == None:
            return ('api', [])
        else:
            return ('api', json.loads(response))


    def get_readme(self, entry):
        # First try to get it via direct HTTP access, to save on API calls.
        base_url = 'https://raw.githubusercontent.com/{}'.format(entry.path)
        readme_1 = base_url + '/master/README.md'
        readme_2 = base_url + '/master/README.rst'
        readme_3 = base_url + '/master/README'
        readme_4 = base_url + '/master/README.txt'
        for alternative in [readme_1, readme_2, readme_3, readme_4]:
            r = requests.get(alternative)
            if r.status_code == 200:
                return ('http', r.text)
            elif r.status_code < 300:
                pdb.set_trace()

        # Resort to GitHub API call.
        # Get the "preferred" readme file for a repository, as described in
        # https://developer.github.com/v3/repos/contents/
        # Using github3.py would need 2 api calls per repo to get this info.
        # Here we do direct access to bring it to 1 api call.
        url = 'https://api.github.com/repos/{}/readme'.format(entry.path)
        return ('api', self.direct_api_call(url))


    def raise_exception_for_response(self, request):
        if request == None:
            raise RuntimeError('Null return value')
        elif request.ok:
            pass
        else:
            response = json.loads(request.text)
            msg = response['message']
            raise RuntimeError('{}: {}'.format(request.status_code, msg))


    def recreate_index(self, db, project_list=None):
        self.create_index_full(db, project_list, False)


    def create_index(self, db, project_list=None, continuation=True):
        count = self.get_total_entries(db)
        msg('There are {} entries currently in the database'.format(count))

        last_seen = self.get_last_seen(db)
        if last_seen:
            if continuation:
                msg('Continuing from highest-known id {}'.format(last_seen))
            else:
                msg('Ignoring last id {} -- starting from the top'.format(last_seen))
                last_seen = None
        else:
            msg('No record of the last repo id seen.  Starting from the top.')
            last_seen = -1

        calls_left = self.api_calls_left()
        msg('Initial GitHub API calls remaining: ', calls_left)

        # The iterator returned by github.all_repositories() is continuous; behind
        # the scenes, it uses the GitHub API to get new data when needed.  Each API
        # call nets 100 repository records, so after we go through 100 objects in the
        # 'for' loop below, we expect that github.all_repositories() will have made
        # another call, and the rate-limited number of API calls left in this
        # rate-limited period will go down by 1.  When we hit the limit, we pause
        # until the reset time.

        if project_list:
            repo_iterator = iter(project_list)
        else:
            repo_iterator = self.get_repo_iterator(last_seen)
        loop_count    = 0
        failures      = 0
        start = time()
        while failures < self._max_failures:
            try:
                repo = next(repo_iterator)
                if repo is None:
                    break

                update_count = True
                if isinstance(repo, int):
                    # GitHub doesn't provide a way to go from an id to a repo,
                    # so all we can do if we're using a list of identifiers is
                    # update our existing entry (if we know about it already).
                    identifier = repo
                    if identifier in db:
                        msg('Overwriting entry for #{}'.format(identifier))
                        entry = db[identifier]
                        project_start = entry.path.find('/') + 1
                        project = entry.path[project_start:]
                        repo = self.github().repository(entry.owner, project)
                        update_count = False
                    else:
                        msg('Skipping {} -- unknown repo id'.format(repo))
                        continue
                else:
                    identifier = repo.id
                    if identifier in db:
                        if continuation:
                            msg('Skipping {} (id #{}) -- already known'.format(
                                repo.full_name, identifier))
                            continue
                        else:
                            msg('Overwriting entry {} (id #{})'.format(
                                repo.full_name, identifier))
                            update_count = False

                self.add_record_from_github3(repo, db)
                msg('{}: {} (id #{})'.format(count, repo.full_name, identifier))
                if update_count:
                    count += 1
                    self.set_total_entries(count, db)
                if identifier > last_seen:
                    self.set_last_seen(identifier, db)
                transaction.commit()
                failures = 0

                loop_count += 1
                if loop_count > 100:
                    calls_left = self.api_calls_left()
                    if calls_left > 1:
                        loop_count = 0
                    else:
                        self.wait_for_reset()
                        calls_left = self.api_calls_left()
                        msg('Continuing')

            except StopIteration:
                msg('github3 repository iterator reports it is done')
                break
            except github3.GitHubError as err:
                if err.code == 403:
                    msg('GitHub API rate limit reached')
                    self.wait_for_reset()
                    loop_count = 0
                    calls_left = self.api_calls_left()
                else:
                    msg('github3 generated an exception: {0}'.format(err))
                    failures += 1
            except Exception as err:
                msg('Exception: {0}'.format(err))
                failures += 1

        transaction.commit()
        if failures >= self._max_failures:
            msg('Stopping because of too many repeated failures.')
        else:
            msg('Done.')


    def add_languages(self, db, project_list=None):
        msg('Initial GitHub API calls remaining: ', self.api_calls_left())
        entries_with_languages = self.get_language_list(db)
        failures = 0
        start = time()

        # If we're iterating over the entire database, we have to make a copy
        # of the keys list because we can't iterate on the database if the
        # number of elements may be changing.  Making this list is incredibly
        # inefficient and takes many minutes to create.

        id_list = project_list if project_list else list(db.keys())
        for count, key in enumerate(id_list):
            if key not in db:
                msg('repository id {} is unknown'.format(key))
                continue
            entry = db[key]
            if not hasattr(entry, 'id'):
                continue
            if key in entries_with_languages:
                continue
            if entry.languages != None:
                # It has a non-empty language field but it wasn't in our list
                # of entries with language info.  Add it and move along.
                entries_with_languages.add(key)
                continue

            if self.api_calls_left() < 1:
                self.wait_for_reset()
                failures = 0
                msg('Continuing')

            retry = True
            while retry and failures < self._max_failures:
                # Don't retry unless the problem may be transient.
                retry = False
                try:
                    t1 = time()
                    (method, results) = self.get_languages(entry)
                    t2 = time()
                    msg('{} (#{}) in {:.2f}s via {}'.format(entry.path, entry.id,
                                                            t2-t1, method))
                    raw_languages = [lang for lang in results]
                    languages = [Language.identifier(x) for x in raw_languages]
                    entry.languages = languages
                    entry._p_changed = True # Needed for ZODB record updates.

                    # Misc bookkeeping.
                    entries_with_languages.add(key)
                    failures = 0
                except github3.GitHubError as err:
                    if err.code == 403:
                        msg('GitHub API rate limit reached')
                        self.wait_for_reset()
                        loop_count = 0
                        calls_left = self.api_calls_left()
                    else:
                        msg('GitHub API exception: {0}'.format(err))
                        failures += 1
                        # Might be a network or other transient error.
                        retry = True
                except EnumerationValueError as err:
                    # Encountered a language string that's not in our enum.
                    # Print a message and go on.
                    msg('Encountered unrecognized language: {}'.format(err))
                    retry = False
                except Exception as err:
                    msg('Exception for "{}": {}'.format(entry.path, err))
                    failures += 1
                    # Might be a network or other transient error.
                    retry = True

            if failures >= self._max_failures:
                msg('Stopping because of too many consecutive failures')
                break
            self.set_language_list(entries_with_languages, db)
            transaction.commit()
            if count % 100 == 0:
                msg('{} [{:2f}]'.format(count, time() - start))
                start = time()

        self.set_language_list(entries_with_languages, db)
        transaction.commit()
        msg('')
        msg('Done.')


    def add_readmes(self, db, project_list=None):
        msg('Initial GitHub API calls remaining: ', self.api_calls_left())
        entries_with_readmes = self.get_readme_list(db)
        failures = 0
        start = time()

        # If we're iterating over the entire database, we have to make a copy
        # of the keys list because we can't iterate on the database if the
        # number of elements may be changing.  Making this list is incredibly
        # inefficient and takes many minutes to create.

        id_list = project_list if project_list else list(db.keys())
        for count, key in enumerate(id_list):
            if key not in db:
                msg('repository id {} is unknown'.format(key))
                continue
            entry = db[key]
            if not hasattr(entry, 'id'):
                continue
            if key in entries_with_readmes:
                continue
            if entry.readme == -1:
                # We already tried to get this one, and it was empty.
                continue
            if entry.readme:
                # It has a non-empty readme field but it wasn't in our
                # list of entries with readme's.  Add it and move along.
                entries_with_readmes.add(key)
                continue

            retry = True
            while retry and failures < self._max_failures:
                # Don't retry unless the problem may be transient.
                retry = False
                try:
                    t1 = time()
                    (method, readme) = self.get_readme(entry)
                    t2 = time()
                    if readme:
                        msg('{} (#{}) in {:.2f}s via {}'.format(entry.path,
                                                                entry.id, t2-t1,
                                                                method))
                        entry.readme = zlib.compress(bytes(readme, 'utf-8'))
                        entry._p_changed = True # Needed for ZODB record updates.
                        entries_with_readmes.add(key)
                    else:
                        # If GitHub doesn't return a README file, we need to
                        # record something to indicate that we already tried.
                        # The something can't be '', or None, or 0.  We use -1.
                        entry.readme = -1
                    entry._p_changed = True # Needed for ZODB record updates.
                    failures = 0
                except github3.GitHubError as err:
                    if err.code == 403:
                        msg('GitHub API rate limit reached')
                        self.wait_for_reset()
                        loop_count = 0
                        calls_left = self.api_calls_left()
                    else:
                        msg('GitHub API exception: {0}'.format(err))
                        failures += 1
                        # Might be a network or other transient error.
                        retry = True
                except Exception as err:
                    msg('Exception for "{}": {}'.format(entry.path, err))
                    failures += 1
                    # Might be a network or other transient error.
                    retry = True

            if failures >= self._max_failures:
                msg('Stopping because of too many consecutive failures')
                break
            self.set_readme_list(entries_with_readmes, db)
            transaction.commit()
            if count % 100 == 0:
                msg('{} [{:2f}]'.format(count, time() - start))
                start = time()

        self.set_readme_list(entries_with_readmes, db)
        transaction.commit()
        msg('')
        msg('Done.')


    # def locate_by_languages(self, db):
    #     msg('Examining our current database')
    #     count = self.get_total_entries(db)
    #     msg('There are {} entries in the database'.format(count))

    #     # We have to do 2 separate searches because there does not seem to
    #     # be an "or" operator in the GitHub search syntax.

    #     # The iterator returned by github.search_repositories() is
    #     # continuous; behind the scenes, it uses the GitHub API to get new
    #     # data when needed.  Each API call nets 100 repository records, so
    #     # after we go through 100 objects in the 'for' loop below, we expect
    #     # that github.all_repositories() will have made another call, and the
    #     # rate-limited number of API calls left in this rate-limited period
    #     # will go down by 1.  When we hit the rate limit max, we pause until
    #     # the reset time.

    #     calls_left = self.api_calls_left()
    #     msg('Initial GitHub API calls remaining: ', calls_left)

    #     # Java

    #     search_iterator = self.get_search_iterator("language:java")
    #     loop_count    = 0
    #     failures      = 0
    #     while failures < self._max_failures:
    #         try:
    #             search_result = next(search_iterator)
    #             if search_result is None:
    #                 msg('Empty return value from github3 iterator')
    #                 failures += 1
    #                 continue

    #             repo = search_result.repository
    #             if repo.full_name in db:
    #                 # We have this in our database.  Good.
    #                 entry = db[repo.full_name]
    #                 if entry.languages:
    #                     if not Language.JAVA in entry.languages:
    #                         entry.languages.append(Language.JAVA)
    #                         entry._p_changed = True
    #                     else:
    #                         msg('Already knew about {}'.format(repo.full_name))
    #                 else:
    #                     entry.languages = [Language.JAVA]
    #                     entry._p_changed = True
    #             else:
    #                 # We don't have this in our database.  Add a new record.
    #                 try:
    #                     add_record(repo, db, languages=[Language.JAVA])
    #                     msg('{}: {} (GitHub id: {})'.format(count,
    #                                                         repo.full_name,
    #                                                         repo.id))
    #                     count += 1
    #                     failures = 0
    #                 except Exception as err:
    #                     msg('Exception when creating RepoEntry: {0}'.format(err))
    #                     failures += 1
    #                     continue

    #             self.set_last_seen(repo.id, db)
    #             self.set_total_entries(count, db)
    #             transaction.commit()

    #             loop_count += 1
    #             if loop_count > 100:
    #                 calls_left = self.api_calls_left()
    #                 if calls_left > 1:
    #                     loop_count = 0
    #                 else:
    #                     self.wait_for_reset()
    #                     calls_left = self.api_calls_left()
    #                     msg('Continuing')

    #         except StopIteration:
    #             msg('github3 search iterator reports it is done')
    #             break
    #         except github3.GitHubError as err:
    #             if err.code == 403:
    #                 msg('GitHub API rate limit reached')
    #                 self.wait_for_reset()
    #                 loop_count = 0
    #                 calls_left = self.api_calls_left()
    #             else:
    #                 msg('github3 generated an exception: {0}'.format(err))
    #                 failures += 1
    #         except Exception as err:
    #             msg('github3 generated an exception: {0}'.format(err))
    #             failures += 1

    #     transaction.commit()
    #     if failures >= self._max_failures:
    #         msg('Stopping because of too many repeated failures.')
    #     else:
    #         msg('Done.')

    # This will no longer work, with the switch to using id numbers as keys.
    # Keeping it here because the sequence of steps took time to work out
    # and may be applicable to other things.
    #
    # def create_index_using_list(self, db, project_list):
    #     calls_left = self.api_calls_left()
    #     msg('Initial GitHub API calls remaining: ', calls_left)

    #     count = self.get_total_entries(db)
    #     if not count:
    #         msg('Did not find a count of entries.  Counting now...')
    #         count = db.__len__()
    #         self.set_total_entries(count, db)
    #     msg('There are {} entries in the database'.format(count))

    #     last_seen = self.get_last_seen(db)

    #     failures   = 0
    #     loop_count = 0
    #     with open(project_list, 'r') as f:
    #         for line in f:
    #             retry = True
    #             while retry and failures < self._max_failures:
    #                 # Don't retry unless the problem may be transient.
    #                 retry = False
    #                 try:
    #                     full_name = line.strip()
    #                     if full_name in db:
    #                         msg('Skipping {} -- already known'.format(full_name))
    #                         continue
    #                     if requests.get('http://github.com/' + full_name).status_code == 404:
    #                         msg('{} not found in GitHub using https'.format(full_name))
    #                         continue

    #                     owner = full_name[:full_name.find('/')]
    #                     project = full_name[full_name.find('/') + 1:]
    #                     repo = self.github().repository(owner, project)

    #                     if not repo:
    #                         msg('{} not found in GitHub using API'.format(full_name))
    #                         continue
    #                     if repo.full_name in db:
    #                         msg('Already know {} renamed from {}'.format(repo.full_name,
    #                                                                      full_name))
    #                         continue

    #                     self.add_record_from_github3(repo, db)
    #                     msg('{}: {} (GitHub id: {})'.format(count, repo.full_name,
    #                                                         repo.id))
    #                     count += 1
    #                     failures = 0
    #                     if repo.id > last_seen:
    #                         self.set_last_seen(repo.id, db)
    #                     self.set_total_entries(count, db)

    #                     transaction.commit()

    #                     loop_count += 1
    #                     if loop_count > 100:
    #                         calls_left = self.api_calls_left()
    #                         if calls_left > 1:
    #                             loop_count = 0
    #                         else:
    #                             self.wait_for_reset()
    #                             calls_left = self.api_calls_left()
    #                             msg('Continuing')
    #                 except github3.GitHubError as err:
    #                     if err.code == 403:
    #                         msg('GitHub API rate limit reached')
    #                         self.wait_for_reset()
    #                         loop_count = 0
    #                         calls_left = self.api_calls_left()
    #                     else:
    #                         msg('GitHub API error: {0}'.format(err))
    #                         failures += 1
    #                         # Might be a network or other transient error.
    #                         retry = True
    #                 except Exception as err:
    #                     msg('github3 generated an exception: {0}'.format(err))
    #                     failures += 1
    #                     # Might be a network or other transient error.
    #                     retry = True

    #             # Stop for-loop if we accumulate too many failures.
    #             if failures >= self._max_failures:
    #                 msg('Stopping because of too many repeated failures.')
    #                 break

    #     transaction.commit()
    #     msg('Done.')
