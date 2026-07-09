# Local development Makefile (not part of upstream; the game builds with CMake).
# End-to-end macOS build: fetches CI-generated shaders if missing, then
# configures and builds via CMake presets.
#
#   make            # full build (shaders + configure + compile)
#   make run        # build, then launch the game
#   make test       # build, then run the test binary
#   make shaders    # fetch precompiled shaders from upstream CI if missing
#   make clean      # remove the build directory for the current preset
#
# Override the preset with e.g. `make PRESET=osx-arm-dist`.

PRESET ?= osx-arm-slim
BUILD_DIR := out/build/$(PRESET)
GAME_BIN := $(BUILD_DIR)/src/cataclysm-bn-tiles
TEST_BIN := $(BUILD_DIR)/tests/cata_test-tiles

.PHONY: build shaders shaders-force configure compile run test clean

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
