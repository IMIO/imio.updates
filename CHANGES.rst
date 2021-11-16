Changelog
=========

0.2 (unreleased)
----------------

- Managed stop and start separately
  [sgeulette]
- Added new parameters to run functions like import step or upgrade step.
  [sgeulette]
- Added new parameter to manage authentication plugins
  [sgeulette]
- Added new parameter to manage messages
  [sgeulette]
- Can change logger level in run_script
  [sgeulette]
- Added new parameter to pass environment variable
  [sgeulette]
- Added new parameter to patch instance-debug interpreter. So bin/instance run is possible without Unauthorized.
  [sgeulette]
- Use portal_membership.searchForUsers to get users from every authentication
  plugins, including LDAP
  [gbastien]
- Added new parameter to update development products
  [sgeulette]
- Added inst_infos module to get site information
  [sgeulette]
- Added Makefile to setup or cleanall
  [sgeulette]
- Added sleep while restarting instances with supervisor
  [mdhyne, odelaere, sgeulette]
- Read and find port using pythonic way
  [odelaere]

0.1 (2018-06-21)
----------------

- Package created
  [sgeulette]
