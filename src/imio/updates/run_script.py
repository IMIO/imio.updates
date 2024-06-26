# -*- coding: utf-8 -*-
from imio.pyutils.system import error
from imio.pyutils.system import load_var
from imio.pyutils.system import verbose
from imio.pyutils.utils import setup_logger
from plone import api

import datetime  # can be in dictionary to eval  # noqa
import logging
import sys
import transaction


LOGGER_LEVEL = 20  # 30=warning, 20=info, 10=debug
logger = logging.getLogger()


if LOGGER_LEVEL != 30:
    setup_logger(logger, level=LOGGER_LEVEL)

# Parameters check
if len(sys.argv) < 3 or not sys.argv[2].endswith("run_script.py"):
    error("Inconsistent or unexpected args len: %s" % sys.argv)
    sys.exit(0)


def run_step():
    if len(sys.argv) < 6:
        error("Missing profile and step names in args")
        sys.exit(0)
    profile = sys.argv[4]
    step = sys.argv[5]
    if not profile.startswith("profile-"):
        profile = "profile-%s" % profile
    # obj is plone site
    obj = obj  # noqa
    if step == "_all_":
        verbose('Running all "%s" steps on %s' % (profile, obj.absolute_url_path()))
        ret = obj.portal_setup.runAllImportStepsFromProfile(profile)
    else:
        verbose('Running "%s#%s" step on %s' % (profile, step, obj.absolute_url_path()))
        ret = obj.portal_setup.runImportStepFromProfile(profile, step, run_dependencies=False)

    if "messages" in ret:
        for step in ret["messages"]:
            verbose("%s:\n%s" % (step, ret["messages"][step]))
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
    obj = obj  # noqa
    mig = Migrator(obj)
    if profile == "_all_":
        verbose("Running all upgrades on %s" % (obj.absolute_url_path()))
        mig.upgradeAll()
    else:
        verbose('Running "%s" upgrade on %s' % (profile, obj.absolute_url_path()))
        mig.upgradeProfile(profile, olds=(len(sys.argv) >= 5 and sys.argv[5:] or []))
    transaction.commit()


def auth():
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod

    # we add the external method cputils_install
    app = app  # noqa
    if not hasattr(app, "cputils_install"):
        manage_addExternalMethod(app, "cputils_install", "", "CPUtils.utils", "install")
    # we run this method
    app.cputils_install(app)
    # change authentication
    status = sys.argv[4]
    app.cputils_change_authentication_plugins(activate=status, dochange="1")
    verbose("Authentication plugins %s" % (status == "0" and "disabled" or "enabled"))
    transaction.commit()


def message():
    from collective.messagesviewlet.utils import _richtextval
    from collective.messagesviewlet.utils import add_message

    id, warning_file = sys.argv[4:6]
    dic = {}
    load_var(warning_file, dic)
    params = dic[id]
    delete = params.pop("delete", False)
    modified = False
    # verbose("Given dictionary: %s" % params)
    config = obj["messages-config"]  # noqa
    if delete:
        if id in config:
            api.content.delete(config[id])
            transaction.commit()
        return
    elif id in config:
        msg = config[id]
        verbose("Updating message with those values: %s" % params)
        if "text" in params:
            msg.text = _richtextval(params.pop("text"))
    # create a new message
    else:
        verbose("Creating message with those values: %s" % params)
        attrs = {}
        attrs.get("msg_type", "warning")
        msg = add_message(id, params.get("title", "imio.updates"), params["text"], **attrs)

    for key in params:
        if key not in ("text", "activate"):
            setattr(msg, key, params[key])
            modified = True
    if modified:
        msg.reindexObject()

    try:
        if params.get("activate", True):
            api.content.transition(msg, transition="activate")
            verbose("Message %s activated" % msg)
        else:
            api.content.transition(msg, transition="deactivate")
            verbose("Message %s deactivated" % msg)
    except Exception:
        pass
    transaction.commit()


info = [
    "You can pass following parameters (with the first one always script number):",
    "step: run profile step",
    "upgrade: run profile upgrade",
    "auth: enable/disable authentication plugins",
    "message",
]
scripts = {"step": run_step, "upgrade": run_upgrade, "auth": auth, "message": message}

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    error("Bad script parameter")
    verbose("\n>> =>".join(info))
    sys.exit(0)

with api.env.adopt_user(username="admin"):
    scripts[sys.argv[3]]()
