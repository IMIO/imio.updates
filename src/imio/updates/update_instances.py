#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import getopt
import os
import re
import sys
# sys.path[0:0] = [
#     '/srv/instances/dmsmail/src/imio.pyutils',  # local
# ]

from imio.pyutils.system import runCommand, verbose, error

doit = False
pattern = ''
basedir = '/srv/instances'
starting = ['zeoserver', 'instance1', 'instance2', 'instance3', 'instance4', 'libreoffice', 'worker-amqp']
buildout = False
stop = ''
restart = ''


def usage():
    verbose("Here are the list of parameters:")
    verbose("-d, --doit : to apply changes")
    verbose("-b, --buildout : to run buildout")
    verbose("-p val, --pattern=val : buildout directory filter with val as re pattern matching")
    verbose("-s val, --superv=val : to run supervisor command (stop|restart|stopall|restartall")
    verbose("\tstop : stop the instances first (not zeo) and restart them at script end")
    verbose("\trestart : restart the instances at script end")
    verbose("\tstop : stop all buildout processes first (not zeo) and restart them at script end")
    verbose("\trestartall : restart all processes at script end")


def get_running_buildouts():
    cmd = 'supervisorctl status | grep RUNNING | cut -f 1 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    #out = ['dmsmail-zeoserver\n', 'dmsmail-instance1\n']
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
    if not os.path.exists(path):
        error("Path '%s' doesn't exist" % path)
        return
    os.chdir(path)
    cmd = 'bin/buildout -N'
    if doit:
        start = datetime.now()
        verbose("=> Running '%s'" % cmd)
        (out, err, code) = runCommand(cmd, outfile='%s/manual-buildout.log' % path)
        if code:
            error("Problem running buildout: see %s/manual-buildout.log file" % path)
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)


def main():
    global doit, pattern, buildout, stop, restart
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdbp:s:", ['help', 'doit', 'buildout', 'pattern=', 'superv='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        if opt in ('-d', '--doit'):
            doit = True
        elif opt in ('-p', '--pattern'):
            pattern = arg
        elif opt in ('-b', '--buildout'):
            buildout = True
        elif opt in ('-s', '--superv'):
            if arg == 'stop':
                stop = restart = 'i'
            elif arg == 'stopall':
                stop = restart = 'a'
            elif arg == 'restart':
                restart = 'i'
            elif arg == 'restartall':
                restart = 'a'
            else:
                usage()
                sys.exit(2)
    if not doit:
        verbose('Simulation mode: use -h to see script usage.')

    start = datetime.now()
    buildouts = get_running_buildouts()
    for bldt in sorted(buildouts.keys()):
        path = '%s/%s' % (basedir, bldt)
        verbose("Buildout %s" % path)
        if stop:
            if stop == 'i':
                run_spv(bldt, 'stop', reversed([p for p in buildouts[bldt] if p.startswith('instance')]))
            elif stop == 'a':
                run_spv(bldt, 'stop', reversed([p for p in buildouts[bldt]]))
        if buildout:
            run_buildout(bldt, path)
        if restart:
            if restart == 'i':
                run_spv(bldt, 'restart', [p for p in buildouts[bldt] if p.startswith('instance')])
            elif restart == 'a':
                run_spv(bldt, 'restart', [p for p in buildouts[bldt]])
    verbose("Script duration: %s" % (datetime.now() - start))
