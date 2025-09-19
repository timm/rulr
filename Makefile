#---- local config --------------------------------------------------

X=rulr

~/tmp/dist.log:  ## run on many files
	$(MAKE) todo=dist files="$(Top)/../moot/optimize/*/*.csv" _run | tee $@ 

setup: ## initial setup - clone moot data
	[ -d $(Data) ] || git clone http://github.com/timm/moot $(Top)/../moot

Data=$(Top)/../moot/optimize

#---- general stuff -------------------------------------------------
SHELL     := bash
MAKEFLAGS += --warn-undefined-variables
.SILENT:
.ONESHELL:

LOUD = \033[1;34m#
HIGH = \033[1;33m#
SOFT = \033[0m#

Top=$(shell git rev-parse --show-toplevel)
Tmp ?= $(HOME)/tmp 

help: ## show help.
	@gawk '\
		BEGIN {FS = ":.*?##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nHelp:\n"}  \
    /^[a-z0-9A-Z_%\.\/-]+:.*?##/ {printf("  \033[36m%-15s\033[0m %s\n", $$1, $$2) | "sort" } \
	' $(MAKEFILE_LIST)

pull: ## update from main
	git pull

push:  ## commit to main
	echo -en "$(LOUD)Why this push? $(SOFT)" 
	read x ; git commit -am "$$x" ;  git push
	git status

sh: ## run custom shell
	clear; tput setaf 3; cat $(Top)/etc/hi.txt; tput sgr0
	sh $(Top)/etc/bash.sh

install: ## install in development mode (when ready)
	pip install -e .

clean:  ## find and delete any __pycache__ dirs
	files="$$(find $(Top) -name __pycache__ -type d)"; \
	for f in $$files; do rm -rf "$$f"; done

docs/index.html: $X/$X.py
	mkdir -p $(Top)/docs
	touch $(Top)/docs/.nojekyll
	pdoc3 --html --force -o $(Top)/docs $<
	mv $(Top)/docs/$X.html $@

docs/index.html : docs/$X.html   ; cp $^ $@
docs/%.py       : $(Top)/$X/%.py ; gawk -f $(Top)/etc/pycco0.awk $^ > $@
docs/%.html     : docs/%.py       
	pycco -d $(Top)/docs $^
	echo 'p {text-align:right;} pre {font-size:small;}' >> $(Top)/docs/pycco.css
	echo 'h2 {border-top: #CCC solid 1px;}'             >> $(Top)/docs/pycco.css

_run:
	@mkdir -p ~/tmp
	time ls -r $(files) \
	  | xargs -P 24 -n 1 -I{} sh -c 'cd $(Top)/$X; python3 -B ${X}test.py -f "{}" --$(todo)'
