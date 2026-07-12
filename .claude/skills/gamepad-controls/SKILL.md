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
Deck via Steam Input's virtual Xbox pad). Two hard-won principles govern
all of it:

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
L3=9 R3=10. In JSON these are `JOY_0` … `JOY_7` (8+ have no names yet).
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
| Drawing an overlay glyph/indicator on a map tile | `src/cata_tiles.{h,cpp}` `init_draw_*` one-frame hooks + a `game::draw_callback_t` that re-arms it each frame (see `init_draw_direction_indicator` / `set_gamepad_aim`) | Yes |

Existing worked examples of each pattern, all in this repo's history:
buttons-as-gamepad-events + keycode-0 sentinel fix (`557a34b`,
`a9eaabe`), LT+d-pad chord (`8e376c1`), stick-aim + RT-move with arrow
overlay (`5f31bb1`), RT hold-to-repeat (`fa10f11`).

## Recipes

**Bind a button to an action in one context** (the common case; JSON
only): find the action's entry (`rg '"id": "map"' data/raw/keybindings/
keybindings.json`); if you need it scoped, add a category entry that
copies the keyboard keys and adds `{ "input_method": "gamepad", "key":
"JOY_n" }`. Check whether other categories override the same action id —
each override needs the button added separately (this bit the
NEXT_TAB/VEH_INTERACT and UILIST UP/DOWN cases). Then
`./build-scripts/format-json.sh <file>` before committing.

**Find a screen's category**: `rg 'input_context ctxt\( "' src/<file>`,
or for uilist-based menus it's `UILIST`. To see what actions a screen
offers, look for its `register_action` calls.

**Add a new raw input**: allocate the next `(256 + n)` code in
src/input.h, register its name in `init_keycode_mapping()`, emit
`input_event( CODE, input_event_t::gamepad )` from the SDL layer. Never
reuse the 0–255 range (raw button numbers live there). Beware: keycode
0 is a valid code (JOY_0) — `get_keycode` returns `std::optional<int>`
for exactly this reason; don't reintroduce 0-as-error.

**Chorded input (modifier + input)**: track the modifier's axis/button
state as a static in sdltiles.cpp; where the base input is translated to
a keycode, substitute the chord code when the modifier is held (see the
`joy_left_trigger_held` handling in `HandleDPad()`). Chord codes are
ordinary bindable keys after that.

**Hold-to-repeat**: poll at the top of `CheckMessages()` with an
initial-delay-then-interval state machine (`HandleRightTriggerRepeat`,
250ms/75ms). Repeats self-throttle because `last_input` is single-slot
and only consumed when the game asks for input.

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

## Current gamepad state (as of 2026-07-13)

- A `JOY_0`: Confirm (shared) · Action Menu (DEFAULTMODE)
- B `JOY_1`: Exit screen (shared) · cancel in UILIST, OVERMAP,
  chargen/worldgen/melee-picker dialogs
- Y `JOY_3`: Exit screen (shared) · Inventory (DEFAULTMODE)
- LB/RB `JOY_4/5`: Prev/Next tab (shared + VEH_INTERACT)
- Select `JOY_6`: View map (DEFAULTMODE) · close map (OVERMAP) — a toggle
- Start `JOY_7`: Main menu (DEFAULTMODE); B closes it (uilist)
- D-pad: menu navigation (shared + UILIST up/down); **unmapped for
  in-world movement** (DEFAULTMODE keyboard-only overrides) — free for
  future in-game bindings
- LT+d-pad up/down: zoom out/in (gameplay `zoom_in/out` + OVERMAP);
  LT+left/right chords exist but are unbound
- Left stick: 8-way aim with white arrow overlay; RT steps that way,
  auto-repeats while held (Qud-style; hardcoded in handle_action, not
  JSON-rebindable)
- Unused so far: X `JOY_2`, right stick, L3/R3/Guide (no keynames yet
  for buttons 8+), LT alone, stick input in menus

## Testing & deploy

JSON binding changes: relaunch only. C++ changes: `make compile` on
Nova; deploy with `make deck-local` **as a background task** (AGENTS.md
convention). Warning: touching src/input.h rebuilds ~115 files (slow on
the Deck). There is no way to test gamepad input on Nova headlessly —
real verification happens on the Deck; say so rather than claiming
tested behavior.
