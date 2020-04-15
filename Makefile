.PHONY: agglom_extent

#################################################################################
# GLOBALS                                                                       #
#################################################################################

## variables
DATA_DIR = data
DATA_RAW_DIR := $(DATA_DIR)/raw
DATA_INTERIM_DIR := $(DATA_DIR)/interim
DATA_PROCESSED_DIR := $(DATA_DIR)/processed

CODE_DIR = lausanne_agglom_extent

## rules
define MAKE_DATA_SUB_DIR
$(DATA_SUB_DIR): | $(DATA_DIR)
	mkdir $$@
endef
$(DATA_DIR):
	mkdir $@
$(foreach DATA_SUB_DIR, \
	$(DATA_RAW_DIR) $(DATA_INTERIM_DIR) $(DATA_PROCESSED_DIR), \
	$(eval $(MAKE_DATA_SUB_DIR)))


#################################################################################
# COMMANDS                                                                      #
#################################################################################

## 1. Download and unzip shapefile
### variables
CADASTRE_FILE_KEY = cantons/vaud/cadastre/Cadastre_agglomeration.zip
CADASTRE_UNZIP_FILEPATTERN = \
	Cadastre/(NPCS|MOVD)_CAD_TPR_(BATHS|CSBOIS|CSDIV|CSDUR|CSEAU|CSVERT)_S.*
CADASTRE_SHP := $(DATA_INTERIM_DIR)/cadastre.shp
#### code
DOWNLOAD_S3_PY := $(CODE_DIR)/download_s3.py
MAKE_CADASTRE_SHP_FROM_ZIP_PY := $(CODE_DIR)/make_cadastre_shp_from_zip.py

### rules
$(DATA_RAW_DIR)/%.zip: | $(DATA_RAW_DIR)
	python $(DOWNLOAD_S3_PY) $(CADASTRE_FILE_KEY) $@
$(DATA_INTERIM_DIR)/%.shp: $(DATA_RAW_DIR)/%.zip $(CADASTRE_SHP_FROM_ZIP_PY) \
	| $(DATA_INTERIM_DIR)
	python $(MAKE_CADASTRE_SHP_FROM_ZIP_PY) $< $@ \
		"$(CADASTRE_UNZIP_FILEPATTERN)"
	touch $@

## 2. Get the urban extent and rasterize shp to a 10m resolution
### variables
AGGLOM_LULC_TIF := $(DATA_PROCESSED_DIR)/agglom-lulc.tif
AGGLOM_EXTENT_SHP := $(DATA_PROCESSED_DIR)/agglom-extent.shp
#### code
MAKE_AGGLOM_LULC_PY := $(CODE_DIR)/make_agglom_lulc.py

### rules
#### Rule with multiple targets https://bit.ly/35B8YdU
#### do not delete `CADASTRE_SHP` despite chained rule
.PRECIOUS: $(CADASTRE_SHP)
$(DATA_PROCESSED_DIR)/%-lulc.tif $(DATA_PROCESSED_DIR)/%-extent.shp: \
	$(CADASTRE_SHP) $(MAKE_AGGLOM_LULC_PY) | $(DATA_PROCESSED_DIR)
	python $(MAKE_AGGLOM_LULC_PY) $< $(AGGLOM_LULC_TIF) $(AGGLOM_EXTENT_SHP)
agglom_extent: $(AGGLOM_LULC_TIF) $(AGGLOM_EXTENT_SHP)


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
