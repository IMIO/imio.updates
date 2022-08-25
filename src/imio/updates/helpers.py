# -*- coding: utf-8 -*-
from AccessControl.SecurityManagement import newSecurityManager
from imio.pyutils.system import error
from imio.pyutils.system import runCommand
from Testing import makerequest
from zope.globalrequest import setRequest


def setup_app(app, username='admin', logger=None):
    acl_users = app.acl_users
    user = acl_users.getUser(username)
    if user:
        user = user.__of__(acl_users)
        newSecurityManager(None, user)
    elif logger:
        logger.error("Cannot find zope user '%s'" % username)
    app = makerequest.makerequest(app)
    # support plone.subrequest
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    return user


def get_git_tag(path):
    cmd = 'git --git-dir={}/.git describe --tags'.format(path)
    (out, err, code) = runCommand(cmd)
    if code or err:
        error("Problem in command '{}': {}".format(cmd, err))
        return 'NO TAG'
    return out[0].strip('\n')
