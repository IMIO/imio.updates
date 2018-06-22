# -*- coding: utf-8 -*-

import sys
import transaction
from plone import api


def verbose(msg):
    print '>> %s' % msg


def error(msg):
    print >> sys.stderr, '!! %s' % msg


# Parameters check
if len(sys.argv) < 3 or not sys.argv[2].endswith('run_script.py'):
    error("Inconsistent or unexpected args len: %s" % sys.argv)
    sys.exit(0)


def run_step():
    if len(sys.argv) < 6:
        error("Missing profile and step names in args")
        sys.exit(0)
    profile = sys.argv[4]
    step = sys.argv[5]
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


def run_upgrade():
    if len(sys.argv) < 5:
        error("Missing profile name in args")
        sys.exit(0)
    profile = sys.argv[4]
    from imio.migrator.migrator import Migrator
    # obj is plone site
    mig = Migrator(obj)
    if profile == '_all_':
        verbose('Running all upgrades on %s' % (obj.absolute_url_path()))
        mig.upgradeAll()
    else:
        verbose('Running "%s" upgrade on %s' % (profile, obj.absolute_url_path()))
        mig.upgradeProfile(profile)
    transaction.commit()


def run_auth():
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
    # we add the external method cputils_install
    if not hasattr(app, 'cputils_install'):
        manage_addExternalMethod(app, 'cputils_install', '', 'CPUtils.utils', 'install')
    # we run this method
    app.cputils_install(app)
    # change authentication
    status = sys.argv[4]
    app.cputils_change_authentication_plugins(activate=status, dochange='1')
    verbose("Authentication plugins %s" % (status == '0' and 'disabled' or 'enabled'))
    transaction.commit()


info = ["You can pass following parameters (with the first one always script number):", "step: run profile step",
        "upgrade: run profile upgrade", "auth: enable/disable authentication plugins"]
scripts = {'step': run_step, 'upgrade': run_upgrade, 'auth': run_auth}

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    error("Bad script parameter")
    verbose('\n>> =>'.join(info))
    sys.exit(0)

with api.env.adopt_user(username='admin'):
    scripts[sys.argv[3]]()
