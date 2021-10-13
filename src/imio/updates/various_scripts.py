#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
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
    from OFS.Folder import manage_addFolder
    if 'oldacl' not in portal:
        manage_addFolder(portal, 'oldacl')
    oa = portal['oldacl']
    if 'users_properties' not in oa:
        oa.manage_importObject('users_properties.zexp')
    if 'acl_users' not in oa:
        oa.manage_importObject('acl_users.zexp')
    ret = recreate_users_groups(portal, only_users=True, dochange='1')
    users = re.findall('(is added| alredy exists)', ret, re.I)
    if 'Problem creating user' in ret or not users:
        error(ret)
        raise Exception('Error when creating users')
    verbose(ret)
    verbose('USERS created: {}'.format(len(users)))
    ret = load_user_properties(portal, dochange='1')
    props = re.findall('has changed properties', ret, re.I)
    verbose(ret)
    verbose('PROPS updated: {}'.format(len(props)))
    if len(props) != len(users):
        error('Users and props doesnt match')
        raise Exception('Counts doesnt match')
    transaction.commit()


info = ["You can pass following parameters (with the first one always script name):", "export_infos: run ports update"]
scripts = {'export_infos': export_infos, 'import_infos': import_infos}

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    error("Bad script parameter")
    verbose('\n>> =>'.join(info))
    sys.exit('Bad script parameter')

with api.env.adopt_user(username='admin'):
    scripts[sys.argv[3]]()
