Title: bdsync-manager v0.0.1 released


This is the first release of the *bdsync-manager* software.

Download the release: [v0.0.1](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager_0.0.1.tar.gz)
                      ([signature](http://download.savannah.gnu.org/releases/bdsync-manager/bdsync-manager_0.0.1.tar.gz.sig))

It is built upon the highly efficient blockdevice synchronization tool [bdsync](https://github.com/TargetHolding/bdsync).

*bdsync-manager* offers the following features:

* define a list of sources and targets for regular blockdevice synchronization
* create and remove LVM snapshots for the duration of the synchronization (optional)
* output statistics regarding patch generation time, patch size and patch application time

*bdsync-manager* is written in Python.

Requirements:

* [bdsync](https://github.com/TargetHolding/bdsync)
* [Python](http://python.org/)
* [plumbum](http://plumbum.readthedocs.org/)
