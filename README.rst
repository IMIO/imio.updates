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
bin/update_instances

To display more information, use "-h" or "--help" parameter

List of available parameters:

* -d, --doit : to apply changes
* -b, --buildout : to run buildout
* -m val, --make=val : run 'make val' command
* -p val, --pattern=val : buildout directory filter with val as re pattern matching
* -s val, --superv=val : to run supervisor command (stop|restart|stopall|restartall

  * 	stop : stop the instances first (not zeo) and restart them at script end
  * 	restart : restart the instances at script end
  * 	stopall : stop all buildout processes first (not zeo) and restart them at script end
  * 	restartall : restart all processes at script end

Helper methods
--------------

* setup_logger: with "bin/instance run", level is 30 (warn). Useful to set it to 20 (info) or 10 (debug)
* setup_app: get admin user, set request

Installation
############

To deploy this package

* git clone https://github.com/IMIO/imio.updates.git
* virtualenv-2.7 .
* bin/pip install --trusted-host devpi.imio.be --extra-index-url http://devpi.imio.be/root/imio/+simple -e .

(if problem with imio.pyutils: bin/pip install -f http://devpi.imio.be/root/imio/+simple/imio.pyutils imio.pyutils)

or

* bin/python setup.py develop
