# -*- coding: utf-8 -*-

from imio.pyutils.system import dump_var
from imio.pyutils.system import load_var
from imio.pyutils.system import read_dir
from imio.pyutils.system import read_file
from plone import api
from Products.CPUtils.Extensions.utils import tobytes

import os
import sys

types_to_count = {'dms': ('dmsincomingmail', 'dmsoutgoingmail', 'task', 'organization', 'person', 'held_position',
                          'dmsommainfile'),
                  'pst': ('projectspace', 'strategicobjective', 'operationalobjective', 'pstaction', 'pstsubaction',
                          'task'),
                  '': ()}

zopedir = os.path.expanduser("~")
instdir = os.getenv('PWD')
dumpfile = os.path.join(zopedir, 'inst_infos.dic')
maindic = {}

# get instance name
inst = instdir.split('/')[-1]
dic = {inst: {'types': {}, 'users': 0, 'groups': 0, 'bl_nm': '', 'fs_sz': 0, 'bl_sz': 0}}
infos = dic[inst]

# get dumped dictionary
load_var(dumpfile, maindic)

# obj is the portal site
portal = obj

# get first parameter
tool = sys.argv[-1]
if tool not in types_to_count.keys():
    tool = ''

# get types count
lengths = dict(portal.portal_catalog.Indexes['portal_type'].uniqueValues(withLengths=True))
for typ in types_to_count.get(tool, []):
    infos['types'][typ] = lengths.get(typ, 0)

# get users count, only keep users that are in a group
users = portal.portal_membership.searchForMembers()
count = 0
for user in users:
    user_groups = user.getGroups()
    if user_groups and user_groups != ['AuthenticatedUsers']:
        count = count + 1
infos['users'] = count

# get groups count
infos['groups'] = len(api.group.get_groups())

# sizes. app is zope
# filestorage
dbs = app['Control_Panel']['Database']
for db in dbs.getDatabaseNames():
    size = dbs[db].db_size()
    size = int(tobytes(size[:-1] + ' ' + size[-1:] + 'B'))
    if size > infos['fs_sz']:
        infos['fs_sz'] = size
# blobstorage
vardir = os.path.join(instdir, 'var')
for blobdirname in read_dir(vardir, only_folders=True):
    if not blobdirname.startswith('blobstorage'):
        continue
    sizefile = os.path.join(vardir, blobdirname, 'size.txt')
    if os.path.exists(sizefile):
        lines = read_file(sizefile)
        size = int(lines[0])
        if size > infos['bl_sz']:
            infos['bl_sz'] = size
            infos['bl_nm'] = blobdirname

# dump dictionary
maindic['inst'].update(dic)
dump_var(dumpfile, maindic)
