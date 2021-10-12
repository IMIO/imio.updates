#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import transaction

from imio.helpers.security import setup_logger
from imio.pyutils.system import error, verbose
from plone import api
from Products.CPUtils.Extensions.utils import load_user_properties
from Products.CPUtils.Extensions.utils import recreate_users_groups
from Products.CPUtils.Extensions.utils import store_user_properties

# Parameters check
if len(sys.argv) < 3 or not sys.argv[2].endswith('various_scripts.py'):
    error("Inconsistent or unexpected args len: %s" % sys.argv)
    sys.exit('Inconsistent args')

setup_logger()


def export_infos():
    portal = obj
    ret = store_user_properties(portal)
    verbose(ret)
    ret = portal.manage_exportObject(id='users_properties')
    ret = portal.manage_exportObject(id='acl_users')


def import_infos():
    portal = obj
    transaction.get()
    if 'oldacl' not in portal:
        portal.manage_addFolder('oldacl')
    oa = portal['oldacl']
    # if 'users_properties' not in oa:
    #     oa.manage_importObject('users_properties.zexp')
    # if 'acl_users' not in oa:
    #     oa.manage_importObject('acl_users.zexp')
    # ret = recreate_users_groups(only_users=True, dochange='1')
    # verbose(ret)
    # ret = load_user_properties(portal, dochange='1')
    # verbose(ret)


info = ["You can pass following parameters (with the first one always script name):", "export_infos: run ports update"]
scripts = {'export_infos': export_infos, 'import_infos': import_infos}

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    error("Bad script parameter")
    verbose('\n>> =>'.join(info))
    sys.exit('Bad script parameter')

with api.env.adopt_user(username='admin'):
    scripts[sys.argv[3]]()
