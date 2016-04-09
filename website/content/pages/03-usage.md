Title: Usage

# Quickstart #

The following minimal setup simply creates a backup copy of your precious */etc/hosts* file. Obviously you may choose more interesting sources and targets.

Start with [installing](installation.html) bdsync-manager and its dependencies.

Create a simple configuration file (e.g. *bdsync-manager.conf*):

	[DEFAULT]
	local_bdsync_bin = /usr/local/bin/bdsync
	create_target_if_missing = True
	apply_patch_in_place = True

	[example-hosts-file]
	source_path = /etc/hosts
	target_path = ~/hosts-file-backup

Start the synchronization:

	bdsync-manager --config bdsync-manager.conf --log-level info

This operation should obviously be finished within seconds due to its simplicity. Hopefully it gives you a feeling for the procedures of *bdsync-manager*.


# Supported source and target combinations #

## Local and remote synchronization ##

Currently the following combinations are supported:

* local source and local target
* local source and remote target

All operations for local targets are usable with remote targets, as well.

## Source and target storage types ##

Both the source and the target may be a blockdevice or a file.

A few special operations are currently limited to specific kinds of targets (e.g. files):

* create target storage if missing: only files
* resize target storage: only files

Some more target types will be supported for the above operations in the future (e.g. resize for LVM volumes).


# Workflows #

## Replicate a virtualization server remotely ##

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


## Backup an encrypted volume to an untrusted backup storage ##

Setup:

* one of your local blockdevices is encrypted (e.g. via *cryptsetup*)
* you can access a remote backup storage via ssh and run software on the other side
* the backup storage is not completely under your control and encrypted / you do not trust it fully

Usage:

1. write a *bdsync-manager* configuration file with a single task definition (your local source and the remote target)
2. transfer an initial copy of your blockdevice or create an empty dummy file on the target host
3. create a cron-job for unattended synchronization or run *bdsync* manually from time to time
