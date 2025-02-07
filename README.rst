.. contents::

Introduction
############

This package contains:

* a script to manipulate deployed plone instances managed with supervisor
* helper methods to be used in a zope context for script run from "bin/instance run ..."

Usage
#####

Main script
-----------
bin/update_instances or bin/instances_update.sh

To display more information, use "-h" or "--help" parameter

List of available parameters:

* -d, --doit : to apply changes
* -p val, --pattern=val : buildout directory filter with val as re pattern matching
* -b, --buildout : to run buildout
* -m0 val, --make0=val : run 'make val' command after stop and before buildout (can use multiple times -m0)
* -m val, --make=val : run 'make val' command (can use multiple times -m)
* -i val, --instance=val : instance name used to run function or make (default instance-debug)
* -f, --function : run a predefined function with arguments. (can use multiple times -f)

  *     step ``profile-name`` ``step-name`` : run the given step for the given profile
  *     step ``profile-name`` _all_ : run all steps for the given profile
  *     upgrade ``profile-name`` : run the upgrade steps for the given profile
  *     upgrade ``profile-name`` ``dest1`` ... : run the given upgrade steps for the given profile
  *     upgrade _all_ : run the upgrade steps for all profiles

* -s val, --superv=val : to run supervisor command (stop|restart|stopall|restartall

  * 	stop : stop the instances (not zeo)
  * 	restart : restart the instances (after buildout if `-b` was provided)
  * 	stopall : stop all buildout processes
  * 	restartall : restart all processes (after buildout if `-b` was provided)
  *     stopworker : stop the worker instances
  *     restartworker : restart the worker instances (after buildout if `-b` was provided)
  *     stopzeo : stop the zeo
  *     startzeo : start all supervised zeo. (after buildout if `-b` was provided)
  *     restartzeo : restart the zeo instance (after buildout if `-b` was provided)

* -a, --auth : enable/disable authentication plugins

  * 0 : disable only
  * 1 : enable only
  * 8 : disable before make or function and enable after (default)
  * 9 : don't do anything

* -u vals, --update vals : update given development products.

* -e, --email : email address used to get an email when finished

* -w, --warning : create or update a message. Parameters like xx="string value". All parameters must be enclosed by quotes: 'xx="val" yy=True'.

  * id="maintenance-soon"
  * text="A maintenance operation will be done at 4pm."
  * activate=True
  * delete=False
  * msg_type="" (info, significant, warning (default))
  * can_hide=True
  * start, end="YYYYMMDD-hhmm"
  * ...

* -wnd, --warning-no-dump : do not write disk message file. The existing one is used.

* -c, --custom : run a custom script with arguments.

  * First parameter is the relative path from your buildout to the script file.
  * Other parameters are arguments to be given to the script when called.

* -v, --vars : Define env variables like XX=YY, used as: env XX=YY make (or function).
  (can use multiple times -v). FUNC_PARTS and BATCH_TOTALS are special var (see examples).

* -t, --traces : Add more traces

* -y, --patchindexing : To hack collective.indexing.monkey, to keep direct indexation during operations

* -z, --patchdebug : Used to patch instance-debug if front-page is a dexterity type and not publically accessible

* -W, --wait : Wait for instance to be up and running during a `-s restart`

To change log level when running instance script, change LOGGER_LEVEL in run_script.py.

Helper methods
--------------

* setup_logger: with "bin/instance run", level is 30 (warn). Useful to set it to 20 (info) or 10 (debug)
* setup_app: get admin user, set request

inst_infos.py script
--------------------

This script is run by instance (as run script) to get various information.
It is compatible py2 / py3.

Tips & examples
---------------

* -p ``'^(?!name)'`` : match instances not starting with name
* -p ``'^(?:(?!name).)*$'`` : match instances not containing name
* -p ``.*_ged_20_1`` : match instances ending with _ged_20_1
* -f step ``imio.dms.mail:default`` ``actions`` : run import step for profile profile-imio.dms.mail:default actions
* -w '``id="maintenance-soon" text="A maintenance operation will be done at 4pm." activate=True``'
* -c ``scripts/my_custom.py param1 param2`` : calls the scripts at buildout/scripts/my_custom.py with param1 and param2 as arguments
* -v FUNC_PARTS=abcde : calls -f multiple time for each letter passed as ENV FUNC_PART=a.
  Can be used to split migration in multiple runs.
* -v FUNC_PARTS=abc -v BATCH_TOTALS=b:2100,c:2000 -v BATCH=1000 : calls the specified parts in batch following totals.
  Sub calls as ENV FUNC_PART=a (one time), ENV FUNC_PART=b (3 times), ENV FUNC_PART=C (2 times)
* -v FUNC_PARTS=abc -v BATCHING=bc -v BATCH=1000 : calls the specified parts with automatic batching.
  Sub calls as ENV FUNC_PART=a (one time), ENV FUNC_PART=b (x times), ENV FUNC_PART=C (y times)

Multiple options:

* -p ``.*_ged_20_1`` -b -s restartall -m ``various-script`` -f step ``imio.dms.mail:default`` ``actions`` -f step ``collective.documentgenerator:default`` ``typeinfo`` -d

Installation
############

To deploy this package

* git clone https://github.com/IMIO/imio.updates.git
* cd imio.updates
* make setup

From the past... :

* virtualenv -p python2 . (if packages python2 and virtualenv are installed)
* (or virtualenv-2.7 . (if python2 manually compiled))
* (bin/pip install setuptools==41.0.1)
* `bin/pip install -e .`  or  `bin/python setup.py develop`

or

* bin/pip install --trusted-host devpi.imio.be --extra-index-url https://devpi.imio.be/root/imio/+simple -e .
* if problem with imio.pyutils: bin/pip install -f https://devpi.imio.be/root/imio/+simple/imio.pyutils imio.pyutils
