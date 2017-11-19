from setuptools import setup
from bdsync_manager import VERSION

setup(
    name="bdsync-manager",
    version=VERSION,
    description="Synchronize one or more blockdevices to a remote target via bdsync",
    url="http://www.nongnu.org/bdsync-manager/",
    author="Lars Kruse",
    author_email="devel@sumpfralle.de",
    packages=["bdsync_manager"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Utilities",
    ],
    install_requires=["plumbum"],
    entry_points={"console_scripts": ["bdsync-manager=bdsync_manager.cmdline:main"]},
)
