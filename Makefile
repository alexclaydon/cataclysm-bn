# Local development Makefile (not part of upstream; the game builds with CMake).
# End-to-end macOS build: fetches CI-generated shaders if missing, then
# configures and builds via CMake presets.
#
#   make            # full build (shaders + configure + compile)
#   make run        # build, then launch the game
#   make test       # build, then run the test binary
#   make shaders    # fetch precompiled shaders from upstream CI if missing
#   make clean      # remove the build directory for the current preset
#   make deck       # Steam Deck build: push branch, run fork CI, download
#                   # the linux-tiles-x64 tarball into out/deck/
#   make deck-local # push branch, then pull + rebuild the native build on
#                   # the Deck itself (via ssh, inside its bn-dev distrobox)
#   make deck-dda   # update + rebuild the from-source Cataclysm-DDA build
#                   # on the Deck (upstream master; scripts copied over first)
#
# Override the preset with e.g. `make PRESET=osx-arm-dist`.

PRESET ?= osx-arm-slim
BUILD_DIR := out/build/$(PRESET)
GAME_BIN := $(BUILD_DIR)/src/cataclysm-bn-tiles
TEST_BIN := $(BUILD_DIR)/tests/cata_test-tiles

.PHONY: build shaders shaders-force configure compile run test clean deck deck-local deck-dda

DECK_SSH ?= steamdeck

build: shaders configure compile

shaders:
	bash build-scripts/fetch-shaders-macos.sh

shaders-force:
	bash build-scripts/fetch-shaders-macos.sh --force

configure:
	cmake --preset $(PRESET)

compile:
	cmake --build --preset $(PRESET)

run: build
	$(GAME_BIN)

test: build
	$(TEST_BIN)

clean:
	rm -rf $(BUILD_DIR)

deck:
	bash build-scripts/deck-build.sh

deck-local:
	git push origin HEAD
	ssh $(DECK_SSH) 'bash ~/cataclysm-bn/build-scripts/deck-update.sh'

deck-dda:
	scp build-scripts/deck-dda-update.sh build-scripts/deck-dda-run.sh $(DECK_SSH):cataclysm-dda/
	ssh $(DECK_SSH) 'chmod +x ~/cataclysm-dda/deck-dda-*.sh && bash ~/cataclysm-dda/deck-dda-update.sh'
