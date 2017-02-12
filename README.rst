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
* -p val, --pattern=val : buildout directory filter with val as re pattern matching
* -s val, --superv=val : to run supervisor command (stop|restart|stopall|restartall

  * 	stop : stop the instances first (not zeo) and restart them at script end
  * 	restart : restart the instances at script end
  * 	stop : stop all buildout processes first (not zeo) and restart them at script end
  * 	restartall : restart all processes at script end

Helper methods
--------------

* setup_app: get admin user, set request

Installation
############
To test this package

* git clone ...
* virtualenv-2.7 .
* bin/python setup.py develop

To use it in production

* virtualenv-2.7 .
* bin/pip install imio.upgrades
