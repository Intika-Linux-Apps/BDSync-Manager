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
* [Python](http://python.org/): *bdsync-manager* is written in Python
* [plumbum](http://plumbum.readthedocs.org/): this python library provides easy access to typical shell-based features (e.g. pipelining processes)


Please note that you also need *bdsync* available on the target host for all remote transfers. You may circumvent this requirement by mounting the remote storage locally (e.g. via *sshfs*), but then you would loose *bdsync*'s efficient mode of remote operation. Please take a look at *bdsync*'s details to fully understand the implications of a local mount instead of a remotely running *bdsync* process.


## Typical Workflows ##

### Replicate a virtualization server remotely ###

Setup:

* you are running a virtualization server
* the virtual guests are stored on blockdevices (e.g. LVM volumes)
* you want to copy all your blockdevices every night to a remote server

Usage:

1. write a *bdsync-manager* configuration file containing all blockdevices that should be synchronized
1. define how to access the remote server in the *DEFAULT* section of the config file (e.g. *ssh bar@foo.baz*)
1. add a *lvm_snapshot_enabled* to the *DEFAULT* section of the config file if you want to backup a time-consistent state of your blockdevics
1. create the target files (e.g. *touch TARGET*) or blockdevices (e.g. *lvcreate*) on the target server
1. run *bdsync-manager* as a nightly cron-job

### Backup an encrypted volume to an untrusted backup storage ###

Setup:

* one of your local blockdevices is encrypted (e.g. via *cryptsetup*)
* you can access a remote backup storage via ssh and run software on the other side
* the backup storage is not completely under your control and encrypted / you do not trust it fully

Usage:

1. write a *bdsync-manager* configuration file with a single task definition (your local source and the remote target)
1. transfer an initial copy of your blockdevice or create an empty dummy file on the target host
1. create a cron-job for unattended synchronization or run *bdsync* manually from time to time


## FAQ ##

### Why should I use bdsync instead of rsync? ###
*rsync* does not work with blockdevices. Thus if you need to synchronize a blockdevice with a local or remote file or blockdevice then you need to use *bdsync* instead.

### Why not use bdsync directly? ###
*bdsync* is carefully designed to minimize the probability of a corrupted backup target by separating the synchronization into three steps:

1. create the patch
2. transfer the patch
3. apply the patch

All three steps could be executed in a single nifty shell command line by piping the output of each piece into the next. Sadly the first step (create a patch) takes quite some time (maybe hours - depending on the size of your blockdevices). By running all steps at the same time your remote blockdevice backup is in inconsistent state for a many hours each day. This is probably not what you want.

*bdsync-manager* makes it easy to run the above workflow easily with a single command in a safe manner. It automatically combines the first two steps (create and transfer the patch). This is safe since it does not affect the remote copy. Afterwards the patch is applied. This usually takes just a few minutes and thus minimizes the risk of data corruption in case of external failures.

In short: *bdsync-manager* makes it just a bit easier to use *bdsync* for a specifc but quite typical use-case.

### How should I transfer the initial copy? ###
This depends on your usage of *bdsync* and is not specific for *bdsync-manager*.

The fail-safe approach for the initial copy is a transfer via *ssh* to the remote host:

    cat SOURCE_BLOCKDEVICE | ssh bar@foo.baz "cat >target.img"

(Use [pv](http://www.ivarch.com/programs/pv.shtml) instead of *cat* for a fancy progress bar.)

Alternatively (provided enough space for a full-size patch on the remote host) you can also create a dummy target file (e.g. *touch target.img*) and use *bdsync_args = --diffsize=resize* in your config file for the initial synchronization.


## Configuration file ##
By default *bdsync-manager* reads its configuration from */etc/bdsync-manager.conf*. You may specify an alternative location as a command line argument (*--config*).

The configuration file is structured with a [ini-file style](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure). Each section describes one task. The special section *DEFAULT* can be used to specify defaults that are used for all other sections (if not overwritten explicitely).

### Example configuration ###

    [DEFAULT]
    local_bdsync_bin = /usr/local/bin/bdsync
    remote_bdsync_bin = /usr/local/bin/bdsync
    connection_command = ssh -p 2200 foo@example.org
    target_patch_dir = bdsync-patches
    bdsync_args = --diffsize=resize

    [example-root]
    source_path = /dev/lvm-foo/example-root
    target_path = bdsync/example-root.img
    lvm_snapshot_enabled = yes
    lvm_snapshot_size = 5G
    lvm_snapshot_name = bdsync-snapshot


### Core settings ###

#### source_path ####
The path of a local blockdevice used as the source for the synchronization.

This setting is required.

#### target_path ####
The local or remote path of a file of blockdevice used as the target for the synchronization. This file or blockdevice must exist prior running *bdsync-manager*. Relative paths are interpretated relative to the current directory (local target) or relative to the remote user's home directory (remote target).

#### connection_command ####
A non-empty value of this settings indicates a remote operation. Typically you will want to use *ssh* for non-interactive remote connections (e.g. *connection_command = ssh -p 10022 backup@example.org*).

You will need to specify *remote_bdsync_bin* if *connection_command* is non-empty.

This setting is optional. The default value is empty.

#### disabled ####
This convenience settings allows you to disable tasks easily. You may use any boolean-like value (0/1/yes/no/y/n/true/false/on/off). Alternatively you may also just comment all lines of the task definition (preprending *#*).

This setting is optional and defaults to *False*.

### bdsync-related settings ###
#### local_bdsync_bin ####
The location of the local *bdsync* binary (e.g. */usr/local/bin/bdsync*).

This setting is required.

#### remote_bdsync_bin ####
The location of the remote *bdsync* binary (e.g. */usr/local/bin/bdsync*).

This setting is required if *connection_command* is specified.

#### bdsync_args ####
*bdsync* allows a few additional arguments for its operation. The arguments given here are applied to the *client* call and to the *patch* call. Reasonable examples are *--diffsize=resize* or *--twopass*. Arguments are passed to *bdsync* as-is - you may specify as many as you like separated with spaces.

#### target_patch_dir ####
*bdsync*'s binary patches are stored locally or transferred to the remote target host. The path may be absolute or relative to the current directory (local target) or relative to the home directory of the remote user (remote target). You need to create this directory manually. You need to make sure that the directory is on a filesystem with enough free capacity for your *bdsync* patches. The full size of the largest blockdevice to be transferred is the worst case capacity requiremnt.

This setting is required.

### LVM support ###
You may want to use LVM's snapshotting feature for creating a time-consistent copy of the source blockdevice.

#### lvm_snapshot_enabled ####
If this setting evaluates to a *true*-like value (1/yes/y/true/on) a snapshot is created for the duration of the synchronization.

This setting is optional. It defaults to *False*

#### lvm_snapshot_size ####
The size of the snapshot volume must be specified (see option *--size* in *man lvcreate*, e.g. *20G*). Please evaluate carefully the amount of changes to be expected for the source blockdevice during the synchronization process. If the snapshot runs out of space it will be invalidated by LVM. Thus the synchronization would fail (without corrupting the target).

This setting is required if *lvm_snapshot_enabled* is *True*.

#### lvm_snapshot_name ####
The name of the snapshot volume should not conflict with the names of other volumes in the same volume group on the local host. *bdsync-manager* will stop if it exists (e.g. a remainder of a previous synchronization run). The snapshot will be removed immediately after each task.

This setting is required if *lvm_snapshot_enabled* is *True*.
