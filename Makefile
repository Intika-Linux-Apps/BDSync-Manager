# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

include makefilet-download-ondemand.mk

RELEASE_DIR = releases
RELEASE_PREFIX = bdsync-manager-
# read the latest "Release" line from the changelog
VERSION = $(shell cat VERSION)
RELEASE_ARCHIVE_FILE = $(RELEASE_DIR)/$(RELEASE_PREFIX)$(VERSION).tar.gz
RELEASE_SIGNATURE_FILE = $(RELEASE_ARCHIVE_FILE).sig
UPLOAD_TARGET = $(UPLOAD_USER)@dl.sv.nongnu.org:/releases/bdsync-manager
PYTHON_BUILD_DIRS = bdsync_manager.egg-info build dist

SETUPTOOLS ?= python3 setup.py


.PHONY: release sign upload pypi-upload website website-upload clean

default-target: help

help:
	@echo "Available targets for bdsync-manager:"
	@echo "	sign		- create a signature for a release archive"
	@echo "	release		- create a release archive"
	@echo "	pypi-upload	- upload the Python package to the Python Package Index (pypi)"
	@echo "	website		- create the html output of the website"
	@echo "	website-upload	- upload the website to savannah"
	@echo "	test		- run code style checks"
	@echo "	clean		- remove temporary files"
	@echo

sign: $(RELEASE_SIGNATURE_FILE)

release: $(RELEASE_ARCHIVE_FILE)

upload: sign release
	@[ -z "$(UPLOAD_USER)" ] && { echo >&2 "ERROR: Missing savannah user name for upload:\n	make upload UPLOAD_USER=foobar"; exit 1; } || true
	rsync -a "$(RELEASE_ARCHIVE_FILE)" "$(UPLOAD_TARGET)/"
	rsync -a "$(RELEASE_SIGNATURE_FILE)" "$(UPLOAD_TARGET)/"

$(RELEASE_SIGNATURE_FILE): $(RELEASE_ARCHIVE_FILE) Makefile
	gpg --detach-sign --use-agent "$<"

$(RELEASE_ARCHIVE_FILE): Makefile
	# verify that the given version exists
	git tag | grep -qwF "v$(VERSION)"
	git archive --prefix=$(RELEASE_PREFIX)$(VERSION)/ --output=$@ v$(VERSION)

pypi-upload: sign release
	$(SETUPTOOLS) sdist upload

website:
	$(MAKE) -C website html

website-upload: website
	$(MAKE) -C website cvs-publish

clean:
	$(MAKE) -C website clean
	# python build directories
	$(RM) -r $(PYTHON_BUILD_DIRS)
