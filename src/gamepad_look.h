#pragma once

#include <optional>

#include "point.h"

namespace gamepad_look
{

/// Set by the gameplay input handler when a right-stick tilt opens look
/// mode, so the look cursor starts one tile in the tilted direction.
auto set_pending_step( point step ) -> void;

/// Consumed (cleared) by game::look_around on entry.
auto take_pending_step() -> std::optional<point>;

} // namespace gamepad_look
