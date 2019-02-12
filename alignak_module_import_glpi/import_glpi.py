#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2019:
#    Frederic Mohier, frederic.mohier@gmail.com
#
# Copyright (c) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    David Durieux, d.durieux@siprossii
#    Frederic Mohier, frederic.mohier@gmail.com
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


"""
This Class is a plugin for the Shinken/Alignak Arbiter. It connects to a Glpi instance
with the Web services plugin installed to get all hosts and configuration.
"""

import logging
import xmlrpclib

from alignak.basemodule import BaseModule

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
for handler in logger.parent.handlers:
    if isinstance(handler, logging.StreamHandler):
        logger.parent.removeHandler(handler)

# pylint: disable=invalid-name
properties = {
    'daemons': ['arbiter'],
    'type': 'import-glpi',
    'external': False,
    'phases': ['configuration'],
}


# called by the plugin manager to get a broker
def get_instance(mod_conf):
    """
    Return a module instance for the modules manager

    :param mod_conf: the module properties as defined globally in this file
    :return:
    """
    logger.info("Give an instance of %s for alias: %s", mod_conf.python_name, mod_conf.module_alias)
    return Glpi_arbiter(mod_conf)


# Just get hostname from a GLPI webservices
class Glpi_arbiter(BaseModule):
    """
    NSCA collector module main class
    """
    def __init__(self, mod_conf):
        """
        Module initialization

        mod_conf is a dictionary that contains:
        - all the variables declared in the module configuration file
        - a 'properties' value that is the module properties as defined globally in this file

        :param mod_conf: module configuration file as a dictionary
        """
        BaseModule.__init__(self, mod_conf)

        # pylint: disable=global-statement
        global logger
        logger = logging.getLogger('alignak.module.%s' % self.alias)

        logger.debug("inner properties: %s", self.__dict__)
        logger.debug("received configuration: %s", mod_conf.__dict__)

        self.uri = getattr(mod_conf, 'uri', '')
        self.verbose = (getattr(mod_conf, 'verbose', '') != '')
        self.login_name = getattr(mod_conf, 'login_name', 'alignak')
        self.login_password = getattr(mod_conf, 'login_password', 'alignak')
        logger.info("configured GLPI uri: %s", self.uri)

        # tag is still managed for compatibility purposes, better use tags!
        self.tag = getattr(mod_conf, 'tag', '')
        self.tags = getattr(mod_conf, 'tags', '')

        if not self.tags:
            self.tags = self.tag
        self.tags = self.tags.split(',')
        if self.tag:
            self.tags += self.tag
        logger.info("configured entities tags: %s", self.tags)

        # Server connection
        self.con = None
        self.session = None

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        """
        Connect to the Glpi Web Service.
        """
        self.con = None
        if not self.uri:
            logger.info("No Glpi WS uri configured, the module is disabled")
            # True because False will make the module get reloaded endlessly!
            return True

        try:
            logger.info("Connecting to %s", self.uri)
            self.con = xmlrpclib.ServerProxy(self.uri, encoding='utf-8', verbose=self.verbose)
            logger.info("Connection opened")
            logger.info("Authentication in progress...")
            arg = {'login_name': self.login_name, 'login_password': self.login_password}
            res = self.con.glpi.doLogin(arg)
            self.session = res['session']
            logger.info("Authenticated, session : %s", self.session)
        except Exception as e:
            logger.error("Glpi WS connection error: %s", str(e))

        return self.con is not None

    # Ok, main function that will load config from GLPI
    def get_objects(self):
        r = {'commands': [],
             'timeperiods': [],
             'hosts': [],
             'hostgroups': [],
             'servicestemplates': [],
             'services': [],
             'contacts': []}

        if not self.session:
            logger.error("No opened session, I cannot provide any objects to the arbiter.")
            return r

        for tag in self.tags:
            tag = tag.strip()
            if tag:
                logger.info(" Getting configuration for entity tagged with '%s'", tag)
            else:
                logger.info(" Getting configuration for all entities")

            # iso8859 is necessary because Arbiter does not deal with UTF8 objects !
            arg = {'session': self.session, 'iso8859': '1', 'tag': tag}

            try:
                # Get commands
                commands = self.con.monitoring.shinkenCommands(arg)
                logger.info("Got %s commands", len(commands) if commands else 'no')
                for item in commands:
                    logger.debug("-: %s", item)

                    if item not in r['commands']:
                        logger.info("- command: %s", item['command_name'])
                        r['commands'].append(item)

                # Get contacts
                contacts = self.con.monitoring.shinkenContacts(arg)
                logger.info("Got %s contacts", len(contacts) if contacts else 'no')
                for item in contacts:
                    logger.debug("-: %s", item)

                    if item not in r['contacts']:
                        logger.info("- contact: %s", item['contact_name'])
                        r['contacts'].append(item)

                # Get timeperiods
                timeperiods = self.con.monitoring.shinkenTimeperiods(arg)
                logger.info("Got %s timeperiods", len(timeperiods) if timeperiods else 'no')
                for item in timeperiods:
                    logger.debug("-: %s", item)

                    if item not in r['timeperiods']:
                        logger.info("- timeperiod: %s", item['timeperiod_name'])
                        r['timeperiods'].append(item)

                # Get hosts
                hosts = self.con.monitoring.shinkenHosts(arg)
                logger.info("Got %s hosts", len(hosts) if hosts else 'no')
                for item in hosts:
                    logger.debug("-: %s ", item)

                    if item not in r['hosts']:
                        logger.info("- host: %s", item['host_name'])
                        r['hosts'].append(item)

                # Get hostgroups
                hostgroups = self.con.monitoring.shinkenHostgroups(arg)
                logger.info("Got %s hostgroups", len(hostgroups) if hostgroups else 'no')
                for item in hostgroups:
                    logger.debug("-: %s ", item)

                    if item not in r['hostgroups']:
                        logger.info("- hostgroup: %s", item['hostgroup_name'])
                        r['hostgroups'].append(item)

                # Get templates
                templates = self.con.monitoring.shinkenTemplates(arg)
                logger.info("Got %s services templates", len(templates) if templates else 'no')
                for item in templates:
                    logger.debug("-: %s", item)

                    if item not in r['servicestemplates']:
                        logger.info("- service template: %s", item['name'])
                        r['servicestemplates'].append(item)

                # Get services
                services = self.con.monitoring.shinkenServices(arg)
                logger.info("Got %s services", len(services) if services else 'no')
                for item in services:
                    logger.debug("-: %s", item)

                    if item not in r['services']:
                        logger.info("- service: %s/%s", item['host_name'], item['service_description'])
                        r['services'].append(item)
            except Exception as exp:
                logger.error("Exception when getting tag '%s': %s / %s", tag, type(exp), str(exp))

        logger.info("Sending all data to the Arbiter:")
        logger.info("- %d commands to Arbiter", len(r['commands']))
        logger.info("- %d timeperiods to Arbiter", len(r['timeperiods']))
        logger.info("- %d contacts to Arbiter", len(r['contacts']))
        logger.info("- %d hosts to Arbiter", len(r['hosts']))
        logger.info("- %d hosts groups to Arbiter", len(r['hostgroups']))
        logger.info("- %d services templates to Arbiter", len(r['servicestemplates']))
        logger.info("- %d services to Arbiter", len(r['services']))

        r['services'] = r['servicestemplates'] + r['services']
        del r['servicestemplates']

        return r
