# CDDA default tileset: UltiCa (UltimateCataclysm)

The from-source CDDA build ships only `gfx/ASCIITileset` — modern CDDA
composes its graphical tilesets in CI from the sprite-source repo
(I-am-Erk/CDDA-Tilesets) and only release builds bundle the results, so
building from source leaves you ASCII-only (the same gap BN has with
soundpacks/tilesets, different mechanism).

Easiest source of a *composed* tileset: the official experimental
release tarball for the exact commit you built (assets like
`cdda-linux-with-graphics-x64-<date>.tar.gz` under the matching
`cdda-experimental-<date>` tag). Extract `*/gfx/` and copy the tileset
folder(s) you want. Composed tilesets are small (UltimateCataclysm =
5.8 MB).

Installed the release tarball's ENTIRE tileset set into
`~/cataclysm-dda/gfx/` on the Deck (all ~61 MB: UltimateCataclysm,
Altica, Ultica_iso, ChibiUltica, Cuteclysm, BrownLikeBears, GiantDays,
HollowMoon, MShockXotto+, NeoDays, PenAndPaper, Retrodays,
SmashButton_iso, plus ASCII_Overmap and SurveyorsMap overmap tilesets).
All are untracked → upstream pulls unaffected; dirs already tracked
in-tree (ASCIITileset, Larwick_Overmap, loading_screens) were left
alone so git stays clean. The in-game "Choose
tileset" option (`TILES` in src/options.cpp) defaults to
`UltimateCataclysm`, so it activates automatically once present;
manual path is Options → Graphics → Choose tileset.

If game/tileset JSON drift after a big upstream update, re-pull the
tileset from the release tarball matching the new build's commit.
