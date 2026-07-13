# Soundpack: which one and where to get it

The ambient music heard in official Bright Nights builds comes from
**Otopack BN Mk 2** — the only soundpack bundled with releases. BN
publishes each release in a plain and a "sounds" flavor; the sounds
flavor bundles this pack into `data/sound/Otopack+ModsUpdates BN/`.
Source builds (including this fork's `make` / `make deck-local`
builds) ship only the `Basic` pack, which has no music — so a fresh
local build is near-silent until the pack is installed by hand.

## Where to get it

The release pipeline pins the exact version in
`data/mods/external.json` (id `otopack_bn_mk_2`):

<https://github.com/NarandBD/Otopack-BN-Mk-2/archive/refs/tags/sorrynotsorry.zip>

The pack proper is the `Otopack+ModsUpdates BN/` directory nested
inside the archive (the wrapper also carries docs and spare sounds
that aren't needed).

## Install (Steam Deck / any machine)

Put the `Otopack+ModsUpdates BN` directory into the **user** sound
directory, not the game checkout:

```sh
cd ~/.cataclysm-bn/sound
curl -sL -o otopack.zip https://github.com/NarandBD/Otopack-BN-Mk-2/archive/refs/tags/sorrynotsorry.zip
unzip -q otopack.zip && rm otopack.zip
mv "Otopack-BN-Mk-2-sorrynotsorry/Otopack+ModsUpdates BN" .
rm -rf Otopack-BN-Mk-2-sorrynotsorry
```

The user directory survives `make deck-local` rebuilds; `data/sound/`
inside the checkout would dirty the working tree and could be clobbered.

Activate in game: **Options → General → Choose soundpack → "Otopack
BN"**, check the music/ambient/effect volume sliders (music sometimes
defaults low), and restart the game.

Installed on the Deck on 2026-07-13 (~192 MB).
