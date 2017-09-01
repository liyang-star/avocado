# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2017
# Authors: Amador Pahim <apahim@redhat.com>

"""
Plugin to run unittest Framework tests in Avocado
"""

import logging
import re
import unittest
import os

from avocado.core import loader
from avocado.core import output
from avocado.core import test
from avocado.core.plugin_interfaces import CLI


class UnitTestTest(test.SimpleTest):

    """
    Run a uniitest command as a SIMPLE test.
    """

    def __init__(self,
                 name,
                 params=None,
                 base_logdir=None,
                 job=None):
        super(UnitTestTest, self).__init__(name, params, base_logdir, job)

    @property
    def filename(self):
        """
        Returns the path of the unittest test suite.
        """
        return self.name.name.split(':')[0]

    def test(self):
        """
        Create the unittest command and execute it.
        """
        test_name = self.name.name.split(':')[1]
        test = unittest.defaultTestLoader.loadTestsFromName(name = test_name)
        result = unittest.TextTestRunner().run(test)

        if result.wasSuccessful():
            self.fail('UnitTest execution returned a '
                      'non-0 exit code (%s)' % result.printErrors())


class NotUnitTestTest(object):

    """
    Not a UnitTest test (for reporting purposes)
    """


class UnitTestLoader(loader.TestLoader):
    """
    UnitTest loader class
    """
    name = "unittest"

    def __init__(self, args, extra_params):
        super(UnitTestLoader, self).__init__(args, extra_params)

    def discover(self, url, which_tests=loader.DEFAULT):
        avocado_suite = []
        subtests_filter = None
        pattern = 'test*.py'
        
	if url is None:
            return []

        if ':' in url:
            url, _subtests_filter = url.split(':', 1)
            subtests_filter = re.compile(_subtests_filter)
        try:
		
            if os.path.isfile(url):
                url,pattern = os.path.split(url)
	    url = os.path.realpath(url)			
            test_data = unittest.defaultTestLoader.discover(url,
                                                            pattern=pattern,
                                                            top_level_dir=None)
           
            unittest_suite = self._find_tests(test_data,test_suite={})
        except Exception as data:
            if which_tests == loader.ALL:
                return [(NotUnitTestTest, {"name": "%s: %s" % (url, data)})]
            return []

	for test in unittest_suite:
            test_name = "%s:%s.%s" % (url,
                                      test.__module__ + "." + test.__class__.__name__,
				      test._testMethodName)
            if subtests_filter and not subtests_filter.search(test_name):
                continue
	    avocado_suite.append((UnitTestTest, {'name': test_name}))
        if which_tests is loader.ALL and not avocado_suite:
            return [(NotUnitTestTest, {"name": "%s: No unittest-like tests found"
                                    % url})]
        return avocado_suite

    def _find_tests(self,data,test_suite):
	test_suite = []
	if isinstance(data,unittest.suite.TestSuite):
		test_suite.extend(self._find_tests(data._tests,test_suite))
	elif isinstance(data,list):
		for tests in data:
			test_suite.extend(self._find_tests(tests,test_suite))
	else:
		test_suite.append(data)
	return test_suite

    @staticmethod
    def get_type_label_mapping():
        return {UnitTestTest: 'UNITTEST',
                NotUnitTestTest: "!UNITTEST"}

    @staticmethod
    def get_decorator_mapping():
        return {UnitTestTest: output.TERM_SUPPORT.healthy_str,
                NotUnitTestTest: output.TERM_SUPPORT.fail_header_str}


class UnitTestCLI(CLI):

    """
    Run UnitTest Framework tests
    """

    name = 'unittest'
    description = "UnitTest Framework options for 'run' subcommand"

    def configure(self, parser):
        pass

    def run(self, args):
        loader.loader.register_plugin(UnitTestLoader)
