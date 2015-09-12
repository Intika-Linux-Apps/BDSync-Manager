# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.


RELEASE_DIR = releases
RELEASE_PREFIX = $(RELEASE_DIR)/bdsync-manager_
# read the latest "Release" line from the changelog
VERSION = $(shell grep -w "^Version" changelog | head -1 | awk '{print $$2}')
RELEASE_ARCHIVE_FILE = $(RELEASE_PREFIX)$(VERSION).tar.gz
RELEASE_SIGNATURE_FILE = $(RELEASE_ARCHIVE_FILE).sig
UPLOAD_TARGET = $(UPLOAD_USER)@dl.sv.nongnu.org:/releases/bdsync-manager


.PHONY: release sign upload


release: $(RELEASE_ARCHIVE_FILE)

sign: $(RELEASE_SIGNATURE_FILE)

upload: sign release
	@[ -z "$(UPLOAD_USER)" ] && { echo >&2 "ERROR: Missing savannah user name for upload:\n	make upload UPLOAD_USER=foobar"; exit 1; } || true
	rsync -a "$(RELEASE_ARCHIVE_FILE)" "$(UPLOAD_TARGET)/"
	rsync -a "$(RELEASE_SIGNATURE_FILE)" "$(UPLOAD_TARGET)/"

$(RELEASE_SIGNATURE_FILE): $(RELEASE_ARCHIVE_FILE)
	gpg --detach-sign --use-agent "$<"

$(RELEASE_ARCHIVE_FILE):
	tar czf "$(RELEASE_ARCHIVE_FILE)" --exclude-vcs --exclude=$(RELEASE_DIR) .
