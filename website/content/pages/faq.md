Title: FAQ


# Why should I use bdsync instead of rsync? #
*rsync* does not work with blockdevices. Thus if you need to synchronize a blockdevice with a local or remote file or blockdevice then you need to use *bdsync* instead.

# Why not use bdsync directly? #
*bdsync* is carefully designed to minimize the probability of a corrupted backup target by separating the synchronization into three steps:

1. create the patch
2. transfer the patch
3. apply the patch

All three steps could be executed in a single nifty shell command line by piping the output of each piece into the next. Sadly the first step (create a patch) takes quite some time (maybe hours - depending on the size of your blockdevices). By running all steps at the same time your remote blockdevice backup is in inconsistent state for a many hours each day. This is probably not what you want.

*bdsync-manager* makes it easy to run the above workflow easily with a single command in a safe manner. It automatically combines the first two steps (create and transfer the patch). This is safe since it does not affect the remote copy. Afterwards the patch is applied. This usually takes just a few minutes and thus minimizes the risk of data corruption in case of external failures.

In short: *bdsync-manager* makes it just a bit easier to use *bdsync* for a specifc but quite typical use-case.

# How should I transfer the initial copy? #
This depends on your usage of *bdsync* and is not specific for *bdsync-manager*.

The fail-safe approach for the initial copy is a transfer via *ssh* to the remote host:

    cat SOURCE_BLOCKDEVICE | ssh bar@foo.baz "cat >target.img"

(Use [pv](http://www.ivarch.com/programs/pv.shtml) instead of *cat* for a fancy progress bar.)

Alternatively (provided enough space for a full-size patch on the remote host) you can also create a dummy target file (e.g. *touch target.img*) and use *bdsync_args = --diffsize=resize* in your config file for the initial synchronization.
