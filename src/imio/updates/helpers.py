# -*- coding: utf-8 -*-
import logging
from AccessControl.SecurityManagement import newSecurityManager
from Testing import makerequest
from zope.globalrequest import setRequest


def setup_logger(level=20):
    """
        When running "bin/instance run ...", the logger level is 30 (warn).
        It is possible to set it to 20 (info) or 10 (debug).
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logging.root.handlers:
        if handler.level == 30 and handler.formatter is not None:
            handler.level = level
            break


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
