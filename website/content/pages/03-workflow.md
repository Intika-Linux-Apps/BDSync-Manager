Title: Workflows

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
