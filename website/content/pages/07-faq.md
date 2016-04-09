Title: FAQ


## Why should I use bdsync instead of rsync? ##
*rsync* does not work with blockdevices. Thus if you need to synchronize a blockdevice with a local or remote file or blockdevice then you need to use *bdsync* instead.

## Why not use bdsync directly? ##
*bdsync* is carefully designed to minimize the probability of a corrupted backup target by separating the synchronization into three steps:

1. create the patch
2. transfer the patch
3. apply the patch

All three steps could be executed in a single nifty shell command line by piping the output of each piece into the next. Sadly the first step (create a patch) takes quite some time (maybe hours - depending on the size of your blockdevices). By running all steps at the same time your remote blockdevice backup is in inconsistent state for a many hours each day. This is probably not what you want.

*bdsync-manager* makes it easy to run the above workflow easily with a single command in a safe manner. It automatically combines the first two steps (create and transfer the patch). This is safe since it does not affect the remote copy. Afterwards the patch is applied. This usually takes just a few minutes and thus minimizes the risk of data corruption in case of external failures.

In short: *bdsync-manager* makes it just a bit easier to use *bdsync* for a specifc but quite typical use-case.

## How should I transfer the initial copy? ##
The first initial copy should be created with an *in-place* operation (setting: *apply_patch_in_place*). This skips the patch creation and applies all changes (i.e. the full source content) on the fly. Afterwards you can disable this setting again if you prefer a more conservative style of operation.

Additionally you may want to enable the setting *create_target_if_missing*, if the target storage should be a file and it does not exist, yet. This option is currently no usable with a generic blockdevice or an LVM target.
