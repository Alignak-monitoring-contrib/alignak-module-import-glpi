#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016: Alignak team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak.
#
# Alignak is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alignak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Alignak.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Test the module
"""

import re
import os
import time
import pytest

from .alignak_test import AlignakTest
from alignak.modulesmanager import ModulesManager
from alignak.objects.module import Module
from alignak.basemodule import BaseModule
from alignak.brok import Brok

# Set environment variable to ask code Coverage collection
os.environ['COVERAGE_PROCESS_START'] = '.coveragerc'

import alignak_module_import_glpi

class TestModules(AlignakTest):
    """
    This class contains the tests for the module
    """

    def test_module_loading(self):
        """
        Test module loading

        Alignak module loading

        :return:
        """
        self.set_unit_tests_logger_level()
        self.setup_with_file('./cfg/alignak.cfg')
        self.assertTrue(self.conf_is_correct)
        self.show_configuration_logs()

        # An arbiter module created
        modules = [m.module_alias for m in self._arbiter.link_to_myself.modules]
        self.assertListEqual(modules, ['import-glpi'])

        # No broker modules
        modules = [m.module_alias for m in self._broker_daemon.modules]
        self.assertListEqual(modules, [])

        # No scheduler modules
        modules = [m.module_alias for m in self._scheduler_daemon.modules]
        self.assertListEqual(modules, ['inner-retention'])

        # No receiver modules
        modules = [m.module_alias for m in self._receiver.modules]
        self.assertListEqual(modules, [])

    def test_module_manager(self):
        """
        Test if the module manager manages correctly all the modules
        :return:
        """
        self.setup_with_file('./cfg/alignak.cfg')
        self.assertTrue(self.conf_is_correct)
        self.clear_logs()

        # Create an Alignak module
        mod = Module({
            'module_alias': 'import-glpi',
            'module_types': 'configuration',
            'python_name': 'alignak_module_import_glpi'
        })

        # Create the modules manager for a daemon type
        self.modulemanager = ModulesManager(self._broker_daemon)

        # Load an initialize the modules:
        #  - load python module
        #  - get module properties and instances
        self.modulemanager.load_and_init([mod])

        # Loading module
        print("Load and init")
        self.show_logs()
        i=0
        self.assert_log_match(re.escape(
            "Importing Python module 'alignak_module_import_glpi' for import-glpi..."
        ), i)
        i += 1
        # Dict order is problematic :/
        # self.assert_log_match(re.escape(
        #     "Module properties: {'daemons': ['broker'], 'phases': ['running'], "
        #     "'type': 'import-glpi', 'external': True}"
        # ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Imported 'alignak_module_import_glpi' for import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Loaded Python module 'alignak_module_import_glpi' (import-glpi)"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Alignak starting module 'import-glpi'"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Give an instance of alignak_module_import_glpi for alias: import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured GLPI uri:"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Dialog parameters, encoding: utf-8, verbose: False"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured entities tags: []"
        ), i)

        time.sleep(1)
        # Reload the module
        self.clear_logs()
        print("Reload")
        self.modulemanager.load([mod])
        self.modulemanager.get_instances()
        #
        # Loading module import-glpi
        self.show_logs()
        i = 0
        self.assert_log_match(re.escape(
            "Importing Python module 'alignak_module_import_glpi' for import-glpi..."
        ), i)
        i += 1
        # self.assert_log_match(re.escape(
        #     "Module properties: {'daemons': ['broker'], 'phases': ['running'], "
        #     "'type': 'import-glpi', 'external': True}"
        # ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Imported 'alignak_module_import_glpi' for import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Loaded Python module 'alignak_module_import_glpi' (import-glpi)"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Alignak starting module 'import-glpi'"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Give an instance of alignak_module_import_glpi for alias: import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured GLPI uri:"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Dialog parameters, encoding: utf-8, verbose: False"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured entities tags: []"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Trying to initialize module: import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "No Glpi WS uri configured, the module is disabled"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Module import-glpi is initialized."
        ), i)
        i += 1
        # self.assert_log_match(re.escape(
        #     "Module properties: {'daemons': ['broker'], 'phases': ['running'], "
        #     "'type': 'import-glpi', 'external': True}"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "Imported 'alignak_module_import_glpi' for import-glpi"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "Loaded Python module 'alignak_module_import_glpi' (import-glpi)"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "Request external process to stop for import-glpi"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "External process stopped."
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "Alignak starting module 'import-glpi'"
        # ), i)
        # i += 1
        # # self.assert_log_match(re.escape(
        # #     "Give an instance of alignak_module_import_glpi for alias: import-glpi"
        # # ), i)
        # # i += 1
        # self.assert_log_match(re.escape(
        #     "Give an instance of alignak_module_import_glpi for alias: import-glpi"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "configured GLPI uri:"
        # ), i)
        # i += 1
        # self.assert_log_match(re.escape(
        #     "configured entities tags: []"
        # ), i)

        my_module = self.modulemanager.instances[0]

        # Get list of not external modules
        self.assertListEqual([my_module], self.modulemanager.get_internal_instances())
        for phase in ['configuration']:
            self.assertListEqual([my_module], self.modulemanager.get_internal_instances(phase))
        for phase in ['late_configuration', 'running', 'retention', 'running']:
            self.assertListEqual([], self.modulemanager.get_external_instances(phase))

        # Get list of external modules
        self.assertListEqual([], self.modulemanager.get_external_instances())
        for phase in ['configuration', 'late_configuration', 'retention']:
            self.assertListEqual([], self.modulemanager.get_external_instances(phase))
        for phase in ['running']:
            self.assertListEqual([], self.modulemanager.get_external_instances(phase))

        # Clear logs
        self.clear_logs()

        # Start externa

    def test_module_start_default(self):
        """Test the module initialization function, no parameters, using default
        :return:
        """
        # Obliged to call to get a self.logger...
        self.setup_with_file('./cfg/alignak.cfg')
        self.assertTrue(self.conf_is_correct)

        # Clear logs
        self.clear_logs()

        # -----
        # Default initialization
        # -----
        # Create an Alignak module
        mod = Module({
            'module_alias': 'import-glpi',
            'module_types': 'configuration',
            'python_name': 'alignak_module_import_glpi'
        })

        instance = alignak_module_import_glpi.get_instance(mod)
        self.assertIsInstance(instance, BaseModule)
        self.show_logs()

        # self.assert_log_match(
        #     re.escape("Give an instance of alignak_module_import_glpi for alias: import-glpi"), 0)
        i = 0
        self.assert_log_match(re.escape(
            "Give an instance of alignak_module_import_glpi for alias: import-glpi"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured GLPI uri:"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "Dialog parameters, encoding: utf-8, verbose: False"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "configured entities tags: []"
        ), i)
