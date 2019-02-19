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
import sys
import time
import logging
import traceback

try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc

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
    return GlpiConfiguration(mod_conf)


class GlpiConfiguration(BaseModule):
    """
    Get Alignak objects configuration from a GLPI instance
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

        self.alignak_name = getattr(mod_conf, 'alignak_name', '')
        self.uri = getattr(mod_conf, 'uri', '')
        logger.info("configured GLPI uri: %s", self.uri)

        self.encoding = getattr(mod_conf, 'encoding', 'utf-8')
        self.verbose = (getattr(mod_conf, 'verbose', '') != '')
        logger.info("Dialog parameters, encoding: %s, verbose: %s", self.encoding, self.verbose)

        self.login_name = getattr(mod_conf, 'login_name', 'alignak')
        self.login_password = getattr(mod_conf, 'login_password', 'alignak')

        # Note that order matters! Get time periods and contacts after all other objects
        self.ws = [
            {
                'type': 'command',
                'method': getattr(mod_conf, 'ws_command',
                                  'monitoring.getConfigCommands')
            },
            {
                'type': 'host',
                'method': getattr(mod_conf, 'ws_host',
                                  'monitoring.getConfigHosts')
            },
            {
                'type': 'hostgroup',
                'method': getattr(mod_conf, 'ws_hostgroup',
                                  'monitoring.getConfigHostgroups')
            },
            {
                'type': 'servicestemplate',
                'method': getattr(mod_conf, 'ws_servicestemplate',
                                  'monitoring.getConfigServicesTemplates')
            },
            {
                'type': 'service',
                'type_name': 'service_description',
                'method': getattr(mod_conf, 'ws_service',
                                  'monitoring.getConfigServices')
            },
            {
                'type': 'realm',
                'method': getattr(mod_conf, 'ws_realm',
                                  'monitoring.getConfigRealms')
            },
            {
                'type': 'timeperiod',
                'method': getattr(mod_conf, 'ws_timeperiod',
                                  'monitoring.getConfigTimeperiods')
            },
            {
                'type': 'contact',
                'method': getattr(mod_conf, 'ws_contact',
                                  'monitoring.getConfigContacts')
            }
        ]

        # tag is the monitoring framework identifier
        self.tag = getattr(mod_conf, 'tag', '')
        if not self.tag:
            self.tag = self.alignak_name

        self.entities = getattr(mod_conf, 'entities', '')
        self.entities = self.entities.split(',')
        if self.entities and not self.entities[0]:
            self.entities = []
        logger.info("configured entities tags: %s", self.entities)

        # Server connection
        self.con = None
        self.session = None

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
            self.con = xc.ServerProxy(self.uri, encoding='utf-8', verbose=self.verbose)
            logger.info("Connection opened")
            logger.info("Authentication in progress...")
            res = self.con.glpi.doLogin({
                'login_name': self.login_name,
                'login_password': self.login_password})
            self.session = res['session']
            logger.info("Authenticated, session : %s", self.session)
        except Exception as e:
            logger.error("Glpi WS connection error: %s", str(e))

        return self.con is not None

    def do_loop_turn(self):
        """This function is called/used when you need a module with
        a loop function (and use the parameter 'external': True)
        """
        logger.info("In loop")
        time.sleep(1)

    def get_objects(self):
        """
        Get configuration objects from GLPI assuming the session was opened
        on module initialization.

        :return:
        """
        result = {
            'commands': [],
            'realms': [],
            'hosts': [],
            'hostgroups': [],
            'servicestemplates': [],
            'services': [],
            'contacts': [],
            'timeperiods': []
        }

        if not self.session:
            logger.error("No opened session, I cannot provide any objects to the arbiter.")
            return result

        # Set entity as empty to get all possible entities from Glpi
        parameters = {
            'session': self.session,
            # 'file_output': '1',
            'entity': ''
        }
        if self.tag:
            parameters['tag'] = self.tag
        if self.alignak_name:
            parameters['name'] = self.alignak_name
        if self.encoding:
            parameters['encoding'] = self.encoding

        if not self.entities:
            try:
                # Get items, request the configured WS
                items = self.con.monitoring.getMonitoredEntities(parameters)
                logger.info("Got %s entities", len(items) if items else 'no')
                for item in items:
                    logger.debug("-: %s", item)

                    if item not in self.entities:
                        logger.info("- entity: %s", item)
                        self.entities.append(item)
            except xc.Fault as exp:
                logger.error("XML RPC fault: %s / %s",
                             exp.faultCode, exp.faultString)
            except xc.ProtocolError as exp:
                logger.error("XML RPC protocol error: %s / %s, url: %s",
                             exp.errcode, exp.errmsg, exp.url)
            except Exception as exp:
                logger.error("Exception when getting entities list: %s / %s", type(exp), str(exp))

        if not self.entities:
            logger.warning("No entities are available to get monitoring configuration.")
            return result

        for entity in self.entities:
            entity = entity.strip()
            if entity:
                logger.info(" Getting configuration for entity tagged with '%s'", entity)
            else:
                logger.info(" Getting configuration for all entities")

            parameters['entity'] = entity

            for ws in self.ws:
                if not ws['method']:
                    continue

                try:
                    if sys.version_info[0] < 3:
                        if ws['type'] == 'command':
                            items = self.con.monitoring.getConfigCommands(parameters)
                        if ws['type'] == 'host':
                            items = self.con.monitoring.getConfigHosts(parameters)
                        if ws['type'] == 'hostgroup':
                            items = self.con.monitoring.getConfigHostgroups(parameters)
                        if ws['type'] == 'servicestemplate':
                            items = self.con.monitoring.getConfigServicesTemplates(parameters)
                        if ws['type'] == 'service':
                            items = self.con.monitoring.getConfigServices(parameters)
                        if ws['type'] == 'contact':
                            items = self.con.monitoring.getConfigContacts(parameters)
                        if ws['type'] == 'realm':
                            items = self.con.monitoring.getConfigRealms(parameters)
                        if ws['type'] == 'timeperiod':
                            items = self.con.monitoring.getConfigTimeperiods(parameters)
                    else:
                        # Get items, request the configured WS
                        fct = getattr(self.con, ws['method'], None)
                        if fct:
                            items = fct(parameters)

                    logger.info("Got %s %ss", len(items) if items else 'no', ws['type'])
                    for item in items:
                        logger.debug("-: %s", item)

                        if item not in result['%ss' % ws['type']]:
                            logger.info("- %s: %s", ws['type'], item)
                            if 'register' in item:
                                # Item is a template
                                logger.info("- %s template: %s", ws['type'], item['name'])
                            else:
                                type_name = ws.get('type_name', '%s_name' % ws['type'])
                                logger.info("- %s: %s", ws['type'], item[type_name])
                            type_list = ws.get('type_list', '%ss' % ws['type'])
                            result[type_list].append(item)
                except xc.Fault as exp:
                    logger.error("XML RPC fault: %s / %s",
                                 exp.faultCode, exp.faultString)
                except xc.ProtocolError as exp:
                    logger.error("XML RPC protocol error: %s / %s, url: %s",
                                 exp.errcode, exp.errmsg, exp.url)
                except Exception as exp:
                    logger.error("Exception when getting tag '%s': %s / %s", entity, type(exp),
                                 str(exp))
                    logger.error(traceback.print_exc())

        # Group services and services templates
        result['services'] = result['servicestemplates'] + result['services']
        del result['servicestemplates']

        logger.info("Returned data:")
        for ws in result:
            logger.info("- %d %s", len(result[ws]), ws)

        return result
