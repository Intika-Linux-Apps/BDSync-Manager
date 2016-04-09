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

### Release archive ###

1. Download and install the requirements (see above)
2. Download and extract the latest release: http://download.savannah.gnu.org/releases/bdsync-manager/
3. Run *./bdsync-manager* from within this directory or specify the full path when calling the program


### From git-checkout ###

1. Download and install the requirements (see above)
2. Clone the *bdsync-manager* repository or download and extract a release archive
3. Run *./bdsync-manager* from within this directory or specify the full path when calling the program


### pip - Python package manager ###

1. *pip install bdsync*
2. Run *bdsync-manager*
