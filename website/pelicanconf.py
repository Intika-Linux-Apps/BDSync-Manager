#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Lars Kruse'
SITENAME = u'bdsync-manager'
SITEURL = 'http://www.nongnu.org/bdsync-manager'

PATH = 'content'

TIMEZONE = 'Europe/Berlin'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = "feed.atom"
FEED_ALL_RSS = "feed.rss"
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
# use the filesystem timestamp
DEFAULT_DATE = "fs"

# Blogroll
LINKS = (
        ('bdsync', 'https://github.com/TargetHolding/bdsync/'),
        ('Python', 'http://python.org/'),
        ('plumbum', 'http://plumbum.readthedocs.org/'),
        ('savannah', 'http://savannah.nongnu.org/'),
        ('Pelican', 'http://getpelican.com/'),
)

# Social widget
SOCIAL = []

DEFAULT_PAGINATION = 10
SUMMARY_MAX_LENGTH = 500

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

#THEME = "notmyidea-bdsync-manager"

# we turn off some details
DISPLAY_CATEGORIES_ON_MENU = False
AUTHOR_SAVE_AS = ""
YEAR_ARCHIVE_SAVE_AS = ""
MONTH_ARCHIVE_SAVE_AS = ""
DAY_ARCHIVE_SAVE_AS = ""
TAG_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
PAGE_LANG_SAVE_AS = ""
