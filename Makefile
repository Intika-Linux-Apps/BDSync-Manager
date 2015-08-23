RELEASE_DIR = releases
RELEASE_PREFIX = $(RELEASE_DIR)/bdsync-manager_
# read the latest "Release" line from the changelog
VERSION = $(shell grep -w "^Version" changelog | head -1 | awk '{print $$2}')

.PHONY: release

release:
	tar czf "$(RELEASE_PREFIX)$(VERSION).tar.gz" --exclude-vcs --exclude=$(RELEASE_DIR) .
