#!/usr/bin/make
#

.PHONY: setup
setup:
	if command -v virtualenv-2.7; then virtualenv-2.7 . ; elif command -v python2 >/dev/null && command -v virtualenv; then virtualenv -p python2 . ; fi
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements.txt -e .
	./bin/update_instances

.PHONY: cleanall
cleanall:
	rm -fr bin include lib local share
	git checkout bin
