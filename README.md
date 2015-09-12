# bdsync-manager #

## Name ##

bdsync-manager - maintain and execute your synchronization tasks of local or remote blockdevices with [bdsync](https://github.com/TargetHolding/bdsync)


## Synopsis ##

  bdsync-manager [--log-level=(DEBUG|INFO|WARNING|ERROR)] [--task TASK_NAME] [--config CONFIG_FILE]


## Description ##

*bdsync-manager* simplifies local or remote synchronization of blockdevices.

As a wrapper around the [bdsync]((https://github.com/TargetHolding/bdsync) tool, it allows to define a list of source and target blockdevices with different specifications (e.g. target hosts, LVM snapshotting). *bdsync-manager* is most suitable as a simple cron-job for keeping a remote backup in sync with your plain or encrypted blockdevices.

You may think of *bdsync* as the blockdevice-oriented counterpart of *rsync* (which cannot handle blockdevices). Thus *bdsync-manager* would be similar to *rsnapshot* for managing multiple sources and targets to be used for non-interactive synchronization tasks.

Please take a detailed look at [bdsync]((https://github.com/TargetHolding/bdsync). If *bdsync*'s features are suitable for your workflow then *bdsync-manager* will probably help you to avoid writing scripts on your own.

*bdsync-manager* is written in [Python](http://python.org) and licensed under the [GPL v3 or later](http://www.gnu.org/licenses/gpl.txt).


## Features ##

* simplify the usage of bdsync's well-designed workflow (create/transfer/apply the patch) 
* define multiple blockdevice synchronization tasks with different options in a single configuration file
* output timing statistics for patch creation and patch application
* [optional] create LVM snapshots for the duration of the synchronization for a time-consistent backup


## Requirements ##
The following software is required for running *bdsync-manager*:

* [bdsync]((https://github.com/TargetHolding/bdsync): efficiently create and apply patches for blockdevice synchronization
* [Python](http://python.org/): *bdsync-manager* is written in Python and requires Python 3.2 or later
* [plumbum](http://plumbum.readthedocs.org/): this python library provides easy access to typical shell-based features (e.g. pipelining processes)


Please note that you also need *bdsync* available on the target host for all remote transfers. You may circumvent this requirement by mounting the remote storage locally (e.g. via *sshfs*), but then you would loose *bdsync*'s efficient mode of remote operation. Please take a look at *bdsync*'s details to fully understand the implications of a local mount instead of a remotely running *bdsync* process.


## Installation ##

1. download and install the requirements (see above)
2. clone the *bdsync-manager* repository or download and extract a release archive
3. (optional) symlink or copy *bdsync-manager* to a path used for executables (e.g. */usr/local/bin/bdsync-manager*)
4. create a configuration file (see below)


## Typical Workflows ##

### Replicate a virtualization server remotely ###

Setup:

* you are running a virtualization server
* the virtual guests are stored on blockdevices (e.g. LVM volumes)
* you want to copy all your blockdevices every night to a remote server

Usage:

1. write a *bdsync-manager* configuration file containing all blockdevices that should be synchronized
2. define how to access the remote server in the *DEFAULT* section of the config file (e.g. *ssh bar@foo.baz*)
3. add a *lvm_snapshot_enabled* to the *DEFAULT* section of the config file if you want to backup a time-consistent state of your blockdevics
4. create the target files (e.g. *touch TARGET*) or blockdevices (e.g. *lvcreate*) on the target server
5. run *bdsync-manager* as a nightly cron-job

### Backup an encrypted volume to an untrusted backup storage ###

Setup:

* one of your local blockdevices is encrypted (e.g. via *cryptsetup*)
* you can access a remote backup storage via ssh and run software on the other side
* the backup storage is not completely under your control and encrypted / you do not trust it fully

Usage:

1. write a *bdsync-manager* configuration file with a single task definition (your local source and the remote target)
2. transfer an initial copy of your blockdevice or create an empty dummy file on the target host
3. create a cron-job for unattended synchronization or run *bdsync* manually from time to time
