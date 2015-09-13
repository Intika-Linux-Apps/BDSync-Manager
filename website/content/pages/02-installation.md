Title: Installation


## Download ##

Download the latest release from [savannah.nongnu.org](http://download.savannah.gnu.org/releases/bdsync-manager/).



## Requirements ##
The following software is required for running *bdsync-manager*:

* [bdsync](https://github.com/TargetHolding/bdsync): efficiently create and apply patches for blockdevice synchronization
* [Python](http://python.org/): *bdsync-manager* is written in Python and requires Python 3.2 or later
* [plumbum](http://plumbum.readthedocs.org/): this python library provides easy access to typical shell-based features (e.g. pipelining processes)


Please note that you also need *bdsync* available on the target host for all remote transfers. You may circumvent this requirement by mounting the remote storage locally (e.g. via *sshfs*), but then you would loose *bdsync*'s efficient mode of remote operation. Please take a look at *bdsync*'s details to fully understand the implications of a local mount instead of a remotely running *bdsync* process.


## Installation ##

1. download and install the requirements (see above)
2. clone the *bdsync-manager* repository or download and extract a release archive
3. (optional) symlink or copy *bdsync-manager* to a path used for executables (e.g. */usr/local/bin/bdsync-manager*)
4. create a configuration file (see below)
