from __future__ import print_function
import argparse
import logging
import transaction

from plone import api

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
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
    # we add the external method cputils_install
    if not hasattr(app, 'cputils_install'):
        manage_addExternalMethod(app, 'cputils_install', '', 'CPUtils.utils', 'install')
    # we run this method
    app.cputils_install(app)
    # change authentication
    app.cputils_change_authentication_plugins(activate=status, dochange='1')
    verbose("Authentication plugins %s" % (status == '0' and 'disabled' or 'enabled'))
    transaction.commit()


parser = argparse.ArgumentParser("Enable or disable auth plugins")
parser.add_argument('status', type=int, choices=[0, 1], help="0 : disable, 1 : enable")
parser.add_argument('-c', dest="my_path")
args = parser.parse_args()

setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    auth(args.status)
