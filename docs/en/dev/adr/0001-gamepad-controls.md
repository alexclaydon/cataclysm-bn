# ADR 0001: Gamepad controls bind in-game actions per input context

- Status: accepted, implemented (fork branch `aec-dev`)
- Date: 2026-07-13
- Scope: SDL input layer, keybinding data, prompt/menu UI

## Context

This fork is played primarily on a Steam Deck. Upstream Bright Nights
is keyboard-centric: gamepad support was vestigial (d-pad partially
worked, buttons produced no usable events), and the game's hundreds of
screens each assume hotkey-driven interaction. We needed the whole game
playable from a controller without forking every screen, and without
creating a parallel control scheme that drifts from the keyboard one.

Two tempting shortcuts were rejected up front:

- **Synthesizing keyboard keys from buttons** (e.g. A emits `\n`).
  This breaks the moment two screens want the same button to mean
  different things, bypasses the game's own rebinding UI, and hides
  the gamepad from the keybindings screens entirely.
- **Steam Input–side mapping** (buttons → key layouts in Steam).
  Same problems, plus the mapping lives outside the repo, can't be
  context-sensitive, and silently fights in-game handling.

## Decision

**Gamepad inputs are first-class input events bound to in-game
actions, scoped per input context, through the same keybinding
pipeline the keyboard uses.** Concretely:

1. **Raw input layer** (`src/sdltiles.cpp`, `src/input.h`): SDL
   joystick events become `input_event_t::gamepad` events carrying
   `JOY_*` keycodes — face/shoulder/system buttons, d-pad (hat),
   LT+d-pad chords, quantized 8-way stick octants plus center codes
   for both sticks, and the right trigger. Hold-to-repeat timing for
   d-pad, RT, and right stick lives here too. New physical inputs are
   added by allocating a keycode and emitting it; everything above
   this layer treats them like any other input.

2. **Binding layer** (`data/raw/keybindings/keybindings.json`):
   buttons are bound to action ids, in the `default` (shared) context
   where the meaning is universal (A = confirm, B = exit, shoulders =
   tabs, d-pad = navigate) and in per-screen categories where it is
   not. A category override **replaces** the shared entry wholesale,
   which doubles as the unmapping mechanism (a keyboard-only override
   removes a button from that screen). The cost — every override is a
   mirror copy of keyboard keys that won't track base edits — is
   accepted and pinned by `tests/keybinding_mirror_test.cpp`, which
   fails loudly on drift and rejects duplicate entries.

3. **Stateful schemes stay in C++**: the Qud-style movement scheme
   (left stick aims with an arrow overlay, right trigger commits the
   step with auto-repeat) and right-stick look-around are raw-event
   intercepts in `handle_action`/`game::look_around`, because they are
   modal state machines, not single action bindings. They are
   deliberately not JSON-rebindable; that trade was made knowingly.

4. **Centralized fallbacks instead of per-screen work**: screens whose
   verbs are hotkey-only get the action palette — an unbound X press
   in `input_context::handle_input` lists the context's registered
   actions and returns the pick as if its hotkey was pressed. This
   made vehicle interaction, advanced inventory, zone manager, etc.
   pad-usable with zero per-screen code.

5. **Prompt conventions**: on every yes/no prompt flavor A answers YES
   and B triggers whichever option carries ESC (a safe back-out, never
   a committed "no"). Each prompt category needs a keyboard-only
   CONFIRM override because binding resolution returns the *first
   registered* matching action, and CONFIRM registers before the
   options. The convention is enforced by the drift test.

6. **The UI adapts to the active device, live**: hints render friendly
   names ("Pad A", "LT+D-Up") via `gamepad_display_name()`, and
   device-gated UI branches on `last_input_was_gamepad()` — recorded
   once at the event-dequeue chokepoint — re-checked on every render,
   so picking up the keyboard instantly restores keyboard affordances.
   First consumer: query popups show colored `(A) Yes / (B) No` glyphs
   (derived from the actual bindings, never hardcoded) and hide the
   selection cursor while on gamepad.

## Consequences

Positive:

- The entire game is playable from the controller; most screens needed
  only JSON, and the biggest wins (palette, prompt conventions,
  device-gated popups) were single central changes.
- Gamepad bindings appear in, and are rebindable from, the in-game
  keybindings UI like any key.
- The scheme is testable: mirror copies, prompt conventions, and
  duplicate entries are locked by a fast data-only test
  (`[keybindings]`, 189 assertions).

Negative / accepted costs:

- Mirror-copy overrides tax every future edit to a mirrored base
  entry; the drift test converts silent divergence into a test
  failure, but the edit still has to be made twice.
- The movement/look schemes are hardcoded in C++ and not rebindable.
- Two engine traps require care and are documented for posterity:
  `JOY_0`'s keycode is literally `0` (collides with "0 = none"
  conventions), and first-registered-action-wins shadowing (the
  CONFIRM/JOY_0 case).
- `src/input.h` edits rebuild ~115 translation units.

## References

- `.claude/skills/gamepad-controls/SKILL.md` — the operational how-to:
  hardware map, keycode allocations, recipes, traps, and the current
  binding table. Kept updated as the scheme evolves; read it before
  touching gamepad behavior.
- `tests/keybinding_mirror_test.cpp` — executable form of the
  conventions above.
