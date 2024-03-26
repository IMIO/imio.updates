from __future__ import print_function

from plone import api

import argparse
import os
import logging
import transaction


LOGGER_LEVEL = 20


def run_step(profile, step):
    if not profile.startswith('profile-'):
        profile = 'profile-%s' % profile
    # obj is plone site
    if step == '_all_':
        verbose('Running all "%s" steps on %s' % (profile, obj.absolute_url_path()))
        ret = obj.portal_setup.runAllImportStepsFromProfile(profile)
    else:
        verbose('Running "%s#%s" step on %s' % (profile, step, obj.absolute_url_path()))
        ret = obj.portal_setup.runImportStepFromProfile(profile, step, run_dependencies=False)

    if 'messages' in ret:
        for step in ret['messages']:
            verbose("%s:\n%s" % (step, ret['messages'][step]))
    else:
        verbose("No output")
    transaction.commit()


parser = argparse.ArgumentParser("Run 1 upgrade steps for a given profile")
parser.add_argument('profile', type=str, help="Profile to upgrade.")
parser.add_argument('step', type=str, help='Target step')
parser.add_argument('-c', dest="my_path")
args = parser.parse_args()

sys.path[0:0] = [ os.path.dirname(args.my_path)]
from script_utils import setup_logger
from script_utils import verbose


setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    run_upgrade(args.profile, args.step)
