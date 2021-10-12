#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from imio.helpers.security import setup_logger
from imio.pyutils.system import error, verbose
from plone import api
from Products.CPUtils.Extensions.utils import store_user_properties

# Parameters check
if len(sys.argv) < 3 or not sys.argv[2].endswith('run_scripts.py'):
    error("Inconsistent or unexpected args len: %s" % sys.argv)
    sys.exit(0)

setup_logger()


def export_infos():
    portal = obj
    ret = store_user_properties(portal)
    verbose(ret)
    ret = portal.manage_exportObject(id='users_properties')
    ret = portal.manage_exportObject(id='acl_users')


def import_infos()
    portal = obj


info = ["You can pass following parameters (with the first one always script name):", "export_infos: run ports update"]
scripts = {'export_infos': export_infos}

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    error("Bad script parameter")
    verbose('\n>> =>'.join(info))
    sys.exit(0)

with api.env.adopt_user(username='admin'):
    scripts[sys.argv[3]]()
