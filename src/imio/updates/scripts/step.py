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

setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    run_upgrade(args.profile, args.step)
