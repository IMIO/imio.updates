#!/usr/bin/make
#

.PHONY: setup
setup:
	virtualenv -p python2 .
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements.txt -e .
	./bin/update_instances

.PHONY: cleanall
cleanall:
	rm -fr bin include lib local share
	git checkout bin
