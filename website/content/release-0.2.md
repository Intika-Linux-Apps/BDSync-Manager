Title: bdsync-manager v0.2 released
Date: 2016-04-12
Authors: Lars Kruse
Category: Release


This is the third release of the *bdsync-manager* software.

Download the release: [v0.2](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager-0.2.tar.gz)
                      ([signature](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager-0.2.tar.gz.sig))

This release includes the following changes:

* add *apply_patch_in_place* setting (simplifying the initial copy)
* LVM: replace the previous dummy operation for snapshot removal with a real one

*bdsync-manager* relies upon the highly efficient blockdevice synchronization tool [bdsync](https://github.com/TargetHolding/bdsync).

*bdsync-manager* offers the following features:

* synchronize one or more blockdevices to a remote location (as a file or blockdevice)
* create and remove LVM snapshots for the duration of the synchronization (optional)
* output statistics regarding patch generation time, patch size and patch application time

*bdsync-manager* is written in Python.

Requirements:

* [bdsync](https://github.com/TargetHolding/bdsync)
* [Python](http://python.org/)
* [plumbum](http://plumbum.readthedocs.org/)
