PY?=python
PELICAN?=pelican
PELICANOPTS=

BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/output
THEMEDIR=$(BASEDIR)/theme
CONFFILE=$(BASEDIR)/pelicanconf.py

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

help:
	@echo 'Makefile for a pelican Web site                                           '
	@echo '                                                                          '
	@echo 'Usage:                                                                    '
	@echo '   make html                           (re)generate the web site          '
	@echo '   make clean                          remove the generated files         '
	@echo '   make regenerate                     regenerate files upon modification '
	@echo '                                                                          '
	@echo 'Set the DEBUG variable to 1 to enable debugging, e.g. make DEBUG=1 html   '
	@echo 'Set the RELATIVE variable to 1 to enable relative urls                    '
	@echo '                                                                          '

html:
	$(PELICAN) --theme-path $(THEMEDIR) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

clean:
	[ ! -d $(OUTPUTDIR) ] || rm -rf $(OUTPUTDIR)

regenerate:
	$(PELICAN) --theme-path $(THEMEDIR) -r $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

cvs-checkout:
	@[ -z "$(UPLOAD_USER)" ] && { echo >&2 "ERROR: Missing savannah user name for upload:\n	make upload UPLOAD_USER=foobar"; exit 1; } || true
	CVS_RSH=ssh cvs -z3 -d:ext:$(UPLOAD_USER)@cvs.sv.gnu.org:/web/bdsync-manager co bdsync-manager
	rm -rf "$(OUTPUTDIR)"
	mv bdsync-manager "$(OUTPUTDIR)"

cvs-publish:
	cd "$(OUTPUTDIR)"; cvs commit

.PHONY: html help clean regenerate publish cvs-checkout check-empty-user
