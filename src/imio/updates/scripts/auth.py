from __future__ import print_function
import argparse
import logging
import transaction

from plone import api
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin

LOGGER_LEVEL = 20


def verbose(*messages):
    print(">>", " ".join(messages))

def setup_logger(level=20):
    """
        When running "bin/instance run ...", the logger level is 30 (warn).
        It is possible to set it to 20 (info) or 10 (debug).
    """
    if level == 30:
        return

    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logging.root.handlers:
        if handler.level == 30 and handler.formatter is not None:
            handler.level = level
            break

def auth(status):
    plugins = obj.acl_users.plugins
    auth_plugins = plugins.getAllPlugins(plugin_type="IAuthenticationPlugin")
    import ipdb
    ipdb.set_trace()
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

setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    auth(args.status)
