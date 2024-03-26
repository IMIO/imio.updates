from __future__ import print_function

from plone import api

import argparse
import os
import logging
import transaction


LOGGER_LEVEL = 20


def run_upgrade(profiles, steps=[]):
    from imio.migrator.migrator import Migrator
    # obj is plone site
    mig = Migrator(obj)
    profile_to_apply = ['Products.CMFPlone:plone'] + profiles.split(' ')
    for profile in profile_to_apply:
        verbose('Running "%s" upgrade on %s' % (profile, obj.absolute_url_path()))
        mig.upgradeProfile(profile, olds=steps)
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

sys.path[0:0] = [ os.path.dirname(args.my_path)]
from script_utils import setup_logger
from script_utils import verbose


setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    run_upgrade(args.profile, args.steps)
