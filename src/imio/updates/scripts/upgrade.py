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


def run_upgrade(profile, steps=[]):
    from imio.migrator.migrator import Migrator
    # obj is plone site
    mig = Migrator(obj)
    if profile == '_all_':
        verbose('Running all upgrades on %s' % (obj.absolute_url_path()))
        mig.upgradeAll()
    else:
        verbose('Running "%s" upgrade on %s' % (profile, obj.absolute_url_path()))
        mig.upgradeProfile(profile, olds=steps)
    transaction.commit()


parser = argparse.ArgumentParser("Upgrades packages")
parser.add_argument('profile', type=str, help="profile to upgrade. '_all_' to upgrade every profiles available")
parser.add_argument('-s', '--step', dest='steps', nargs='*', default=[],
                    help='Upgrade steps to run for the given profile')
parser.add_argument('-c', dest="my_path")
args = parser.parse_args()

setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    run_upgrade(args.profile, args.steps)
