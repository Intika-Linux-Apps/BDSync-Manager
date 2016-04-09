Title: bdsync-manager v0.1 released
Date: 2016-04-05
Authors: Lars Kruse
Category: Release


This is the second release of the *bdsync-manager* software.

Download the release: [v0.1](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager_0.1.tar.gz)
                      ([signature](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager_0.1.tar.gz.sig))

This release includes the following changes:

* missing target files can be created automatically
* user path expansion (tilde expansion) is applied to most path settings

*bdsync-manager* relies upon the highly efficient blockdevice synchronization tool [bdsync](https://github.com/TargetHolding/bdsync).

*bdsync-manager* offers the following features:

* define a list of sources and targets for regular blockdevice synchronization
* create and remove LVM snapshots for the duration of the synchronization (optional)
* output statistics regarding patch generation time, patch size and patch application time

*bdsync-manager* is written in Python.

Requirements:

* [bdsync](https://github.com/TargetHolding/bdsync)
* [Python](http://python.org/)
* [plumbum](http://plumbum.readthedocs.org/)
