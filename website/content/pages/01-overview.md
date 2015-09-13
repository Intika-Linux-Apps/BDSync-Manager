Title: Overview


## Name ##

bdsync-manager - maintain and execute your synchronization tasks of local or remote blockdevices with [bdsync](https://github.com/TargetHolding/bdsync)


## Synopsis ##

  bdsync-manager [--log-level=(DEBUG|INFO|WARNING|ERROR)] [--task TASK_NAME] [--config CONFIG_FILE]


## Description ##

*bdsync-manager* simplifies local or remote synchronization of blockdevices.

As a wrapper around the [bdsync](https://github.com/TargetHolding/bdsync) tool, it allows to define a list of source and target blockdevices with different specifications (e.g. target hosts, LVM snapshotting). *bdsync-manager* is most suitable as a simple cron-job for keeping a remote backup in sync with your plain or encrypted blockdevices.

You may think of *bdsync* as the blockdevice-oriented counterpart of *rsync* (which cannot handle blockdevices). Thus *bdsync-manager* would be similar to *rsnapshot* for managing multiple sources and targets to be used for non-interactive synchronization tasks.

Please take a detailed look at [bdsync](https://github.com/TargetHolding/bdsync). If *bdsync*'s features are suitable for your workflow then *bdsync-manager* will probably help you to avoid writing scripts on your own.

*bdsync-manager* is written in [Python](http://python.org) and licensed under the [GPL v3 or later](http://www.gnu.org/licenses/gpl.txt).


## Features ##

* simplify the usage of bdsync's well-designed workflow (create/transfer/apply the patch) 
* define multiple blockdevice synchronization tasks with different options in a single configuration file
* output timing statistics for patch creation and patch application
* [optional] create LVM snapshots for the duration of the synchronization for a time-consistent backup
