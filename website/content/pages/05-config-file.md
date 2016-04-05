Title: Configuration


By default *bdsync-manager* reads its configuration from */etc/bdsync-manager.conf*. You may specify an alternative location as a command line argument (*--config*).

The configuration file is structured with a [ini-file style](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure). Each section describes one task. The special section *DEFAULT* can be used to specify defaults that are used for all other sections (if not overwritten explicitely).

## Example configuration ##

See the [example configuration file](bdsync-manager.conf.sample) for the definitions of a few typical tasks.


## Core settings ##

### source_path ###
The path of a local blockdevice used as the source for the synchronization.

This setting is required.

### target_path ###
The local or remote path of a file of blockdevice used as the target for the synchronization. This file or blockdevice must exist prior running *bdsync-manager*. Relative paths are interpretated relative to the current directory (local target) or relative to the remote user's home directory (remote target).

### connection_command ###
A non-empty value of this setting indicates a remote operation. Typically you will want to use *ssh* for non-interactive remote connections (e.g. *connection_command = ssh -p 10022 backup@example.org*).

You will need to specify *remote_bdsync_bin* if *connection_command* is non-empty.

This setting is optional. The default value is empty.

### disabled ###
This convenience settings allows you to disable tasks easily. You may use any boolean-like value (0/1/yes/no/y/n/true/false/on/off). Alternatively you may also just comment all lines of the task definition (preprending *#*).

This setting is optional and defaults to *False*.

## bdsync-related settings ##
### local_bdsync_bin ###
The location of the local *bdsync* binary (e.g. */usr/local/bin/bdsync*).

This setting is required.

### remote_bdsync_bin ###
The location of the remote *bdsync* binary (e.g. */usr/local/bin/bdsync*).

This setting is required if *connection_command* is specified.

### bdsync_args ###
*bdsync* allows a few additional arguments for its operation. The arguments given here are applied to the *client* call and to the *patch* call. Reasonable examples are *--diffsize=resize* or *--twopass*. Arguments are passed to *bdsync* as-is - you may specify as many as you like separated with spaces.

### target_patch_dir ###
*bdsync*'s binary patches are stored locally or transferred to the remote target host. The path may be absolute or relative to the current directory (local target) or relative to the home directory of the remote user (remote target). You need to create this directory manually. You need to make sure that the directory is on a filesystem with enough free capacity for your *bdsync* patches. The full size of the largest blockdevice to be transferred is the worst case capacity requiremnt.

This setting is required.

### create_target_if_missing ###
*bdsync-manager* will try to create an empty target file (issuing a *touch* command) if the target is missing.

This setting simplifies the initial run of a backup.

This setting is optional and defaults to *False*.

## LVM support ##
You may want to use LVM's snapshotting feature for creating a time-consistent copy of the source blockdevice.

### lvm_snapshot_enabled ###
If this setting evaluates to a *true*-like value (1/yes/y/true/on) a snapshot is created for the duration of the synchronization.

This setting is optional. It defaults to *False*

### lvm_snapshot_size ###
The size of the snapshot volume must be specified (see option *--size* in *man lvcreate*, e.g. *20G*). Please evaluate carefully the amount of changes to be expected for the source blockdevice during the synchronization process. If the snapshot runs out of space it will be invalidated by LVM. Thus the synchronization would fail (without corrupting the target).

This setting is required if *lvm_snapshot_enabled* is *True*.

### lvm_snapshot_name ###
The name of the snapshot volume should not conflict with the names of other volumes in the same volume group on the local host. *bdsync-manager* will stop if it exists (e.g. a remainder of a previous synchronization run). The snapshot will be removed immediately after each task.

This setting is required if *lvm_snapshot_enabled* is *True*.

### lvm_program_path ###
The location of the *lvm* executable is needed for LVM snapshot management.

This setting defaults to */sbin/lvm*.
