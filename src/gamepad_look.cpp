#include "gamepad_look.h"

#include <utility>

namespace
{
std::optional<point> pending_step;
} // namespace

namespace gamepad_look
{

auto set_pending_step( const point step ) -> void
{
    pending_step = step;
}

auto take_pending_step() -> std::optional<point>
{
    return std::exchange( pending_step, std::nullopt );
}

} // namespace gamepad_look
