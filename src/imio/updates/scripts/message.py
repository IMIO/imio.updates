from __future__ import print_function

import argparse
import logging
from datetime import datetime

import transaction
from plone import api

LOGGER_LEVEL = 20


def verbose(*messages):
    print(">>", " ".join(messages))


def setup_logger(level=20):
    """
        When running "bin/instance run ...", the logger level is 30 (warn).
        It is possible to set it to 20 (info) or 10 (debug).
    """
    if level == 30:
        return

    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logging.root.handlers:
        if handler.level == 30 and handler.formatter is not None:
            handler.level = level
            break


def message(id, can_hide, message, title, msg_type, start, end, activate):
    from collective.messagesviewlet.utils import add_message, _richtextval
    modified = False
    config = obj['messages-config']
    # update existing message
    if id in config:
        msg = config[id]
        verbose("Updating message")
        if title is not None:
            msg.title = title
        if message is not None:
            msg.text = _richtextval(message)
    # create a new message
    else:
        verbose("Creating message")
        attrs = {}
        attrs.get('msg_type', 'warning')
        msg = add_message(id, title or 'imio.updates', message)

    if msg_type is not None:
        msg.msg_type = msg_type
    if can_hide is not None:
        msg.can_hide = can_hide
    if start is not None:
        msg.start = start
    if end is not None:
        msg.end = end
    msg.reindexObject()

    if activate is not None:
        try:
            if activate:
                api.content.transition(msg, transition='activate')
                verbose("Message %s activated" % msg)
            else:
                api.content.transition(msg, transition='deactivate')
                verbose("Message %s deactivated" % msg)
        except Exception:
            pass
    transaction.commit()


parser = argparse.ArgumentParser("Updates messagesviewlets objects")
parser.add_argument('id', type=str, help="Message's id")
parser.add_argument('-a', '--activate', dest='activate', type=lambda i: i == '1',
                    help="Message is active (1 if it should be)")
parser.add_argument('-H', '--hide', dest='can_hide', type=lambda i: i == '1', help="Message can be hidden (1 if it can)")
parser.add_argument('-m', '--message', dest='message', type=str, help="Text to display")
parser.add_argument('-t', '--title', dest='title', type=str, help="Message title")
parser.add_argument('-T', '--type', dest='msg_type', type=str, choices=['info', 'significant', 'warning'],
                    help="Message type")
parser.add_argument('-s',
                    '--start',
                    dest='start',
                    type=lambda s: datetime.strptime(s, '%Y%m%d-%H%M'),
                    help="Start datetime formatted as YYYYmmDD-HHMM",
                    default=datetime.now())
parser.add_argument('-e',
                    '--end',
                    dest='end',
                    type=lambda s: datetime.strptime(s, '%Y%m%d-%H%M'),
                    help="End datetime formatted as YYYYmmDD-HHMM")

parser.add_argument('-c', dest="my_path")

args = parser.parse_args()

setup_logger(LOGGER_LEVEL)

with api.env.adopt_user(username='admin'):
    message(args.id, args.can_hide, args.message, args.title, args.msg_type, args.start, args.end, args.activate)
