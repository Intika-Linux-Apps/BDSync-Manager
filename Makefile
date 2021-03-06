# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

include makefilet-download-ondemand.mk

RELEASE_DIR = releases
RELEASE_PREFIX = bdsync-manager
# read the latest "Release" line from the changelog
VERSION = $(shell cat VERSION)
RELEASE_ARCHIVE_FILE = $(RELEASE_DIR)/$(RELEASE_PREFIX)-$(VERSION).tar.gz
RELEASE_DEB_FILE = $(RELEASE_DIR)/$(RELEASE_PREFIX)_$(VERSION)-1_all.deb
RELEASE_SIGNATURE_FILE = $(RELEASE_ARCHIVE_FILE).sig
UPLOAD_TARGET = $(UPLOAD_USER)@dl.sv.nongnu.org:/releases/bdsync-manager
PYTHON_BUILD_DIRS = bdsync_manager.egg-info build dist
MANPAGE = $(DIR_BUILD)/bdsync-manager.1

SETUPTOOLS ?= python3 setup.py

PYPI_UPLOAD_TARGET = pypi


.PHONY: release sign upload pypi-upload website website-upload clean

default-target: help

help:
	@echo "Available targets for bdsync-manager:"
	@echo "	sign		- create a signature for a release archive"
	@echo "	release		- create distributable files for a release"
	@echo "	upload-python	- upload the Python package to the Python Package Index (pypi)"
	@echo "	upload-savannah	- upload release files to the savannah hosting"
	@echo "	website		- create the html output of the website"
	@echo "	website-upload	- upload the website to savannah"
	@echo "	test		- run code style checks"
	@echo "	clean		- remove temporary files"
	@echo

sign: $(RELEASE_SIGNATURE_FILE)

release: $(RELEASE_ARCHIVE_FILE) $(RELEASE_DEB_FILE)

build: manpages

.PHONY: manpages
manpages: $(MANPAGE)

$(MANPAGE): Makefile bdsync-manager.help2man.include
	help2man --no-info --include bdsync-manager.help2man.include ./bdsync-manager >"$@.new"
	mv "$@.new" "$@"

upload-savannah: sign release
	@[ -z "$(UPLOAD_USER)" ] && { echo >&2 "ERROR: Missing savannah user name for upload:\n	make upload-savannah UPLOAD_USER=foobar"; exit 1; } || true
	rsync -a "$(RELEASE_ARCHIVE_FILE)" "$(RELEASE_SIGNATURE_FILE)" "$(RELEASE_DEB_FILE)" "$(UPLOAD_TARGET)/"

$(RELEASE_SIGNATURE_FILE): $(RELEASE_ARCHIVE_FILE) Makefile
	gpg --detach-sign --use-agent "$<"

$(RELEASE_ARCHIVE_FILE): Makefile
	# verify that the given version exists
	git tag | grep -qwF "v$(VERSION)"
	git archive --prefix=$(RELEASE_PREFIX)-$(VERSION)/ --output=$@ v$(VERSION)

$(RELEASE_DEB_FILE): Makefile dist-deb $(DIR_DEBIAN_BUILD)/$(notdir $@)
	cp "$(DIR_DEBIAN_BUILD)/$(notdir $@)" "$@"

website:
	$(MAKE) -C website html

website-upload: website
	$(MAKE) -C website cvs-publish

clean:
	$(MAKE) -C website clean
	# python build directories
	$(RM) -r $(PYTHON_BUILD_DIRS)
