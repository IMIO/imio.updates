Changelog
=========

0.3 (unreleased)
----------------

- Added stopzeo and restartzeo parameters
  [sgeulette]
- Added a QUERY_YEAR env var to inst_info to be able to count content created for a specific year.
  [aduchene]
- Can call multiple times a function with FUNC_PARTS variable and by batch with BATCH_TOTALS AND BATCH values
  [sgeulette]
- Stopped really when error in a function loop
  [sgeulette]
- Various improveents in inst_infos
  [sgeulette]
- Handled FATAL and EXITED supervisor status
  [sgeulette]
- Improved batching with automatic BATCHING handling
  [sgeulette]
- Added some tests in py3
  [sgeulette]
- Added IU_RUN1 env var when doing first call
  [sgeulette]

0.2 (2022-02-12)
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
- Can call multiple times a function with FUNC_PARTS variable
  [sgeulette]

0.1 (2018-06-21)
----------------

- Package created
  [sgeulette]
