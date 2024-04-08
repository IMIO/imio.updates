# -*- coding: utf-8 -*-
#
# tests utis methods
# IMIO <support@imio.be>
#
# can be run with commaned: bin/update_instances -c _path_/batch_script.py 10 -v FUNC_PARTS=a -v BATCH=5 -v BATCHING=a
from imio.helpers.batching import batch_delete_files
from imio.helpers.batching import batch_get_keys
from imio.helpers.batching import batch_handle_key
from imio.helpers.batching import batch_hashed_filename
from imio.helpers.batching import batch_loop_else
from imio.helpers.batching import batch_skip_key
from imio.pyutils.system import stop
from imio.pyutils.utils import setup_logger

import logging
import os
import sys


logger = logging.getLogger('batch_script')
INFILE = 'keys.pkl'
processed = {'keys': [], 'commits': 0, 'errors': 0}


def loop_process(loop_len):
    """Process the loop using the batching module."""
    ifile = batch_hashed_filename(INFILE)
    batch_keys, config = batch_get_keys(ifile, loop_len)
    logger.info('CONFIG DIC: {}'.format(config))
    logger.info('ALREADY DONE: {}'.format(len(batch_keys)))
    for key in range(1, loop_len + 1):
        if batch_skip_key(key, batch_keys, config):
            continue
        # processed['keys'].append(key)
        logger.info('CURRENT KEY: {}'.format(key))
        if batch_handle_key(key, batch_keys, config):
            break
    else:
        batch_loop_else(config['lc'] > 1 and key or None, batch_keys, config)
    if config['bl']:
        batch_delete_files(batch_keys, config, rename=False)


# portal = obj  # noqa
if len(sys.argv) < 4:
    stop("Missing loop len in args")
loop_length = int(sys.argv[3])
batch = int(os.getenv('BATCH', 0))

if not batch:
    stop("Missing BATCH env")
setup_logger(logger, level=20)
loop_process(loop_length)
