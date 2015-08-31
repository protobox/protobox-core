# Based on `https://github.com/ansible/ansible/blob/stable-1.9/lib/ansible/runner/lookup_plugins/file.py` for Ansible v1
# Based on `https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/lookup/file.py` for Ansible v2
# Based on `https://github.com/debops/debops-playbooks/blob/master/playbooks/lookup_plugins/task_src.py`
#
#   (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#   (c) 2015, Robert Chady <rchady@sitepen.com>
#   (c) 2015, Patrick Heeney <patrickheeney@gmail.com>
#
# This file is NOT part of Ansible yet.
#
# Debops is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Debops.  If not, see <http://www.gnu.org/licenses/>.

'''

This file implements the `task_src` lookup filter for Ansible. It
mimics the Debops version, but just returns the values instead of
searching custom paths.

'''

import os
#import codecs

__author__ = "Patrick Heeney <patrickheeney@gmail.com>"
__copyright__ = "Copyright 2015 by Robert Chady <rchady@sitepen.com>"
__license__ = "GNU General Public LIcense version 3 (GPL v3) or later"

conf_template_paths = 'task-paths'

from distutils.version import LooseVersion
from ansible import __version__ as __ansible_version__

class LookupModule(object):
    def __new__(class_name, *args, **kwargs):
        if LooseVersion(__ansible_version__) < LooseVersion("2.0"):

            from ansible import utils, errors

            class LookupModuleV1(object):
                def __init__(self, basedir, *args, **kwargs):
                    self.basedir = basedir

                def run(self, terms, inject=None, **kwargs):

                    terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
                    ret = []

                    # this can happen if the variable contains a string, strictly not desired for lookup
                    # plugins, but users may try it, so make it work.
                    if not isinstance(terms, list):
                        terms = [ terms ]

                    # We need to search for the term in the relative path, and return
                    # the file path, instead of the contents due to how this lookup
                    # is used in a playbook

                    for term in terms:
                        path  = None

                        if '_original_file' in inject:
                            path = utils.path_dwim_relative(inject['_original_file'], 'tasks', '', self.basedir, check=False)
                            path = os.path.join(path, term)

                        if path and os.path.exists(path):
                            ret.append(path)
                            break
                        else:
                            raise errors.AnsibleError("could not locate task in lookup: %s" % term)

                    return ret

            return LookupModuleV1(*args, **kwargs)

        else:

            from ansible.errors import AnsibleError, AnsibleParserError
            from ansible.plugins.lookup import LookupBase

            class LookupModuleV2(LookupBase):

                def run(self, terms, variables=None, **kwargs):

                    ret = []

                    basedir = self.get_basedir(variables)

                    for term in terms:
                        self._display.debug("File lookup term: %s" % term)

                        # Special handling of the file lookup, used primarily when the
                        # lookup is done from a role. If the file isn't found in the
                        # basedir of the current file, use dwim_relative to look in the
                        # role/tasks/ directory, and finally the playbook directory
                        # itself (which will be relative to the current working dir)

                        lookupfile = self._loader.path_dwim_relative(basedir, 'tasks', term)
                        self._display.vvvv("File lookup using %s as file" % lookupfile)
                        try:
                            if lookupfile:
                                ret.append(lookupfile)
                            else:
                                raise AnsibleParserError()
                        except AnsibleParserError:
                            raise AnsibleError("could not locate file in lookup: %s" % term)

                    return ret

            return LookupModuleV2(*args, **kwargs)
