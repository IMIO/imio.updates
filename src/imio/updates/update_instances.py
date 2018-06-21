#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import argparse
import os
import re
# import sys
# sys.path[0:0] = [
#     '/srv/instances/dmsmail/src/imio.pyutils',  # local
# ]

from imio.pyutils.system import runCommand, verbose, error

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
make = []
functions = []


def get_running_buildouts():
    """ Get running buildouts and instances"""
    cmd = 'supervisorctl status | grep RUNNING | cut -f 1 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    #out = ['dmsmail-zeoserver\n', 'dmsmail-instance1\n']
    #out = ['project-instance1\n']
    buildouts = {}
    # getting buildout and started programs
    for name in out:
        name = name.strip('\n')
        for started in starting:
            if name.endswith('-%s' % started):
                bldt = name[:-(len(started)+1)]
                if bldt not in buildouts:
                    buildouts[bldt] = [started]
                else:
                    buildouts[bldt].append(started)
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
            buildouts[bldt].sort(key=lambda x: starting.index(x))
    if escaped:
        verbose("Escaped buildouts: %s" % ', '.join(sorted(escaped)))
    return buildouts


def get_plone_site(path):
    name = None
    cmd = 'grep plone-path %s/port.cfg|cut -c 14-' % path
    (out, err, code) = runCommand(cmd)
    for name in out:
        name = name.strip('\n')
        break
    else:
        error("Cannot extract plone-path from '%s/port.cfg'" % path)
    return name


def run_spv(bldt, command, processes):
    for proc in processes:
        cmd = 'supervisorctl %s %s-%s' % (command, bldt, proc)
        if doit:
            verbose("=> Running '%s'" % cmd)
            (out, err, code) = runCommand(cmd)
            if code:
                error("Problem running supervisor command")
        else:
            verbose("=> Will be run '%s'" % cmd)


def run_buildout(bldt, path):
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


def run_make(buildouts, bldt, path, make):
    os.chdir(path)
    cmd = 'make %s' % make
    if instance != 'instance-debug':
        cmd += ' instance=%s' % instance
    code = 0
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile='%s/make.log' % path)
        if code:
            error("Problem running make: see %s/make.log file" % path)
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_function(buildouts, bldt, path, params):
    os.chdir(path)
    plone = get_plone_site(path)
    cmd = '%s/bin/%s -O%s run %s %s %s' % (path, instance, plone, function_script, params)
    code = 0
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile='%s/make.log' % path)
        if code:
            error("Problem running make: see %s/make.log file" % path)
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def main():
    global doit, pattern, buildout, instance, stop, restart, make, functions
    parser = argparse.ArgumentParser(description='Run some operations on zope instances.')
    parser.add_argument('-d', '--doit', action='store_true', dest='doit', help='To apply changes')
    parser.add_argument('-b', '--buildout', action='store_true', dest='buildout', help='To run buildout')
    parser.add_argument('-p', '--pattern', dest='pattern',
                        help='Buildout directory filter with PATTERN as re pattern matching')
    parser.add_argument('-m', '--make', nargs='+', dest='make', action='append', default=[],
                        help="Run 'make MAKE...' command")
    parser.add_argument('-f', '--function', nargs='+', dest='functions', action='append', default=[],
                        help="Run a function with args:"
                             " * step `profile` `step`"
                             " * step `profile` `_all_`"
                             " * upgrade `profile`"
                             " * upgrade `_all_`"
                        )
    parser.add_argument('-i', '--instance', dest='instance', default='instance-debug',
                        help='instance name used to run function or make (default instance-debug)')
    parser.add_argument('-s', '--superv', dest='superv',
                        choices=['stop', 'restart', 'stopall', 'restartall', 'stopworker', 'restartworker'],
                        help="To run supervisor command:"
                             " * stop : stop the instances first (not zeo) and restart it after buildout."
                             " * restart : restart the instances after buildout."
                             " * stopall : stop all buildout processes first and restart it after buildout."
                             " * restartall : restart all processes after buildout."
                             " * stopworker : stop the worker instances first (not zeo) and restart it after buildout."
                             " * restartworker : restart the worker instances after buildout.")
    ns = parser.parse_args()
    doit, buildout, instance, pattern = ns.doit, ns.buildout, ns.instance, ns.pattern
    make, functions = ns.make, ns.functions
    if not doit:
        verbose('Simulation mode: use -h to see script usage.')
    if ns.superv == 'stop':
        stop = restart = 'i'
    elif ns.superv == 'stopall':
        stop = restart = 'a'
    elif ns.superv == 'stopworker':
        stop = restart = 'w'
    elif ns.superv == 'restart':
        restart = 'i'
    elif ns.superv == 'restartall':
        restart = 'a'
    elif ns.superv == 'restartworker':
        restart = 'w'

    start = datetime.now()
    buildouts = get_running_buildouts()
    for bldt in sorted(buildouts.keys()):
        path = '%s/%s' % (basedir, bldt)
        if not os.path.exists(path):
            error("Path '%s' doesn't exist" % path)
            continue

        verbose("Buildout %s" % path)
        if stop:
            if stop == 'i':
                run_spv(bldt, 'stop', reversed([p for p in buildouts[bldt] if p.startswith('instance')]))
            elif stop == 'a':
                run_spv(bldt, 'stop', reversed([p for p in buildouts[bldt]]))
            elif stop == 'w':
                run_spv(bldt, 'stop', reversed([p for p in buildouts[bldt] if p.startswith('worker')]))
        if buildout:
            if run_buildout(bldt, path):
                continue
        if restart:
            if restart == 'i':
                run_spv(bldt, 'restart', [p for p in buildouts[bldt] if p.startswith('instance')])
            elif restart == 'a':
                run_spv(bldt, 'restart', [p for p in buildouts[bldt]])
            elif restart == 'w':
                run_spv(bldt, 'restart', [p for p in buildouts[bldt] if p.startswith('worker')])

        if 'zeoserver' not in buildouts[bldt]:
            error("Zeoserver isn't running")
            continue

        if make:
            for param_list in make:
                run_make(buildouts, bldt, path, ' '.join(param_list))
        if functions:
            for param_list in functions:
                run_function(buildouts, bldt, path, ' '.join(param_list))
    verbose("Script duration: %s" % (datetime.now() - start))
