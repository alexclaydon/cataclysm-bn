---
name: gamepad-controls
description: >-
  How to implement consistent, context-sensitive gamepad controls in this
  Cataclysm BN fork — binding buttons to in-game actions per input context,
  adding new raw inputs (buttons, axes, chords, sticks), input repeat,
  stateful control schemes like stick-aim + trigger-move, and drawing
  gamepad UI overlays on the map. Use this skill whenever work touches
  gamepad, controller, joystick, or Steam Deck input: mapping or remapping
  buttons, changing what a button does on some screen, adding trigger or
  stick behavior, editing gamepad entries in keybindings.json, or touching
  the SDL input layer in sdltiles.cpp — even for one-line binding tweaks,
  because the context-scoping rules here are easy to get wrong.
---

# Gamepad controls for Cataclysm BN

This fork is building first-class gamepad support (primary target: Steam
Deck via Steam Input's virtual Xbox pad). These hard-won principles
govern all of it:

1. **Bind actions, not keys.** Never make a button synthesize a keyboard
   keypress. Buttons bind to *action ids* ("Go to next tab", "CONFIRM",
   "map") in keybindings.json, exactly like keyboard keys do. A binding
   only fires on screens whose input context *registers* that action —
   that is what makes one button safely mean different things in
   different places.
2. **Scope by context (mode-based input).** Every screen creates an
   `input_context` with a category ("DEFAULTMODE" for the main viewport,
   "UILIST" for list menus, "OVERMAP" for the map, "INVENTORY", …).
   Decide per context what each button means; leave buttons unbound in
   contexts where they have no job yet, so they stay free.
3. **Prefer the minimally invasive mechanism, and weigh second-order
   effects BEFORE changing anything.** The mechanisms below are ordered
   by cost: a binding on an existing shared entry (zero copies — scoping
   comes free from action registration) < a category override (forks a
   copy of the base bindings you now own) < a private uilist category
   (forks ALL of that menu's bindings) < C++ changes. Before picking
   one, ask: does this button already mean something in an ancestor or
   sibling context (conflict)? Does it create UX inconsistency (same
   button, different meaning across similar screens)? Who else resolves
   this action id, and what happens to them (check every category that
   overrides it)? What copies does this create, and will they drift on
   upstream merges? If a change turns out bigger than the feature it
   delivers, that is a signal to stop and reconsider — say so to the
   user rather than pushing through.
4. **Follow Caves of Qud's Steam Deck conventions when picking button
   placements.** Qud has the best gamepad reputation among traditional
   roguelikes, and this fork's whole movement scheme (stick aims, RT
   commits) is copied from it. When a new binding decision has a Qud
   equivalent, take Qud's answer unless there's a concrete conflict —
   and check its layout table (below) before inventing a placement.

## Caves of Qud Steam Deck layout (the reference convention)

From the Qud wiki Controls page (Steam Deck section). Our equivalents
diverge only where the games differ.

| Qud control | Qud action | Us |
| --- | --- | --- |
| Left stick + RT | point direction, RT takes the step | same |
| Right stick | look around | same |
| A / LT+A | use (dynamic interact) / use direction | A = confirm / action menu; LT+A free |
| B / LT+B | wait a turn / wait menu | B = wait (DEFAULTMODE); LT+B free |
| X / LT+X | use ability / ability menu | X = examine + palette; LT+X free |
| Y / LT+Y | move to edge / auto-explore | Y = inventory; LT+Y = advanced inventory |
| D-pad L/R | select ability | pick up all / smash |
| D-pad U/D | level up / level down | same (ascend/descend stairs) |
| L3 | points of interest | movement mode menu |
| LB / RB | target self / fire | prev tab / RB = fire |
| LT+RB | throw | same |
| LT+D-pad L/R | zoom out / in | same |
| Select / Start | main menu / character info | map / main menu (pre-existing divergence) |

## How binding resolution works (the part people get wrong)

- keybindings.json entries **without** `"category"` live in the shared
  `default` context. They apply on any screen that registers the action.
  This is NOT "global key mapping" — it is "wherever this action
  exists". E.g. shoulder buttons on `NEXT_TAB` do nothing in the main
  viewport because DEFAULTMODE never registers `NEXT_TAB`.
- An entry **with** `"category": "X"` **fully replaces** the default
  entry for that action while context X is active — it does not merge.
  A category override must therefore re-list the keyboard keys it wants
  to keep. This is also the mechanism for *unmapping*: override with
  keyboard-only bindings (see the DEFAULTMODE movement entries, which
  strip the d-pad from in-world movement while menus keep it).
- Same-id entries in different categories coexist; lookup checks the
  active context's category first, then falls back to `default`
  (`input_manager::get_action_attributes`, src/input.cpp).

## Hardware map (Steam Deck / XInput-style, raw SDL joystick API)

Buttons: A=0 B=1 X=2 Y=3 LB=4 RB=5 Back/Select=6 Start=7 Guide=8
L3=9 R3=10. In JSON these are `JOY_0` … `JOY_7`; the stick clicks are
remapped at the SDL layer to `JOY_L3`/`JOY_R3` (256+n codes), and the
Guide button is swallowed there (Steam owns it in Game Mode). Buttons
0–7 pressed while LT is held emit `JOY_LT_0` … `JOY_LT_7` instead.
Axes: LX=0 LY=1 **LT=2** RX=3 RY=4 **RT=5**; sticks idle near 0,
triggers rest at -32768 (so "pulled" = value > 0). D-pad arrives as a
hat, not buttons (handled by `HandleDPad()` in src/sdltiles.cpp).

The game uses SDL's legacy joystick API (not the SDL3 Gamepad API), one
device, gated on the `ENABLE_JOYSTICK` option. The Steam Input layout
for the shortcut must be a **Gamepad template** — if Steam maps buttons
to keys itself, SDL never sees button events.

## Engine layout (where each kind of change goes)

| Change | Where | Rebuild? |
| ------ | ----- | -------- |
| Button ↔ action binding in some context | `data/raw/keybindings/keybindings.json` | No — relaunch only |
| New raw input (button >7, axis, chord) needs a keycode | `src/input.h` (`JOY_*` defines, 256+n block) + name registration in `src/input.cpp` `init_keycode_mapping()` | Yes |
| Reading SDL events / axes / repeat behavior | `src/sdltiles.cpp` (`CheckMessages()` event switch, `HandleDPad()`, `HandleRightTriggerRepeat()`) | Yes |
| Stateful in-game control schemes (multi-input, with UI state) | `src/handle_action.cpp` — intercept raw gamepad events in `game::handle_action()` just before the unknown-command block | Yes |
| Drawing an overlay glyph/indicator on a map tile | `src/cata_tiles.{h,cpp}` `init_draw_*` one-frame hooks + a `game::draw_callback_t` that re-arms it each frame (see `init_draw_direction_indicator` / `set_gamepad_aim`). For zoom-scaled, tile-centered shapes, draw geometry sized off `tile_width/height` via `SDL_RenderGeometry` (see `draw_direction_indicator_frame`) — font-rendered overlay strings are fixed-size and top-anchored. Indicator direction is screen-space: derive from the action with `iso_rotate::no`. Holding the callback in a global/static (like `gamepad_aim_cb`) is safe: `~draw_callback_t` null-checks `g`, which exit_handler resets before static destructors run — that unguarded `g->` was the segfault-on-quit bug every stick-aim session hit | Yes |

Existing worked examples of each pattern, all in this repo's history:
buttons-as-gamepad-events + keycode-0 sentinel fix (`557a34b`,
`a9eaabe`), LT+d-pad chord (`8e376c1`), stick-aim + RT-move with arrow
overlay (`5f31bb1`), RT hold-to-repeat (`fa10f11`).

## Recipes

**Bind a button to an action in one context** (the common case; JSON
only): find the action's entry (`rg '"id": "map"' data/raw/keybindings/
keybindings.json`) — and check its `category` field, which can appear
BEFORE or AFTER the id (field order varies; three "shared" entries
turned out to be DEFAULTMODE-scoped already, and adding an "override"
created silent duplicates that the loader resolves last-one-wins). If
the entry is already scoped where you need it, just add the binding to
it. If you need it scoped, add a category entry that copies the
keyboard keys and adds `{ "input_method": "gamepad", "key": "JOY_n" }`.
Check whether other categories override the same action id — each
override needs the button added separately (this bit the
NEXT_TAB/VEH_INTERACT and UILIST UP/DOWN cases). Then
`./build-scripts/format-json.sh <file>` before committing.

**The mirror-copy tax & drift test**: every category override forks a
copy of its base entry's bindings that will NOT track future changes
(overrides replace, never merge). All such mirrors are pinned by
`tests/keybinding_mirror_test.cpp` (`[keybindings]` tag; run with
`CATA_TEST_COMPUTE_ACCELERATION=cpu` on machines without the GPU
backend), which also rejects duplicate category/id entries file-wide.
When you create a new mirror (category override or private uilist
category), REGISTER IT in that test; when the test fails after a
keybindings edit, re-sync the mirror with its base or update the
expectation if the divergence is intentional.

**Find a screen's category**: `rg 'input_context ctxt\( "' src/<file>`,
or for uilist-based menus it's `UILIST`. To see what actions a screen
offers, look for its `register_action` calls.

**Scope bindings to ONE specific uilist** (uilists normally share the
`UILIST` category, so anything bound there hits every list menu): set
`my_uilist.input_category = "MY_CATEGORY"` before `query()`, then
mirror the UILIST entries (SCROLL_UP/DOWN, UP, DOWN, FILTER, QUIT) into
that category in keybindings.json — a category switch replaces ALL of
them, not just the one you're changing — and add your extra binding.
Worked example: `INGAME_MAIN_MENU` in src/action.cpp
`handle_main_menu()`, which lets the start button close the ESC menu it
opened (`9f235d2`).

**Add a new raw input**: allocate the next `(256 + n)` code in
src/input.h, register its name in `init_keycode_mapping()`, emit
`input_event( CODE, input_event_t::gamepad )` from the SDL layer. Never
reuse the 0–255 range (raw button numbers live there).

**The registration-order shadowing trap**: `input_to_action` returns the
FIRST registered action whose bindings match the event. Binding a pad
button to a later-registered action does nothing if an earlier-registered
action in scope also carries that button — e.g. query_popup registers
CONFIRM (shared binding: RETURN + JOY_0) before its YES/NO options, so
A resolved to confirm-highlighted instead of YES until the five prompt
categories got keyboard-only CONFIRM overrides. When a new binding
"doesn't fire", list the screen's registrations in order and check what
else resolves that button first. The keybindings test enforces the
prompt-category case.

**The keycode-0 trap** (has bitten twice; assume more lurk): `JOY_0`'s
keycode is literally 0, and the codebase is full of "0 means none/
error" conventions. Known instances: the keybinding loader's error
sentinel (fixed — `get_keycode` returns `std::optional<int>`; don't
reintroduce 0-as-error) and inventory invlet matching (fixed — entries
without a hotkey store `invlet == 0`, so the A button "matched" the
first letterless item; `inventory_selector::get_input` now restricts
invlet lookup to keyboard events). When gamepad events flow into code
that compares raw keycodes against hotkeys, invlets, or 0-defaulted
ids, gate the comparison on `evt.type == input_event_t::keyboard` —
a gamepad button should never act as a character hotkey. When a button
"mysteriously" triggers the wrong thing, grep the handling screen for
`== 0`, `get_first_input`, and hotkey/invlet lookups first.

**Chorded input (modifier + input)**: track the modifier's axis/button
state as a static in sdltiles.cpp; where the base input is translated to
a keycode, substitute the chord code when the modifier is held (see the
`joy_left_trigger_held` handling in `HandleDPad()` for the d-pad and in
the `SDL_EVENT_JOYSTICK_BUTTON_DOWN` case for buttons — `JOY_LT_0` …
`JOY_LT_7`). Chord codes are ordinary bindable keys after that.

**Hold-to-repeat**: poll at the top of `CheckMessages()` with an
initial-delay-then-interval state machine (`HandleRightTriggerRepeat`,
250ms/75ms). Repeats self-throttle because `last_input` is single-slot
and only consumed when the game asks for input.

**The repeat event-starvation trap**: synthesized repeats must NEVER
preempt the SDL event poll. The RT/right-stick repeat handlers
originally ran before the poll and returned early; when repeats came
due more often than the game consumed input, the poll never ran, the
queued release event was never dequeued, and movement repeated forever
(the runaway bug). Patching that with live-axis checks
(`SDL_UpdateJoysticks` + `SDL_GetJoystickAxis`) spawned worse bugs:
writing the held-flag from live state desynced press-edge detection
from the queued event stream (single pull stepped twice), and gating
on a jittery half-pulled trigger kept disarming the repeat timer
(sluggish repeat), while the starved queue also ate stick direction
changes (couldn't re-aim while holding RT). The correct shape, now
implemented: `CheckMessages()` runs the full event poll FIRST, then
synthesizes a repeat only if `last_input` is still empty. Real events
always win — releases stop the repeat, direction changes land while
held — and the handlers stay pure event-driven timer machines with no
live polling. Put any future repeat synthesis in that same post-poll
slot. (`HandleDPad` still runs pre-poll; it reads live hat state,
which is safe, and is upstream code.)

**Stateful schemes beyond bindings** (e.g. stick aims → trigger
commits): keybindings can't express state, so intercept the raw events
in `game::handle_action()` — check `ctxt.get_raw_input()` for
`input_event_t::gamepad` codes when no action resolved, keep the state
in file-local statics, and `return false` to consume without passing a
turn. To commit a move, set `act` to the real `ACTION_*` and fall
through so all normal movement handling (vehicles, prompts) applies.
Consume unknown *gamepad* events silently rather than letting them hit
the "Unknown command" message when they're part of your scheme.

## Text input & the on-screen keyboard (SDL3 lifecycle)

SDL text-input mode is **off by default** and enabled only while a text
field is active — that is what makes SteamOS pop its on-screen keyboard
exactly when a text box opens instead of at launch (`5f77394`). The
moving parts, and their gotchas:

- The chokepoint is `enable_ime`/`disable_ime` in src/ime.cpp, driven
  by RAII `ime_sentry` guards that already wrap every text field
  (string_input_popup, uilist filter, character/world naming, map
  notes…). New text-entry UIs MUST construct an `ime_sentry` (enable
  mode) for their query loop, or the OSK won't appear on the Deck —
  though physical keyboards still work via the fallback below.
- Do NOT reintroduce `SDL_StartTextInput` at startup or leave it on
  permanently: SteamOS interprets active text input as "show the OSK".
- The reason it used to be permanently on: `sdl_keysym_to_curses`
  returns 0 for printable characters, so ALL letter/number/symbol input
  historically arrived via `SDL_EVENT_TEXT_INPUT` only. With text input
  off, printables are derived from key events in `CheckMessages`
  (`SDL_GetKeyFromScancode( scancode, mod, false )`), gated on
  `!SDL_TextInputActive` so nothing double-delivers inside fields.
  Touch that fallback carefully — it carries every keyboard command in
  the game.

## The action palette (hotkey-only screens)

Pressing X on a screen where `JOY_2` matches nothing opens a uilist of
that context's actions and returns the pick as if its hotkey was
pressed — implemented centrally in `input_context::handle_input` /
`display_action_palette()` (src/input.cpp), so hotkey-legend screens
(advanced inventory ops, zone manager verbs, crafting extras,
construction) are pad-usable with zero per-screen work. Entries are
derived from usability, not raw registrations: an action is listed only
if it has a display name (nameless = plumbing), has a keyboard binding
in the context (the palette replaces the hotkey legend), and is NOT
already pad-bound (directly reachable); a static skip set drops
navigation actions, and entries sort by localized name. Rebinding
changes the palette automatically — don't add per-screen curation
lists.

The palette never fires where JOY_2 is bound, and by default not where
ANY_INPUT is registered (key-capture screens must see raw presses).
Screens whose ANY_INPUT handling only consumes keyboard hotkeys can
opt in with `ctxt.allow_palette_with_any_input()` — done for the main
OVERMAP context and veh_interact (where an unhandled pad X could even
select the part with hotkey '2' via the keycode-0-family trap,
JOY_2 == 2). Popups, text inputs, and uilists stay opted out so
"press any key" and typing behavior are untouched.
This is the default answer for "this screen's verbs are hotkey-only";
hand-bind a button in that screen's category only for verbs frequent
enough to deserve one.

## Yes/no prompts (A answers yes, B backs out)

All five prompt categories (YESNO, YESNOQUIT,
CANCEL_ACTIVITY_OR_IGNORE_QUERY, YES_NO_ALWAYS_NEVER, YN_IGNORE_QUERY)
bind A→YES; B goes to whichever option carries ESC — NO on plain
yes/no flavors, ABORT on salvage prompts, QUIT on yes/no/quit prompts
(there NO is a committed answer, not a back-out — keep it off B). Each
category needs a keyboard-only CONFIRM override (see the shadowing
trap). The convention table lives in tests/keybinding_mirror_test.cpp —
new prompt categories must be added to it.

Gamepad inputs display player-facing names ("Pad A", "LB", "LT+D-Up",
"R-Stick Up") everywhere hints render — `gamepad_display_name()` in
src/input.cpp, used by `get_keyname` for non-portable output only; the
JOY_* identifiers remain the config/serialization names. New JOY_*
codes need an entry there or they display raw.

## Device-gated dynamic UI (last_input_was_gamepad)

UI affordances can branch on the device the player is actively using:
`last_input_was_gamepad()` (src/input.h) flips true on any gamepad
event and false on keyboard/mouse, recorded once at the dequeue
chokepoint (`record_last_input_device` call in
`input_manager::get_input_event`, src/sdltiles.cpp; timeout/error
events don't touch it, curses builds stay false forever). The pattern
that makes this work: the gate is **live, not sticky** — check it on
every render and the UI follows whichever device was touched last, no
settings toggle. Anything that caches a layout must remember which mode
it was built for and rebuild on mismatch (see `gamepad_ui` in
query_popup — option text width differs between modes, so a stale cache
misplaces buttons).

`gamepad_hint_glyph( keycode )` (src/input.cpp) returns colored face
button glyphs — green (A), red (B), blue (X), yellow (Y), Xbox
convention — for inline hints; std::nullopt for everything else, so
callers fall back to their keyboard hint. Keep hints derived from the
**actual bindings** in the current context (look up the action's first
gamepad event and glyph that) rather than hardcoding "A means yes" —
that way rebinds, filters, and pad-unbound options (e.g. NO on
yes/no/quit) degrade correctly for free.

Consumers so far:

- query_popup (src/popup.cpp) renders "(A) Yes / (B) No" and hides the
  selection cursor when on gamepad; keyboard style ("(Y)es", highlight
  cursor) returns the moment a key is pressed. This closed the former
  highlight-cursor gap on prompts.
- `input_context::get_desc` (both variants, src/input.cpp) reorders
  the action's bindings pad-first when on gamepad (stable partition —
  keyboard mode is byte-identical to before), so every screen built on
  it (chargen tabs, construction, editmap, worldfactory, …) shows
  "Pad A"-style hints for free. The text variant also skips the inline
  "(Y)es" keyboard form when a pad binding will be shown, falling back
  to the separate "[Pad A] Yes" form.
- `input_context::press_x` (src/input.cpp) shows only the active
  device's bindings (fixes the old "Press $ or Pad A" concatenation
  both ways), falling back to the full list when the active device has
  none. Covers sidebar/sleep/safe-mode/vehicle messages and the
  monster-info look/fire hints.

These central generators emit plain friendly names ("Pad A"), NOT the
colored glyphs — their output flows into wprintz/format paths that
don't all parse color tags. Colored glyphs stay popup-only. Screens
that build hint strings per redraw get live gating for free; a screen
that caches hints once shows stale device flavor until reopened —
acceptable, but prefer per-redraw generation in new code. Extend
further UI adaptation screen-by-screen (uilist hints, AIM headers, the
future button-hint bar), not with a global switch — each screen's
fallback needs verifying on the Deck.

## Current gamepad state (as of 2026-07-13)

- Yes/no prompts render device-aware: colored "(A) Yes / (B) No"
  glyphs, no cursor, when the last input was gamepad; classic keyboard
  style otherwise (live gate, see Device-gated dynamic UI)
- Keybinding hints game-wide are device-aware: get_desc prefers pad
  bindings and press_x shows only the active device's bindings when
  the last input was gamepad (see Device-gated dynamic UI consumers)
- A `JOY_0`: Confirm (shared) · Action Menu (DEFAULTMODE) · YES on
  prompts · Fire (TARGET)
- B `JOY_1`: Exit screen (shared) · **wait a turn (DEFAULTMODE, Qud
  convention)** · cancel in UILIST, OVERMAP, chargen/worldgen/
  melee-picker dialogs · NO/ABORT on prompts
- X `JOY_2`: Examine (DEFAULTMODE) · Reload-and-abort-aiming (TARGET) ·
  action palette anywhere it is otherwise unbound
- Y `JOY_3`: Exit screen (shared) · Inventory (DEFAULTMODE)
- LB/RB `JOY_4/5`: Prev/Next tab (shared + VEH_INTERACT) · Fire on RB
  (DEFAULTMODE) · Prev/Next target (TARGET)
- Select `JOY_6`: View map (DEFAULTMODE) · close map (OVERMAP) — a toggle
- Start `JOY_7`: Main menu (DEFAULTMODE) · close it (INGAME_MAIN_MENU) —
  a toggle
- L3 `JOY_L3`: Movement mode menu (DEFAULTMODE). R3 `JOY_R3`: free.
  Guide: unavailable (swallowed; Steam owns it)
- D-pad: menu navigation (shared + UILIST up/down, dialogue, item
  actions, melee picker, keybindings help); in DEFAULTMODE left/right =
  pick up all / smash, up/down = ascend/descend stairs (Qud convention;
  cardinal *movement* stays unmapped via the keyboard-only overrides,
  and d-pad diagonals stay unbound in-world so mispresses no-op). B
  backs out of trade/prompts/dialogs; A or B dismisses wait popups;
  dialogue is a raw-input loop with explicit pad translation in
  npctalk.cpp (`7456baa`)
- LT+d-pad left/right: zoom out/in (gameplay `zoom_in/out` + OVERMAP;
  Qud convention). LT+up/down chords exist but are now unbound
- LT+buttons: LT+Y = advanced inventory, LT+RB = throw (DEFAULTMODE);
  LT+RB = switch firing mode (TARGET); other `JOY_LT_n` codes free
- Left stick: 8-way aim with a white triangle indicator (geometry-drawn:
  tile-centered, zoom-scaled, 80% tile size); RT steps that way,
  auto-repeats while held (Qud-style; hardcoded in handle_action, not
  JSON-rebindable); also answers direction prompts (CHOOSE_DIRECTION)
- Right stick: opens look-around from the viewport (first tilt = first
  cursor step via gamepad_look pending-step handoff) and drives the
  look cursor with hold-to-repeat (LOOK direction overrides)
- Firing mode (TARGET): either stick or the d-pad moves the aim cursor
  (direction mirrors; right stick repeats via the global rstick repeat),
  A or RT fires, X reloads (aborts aiming through ExitCode::Reload,
  reload UI opens on exit), LB/RB cycle targets, LT+RB switches firing
  mode, B or Y backs out (shared QUIT). AIM/aimed-shot actions are
  keyboard-only so far
- Unused so far: R3, LT+A/B/X/LB/Select/Start, LT alone, stick input
  in menus

## Testing & deploy

JSON binding changes: relaunch only. C++ changes: `make compile` on
Nova. Commit and push freely, but deploy to the Deck (`make
deck-local`) **only when the user asks** — small changes batch into one
Deck compile — and run it **as a background task** (AGENTS.md
convention). Warning: touching src/input.h rebuilds ~115 files (slow on
the Deck). There is no way to test gamepad input on Nova headlessly —
real verification happens on the Deck; say so rather than claiming
tested behavior.
