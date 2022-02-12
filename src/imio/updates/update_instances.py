#!/usr/bin/python
# -*- coding: utf-8 -*-
import shutil
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests as requests
from imio.pyutils.system import dump_var
from imio.pyutils.system import error
from imio.pyutils.system import read_file
from imio.pyutils.system import runCommand
from imio.pyutils.system import verbose

import argparse
import os
import re
import smtplib
import socket


# import sys
# sys.path[0:0] = [
#     '/srv/instances/dmsmail/src/imio.pyutils',  # local
# ]


doit = False
pattern = ''
function_script = os.path.join(os.path.dirname(__file__), 'run_script.py')
basedir = '/srv/instances'
starting = ['zeoserver', 'instance1', 'instance2', 'instance3', 'instance4', 'libreoffice',
            'worker-amqp', 'worker-async']
buildout = False
instance = 'instance-debug'
stop = ''
restart = ''
warning_dic = {}
warning_errors = False
warning_file = os.path.join(basedir, 'messagesviewlet_dump.txt')
warning_first_pass = True
warning_ids = []
wait = False
dev_mode = False
traces = False


def trace(msg):
    if traces:
        verbose(msg)


def get_running_buildouts():
    """ Get running buildouts and instances"""
    cmd = 'supervisorctl status | grep RUNNING | cut -f 1 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    if dev_mode:
        # out = ['dmsmail-zeoserver\n', 'dmsmail-instance1\n', 'project-zeoserver\n', 'project-instance1\n']
        out = ['TAGS/dmsmail3.0-zeoserver\n', 'TAGS/dmsmail3.0-instance-debug\n']
        # out = ['dmsmail_solr-instance1\n']
    buildouts = {}
    # getting buildout and started programs
    for name in out:
        name = name.strip('\n')
        for started in starting:
            if name.endswith('-%s' % started):
                bldt = name[:-(len(started)+1)]
                if bldt not in buildouts:
                    buildouts[bldt] = {'spv': [started]}
                else:
                    buildouts[bldt]['spv'].append(started)
                break
        else:
            error("Cannot extract buildout name from '%s'" % name)
    # escape if pattern not matched
    # order started following defined list
    escaped = []
    for bldt in buildouts.keys():
        if pattern and not re.match(pattern, bldt, re.I):
            del buildouts[bldt]
            escaped.append(bldt)
        else:
            buildouts[bldt]['spv'].sort(key=lambda x: starting.index(x))
    if escaped:
        verbose("Escaped buildouts: %s" % ', '.join(sorted(escaped)))
    return buildouts


def patch_debug(path):
    idp = os.path.join(path, 'parts/instance-debug/bin/interpreter')
    if not os.path.exists(idp):
        error("'{}' doesn't exist: cannot patch it".format(idp))
        return False
    if not doit:
        verbose("=> Will be patched: '{}'".format(idp))
    else:
        lines = read_file(idp)
        if 'ploneCustom.css' not in ''.join(lines):
            sp = 0
            for (i, line) in enumerate(lines):
                if 'exec(_val)' in line:
                    nl = line.lstrip()
                    sp = len(line) - len(nl)
                    break
            lines.insert(i, "{}{}".format(' ' * sp,
                                          '_val = _val.replace("\'); from AccessControl.SpecialUsers import system '
                                          'as user;", "/ploneCustom.css\'); from AccessControl.SpecialUsers import '
                                          'system as user;")'))
            verbose("=> Patching: '{}'".format(idp))
            fh = open(idp, 'w')
            fh.write('\n'.join(lines))
            fh.close()
        else:
            verbose("=> Already patched: '{}'".format(idp))
    return True


def patch_indexing(path):
    """Avoid monkey patch to not queue indexation operations"""
    cip = os.path.join(path, 'parts/omelette/collective/indexing/monkey.py')
    if not os.path.exists(cip):
        error("'{}' doesn't exist: cannot patch it".format(cip))
        return False
    if not doit:
        verbose("=> Will be patched: '{}'".format(cip))
    else:
        verbose("=> Patching: '{}'".format(cip))
        cipbck = cip + '.bck'
        cmd = "sed -i'' '/^ \\+module.indexObject = indexObject/,+3 s/^/#/' {}".format(cip)
        if not os.path.exists(cipbck):
            cmd = cmd.replace("sed -i'' ", "sed -i'.bck' ")
        (out, err, code) = runCommand(cmd)
        if code or err:
            error("Problem patching indexing: {}".format(err))
            return False
    return True


def unpatch_indexing(path):
    """Undo patch_indexing"""
    cip = os.path.join(path, 'parts/omelette/collective/indexing/monkey.py')
    cipbck = cip + '.bck'
    if not os.path.exists(cipbck):
        error("'{}' doesn't exist: cannot unpatch it".format(cipbck))
        return False
    if not doit:
        verbose("=> Will be unpatched: '{}'".format(cip))
    else:
        shutil.copy2(cipbck, cip)


def search_in_port_cfg(path, to_find, is_int=False):
    for line in read_file("%s/port.cfg" % path):
        if to_find in line:
            port = line.split(' ')[-1]
            break
    else:
        error("Cannot extract %s from '%s/port.cfg'" % (to_find, path))
        return None
    if is_int:
        try:
            int(port)
        except ValueError:
            error("%s has invalid port value : '%s'" % (to_find, port))
            return None
    return port


def get_instance_port(path, inst='instance1'):
    proc_http_name = "%s-http" % inst
    return search_in_port_cfg(path, proc_http_name, is_int=True)


def run_spv(bldt, path, plone_path, command, processes):
    for proc in processes:
        if dev_mode:
            cmd = '{}/bin/{} {}'.format(path, proc, command)
        else:
            cmd = 'supervisorctl %s %s-%s' % (command, bldt, proc)
        if doit:
            verbose("=> Running '%s'" % cmd)
            (out, err, code) = runCommand(cmd)
            if code:
                error("Problem running supervisor command")
            elif wait:
                threshold = 20
                interval = 10
                trace('Waiting %d sec ...' % threshold)
                time.sleep(threshold)
                if not (proc.startswith('instance') or proc.startswith('worker')):
                    continue
                port = get_instance_port(path, proc.replace('worker', 'instance'))
                url = 'http://localhost:%s/%s/ok' % (port, plone_path)
                for i in range(0, 9):
                    try:
                        trace('Checking %s' % url)
                        response = requests.get(url)
                        if response.status_code == 200:
                            break
                        else:
                            trace("Status HTTP status code for 'ok' was %d. Waiting another %d sec..." %
                                  (response.status_code, interval))
                            time.sleep(interval)
                    except Exception as err:  # noqa
                        # Don't care the nature of this error
                        error(str(err))
        else:
            verbose("=> Will be run '%s'" % cmd)


def run_buildout(buildouts, bldt):
    path = buildouts[bldt]['path']
    os.chdir(path)
    cmd = 'bin/buildout -N'
    code = 0
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile='%s/manual-buildout.log' % path)
        if code:
            error("Problem running buildout: see %s/manual-buildout.log file" % path)
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_make(buildouts, bldt, env, make):
    path = buildouts[bldt]['path']
    os.chdir(path)
    cmd = '%smake %s' % (env and 'env {} '.format(env) or '', make)
    if instance != 'instance-debug':
        cmd += ' instance=%s' % instance
    code = 0
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile=(make != 'copy' and '%s/make.log' % path or None))
        if code:
            error("Problem running make: see %s/make.log file" % path)
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_function(buildouts, bldt, env, fct, params, script=function_script):
    path = buildouts[bldt]['path']
    os.chdir(path)
    cmd = (env and 'env {} '.format(env) or '')
    cmd += '%s/bin/%s -O%s run %s %s %s' % (path, instance, buildouts[bldt]['plone'], script, fct, params)
    code = 0
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile='%s/make.log' % path)
        if code:
            error("Problem running '%s' function: see %s/make.log file" % (fct, path))
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_develop(buildouts, bldt, products):
    path = buildouts[bldt]['path']
    os.chdir(path)
    cmd = 'bin/develop up -a {}'.format(' '.join(products))
    code = 0
    if doit:
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd)
        if code:
            error("Problem running bin/develop: {}".format(err))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def compile_warning(i, params):
    global warning_errors
    p_dic = {}
    import re
    regex = re.compile(r'[^"\s]+(?:"[^"\\]*(?:\\.[^"\\]*)*")*', re.VERBOSE)
    # [^"\s]+  something different from doublequotes
    # (?:"")*  optional doublequotes
    # [^"\\]*(?:\\.[^"\\]*)*  something different from doublequote, escaping protected doublequotes

    for param in params:
        for part in regex.findall(param):
            try:
                p_dic.update(eval('dict(%s)' % part))
            except Exception as msg:
                error("Problem in -w with param '%s': %s" % (part, msg))
                warning_errors = True
    verbose("Message parameters: %s" % p_dic)
    mandatory_params = ['id', 'activate']
    for param in mandatory_params:
        if param not in p_dic:
            error("Parameter '%s' is required !" % param)
            warning_errors = True
    for dt in ('start', 'end'):
        if dt in p_dic:
            try:
                p_dic[dt] = datetime.strptime(p_dic[dt], '%Y%m%d-%H%M')
            except ValueError as msg:
                error("Cannot compile datetime '%s' : %s" % (p_dic[dt], msg))
                warning_errors = True

    id = p_dic.pop('id', 'no_id')
    warning_dic[id] = p_dic
    dump_var(warning_file, warning_dic)
    warning_ids.insert(i, id)


def email(buildouts, recipient):
    hostname = socket.gethostname()  # ged-prod4.imio.be, ged-prod5, ged18
    lanhost = hostname.replace('.imio.be', '').replace('-prod', '')
    output = []
    for bldt in sorted(buildouts.keys()):
        if 'port' not in buildouts[bldt]:
            continue
        output.append("Buildout '{0}': http://{1}:{2}/manage_main".format(bldt, lanhost, buildouts[bldt]['port']))
    msg = MIMEMultipart()
    sender = 'imio.updates@imio.be'
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = 'imio.updates finished on {}'.format(hostname)
    msg.attach(MIMEText('\n'.join(output)))
    s = smtplib.SMTP('mailrelay.imio.be', 25)
    s.sendmail(sender, [recipient], msg.as_string())
    s.quit()


def main():
    global doit, pattern, instance, stop, restart, warning_first_pass, wait, traces
    parser = argparse.ArgumentParser(description='Run some operations on zope instances.')
    parser.add_argument('-d', '--doit', action='store_true', dest='doit', help='To apply changes')
    parser.add_argument('-b', '--buildout', action='store_true', dest='buildout', help='To run buildout')
    parser.add_argument('-p', '--pattern', dest='pattern',
                        help='Buildout directory filter with PATTERN as re pattern matching')
    parser.add_argument('-m0', '--make0', nargs='+', dest='make0', action='append', default=[],
                        help="Run 'make MAKE...' command before a buildout and restart")
    parser.add_argument('-m', '--make', nargs='+', dest='make', action='append', default=[],
                        help="Run 'make MAKE...' command")
    parser.add_argument('-f', '--function', nargs='+', dest='functions', action='append', default=[],
                        help="Run a function with args:"
                             " * step `profile` `step`"
                             " * step `profile` `_all_`"
                             " * upgrade `profile`"
                             " * upgrade `profile` `1000` `1001`"
                             " * upgrade `_all_`"
                        )
    parser.add_argument('-s', '--superv', dest='superv', action='append',
                        choices=['stop', 'restart', 'stopall', 'restartall', 'stopworker', 'restartworker', 'stopzeo'
                                 'restartzeo'],
                        help="To run supervisor command:"
                             " * stop : stop the instances (not zeo)."
                             " * restart : restart the instances and waits for it to be up and running (after "
                             "buildout if `-b` was provided)."
                             " * stopall : stop all buildout processes."
                             " * restartall : restart all processes (after buildout if `-b` was provided)."
                             " * stopworker : stop the worker instances."
                             " * restartworker : restart the worker instances (after buildout if `-b` was provided)."
                             " * stopzeo : stop the zeo."
                             " * restartzeo : restart the zeo instance (after buildout if `-b` was provided).")
    parser.add_argument('-i', '--instance', dest='instance', default='instance-debug',
                        help='instance name used to run function or make (default instance-debug)')
    parser.add_argument('-a', '--auth', dest='auth', choices=['0', '1', '8', '9'], default='9',
                        help='Enable/disable authentication plugins:'
                             ' * 0 : disable only'
                             ' * 1 : enable only'
                             ' * 8 : disable before make or function and enable after (default)'
                             ' * 9 : don''t do anything')
    parser.add_argument('-u', '--update', nargs='+', dest='develop',
                        help="Update given development products")
    parser.add_argument('-e', '--email', dest='email',
                        help='Email address used to send an email when finished')
    parser.add_argument('-w', '--warning', nargs='+', dest='warnings', action='append', default=[],
                        help='Create or update a message. Parameters like xx="string value".'
                             ' All parameters must be enclosed by quotes: \'xx="val" yy=True\'.'
                             ' Following parameters are possible:'
                             ' * id="maintenance-soon"'
                             ' * text="A maintenance operation will be done at 4pm."'
                             ' * activate=True'
                             ' * ...'
                        ),
    parser.add_argument('-v', '--vars', dest='vars', action='append', default=[],
                        help="Define env variables like XX=YY, used as: env XX=YY make (or function). (can use "
                             "multiple times -v). FUNC_PARTS is a special var (see docs).")
    parser.add_argument('-c', '--custom', nargs='+', action='append', dest='custom', help="Run a custom script")
    parser.add_argument('-t', '--traces', action='store_true', dest='traces', help="Add more traces")
    parser.add_argument('-y', '--patchindexing', action='store_true', dest='patchindexing',
                        help='To hack collective.indexing.monkey, to keep direct indexation during operations')
    parser.add_argument('-z', '--patchdebug', action='store_true', dest='patchdebug',
                        help='To hack instance-debug. (Needed for Project)')
    parser.add_argument('-W', '--wait', action='store_true', dest='wait',
                        help='Wait for instance to be up and running during a `-s restart`')

    ns = parser.parse_args()
    doit, buildout, instance, pattern = ns.doit, ns.buildout, ns.instance, ns.pattern
    make, functions, auth, warnings = ns.make, ns.functions, ns.auth, ns.warnings
    wait, traces = ns.wait, ns.traces

    if not doit:
        verbose('Simulation mode: use -h to see script usage.')
    for sv in ns.superv or []:
        if sv == 'stop':
            stop += 'i'
        elif sv == 'stopall':
            stop += 'a'
        elif sv == 'stopworker':
            stop += 'w'
        elif sv == 'stopzeo':
            stop += 'z'
        elif sv == 'restart':
            restart += 'i'
        elif sv == 'restartall':
            restart += 'a'
        elif sv == 'restartworker':
            restart += 'w'
        elif sv == 'restartzeo':
            restart += 'z'

    func_parts = []
    envs = []
    for var in ns.vars:
        if var.startswith('FUNC_PARTS='):
            func_parts = [l for l in var.split('=')[1]]
        else:
            envs.append(var)
    env = ' '.join(envs)

    start = datetime.now()
    buildouts = get_running_buildouts()
    for bldt in sorted(buildouts.keys()):
        path = '%s/%s' % (basedir, bldt)
        if not os.path.exists(path):
            error("Path '%s' doesn't exist" % path)
            continue

        buildouts[bldt]['path'] = path
        plone_path = search_in_port_cfg(path, 'plone-path')
        buildouts[bldt]['plone'] = plone_path
        buildouts[bldt]['port'] = get_instance_port(path)

        verbose("Buildout %s" % path)
        if stop:
            if 'i' in stop:
                run_spv(bldt, path, plone_path, 'stop', reversed([p for p in buildouts[bldt]['spv']
                                                                  if p.startswith('instance')]))
            if 'a' in stop:
                run_spv(bldt, path, plone_path, 'stop', reversed([p for p in buildouts[bldt]['spv']]))
            if 'w' in stop:
                run_spv(bldt, path, plone_path, 'stop', reversed([p for p in buildouts[bldt]['spv']
                                                                  if p.startswith('worker')]))
            if 'z' in stop:
                run_spv(bldt, path, plone_path, 'stop', reversed([p for p in buildouts[bldt]['spv']
                                                                  if p.startswith('zeoserver')]))

        if ns.make0:
            for param_list in ns.make0:
                run_make(buildouts, bldt, env, ' '.join(param_list))

        if buildout:
            if run_buildout(buildouts, bldt):
                continue
        elif ns.develop:
            run_develop(buildouts, bldt, ns.develop)
        if restart:
            if 'z' in restart:
                run_spv(bldt, path, plone_path, 'restart', [p for p in buildouts[bldt]['spv']
                                                            if p.startswith('zeoserver')])
            if 'a' in restart:
                run_spv(bldt, path, plone_path, 'restart', [p for p in buildouts[bldt]['spv']])
            if 'i' in restart:
                run_spv(bldt, path, plone_path, 'restart', [p for p in buildouts[bldt]['spv']
                                                            if p.startswith('instance')])
            if 'w' in restart:
                run_spv(bldt, path, plone_path, 'restart', [p for p in buildouts[bldt]['spv']
                                                            if p.startswith('worker')])

        if 'zeoserver' not in buildouts[bldt]['spv']:
            error("Zeoserver isn't running")
            if not instance:
                continue

        if ns.patchdebug:
            if not patch_debug(buildouts[bldt]['path']):
                continue

        if ns.patchindexing:
            if not patch_indexing(buildouts[bldt]['path']):
                continue

        if auth == '0' or (auth == '8' and (make or functions)):
            run_function(buildouts, bldt, '', 'auth', '0')

        if make:
            for param_list in make:
                run_make(buildouts, bldt, env, ' '.join(param_list))

        if ns.custom:
            for param_list in ns.custom:
                # function is optional or can be a param so we need to handle it
                run_function(buildouts, bldt, env, script=param_list[0], fct=''.join(param_list[1:2]),
                             params=' '.join(param_list[2:]))

        if functions:
            for param_list in functions:
                if func_parts:
                    for part in func_parts:
                        new_env = 'FUNC_PART={} '.format(part) + env
                        ret = run_function(buildouts, bldt, new_env, param_list[0], ' '.join(param_list[1:]))
                        if ret != 0:
                            error("Loop on FUNC_PARTS '{}' is broken at part '{}'".format(''.join(func_parts), part))
                            break
                else:
                    run_function(buildouts, bldt, env, param_list[0], ' '.join(param_list[1:]))

        if warnings:
            if warning_first_pass:
                for i, param_list in enumerate(warnings):
                    compile_warning(i, param_list)
                warning_first_pass = False
            if not warning_errors:
                for id in warning_ids:
                    run_function(buildouts, bldt, env, 'message', '%s %s' % (id, warning_file))

        if ns.patchindexing:
            unpatch_indexing(buildouts[bldt]['path'])

        if auth == '1' or (auth == '8' and (make or functions)):
            run_function(buildouts, bldt, '', 'auth', '1')

    if ns.email and doit:
        email(buildouts, ns.email)

    verbose("Script duration: %s" % (datetime.now() - start))
