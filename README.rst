.. contents::

Introduction
############

This package contains:

* a script to manipulate deployed plone instances managed with supervisor
* helper methods to be used in a zope context for script run from "bin/instance run ..."

Usage
#####

Script
------
bin/update_instances or bin/instances_update.sh

To display more information, use "-h" or "--help" parameter

List of available parameters:

* -d, --doit : to apply changes
* -p val, --pattern=val : buildout directory filter with val as re pattern matching
* -b, --buildout : to run buildout
* -a, --auth : enable/disable authentication plugins

  * 0 : disable only
  * 1 : enable only
  * 8 : disable before make or function and enable after (default)
  * 9 : don't do anything

* -m val, --make=val : run 'make val' command (can use multiple times -m)
* -i val, --instance=val : instance name used to run function or make (default instance-debug)
* -f, --function : run a predefined function with arguments. (can use multiple times -f)

  *     step ``profile-name`` ``step-name`` : run the given step for the given profile
  *     step ``profile-name`` _all_ : run all steps for the given profile
  *     upgrade ``profile-name`` : run the upgrade steps for the given profile
  *     upgrade _all_ : run the upgrade steps for all profiles

* -s val, --superv=val : to run supervisor command (stop|restart|stopall|restartall

  * 	stop : stop the instances first (not zeo) and restart it after buildout
  * 	restart : restart the instances after buildout
  * 	stopall : stop all buildout processes first and restart it after buildout
  * 	restartall : restart all processes after buildout
  *     stopworker : stop the worker instances first (not zeo) and restart it after buildout
  *     restartworker : restart the worker instances after buildout

Helper methods
--------------

* setup_logger: with "bin/instance run", level is 30 (warn). Useful to set it to 20 (info) or 10 (debug)
* setup_app: get admin user, set request

Tips & examples
---------------

* -p ``'^(?!name)'`` : match instances not starting with name
* -p ``.*_ged_20_1`` : match instances ending with _ged_20_1
* -f step ``imio.dms.mail:default`` ``actions`` : run import step for profile profile-imio.dms.mail:default actions

Multiple options:

* -p ``.*_ged_20_1`` -b -s restartall -m ``various-script`` -f step ``imio.dms.mail:default`` ``actions`` -f step ``collective.documentgenerator:default`` ``typeinfo`` -d

Installation
############

To deploy this package

* git clone https://github.com/IMIO/imio.updates.git
* virtualenv-2.7 .
* bin/pip install --trusted-host devpi.imio.be --extra-index-url http://devpi.imio.be/root/imio/+simple -e .

(if problem with imio.pyutils: bin/pip install -f http://devpi.imio.be/root/imio/+simple/imio.pyutils imio.pyutils)

or

* bin/python setup.py develop
