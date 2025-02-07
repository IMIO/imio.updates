#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imio.pyutils.batching import batch_delete_files
from imio.pyutils.system import dump_var
from imio.pyutils.system import error
from imio.pyutils.system import get_git_tag
from imio.pyutils.system import load_var
from imio.pyutils.system import post_request
from imio.pyutils.system import read_dir_filter
from imio.pyutils.system import read_file
from imio.pyutils.system import runCommand
from imio.pyutils.system import verbose
from imio.pyutils.utils import append
from six.moves import range

import argparse
import os
import re
import requests as requests
import shutil
import smtplib
import socket
import sys
import time


# import sys
# sys.path[0:0] = [
#     '/srv/instances/dmsmail/src/imio.pyutils',  # local
# ]
dev_mode = 0
dev_config = {1: {"bldt": "TAGS/dmsmail3.0"}, 2: {"bldt": "dmsmail"}}
dev_buildout = dev_config.get(dev_mode, {}).get("bldt")

doit = False
pattern = ""
function_script = os.path.join(os.path.dirname(__file__), "run_script.py")
basedir = "/srv/instances"
starting = [
    "zeoserver",
    "instance1",
    "instance2",
    "instance3",
    "instance4",
    "libreoffice",
    "worker-amqp",
    "worker-async",
]
buildout = False
instance = "instance-debug"
stop = ""
restart = ""
warning_dic = {}
warning_errors = False
warning_file = os.path.join(basedir, "messagesviewlet_dump.txt")
warning_first_pass = True
warning_ids = []
wait = False
traces = False
ns = None
messages = []


def trace(msg):
    if traces:
        verbose(msg)


def get_running_buildouts():
    """Get running buildouts and instances"""
    cmd = 'supervisorctl status | grep RUNNING | cut -f 1 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    if dev_mode:
        out = ["{}-zeoserver\n".format(dev_buildout), "{}-instance1\n".format(dev_buildout)]
    buildouts = {}
    # getting buildout and started programs
    for name in out:
        name = name.strip("\n")
        for started in starting:
            if name.endswith("-%s" % started):
                bldt = name[: -(len(started) + 1)]
                if bldt not in buildouts:
                    buildouts[bldt] = {"spv": [started]}
                else:
                    buildouts[bldt]["spv"].append(started)
                break
        else:
            error("Cannot extract buildout name from '%s'" % name)
    # get stopped zeo
    cmd = 'supervisorctl status | grep "\\-zeoserver" | grep STOPPED | cut -f 1 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    if dev_mode:
        out = ["{}-zeoserver\n".format(dev_buildout)]
    for name in out:
        name = name.strip("\n")
        bldt = name[:-10]
        if bldt not in buildouts:
            buildouts[bldt] = {"spv": []}
    # escape if pattern not matched
    # order started following defined list
    escaped = []
    for bldt in buildouts.keys():
        if pattern and not re.match(pattern, bldt, re.I):
            del buildouts[bldt]
            escaped.append(bldt)
        else:
            buildouts[bldt]["spv"].sort(key=lambda x: starting.index(x))
    if escaped:
        verbose("Escaped buildouts: %s" % ", ".join(sorted(escaped)))
    return buildouts


def get_supervised_buildouts():
    """Get supervised buildouts and instances"""
    cmd = 'supervisorctl status | grep -v STOPPED| tr -s " " |cut -f 1,2 -d " " | sort -r'
    (out, err, code) = runCommand(cmd)
    if dev_mode:
        out = ["{}-zeoserver RUNNING\n".format(dev_buildout), "{}-instance1 RUNNING\n".format(dev_buildout)]
    buildouts = {}
    # getting buildout and started programs
    for line in out:
        name, status = line.strip("\n").split()
        for started in starting:
            if name.endswith("-%s" % started):
                bldt = name[: -(len(started) + 1)]
                if bldt not in buildouts:
                    buildouts[bldt] = {"spv": [(started, status)]}
                else:
                    buildouts[bldt]["spv"].append((started, status))
    # escape if pattern not matched
    # order started following defined list
    escaped = []
    buildouts_keys = list(buildouts.keys())
    for bldt in buildouts_keys:
        if pattern and not re.match(pattern, bldt, re.I):
            del buildouts[bldt]
            escaped.append(bldt)
        else:
            buildouts[bldt]["spv"].sort(key=lambda x: starting.index(x[0]))
    if escaped:
        verbose("Escaped buildouts: %s" % ", ".join(sorted(escaped)))
    return buildouts


def patch_instance(path):
    idp = os.path.join(path, "parts/{}/bin/interpreter".format(instance))
    if not os.path.exists(idp):
        error(append(messages, "'{}' doesn't exist: cannot patch it".format(idp)))
        return False
    if not doit:
        verbose("=> Will be patched: '{}'".format(idp))
    else:
        lines = read_file(idp)
        if "ploneCustom.css" not in "".join(lines):
            sp = 0
            for (i, line) in enumerate(lines):
                if "exec(_val)" in line:
                    nl = line.lstrip()
                    sp = len(line) - len(nl)
                    break
            lines.insert(
                i,
                "{}{}".format(
                    " " * sp,
                    "_val = _val.replace(\"'); from AccessControl.SpecialUsers import system "
                    'as user;", "/ploneCustom.css\'); from AccessControl.SpecialUsers import '
                    'system as user;")',
                ),
            )
            verbose(append(messages, "=> Patching: '{}'".format(idp)))
            fh = open(idp, "w")
            fh.write("\n".join(lines))
            fh.close()
        else:
            verbose("=> Already patched: '{}'".format(idp))
    return True


def patch_indexing(path):
    """Avoid monkey patch to not queue indexation operations"""
    cip = os.path.join(path, "parts/omelette/collective/indexing/monkey.py")
    if not os.path.exists(cip):
        error(append(messages, "'{}' doesn't exist: cannot patch it".format(cip)))
        return False
    if not doit:
        verbose("=> Will be patched: '{}'".format(cip))
    else:
        verbose("=> Patching: '{}'".format(cip))
        cipbck = cip + ".bck"
        cmd = "sed -i'' '/^ \\+module.indexObject = indexObject/,+3 s/^/#/' {}".format(cip)
        if not os.path.exists(cipbck):
            cmd = cmd.replace("sed -i'' ", "sed -i'.bck' ")
        (out, err, code) = runCommand(cmd)
        if code or err:
            error(append(messages, "Problem patching indexing: {}".format(err)))
            return False
    return True


def unpatch_indexing(path):
    """Undo patch_indexing"""
    cip = os.path.join(path, "parts/omelette/collective/indexing/monkey.py")
    cipbck = cip + ".bck"
    if not os.path.exists(cipbck):
        error(append(messages, "'{}' doesn't exist: cannot unpatch it".format(cipbck)))
        return False
    if not doit:
        verbose("=> Will be unpatched: '{}'".format(cip))
    else:
        shutil.copy2(cipbck, cip)


def search_in_port_cfg(path, to_find, is_int=False):
    for line in read_file("%s/port.cfg" % path):
        if to_find in line:
            port = line.split(" ")[-1]
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


def get_instance_port(path, inst="instance1"):
    proc_http_name = "%s-http" % inst
    return search_in_port_cfg(path, proc_http_name, is_int=True)


def get_instance_home(buildout_path):
    return os.path.join(buildout_path, "parts", instance)


def get_batch_config(dirs=()):
    """Get latest batching config file"""

    dirs.extend([os.getenv("INSTANCE_HOME", ".")])
    all_files = []
    for adir in dirs:
        files = read_dir_filter(adir, with_path=True, patterns=[r".*_config\.txt$"])
        all_files.extend(files)
    if not all_files:
        return None
    latest_file = max(all_files, key=os.path.getmtime)
    if latest_file:
        config = {}
        load_var(latest_file, config)
        return config
    return None


def run_spv(bldt, path, plone_path, command, processes):
    for proc in processes:
        if dev_mode:
            cmd = "{}/bin/{} {}".format(path, proc, command)
        else:
            cmd = "supervisorctl %s %s-%s" % (command, bldt, proc)
        if doit:
            verbose(append(messages, "=> Running '%s'" % cmd))
            (out, err, code) = runCommand(cmd)
            if code:
                error(append(messages, "Problem running supervisor command"))
            elif wait:
                threshold = 20
                interval = 10
                trace("Waiting %d sec ..." % threshold)
                time.sleep(threshold)
                if not (proc.startswith("instance") or proc.startswith("worker")):
                    continue
                port = get_instance_port(path, proc.replace("worker", "instance"))
                url = "http://localhost:%s/%s/ok" % (port, plone_path)
                for i in range(0, 9):
                    try:
                        trace("Checking %s" % url)
                        response = requests.get(url)
                        if response.status_code == 200:
                            break
                        else:
                            trace(
                                "Status HTTP status code for 'ok' was %d. Waiting another %d sec..."
                                % (response.status_code, interval)
                            )
                            time.sleep(interval)
                    except Exception as err:  # noqa
                        # Don't care the nature of this error
                        error(append(messages, str(err)))
        else:
            verbose("=> Will be run '%s'" % cmd)


def repair_fatals(buildouts, fatals, bldt, path, plone_path):
    change = False
    for fatal in fatals:
        cmd = 'ps -ef | grep /{}/bin/{}| grep /srv/instances |tr -s " " |cut -f 2,3,8,9 -d " "'.format(bldt, fatal)
        (out, err, code) = runCommand(cmd)
        for line in out:
            pid, ppid, python, process = line.strip("\n").split()
            if not process.endswith("/bin/{}".format(fatal)):
                continue
            verbose("=> Repair FATAL: found another process '{}' with parent id '{}'".format(process, ppid))
            verbose("=> Repair FATAL: will kill pid '{}' and start '{}'".format(pid, fatal))
            cmd = "bash -c 'kill -s SIGTERM -- -{}'".format(pid)
            if doit:
                (out, err, code) = runCommand(cmd)
                if not code:
                    run_spv(bldt, path, plone_path, "start", [fatal])
                    time.sleep(5)
                    change = True
    if change:
        new_buildouts = get_supervised_buildouts()
        buildouts[bldt]["spv"] = new_buildouts[bldt]["spv"]


def run_buildout(buildouts, bldt):
    path = buildouts[bldt]["path"]
    os.chdir(path)
    cmd = "bin/buildout -N"
    code = 0
    if doit:
        start = datetime.now()
        verbose(append(messages, "=> Running '%s'" % cmd))
        (out, err, code) = runCommand(cmd, outfile="%s/manual-buildout.log" % path)
        if code:
            error(append(messages, "Problem running buildout: see %s/manual-buildout.log file" % path))
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_make(buildouts, bldt, env, make):
    path = buildouts[bldt]["path"]
    os.chdir(path)
    cmd = "%smake %s" % (env and "env {} ".format(env) or "", make)
    if instance != "instance-debug":
        cmd += " instance=%s" % instance
    code = 0
    if doit:
        start = datetime.now()
        verbose(append(messages, "=> Running '%s'" % cmd))
        (out, err, code) = runCommand(cmd, outfile=(make != "copy" and "%s/make.log" % path or None))
        if code:
            error(append(messages, "Problem running make: see %s/make.log file" % path))
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def run_function(buildouts, bldt, env, fct, params, script=function_script, run_nb=0):
    path = buildouts[bldt]["path"]
    os.chdir(path)
    cmd = env and "env {} ".format(env) or ""
    cmd += "%s/bin/%s -O%s run %s %s %s" % (path, instance, buildouts[bldt]["plone"], script, fct, params)
    code = 0
    if doit:
        start = datetime.now()
        verbose(append(messages, "=> Running %s'%s'" % (run_nb and "{} ".format(run_nb) or "", cmd)))
        (out, err, code) = runCommand(cmd, outfile="%s/make.log" % path)
        if code:
            error(append(messages, "Problem running '%s' function: see %s/make.log file" % (fct, path)))
        verbose("\tDuration: %s" % (datetime.now() - start))
    else:
        verbose("=> Will be run %s'%s'" % (run_nb and "{} ".format(run_nb) or "", cmd))
    return code


def run_function_parts(func_parts, batches_conf, params):
    """Run function multiple time if needed.

    :param func_parts: letters list where one letter is the part name
    :param batches_conf: batching dict {'batch': 1000, 'A': 5000, 'B': 8000, ...} when BATCH_TOTALS or
                                       {'batch': 1000, 'batching': ['A', 'B']} when BATCHING
    :param params: dict {'buildouts': dict, 'bldt': bldt, 'env': env, 'script': '', 'fct': '', 'params': '', ...}
    """
    if func_parts:
        original_env = params["env"]
        for part in func_parts:
            env = original_env and "{} ".format(original_env) or ""
            params["env"] = "{}FUNC_PART={}".format(env, part)
            first = 1
            last = 2  # so range(1, 2) return [1]
            if batches_conf:
                first = 2
                # BATCH_TOTALS use
                if part in batches_conf:
                    params["env"] += " BATCH={}".format(batches_conf["batch"])
                    last = 1 + batches_conf[part] // batches_conf["batch"]  # int part
                    if batches_conf[part] % batches_conf["batch"]:  # modulo if p > b or p < b
                        last += 1
                # BATCHING use
                if part in batches_conf.get("batching", ""):
                    params["env"] += " BATCH={}".format(batches_conf["batch"])
                # made a first run to set batching dict
                saved_env = params["env"]
                params["env"] += " IU_RUN1=1"
                ret = run_function(run_nb=1, **params)
                if ret != 0:
                    error(
                        append(
                            messages, "Loop on FUNC_PARTS '{}' is broken at part '{}'".format("".join(func_parts), part)
                        )
                    )
                    break
                params["env"] = saved_env
                # BATCHING use
                if part in batches_conf.get("batching", ""):
                    # get batching dict
                    if doit:
                        bldtdir = params["buildouts"][params["bldt"]]["path"]
                        batch_config = get_batch_config([bldtdir, get_instance_home(bldtdir)])
                        if batch_config is None:
                            error(append(messages, "Cannot get batching config file in '{}'".format(bldtdir)))
                            error(
                                append(
                                    messages,
                                    "Loop on FUNC_PARTS '{}' is broken at part '{}'".format("".join(func_parts), part),
                                )
                            )
                            break
                        # modify last, following batching
                        yet_to_treat = batch_config["ll"] - batch_config["kc"]
                        last = 2 + yet_to_treat // batch_config["bn"]  # int part
                        if yet_to_treat % batch_config["bn"]:  # modulo if p > b or p < b
                            last += 1
                        if last == 2:  # only one run, already done
                            batch_delete_files({}, batch_config)
            for batch in range(first, last):
                if " BATCH=" in params["env"] and batch == (last - 1):
                    params["env"] += " BATCH_LAST=1"
                ret = run_function(run_nb=(last > 2 and batch or 0), **params)
                if ret != 0:
                    break
            else:
                continue
            # only here when doing a break
            error(append(messages, "Loop on FUNC_PARTS '{}' is broken at part '{}'".format("".join(func_parts), part)))
            break
        else:
            pass
        return
    else:
        run_function(**params)


def run_develop(buildouts, bldt, products):
    path = buildouts[bldt]["path"]
    os.chdir(path)
    cmd = "bin/develop up -a {}".format(" ".join(products))
    code = 0
    if doit:
        verbose(append(messages, "=> Running '%s'" % cmd))
        (out, err, code) = runCommand(cmd)
        if code:
            error(append(messages, "Problem running bin/develop: {}".format(err)))
    else:
        verbose("=> Will be run '%s'" % cmd)
    return code


def compile_warning(i, params, dump_warnings):
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
                p_dic.update(eval("dict(%s)" % part))
            except Exception as msg:
                error("Problem in -w with param '%s': %s" % (part, msg))
                warning_errors = True
    verbose("Message parameters: %s" % p_dic)
    mandatory_params = ["id", "activate|delete"]
    for param in mandatory_params:
        if not any([prm in p_dic for prm in param.split("|")]):
            error("Parameter '%s' is required !" % param)
            warning_errors = True
    for dt in ("start", "end"):
        if dt in p_dic:
            try:
                p_dic[dt] = datetime.strptime(p_dic[dt], "%Y%m%d-%H%M")
            except ValueError as msg:
                error("Cannot compile datetime '%s' : %s" % (p_dic[dt], msg))
                warning_errors = True

    id = p_dic.pop("id", "no_id")
    if id not in warning_ids:
        warning_ids.insert(i, id)
    if dump_warnings:
        warning_dic[id] = p_dic
        dump_var(warning_file, warning_dic)


def email(buildouts, recipient):
    hostname = socket.gethostname()  # ged-prod4.imio.be, ged-prod5, ged18
    lanhost = hostname.replace(".imio.be", "").replace("-prod", "")
    output = []
    for bldt in sorted(buildouts.keys()):
        if "port" not in buildouts[bldt]:
            continue
        output.append("Buildout '{0}': http://{1}:{2}/manage_main".format(bldt, lanhost, buildouts[bldt]["port"]))
    msg = MIMEMultipart()
    sender = "imio.updates@imio.be"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "imio.updates finished on {}".format(hostname)
    msg.attach(MIMEText("\n".join(output)))
    s = smtplib.SMTP("mailrelay.imio.be", 25)
    s.sendmail(sender, [recipient], msg.as_string())
    s.quit()


def main():
    global ns, doit, pattern, instance, stop, restart, warning_first_pass, wait, traces
    parser = argparse.ArgumentParser(description="Run some operations on zope instances.")
    parser.add_argument("-d", "--doit", action="store_true", dest="doit", help="To apply changes")
    parser.add_argument("-b", "--buildout", action="store_true", dest="buildout", help="To run buildout")
    parser.add_argument(
        "-p", "--pattern", dest="pattern", help="Buildout directory filter with PATTERN as re pattern matching"
    )
    parser.add_argument(
        "-m0",
        "--make0",
        nargs="+",
        dest="make0",
        action="append",
        default=[],
        help="Run 'make MAKE...' command before a buildout and restart",
    )
    parser.add_argument(
        "-m", "--make", nargs="+", dest="make", action="append", default=[], help="Run 'make MAKE...' command"
    )
    parser.add_argument(
        "-f",
        "--function",
        nargs="+",
        dest="functions",
        action="append",
        default=[],
        help="Run a function with args:"
        " * step `profile` `step`"
        " * step `profile` `_all_`"
        " * upgrade `profile`"
        " * upgrade `profile` `1000` `1001`"
        " * upgrade `_all_`",
    )
    parser.add_argument(
        "-s",
        "--superv",
        dest="superv",
        action="append",
        choices=[
            "stop",
            "restart",
            "stopall",
            "restartall",
            "stopworker",
            "restartworker",
            "stopzeo",
            "startzeo",
            "restartzeo",
            "fatal",
        ],
        help="To run supervisor command:"
        " * stop : stop the instances (not zeo)."
        " * restart : restart the instances and waits for it to be up and running (after "
        "buildout if `-b` was provided)."
        " * stopall : stop all buildout processes."
        " * restartall : restart all processes (after buildout if `-b` was provided)."
        " * stopworker : stop the worker instances."
        " * restartworker : restart the worker instances (after buildout if `-b` was provided)."
        " * stopzeo : stop the zeo."
        " * startzeo : start all supervised zeo. (after buildout if `-b` was provided)"
        " * restartzeo : restart the zeo instance (after buildout if `-b` was provided)."
        " * fatal : restart all FATAL process. (after buildout if `-b` was provided)",
    )
    parser.add_argument(
        "-i",
        "--instance",
        dest="instance",
        default="instance-debug",
        help="instance name used to run function or make (default instance-debug)",
    )
    parser.add_argument(
        "-a",
        "--auth",
        dest="auth",
        choices=["0", "1", "8", "9"],
        default="9",
        help="Enable/disable authentication plugins:"
        " * 0 : disable only"
        " * 1 : enable only"
        " * 8 : disable before make or function and enable after (default)"
        " * 9 : don"
        "t do anything",
    )
    parser.add_argument("-u", "--update", nargs="+", dest="develop", help="Update given development products")
    parser.add_argument("-e", "--email", dest="email", help="Email address used to send an email when finished")
    parser.add_argument("-post", "--post", dest="post", help="Mattermost hook string to post a message")
    parser.add_argument("-notif", "--notif", dest="notif", default="", help="User to mention in post message")
    parser.add_argument(
        "-w",
        "--warning",
        nargs="+",
        dest="warnings",
        action="append",
        default=[],
        help='Create or update a message. Parameters like xx="string value".'
        " All parameters must be enclosed by quotes: 'xx=\"val\" yy=True'."
        " Following parameters are possible:"
        ' * id="maintenance-soon"'
        ' * text="A maintenance operation will be done at 4pm."'
        " * activate=True"
        " * ...",
    ),
    parser.add_argument(
        "-wnd",
        "--warning-no-dump",
        action="store_false",
        dest="dump_warnings",
        default="True",
        help="To not dump warnings. Use dump file already there!",
    )
    parser.add_argument(
        "-v",
        "--vars",
        dest="vars",
        action="append",
        default=[],
        help="Define env variables like XX=YY, used as: env XX=YY make (or function). (can use "
        "multiple times -v). FUNC_PARTS, BATCH_TOTALS and BATCHING are special var "
        "(see readme examples).",
    )
    parser.add_argument("-c", "--custom", nargs="+", action="append", dest="custom", help="Run a custom script")
    parser.add_argument("-t", "--traces", action="store_true", dest="traces", help="Add more traces")
    parser.add_argument(
        "-y",
        "--patchindexing",
        action="store_true",
        dest="patchindexing",
        help="To hack collective.indexing.monkey, to keep direct indexation during operations",
    )
    parser.add_argument(
        "-z",
        "--patchinstance",
        action="store_true",
        dest="patchinstance",
        help="To hack instance. (Needed when home page is private)",
    )
    parser.add_argument(
        "-W",
        "--wait",
        action="store_true",
        dest="wait",
        help="Wait for instance to be up and running during a `-s restart`",
    )

    ns = parser.parse_args()
    doit, buildout, instance, pattern = ns.doit, ns.buildout, ns.instance, ns.pattern
    make, functions, auth, warnings = ns.make, ns.functions, ns.auth, ns.warnings
    wait, traces = ns.wait, ns.traces
    start = datetime.now()

    if not doit:
        verbose("Simulation mode: use -h to see script usage.")
    else:
        verbose(append(messages, "NEW RUN on {}".format(start.strftime("%Y%m%d-%H%M"))))
    for sv in ns.superv or []:
        if sv == "stop":
            stop += "i"
        elif sv == "stopall":
            stop += "a"
        elif sv == "stopworker":
            stop += "w"
        elif sv == "stopzeo":
            stop += "z"
        elif sv == "restart":
            restart += "i"
        elif sv == "restartall":
            restart += "a"
        elif sv == "restartworker":
            restart += "w"
        elif sv == "restartzeo":
            restart += "z"
        elif sv == "startzeo":
            restart += "y"
        elif sv == "fatal":
            restart += "f"

    if ns.post and not ns.post.startswith("http"):
        ns.post = "https://chat.imio.be/hooks/{}".format(ns.post)
    if ns.notif:
        ns.notif = "@{} ".format(ns.notif)

    func_parts = []
    batch_totals = []
    batches_conf = {}
    envs = []
    for var in ns.vars:
        if var.startswith("FUNC_PARTS="):
            func_parts = [ltr for ltr in var.split("=")[1]]
        elif var.startswith("BATCH_TOTALS="):
            batch_totals = var.split("=")[1].split(",")
        elif var.startswith("BATCHING="):
            parts = [ltr for ltr in var.split("=")[1] if ltr.isalpha()]
            if parts:
                batches_conf["batching"] = parts
        elif var.startswith("BATCH="):
            batches_conf["batch"] = int(var.split("=")[1])
        else:
            envs.append(var)
    if batch_totals:  # we check content
        for val in batch_totals:
            matched = re.match(r" *(\w) *: *(\d+) *$", val)
            if not matched:
                error(append(messages, "BATCH_TOTALS content check: '{}' not matched !".format(val)))
                sys.exit(1)
            batches_conf[matched.group(1)] = int(matched.group(2))
    if "batch" in batches_conf and len(batches_conf) == 1:
        error(append(messages, "BATCH parameter used without BATCH_TOTALS or BATCHING parameter !"))
        sys.exit(1)
    if batches_conf and "batch" not in batches_conf:
        batches_conf["batch"] = 5000
    if "batching" in batches_conf and len(batches_conf) > 2:
        error(append(messages, "BATCH_TOTALS and BATCHING cannot be used at the same time !"))
        sys.exit(1)
    env = " ".join(envs)

    # buildouts = get_running_buildouts()
    buildouts = get_supervised_buildouts()
    for bldt in sorted(buildouts.keys()):
        path = "%s/%s" % (basedir, bldt)
        if not os.path.exists(path):
            error(append(messages, "Path '%s' doesn't exist" % path))
            continue

        buildouts[bldt]["path"] = path
        plone_path = search_in_port_cfg(path, "plone-path")
        buildouts[bldt]["plone"] = plone_path
        buildouts[bldt]["port"] = get_instance_port(path)

        verbose(append(messages, "Buildout %s    (%s)" % (path, get_git_tag(path))))
        if "f" in restart:
            fatals = [p for p, st in buildouts[bldt]["spv"] if st in ("FATAL", "EXITED")]
            if fatals:
                repair_fatals(buildouts, fatals, bldt, path, plone_path)

        if stop:
            if "i" in stop:
                run_spv(
                    bldt,
                    path,
                    plone_path,
                    "stop",
                    reversed([p for p, st in buildouts[bldt]["spv"] if p.startswith("instance")]),
                )
            if "a" in stop:
                run_spv(bldt, path, plone_path, "stop", reversed([p for p, st in buildouts[bldt]["spv"]]))
            if "w" in stop:
                run_spv(
                    bldt,
                    path,
                    plone_path,
                    "stop",
                    reversed([p for p, st in buildouts[bldt]["spv"] if p.startswith("worker")]),
                )
            if "z" in stop:
                run_spv(bldt, path, plone_path, "stop", ["zeoserver"])

        if ns.make0:
            for param_list in ns.make0:
                run_make(buildouts, bldt, env, " ".join(param_list))

        if buildout:
            if run_buildout(buildouts, bldt):
                continue
        elif ns.develop:
            run_develop(buildouts, bldt, ns.develop)
        if restart:
            if "z" in restart or "y" in restart:
                if [p for p, st in buildouts[bldt]["spv"] if p == "zeoserver" and st == "RUNNING"]:
                    run_spv(bldt, path, plone_path, "restart", ["zeoserver"])
                else:
                    run_spv(bldt, path, plone_path, "start", ["zeoserver"])
                    buildouts[bldt]["spv"] = [tup for tup in buildouts[bldt]["spv"] if tup[0] != "zeoserver"]
                    buildouts[bldt]["spv"].insert(0, ("zeoserver", "RUNNING"))
            if "a" in restart:
                run_spv(bldt, path, plone_path, "restart", [p for p, st in buildouts[bldt]["spv"] if st == "RUNNING"])
            if "i" in restart:
                run_spv(
                    bldt,
                    path,
                    plone_path,
                    "restart",
                    [p for p, st in buildouts[bldt]["spv"] if p.startswith("instance") and st == "RUNNING"],
                )
            if "w" in restart:
                run_spv(
                    bldt,
                    path,
                    plone_path,
                    "restart",
                    [p for p, st in buildouts[bldt]["spv"] if p.startswith("worker") and st == "RUNNING"],
                )

        if [p for p, st in buildouts[bldt]["spv"] if p == "zeoserver" and st != "RUNNING"]:
            error(append(messages, "Zeoserver isn't running"))
            if not instance:
                continue

        if ns.patchinstance:
            if not patch_instance(buildouts[bldt]["path"]):
                continue

        if ns.patchindexing:
            if not patch_indexing(buildouts[bldt]["path"]):
                continue

        if auth == "0" or (auth == "8" and (make or functions)):
            run_function(buildouts, bldt, "", "auth", "0")

        if make:
            for param_list in make:
                run_make(buildouts, bldt, env, " ".join(param_list))

        if ns.custom:
            for param_list in ns.custom:
                # function is optional or can be a param so we need to handle it
                params = {
                    "buildouts": buildouts,
                    "bldt": bldt,
                    "env": env,
                    "script": param_list[0],
                    "fct": "".join(param_list[1:2]),
                    "params": " ".join(param_list[2:]),
                }
                run_function_parts(func_parts, batches_conf, params)

        if functions:
            for param_list in functions:
                params = {
                    "buildouts": buildouts,
                    "bldt": bldt,
                    "env": env,
                    "fct": param_list[0],
                    "params": " ".join(param_list[1:]),
                }
                run_function_parts(func_parts, batches_conf, params)

        if warnings:
            if warning_first_pass:
                for i, param_list in enumerate(warnings):
                    compile_warning(i, param_list, ns.dump_warnings)
                warning_first_pass = False
            if not warning_errors:
                for id in warning_ids:
                    run_function(buildouts, bldt, env, "message", "%s %s" % (id, warning_file))

        if ns.patchindexing:
            unpatch_indexing(buildouts[bldt]["path"])

        if auth == "1" or (auth == "8" and (make or functions)):
            run_function(buildouts, bldt, "", "auth", "1")

    if ns.email and doit:
        email(buildouts, ns.email)

    if ns.post and doit:
        post_request(ns.post, json={"text": "{}{}".format(ns.notif, "\n".join(messages))})

    verbose("Script duration: %s" % (datetime.now() - start))
