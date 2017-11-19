Title: bdsync-manager v0.3.0 released
Date: 2017-11-19
Authors: Lars Kruse
Category: Release


This is the fourth release of the *bdsync-manager* software.

Download the release: [v0.3.0](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager-0.3.0.tar.gz)
                      ([signature](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager-0.3.0.tar.gz.sig))
                      ([deb package](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager_0.3.0-1_all.deb))

This release includes the following changes:

* continue with the next task if program execution error occoured
* add deb packaging
* configurable bandwidth limitation (via pv)

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
