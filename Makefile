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
#
# Override the preset with e.g. `make PRESET=osx-arm-dist`.
# (deck-dda / deck-tlg live in the ../.. cataclysm meta-repo Makefile.)

PRESET ?= osx-arm-slim
BUILD_DIR := out/build/$(PRESET)
GAME_BIN := $(BUILD_DIR)/src/cataclysm-bn-tiles
TEST_BIN := $(BUILD_DIR)/tests/cata_test-tiles

.PHONY: build shaders shaders-force configure compile run test clean deck deck-local

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
	# Copy the update script over before running it. It used to be run from
	# whatever the Deck's clone happened to hold, which only changes on a
	# successful pull — so a fix to the pulling logic could never reach the
	# Deck if the pull itself was broken. Same pattern as the meta-repo's
	# deck-dda target.
	scp build-scripts/deck-update.sh $(DECK_SSH):cataclysm-bn/build-scripts/
	ssh $(DECK_SSH) 'bash ~/cataclysm-bn/build-scripts/deck-update.sh'
