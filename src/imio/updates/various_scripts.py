#!/usr/bin/python3
# -*- coding: utf-8 -*-

from imio.helpers.security import setup_logger
from imio.pyutils.system import error
from imio.pyutils.system import verbose
from plone import api
from Products.CPUtils.Extensions.utils import load_user_properties
from Products.CPUtils.Extensions.utils import recreate_users_groups
from Products.CPUtils.Extensions.utils import store_user_properties

import re
import sys
import transaction


# Parameters check
if len(sys.argv) < 3 or not sys.argv[2].endswith('various_scripts.py'):
    error("Inconsistent or unexpected args len: %s" % sys.argv)
    sys.exit('Inconsistent args')

setup_logger()


def export_users():
    """Export acl_users and users_properties file"""
    portal = obj
    ret = store_user_properties(portal)
    verbose(ret)
    transaction.commit()
    ret = portal.manage_exportObject(id='users_properties')
    ret = portal.manage_exportObject(id='acl_users')


def import_users():
    """Import acl_users and recreate users with their properties"""
    portal = obj
    from OFS.Folder import manage_addFolder
    commit = False
    if 'oldacl' not in portal:
        manage_addFolder(portal, 'oldacl')
        commit = True
    oa = portal['oldacl']
    if 'users_properties' not in oa:
        oa.manage_importObject('users_properties.zexp')
        commit = True
    if 'acl_users' not in oa:
        oa.manage_importObject('acl_users.zexp')
        commit = True
    if commit:
        transaction.commit()
    ret = recreate_users_groups(portal, only_users=True, dochange='1')
    users = re.findall('(is added| already exists)', ret, re.I)
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


scripts = {'export_users': export_users, 'import_users': import_users}
info = ["You can pass following parameters (with the first one always script name):"]
info.extend(['"{}": "{}"'.format(k, v.__doc__) for k, v in scripts.items()])

if len(sys.argv) < 4 or sys.argv[3] not in scripts:
    verbose('\n>> =>'.join(info))
    sys.exit('Bad script parameter')

with api.env.adopt_user(username='admin'):
    scripts[sys.argv[3]]()
