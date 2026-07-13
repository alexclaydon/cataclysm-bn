# CDDA default soundpack: CC-Sounds

The from-source Cataclysm-DDA build on the Deck (`~/cataclysm-dda`)
ships silent, same as BN from source. The pack the official CDDA
releases bundle is **CC-Sounds**, fetched by their release workflow
(`.github/workflows/release.yml`) from
<https://github.com/Fris0uman/CDDA-Soundpacks> — the individual packs
are git **submodules** of that repo, so a plain tarball download comes
back empty; clone shallow and `git submodule update --init --depth 1
sound/CC-Sounds`.

Installed to `~/cataclysm-dda/sound/CC-Sounds` on the Deck — the
*user* soundpack directory (`PATH_INFO::user_sound()`; with
USE_HOME_DIR off the user dir is the game root, and top-level `sound/`
is untracked, so upstream pulls never touch it). This parallels the BN
setup, where Otopack lives in `~/.cataclysm-bn/sound/` (see the
20260713 otopack journal entry).

Activate in-game: Options → General → Soundpack → CC-Sounds (sound was
compiled in via SOUND=1 + the from-source SDL3_mixer in the distrobox).

Re-install after wiping the clone: repeat the clone/submodule steps
above; nothing in our repos automates it (deliberately — it's a
one-time asset install, not part of the build).
