from __future__ import print_function

from plone import api
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin

import argparse
import os
import sys
import transaction


LOGGER_LEVEL = 20


def auth(status):
    plugins = obj.acl_users.plugins
    auth_plugins = plugins.getAllPlugins(plugin_type="IAuthenticationPlugin")
    if status == 1:
        for plugin in auth_plugins['available']:
            verbose("Activate plugins %s for %s" % (plugin, obj))
            plugins.activatePlugin(IAuthenticationPlugin, plugin)
    elif status == 0:
        for plugin in auth_plugins['active']:
            verbose("Deactivate plugins %s for %s" % (plugin, obj))
            plugins.deactivatePlugin(IAuthenticationPlugin, plugin)

    verbose("Authentication plugins %s" % (status == 0 and 'disabled' or 'enabled'))
    transaction.commit()


parser = argparse.ArgumentParser("Enable or disable auth plugins")
parser.add_argument('status', type=int, choices=[0, 1], help="0 : disable, 1 : enable")
parser.add_argument('-c', dest="my_path")
args = parser.parse_args()

sys.path[0:0] = [ os.path.dirname(args.my_path)]
from script_utils import setup_logger
from script_utils import verbose


setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    auth(args.status)
