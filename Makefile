#---- header : do not move -------------------------------------------
SHELL     := bash
MAKEFLAGS += --warn-undefined-variables
.ONESHELL:

# Define phony targets (targets that don't create files)
.PHONY: help setup pull push sh install clean docs test

#---- variables ------------------------------------------------------
X    := rulr
Top  := $(shell git rev-parse --show-toplevel)
Tmp  ?= $(HOME)/tmp
Data := $(Top)/../moot/optimize

# Color definitions for output
LOUD := \033[1;34m#
HIGH := \033[1;33m#
SOFT := \033[0m#

#---- help -----------------------------------------------------------
# default action for "make" (so always keep this as first rule)
help: ## show help
	@printf "\nUsage:\n  make \033[36m<target>\033[0m\n\ntargets:\n"
	@gawk '\
		BEGIN {FS = ":.*?##"} \
		/^[a-zA-Z0-9_\.\/-]+:.*?##/ {printf("  \033[36m%-15s\033[0m %s\n", $$1, $$2)}' \
		$(MAKEFILE_LIST) | sort

#---- setup and data management -------------------------------------
setup: ## initial setup - clone moot data
	@if [ ! -d "$(Data)" ]; then \
		echo "Cloning moot data..."; \
		git clone http://github.com/timm/moot $(Top)/../moot; \
	else \
		echo "Data directory already exists at $(Data)"; \
	fi

$(Data): setup  ## ensure data directory exists

#---- main targets --------------------------------------------------

$(Tmp)/dist.log : $(Data) 
	@mkdir -p $(dir $@)
	$(MAKE) todo=dist files="$(Data)/*/*.csv" _run | tee $@

test: $(Data) ## run tests
	cd $(Top)/$(X) && python3 -B $(X)test.py --all

#---- git operations ------------------------------------------------
pull: ## update from main
	git pull

push: ## commit and push to main
	@echo -en "$(LOUD)Why this push? $(SOFT)"
	@read x && git add -A && git commit -m "$$x" &&  git push &&  git status

#---- development ---------------------------------------------------
sh: ## run custom shell
	@clear; tput setaf 3; cat $(Top)/etc/hi.txt; tput sgr0;
	@sh $(Top)/etc/bash.sh 

install: ## install in development mode
	@echo "Installing $(X) in development mode..."
	cd $(Top); pip install -e .
	@echo "Installation completed."

clean: ## find and delete any __pycache__ dirs
	@echo "Cleaning __pycache__ directories..."
	@find $(Top) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find $(Top) -name "*.pyc" -delete 2>/dev/null || true

#---- documentation ------------------------------------------------
docs: docs/index.html ## generate documentation

docs/index.html: docs/$(X).html   ; cp $< $@
docs/%.py      : $(Top)/$(X)/%.py ; @mkdir -p docs; gawk -f $(Top)/etc/pycco0.awk $< > $@
docs/%.html    : docs/%.py
	pycco -d $(Top)/docs $<
	@echo 'p {text-align:right;} pre {font-size:small;}' >> $(Top)/docs/pycco.css
	@echo 'h2 {border-top: #CCC solid 1px;}'             >> $(Top)/docs/pycco.css

#---- internal targets ----------------------------------------------
_run: ## internal target for parallel execution
	@echo "Running parallel execution on files: $(files)"
	@mkdir -p $(Tmp)
	time ls $(files) 2>/dev/null | \
		xargs -P 24 -n 1 -I{} sh -c 'cd $(Top)/$(X) && python3 -B $(X)test.py -f "{}" --$(todo)'

#---- maintenance ---------------------------------------------------
check-deps: ## check if required tools are available
	@command -v git >/dev/null 2>&1 || { echo "git is required but not installed"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "python3 is required but not installed"; exit 1; }
	@command -v gawk >/dev/null 2>&1 || { echo "gawk is required but not installed"; exit 1; }
	@echo "All dependencies satisfied."

status: ## show project status
	@echo "Project: $(X)"
	@echo "Top directory: $(Top)"
	@echo "Data directory: $(Data)"
	@echo "Temp directory: $(Tmp)"
	@echo "Git status:"
	@git status --short

validate: check-deps $(Data) ## validate project setup
	@test -d $(Top)/$(X) || { echo "Error: $(X) directory not found"; exit 1; }
	@test -f $(Top)/$(X)/$(X)test.py || { echo "Error: test file not found"; exit 1; }
	@echo "Project validation completed successfully."
