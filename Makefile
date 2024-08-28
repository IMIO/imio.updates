#!/usr/bin/make
#

.PHONY: setup
setup:
	virtualenv .
	@if [ "`./bin/python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1`" -ne "3" ]; then \
	    echo "Error: Python 3 is required. Current version is `./bin/python --version`."; exit 1; fi
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements.txt -e .
	./bin/update_instances

.PHONY: cleanall
cleanall:
	rm -fr bin include lib local share
	git checkout bin
