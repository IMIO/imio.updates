#!/usr/bin/make
#

.PHONY: setup
setup:
	virtualenv-2.7 .
	./bin/pip install --upgrade pip
	./bin/pip install -e .
	./bin/update_instances

.PHONY: cleanall
cleanall:
	rm -fr bin include lib local share
	git checkout bin
