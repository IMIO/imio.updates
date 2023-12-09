# -*- coding: utf-8 -*-
# Run by imio.updates : bin/update_instances -c ~/imio.updates/src/imio/updates/inst_infos.py dms
# or with bin/instance1 -Ostavelot run imio.updates/src/imio/updates/inst_infos.py dms

from datetime import datetime
from dateutil.relativedelta import relativedelta
# from imio.pyutils.system import get_git_tag
from imio.pyutils.system import dump_var
from imio.pyutils.system import error
from imio.pyutils.system import load_var
from imio.pyutils.system import runCommand
from plone import api
from Products.CMFPlone.utils import base_hasattr
from Products.CPUtils.Extensions.utils import tobytes

import json
import os
import sys


types_to_count = {
    'dms':
    {'portal_type':
        ('dmsincomingmail', 'dmsincoming_email', 'dmsoutgoingmail', 'task', 'organization',
         'person', 'held_position', 'dmsommainfile'), },
    'pst':
    {'portal_type':
        ('projectspace', 'strategicobjective', 'operationalobjective',
         'pstaction', 'pstsubaction', 'task'), },
    'pm':
    {'meta_type':
        ('Meeting', 'MeetingItem', 'MeetingConfig'),
     'portal_type':
        ('annex', 'annexDecision', 'meetingadvice', 'meetingadvicefinances'), },
    'urban':
    {'portal_type':
         ('File',), },
}

zopedir = os.path.expanduser("~")
instdir = os.getenv('PWD')
dumpfile = os.path.join(zopedir, 'inst_infos.dic')
maindic = {}


def get_git_tag(path):
    # TODO removed it when imio.pyutils is at 0.25 version in instances
    cmd = 'git --git-dir={}/.git describe --tags'.format(path)
    (out, err, code) = runCommand(cmd)
    if code or err:
        error("Problem in command '{}': {}".format(cmd, err))
        return 'NO TAG'
    return out[0].strip('\n')


# get instance name
inst = instdir.split('/')[-1]
dic = {inst: {'types': {}, 'users': 0, 'groups': 0, 'fs_sz': 0, 'bl_sz': 0, 'checks': {}, 'admins': [],
              'tag': get_git_tag(instdir)}}
infos = dic[inst]

# get dumped dictionary
load_var(dumpfile, maindic)

# obj is the portal site
portal = obj  # noqa F821

# get first parameter
tool = sys.argv[-1]
if tool not in types_to_count.keys():
    tool = ''

# get types count
catalog = portal.portal_catalog
now = datetime.now()
this_year = now.year
l_y_frame = now - relativedelta(years=1)  # last year frame

for index_name, type_names in types_to_count.get(tool, []).items():
    lengths = dict(catalog.Indexes[index_name].uniqueValues(withLengths=True))
    for type_name in type_names:
        tdic = {'tot': lengths.get(type_name, 0), 'years': {}, 'first': ''}
        first_year = this_year
        brains = catalog.unrestrictedSearchResults(**{index_name: [type_name], 'sort_on': 'created', 'sort_limit': 1})
        if brains:
            dte = brains[0].creation_date
            tdic['first'] = dte.strftime('%Y%m%d-%H:%M:%S')
            first_year = dte.year()  # DateTime
        # all years
        for year in range(first_year, this_year+1):
            year_range = {'query': (datetime(year, 1, 1), datetime(year+1, 1, 1)), 'range': 'min:max'}
            tdic['years'][str(year)] = len(catalog.unrestrictedSearchResults(
                                           **{index_name: type_name, 'created': year_range}))
        # last year frame
        year_range = {'query': (now, l_y_frame), 'range': 'min:max'}
        tdic['frame'] = len(catalog.unrestrictedSearchResults(**{index_name: type_name, 'created': year_range}))
        infos['types'][type_name] = tdic


def check_wsclient():
    """Check if wsclient is activated """
    prefix = 'imio.pm.wsclient.browser.settings.IWS4PMClientSettings'
    if not api.portal.get_registry_record('{}.pm_url'.format(prefix), default=False):
        return ''
    gen_act = api.portal.get_registry_record('{}.generated_actions'.format(prefix))
    if gen_act and gen_act[0].get('permissions') and gen_act[0]['permissions'] != 'Modify view template':
        return api.portal.get_registry_record('{}.pm_url'.format(prefix))
    return ''


# checks
if tool == 'pm':
    brains = catalog(meta_type='MeetingConfig')
    infos['checks']['classifier'] = len(portal.reference_catalog(relationship='ItemClassification'))

if tool == 'dms':
    # get group encoder options
    for key in ('imail_group_encoder', 'omail_group_encoder', 'contact_group_encoder'):
        val = int(api.portal.get_registry_record('imio.dms.mail.browser.settings.IImioDmsMailConfig.{}'.format(key)))
        infos['checks'][key.replace('group_encoder', 'ge')] = val
    # get applied workflow adaptations
    from collective.wfadaptations.api import get_applied_adaptations
    applied = ', '.join([d['adaptation'] for d in get_applied_adaptations()])
    for sub, rep in (('imio.dms.mail.wfadaptations.', ''), ('ServiceValidation', 'sv'), ('ToPrint', 'tp')):
        applied = applied.replace(sub, rep)
    infos['checks']['wfadaptations'] = applied
    # get assigned_user option
    infos['checks']['assigned_user'] = api.portal.get_registry_record('imio.dms.mail.browser.settings.'
                                                                      'IImioDmsMailConfig.assigned_user_check')
    # get wsclient option
    infos['checks']['pm'] = check_wsclient()
    # get query next prev max result value
    infos['checks']['qnp'] = int(api.portal.get_registry_record('collective.querynextprev.maxresults') or 0)
    # temporary
    # types = api.portal.get_registry_record('imio.dms.mail.browser.settings.IImioDmsMailConfig.omail_types') or []
    # TODO in dms 3.0 mt_title => dtitle
    # infos['checks']['omt'] = u', '.join([tdic.get('mt_title', tdic.get('dtitle', u'')) for tdic in types])
    # solr
    infos['checks']['solr'] = int(api.portal.get_registry_record('collective.solr.active', default=0))
    # temporary
    dvcj = api.portal.get_registry_record('imio.dms.mail.dv_clean_days')
    dvcd = api.portal.get_registry_record('imio.dms.mail.dv_clean_date')
    infos['checks']['zdvc'] = dvcj or (dvcd and dvcd.strftime('%Y-%m-%d')) or u''

if tool == 'pst':
    from imio.project.core.content.project import IProject  # noqa
    count = 0
    brains = catalog.unrestrictedSearchResults(object_provides=IProject.__identifier__)
    for brain in brains:
        obj = brain.getObject()
        if base_hasattr(obj, 'analytic_budget') and obj.analytic_budget:
            count += 1
    infos['checks']['budget'] = count
    # get wsclient option
    infos['checks']['pm'] = check_wsclient()

# get catalog count
infos['catalog'] = len(catalog.unrestrictedSearchResults(path='/'))

# get users count, only keep users that are in a group
users = portal.portal_membership.searchForMembers()  # ok with wca
count = 0
for user in users:
    user_groups = user.getGroups()
    if user_groups and user_groups != ['AuthenticatedUsers']:
        count = count + 1
    if user.has_role('Manager') or user.has_role('Site Administrator'):
        if user.getProperty('email') not in infos['admins']:
            infos['admins'].append(user.getProperty('email'))
infos['users'] = count

# get groups count
infos['groups'] = len(api.group.get_groups())

# get mail host
infos['mailhost'] = portal.MailHost.smtp_host

# sizes. app is zope
# filestorage
dbs = app['Control_Panel']['Database']  # noqa F821
for db in dbs.getDatabaseNames():
    size = dbs[db].db_size()
    size = int(tobytes(size[:-1] + ' ' + size[-1:] + 'B'))
    if size > infos['fs_sz']:
        infos['fs_sz'] = size
# blobstorage
# .sizes.json
sizefile = os.path.join(instdir, '.sizes.json')
try:
    fh = open(sizefile)
    res = json.load(fh)
    fh.close()
    size = int(res.get(u'local_size', 0))
    if size > infos['fs_sz']:
        size -= infos['fs_sz']
        infos['bl_sz'] = size
except Exception as msg:
    error(u".sizes.json not valid in '{}': '{}'".format(instdir, msg))

# vardir = os.path.join(instdir, 'var')
# for blobdirname in read_dir(vardir, only_folders=True):
#     if not blobdirname.startswith('blobstorage'):
#         continue
#     sizefile = os.path.join(vardir, blobdirname, 'size.txt')
#     if os.path.exists(sizefile):
#         lines = read_file(sizefile)
#         size = int(lines and lines[0] or 0)
#         if size > infos['bl_sz']:
#             infos['bl_sz'] = size
#             infos['bl_nm'] = blobdirname

# dump dictionary
if 'inst' not in maindic:
    maindic['inst'] = {}

maindic['inst'].update(dic)
dump_var(dumpfile, maindic)
