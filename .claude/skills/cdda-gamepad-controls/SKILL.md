---
name: cdda-gamepad-controls
description: Architecture and conventions of upstream Cataclysm-DDA's built-in gamepad support (clones at ~/dev/cataclysm-dda on Nova and ~/cataclysm-dda on the Deck). Use whenever reading, auditing, comparing against, or modifying CDDA's controller scheme — its keybindings, radial menus, LT alt-layer, stick movement, or menu handling — and when porting ideas between CDDA and our Cataclysm-BN fork. Despite shared roots, the two engines' gamepad architectures differ fundamentally: do NOT apply the BN gamepad-controls skill's assumptions to CDDA, or vice versa.
---

# CDDA gamepad controls (upstream scheme)

Upstream Cataclysm-DDA ships first-class controller support. We run it
from source, unmodified: Nova clone `~/dev/cataclysm-dda` (remotes:
`origin` = CleverRaven/Cataclysm-DDA, `forgejo` = private mirror), Deck
clone `~/cataclysm-dda` (deploy target; `make deck-dda` from the BN
repo — see the cataclysm-bn-dev skill's fork-workflow reference).
Treat CDDA as read-mostly: local experiments are fine, but there is no
GitHub fork; anything we'd keep means creating one first.

This skill is a map of THEIR design, audited at commit 704ecc6
(2026-07-13). Line numbers will drift with upstream; re-verify before
relying on them. It exists alongside the BN `gamepad-controls` skill
because the two schemes solve the same problem with different
mechanisms — the comparison table at the end is the fastest way to
avoid cross-contaminating assumptions.

## Architecture in one paragraph

Everything raw lives in one self-contained module, `src/sdl_gamepad.{h,cpp}`
(namespace `gamepad`), built on the SDL **Gamepad/GameController API**
(not the legacy joystick API): one controller, hotplug handled, gated on
the `ENABLE_JOYSTICK` option (`src/sdltiles.cpp` calls `gamepad::init()`).
`CheckMessages` offers every unhandled SDL event to
`gamepad::is_gamepad_event()` / `handle_event()`. The module translates
hardware state into either (a) named `JOY_*` input events resolved
through the ordinary keybinding pipeline, or (b) **synthesized keyboard
keys when a menu is open** — a deliberate hybrid. Repeats come from an
SDL timer that pushes a `SDL_GAMEPAD_SCHEDULER` user event every 50ms,
driving per-input scheduled "tasks".

## The three input planes

1. **Gameplay plane (bindable)**: in the world (UI stack depth 1),
   buttons emit named gamepad codes — `JOY_A`, `JOY_UP`, `JOY_RT`… —
   bound to action ids in `data/raw/keybindings.json` exactly like
   keyboard keys (305 gamepad entries; same input_manager lineage as
   BN, category overrides beat the shared `default` context).
2. **Menu plane (hardcoded synthesis)**: `gamepad::is_in_menu()` is
   `ui_adaptor::ui_stack_size() > 1`. When true, the module emits
   *keyboard* events instead: A→`'\n'`, B/Start/Back→ESC, RB→Tab,
   LB→BTAB, d-pad→arrow keys (unless LT held), right stick→numpad
   digit chars `'1'`–`'9'`. This is exactly the key-synthesis approach
   our BN ADR rejected; CDDA accepts its costs (menu behavior is not
   rebindable, B can never mean anything but escape in a menu) in
   exchange for zero per-screen menu work. X and Y stay `JOY_X`/`JOY_Y`
   even in menus, so menus CAN bind those.
3. **Layer plane (LT = alt modifier + radials)**: holding LT sets
   `alt_modifier_held`. Any button pressed while held emits its
   `JOY_ALT_*` twin (dedicated keycodes, not chords assembled at
   lookup). Deflecting a stick while held opens that side's **radial
   menu** (mutually exclusive left/right); releasing LT commits the
   last-pointed octant as a `JOY_L_RADIAL_*` / `JOY_R_RADIAL_*` event.
   All ALT and RADIAL codes are ordinary bindable keys — the radial
   "menu" is just eight bindings plus an overlay.

## Keycode map (`src/input.h`)

| Range | Codes |
| ----- | ----- |
| 256+0..16 | `JOY_LS_*` / `JOY_RS_*` stick octant events (LEFT/RIGHT/UP/DOWN + diagonals) |
| 256+32..47 | Named buttons: `JOY_A B X Y LB RB LT RT LS RS UP DOWN LEFT RIGHT START BACK` |
| 256+48..63 | `JOY_ALT_*` twins (no `ALT_LT`; `ALT_RT` = LT+RT) |
| 256+64..71 | `JOY_L_RADIAL_N..NW` (compass order) |
| 256+72..79 | `JOY_R_RADIAL_N..NW` |

JSON key names are the part after `JOY_` ("A", "ALT_X", "L_RADIAL_N",
"LS_UP"…), registered in `src/input.cpp` `init_keycode_mapping()`
(~594-724). Legacy `JOY_0..30` raw-button names still register but
nothing emits them. Face buttons start at 256+32, so CDDA never had
BN's keycode-0-collision trap.

## Movement & sticks (Qud-style, like ours but wired differently)

- **Left stick** quantizes by angle into equal 45° sectors (atan2,
  magnitude > 16000). On direction *change* it emits a `JOY_LS_*`
  octant event; the shared context binds these to the movement actions
  (`LS_UP`→`UP`, `LS_UP_LEFT`→`LEFTUP`, …), so a stick flick moves one
  step. `cata_tiles.cpp` (~1545) draws the `"cursor"` tile sprite on
  the adjacent tile while deflected — the aim indicator.
- **RT** while the stick is deflected re-sends the stick direction and
  auto-repeats (hold to walk). **RT with stick centered** emits
  `JOY_RT` → bound to `pause` (wait a turn). Triggers use 16000 ± 2000
  hysteresis.
- **Directional verbs read the stick implicitly**: `handle_action.cpp`
  (~3329) sets `mouse_target` to player+offset for a whitelist of
  actions (EXAMINE, SMASH, GRAB, PICKUP, PEEK, CONTROL_VEHICLE, …), so
  "stick aims, button acts" works without a direction prompt.
- **Right stick, gameplay**: `JOY_RS_*` octants → `shift_*` view-pan
  actions (gamepad-only bindings). **Right stick, menus**: synthesized
  numpad digits — i.e. list navigation/counts, not bindable.

## Radial menus (the marquee feature)

State machine in `sdl_gamepad.cpp`: LT hold + stick deflect sets
`radial_{left,right}_open` and tracks `radial_*_last_dir`; LT release
fires `direction_to_radial_joy(last_dir, stick)` as an input event and
resets. Selection is therefore **flick-and-release** — no click.

Rendering is `draw_gamepad_radial_menu()` in `src/sdltiles.cpp`
(~4884-4972), called every present while `is_active() && is_alt_held()`:
dark scrim, 8 labels on a circle (radius 40% of window height),
selected octant yellow. **Labels resolve live from the top of
`input_context::input_context_stack`**: each octant's radial keycode →
`input_to_action(event)` → `get_action_name(action)`, "None" if
unbound. Consequence: *what a radial contains is purely a property of
the active context's JSON bindings* — adding a verb to a screen's
radial is one keybindings.json entry, zero C++. Many categories ship
radial sets (ADVANCED_INVENTORY, INVENTORY, VEH_INTERACT, ZONES_MANAGER,
TARGET, CRAFTING, OVERMAP, SAFEMODE, yes/no prompts…), so radials work
inside menus too — the menu plane's key synthesis skips the d-pad/A/B
only while LT is held.

## Default gameplay layout (DEFAULTMODE + shared)

| Input | Action | | Input | Action |
| ----- | ------ |-| ----- | ------ |
| A | interact | | ALT_A | action_menu |
| B | grab | | ALT_B | haul |
| X | smash | | ALT_X | item_action_menu |
| Y | throw | | ALT_Y | cast_spell |
| LB | fire | | ALT_LB | reload_item |
| RB | autoattack | | ALT_RB | pick_style |
| RT | pause / move-commit | | ALT_RT | open_movement |
| LS click | ignore_enemy | | ALT_LS | safemode |
| RS click | peek | | ALT_RS | listitems |
| D-up | eat | | ALT_UP | LEVEL_UP (shared) |
| D-down | drop | | ALT_DOWN | LEVEL_DOWN (shared) |
| D-left | wear | | ALT_LEFT | take_off |
| D-right | wield | | ALT_RIGHT | apply_wielded |
| START | main_menu | | ALT_START | zoom_in (shared) |
| BACK | map | | ALT_BACK | zoom_out (shared) |
| RS octants | shift_* view pan | | LS octants | movement (shared) |

Left radial (N→NW): craft, read, chat, wait, construct, sleep,
disassemble, unload. Right radial: player_data, medical, factions,
advinv, inventory, bodystatus, missions, morale. Shared-context
radials add overmap-travel verbs (CHOOSE_DESTINATION etc.) and
INCREASE/DECREASE_VALUE; TARGET's left radial holds aimed/careful/
precise shot; prompts bind YES/NO to radial N/S.

## Timing, tunables, options

All hardcoded statics in `sdl_gamepad.cpp` (~93-118), no UI options:
`sticks_threshold` / `triggers_threshold` 16000, `error_margin` 2000
(trigger hysteresis), `repeat_delay` 400ms, `repeat_interval` 50ms.
Repeats: d-pad, RT, and stick-octant events only, driven by the 50ms
SDL timer → `SDL_GAMEPAD_SCHEDULER` event → task array (button-up or
direction change cancels). The only player-facing option is
`ENABLE_JOYSTICK`. No rumble, no deadzone setting, and **no button
glyphs anywhere** — hints show textual key names ("A", "L_RADIAL_N").

## Working on it: recipes

- **Change what a button/octant does on a screen**: edit that
  category's entry in `data/raw/keybindings.json` (`"input_method":
  "gamepad"`, `"key": "<NAME>"`). Keyboard and pad keys share one
  entry; category overrides replace the shared entry (same loader
  semantics as BN — re-list what you keep).
- **Fill a radial slot**: bind `L_RADIAL_x`/`R_RADIAL_x` to an action
  registered by that screen's context. The wheel label follows
  automatically.
- **Change menu-plane behavior** (what A/B/d-pad do in menus): C++
  only, in `handle_button_event()`'s `is_in_menu()` branches.
- **Tune feel** (thresholds, repeat): edit the statics; rebuild.
- **In-game rebinding** works for the gameplay plane like any key
  (press the key name shows as "A", "ALT_B", …).

## Traps

- `src/input.h`'s comment "LB (ALT modifier)" is stale — **LT** is the
  modifier (`alt_modifier_held` in sdl_gamepad.cpp). LB is just a
  button (PREV_TAB / BTAB in menus).
- `JOY_LT` exists as a code but is never emitted; LT is consumed
  entirely as the modifier. There is no `JOY_ALT_LT`.
- The ALT transform applies only to events still typed `gamepad`; menu
  -plane synthesized keys ignore it except that LT+d-pad in menus
  emits `JOY_ALT_UP/DOWN` etc. (that's how ALT_UP scroll-info bindings
  work inside list screens).
- Gamepad events are only *valid* in a context while a controller is
  connected: `input_context::is_event_type_enabled` returns
  `gamepad::is_active()`. On the Deck, Steam Input must present a
  Gamepad template or `SDL_OpenGamepad` sees nothing.
- Several categories bind the same octant to two action ids (e.g.
  INVENTORY `L_RADIAL_N` → EXAMINE and INCREASE_COUNT); which fires
  depends on what the active screen registers — first registered wins,
  same shadowing rule as BN.
- CONSTRUCTION binds `ALT_DOWN`→SCROLL_STAGE_UP and `ALT_UP`→
  SCROLL_STAGE_DOWN (inverted names upstream; not a local bug).
- Radial selection fires on **LT release** — code that swallows or
  reorders the LT-up axis event breaks every radial at once.

## CDDA vs our BN fork (don't cross-contaminate)

| Aspect | CDDA (this skill) | Our BN fork (gamepad-controls skill) |
| ------ | ----------------- | ------------------------------------ |
| SDL layer | Gamepad API, hotplug | Legacy joystick API, one device at init |
| Face keycodes | 256+32.. (collision-safe) | 0-3 (keycode-0 traps) |
| Menus | Synthesized keyboard keys via `is_in_menu()` | First-class gamepad events + context bindings everywhere |
| Modifier layer | LT → dedicated `JOY_ALT_*` codes in gamepad module | LT → `JOY_LT_*` chord codes substituted in SDL layer |
| Radial menus | Yes — flick + LT-release, labels from live context | None (we use the X action palette uilist instead) |
| Hotkey-only screens | Radial sets curated per category in JSON | Auto-derived action palette on X |
| Movement | LS octant events bound in JSON + RT commit in C++ | Stick-aim + RT commit hardcoded in handle_action |
| Wait a turn | RT with stick centered | B (Qud convention) |
| Repeat engine | SDL timer → scheduler user event, 400/50ms | Post-poll synthesis in CheckMessages, 250/60ms |
| Stick zones | Equal 45° atan2 sectors, threshold 16000 | Equal 45° sectors (tan 22.5°), deadzone 7000 |
| Trigger hysteresis | 16000 ± 2000 | press -16384 / release -22938 |
| Device-gated UI | `is_active()` = controller plugged in | `last_input_was_gamepad()` live per-event gate |
| Button glyphs | None (text names) | PS/Xbox/text glyph setting, colored hints |
| Prompt convention | Radial N/S = YES/NO; B = ESC | A = YES, B = ESC-carrier; colored (A)/(B) glyphs |
| Tunables | Hardcoded statics | Hardcoded constexpr (documented in skill) |

Ideas worth stealing are fair game in either direction — but port the
*behavior*, re-implemented in the target engine's own mechanism.
