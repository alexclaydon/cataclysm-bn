#include <algorithm>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "catch/catch.hpp"
#include "json.h"

// Drift check for mirrored keybinding categories.
//
// A category override in keybindings.json REPLACES the base entry's bindings
// wholesale, so every category that forks a base entry (to add or remove a
// gamepad button) owns a copy of its keyboard bindings that will NOT track
// future changes to the base. This test pins each mirror to its base so
// divergence fails loudly instead of silently changing one screen's controls.
//
// When adding a new mirror category (e.g. giving a uilist its own
// input_category), register it here. When this test fails after editing
// keybindings.json, update the mirror copies to match their base (or adjust
// the expectations below if the divergence is intentional).

namespace
{

struct binding_set {
    std::multiset<std::string> keyboard;
    std::multiset<std::string> mouse;
    std::multiset<std::string> gamepad;
};

using binding_map = std::map<std::pair<std::string, std::string>, binding_set>;

struct loaded_bindings {
    binding_map by_id;
    // (category, id) pairs appearing more than once: the loader silently
    // lets the later entry win, which is almost always an editing mistake.
    std::vector<std::pair<std::string, std::string>> duplicates;
};

auto load_bindings() -> loaded_bindings
{
    std::ifstream file( "data/raw/keybindings/keybindings.json",
                        std::ifstream::in | std::ifstream::binary );
    REQUIRE( file.good() );
    JsonIn jsin( file );
    loaded_bindings res;
    jsin.start_array();
    while( !jsin.end_array() ) {
        JsonObject entry = jsin.get_object();
        entry.allow_omitted_members();
        if( entry.get_string( "type", "keybinding" ) != "keybinding" ) {
            continue;
        }
        const auto key = std::pair{ entry.get_string( "category", "default" ),
                                    entry.get_string( "id" ) };
        if( res.by_id.contains( key ) ) {
            res.duplicates.push_back( key );
        }
        auto &set = res.by_id[key];
        for( const JsonObject bind : entry.get_array( "bindings" ) ) {
            bind.allow_omitted_members();
            const auto method = bind.get_string( "input_method" );
            std::vector<std::string> keys;
            if( bind.has_array( "key" ) ) {
                for( const std::string k : bind.get_array( "key" ) ) {
                    keys.push_back( k );
                }
            } else {
                keys.push_back( bind.get_string( "key" ) );
            }
            for( const auto &k : keys ) {
                if( method == "keyboard" ) {
                    set.keyboard.insert( k );
                } else if( method == "mouse" ) {
                    set.mouse.insert( k );
                } else if( method == "gamepad" ) {
                    set.gamepad.insert( k );
                }
            }
        }
    }
    return res;
}

auto get_set( const binding_map &bindings, const std::string &cat,
              const std::string &id ) -> const binding_set &
{
    const auto it = bindings.find( { cat, id } );
    INFO( "missing keybinding entry: category=" << cat << " id=" << id );
    REQUIRE( it != bindings.end() );
    return it->second;
}

} // namespace

TEST_CASE( "keybinding_mirror_categories_track_their_base", "[keybindings]" )
{
    const auto loaded = load_bindings();
    const auto &bindings = loaded.by_id;

    SECTION( "no duplicate category/id entries" ) {
        for( const auto &[cat, id] : loaded.duplicates ) {
            INFO( "duplicate keybinding entry: category=" << cat << " id=" << id );
            CHECK( false );
        }
    }

    SECTION( "INGAME_MAIN_MENU mirrors every UILIST override" ) {
        // The ESC menu's private category (src/action.cpp handle_main_menu)
        // must re-declare all UILIST overrides; keyboard/mouse identical,
        // gamepad at least what UILIST has (it adds JOY_7 on QUIT).
        for( const auto &[key, base] : bindings ) {
            if( key.first != "UILIST" ) {
                continue;
            }
            INFO( "action id: " << key.second );
            const auto &mirror = get_set( bindings, "INGAME_MAIN_MENU", key.second );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( mirror.mouse == base.mouse );
            CHECK( std::ranges::includes( mirror.gamepad, base.gamepad ) );
        }
    }

    SECTION( "DEFAULTMODE movement overrides keep base keyboard keys, no gamepad" ) {
        // In-world d-pad movement is deliberately unmapped; keyboard keys
        // must stay in lockstep with the shared pan/move entries.
        for( const std::string id : {
                 "UP", "DOWN", "LEFT", "RIGHT", "LEFTUP", "RIGHTUP", "LEFTDOWN", "RIGHTDOWN"
             } ) {
            INFO( "action id: " << id );
            const auto &base = get_set( bindings, "default", id );
            const auto &mirror = get_set( bindings, "DEFAULTMODE", id );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( mirror.gamepad.empty() );
        }
    }

    SECTION( "DEFAULTMODE stairs overrides keep base keys and add LT+d-pad" ) {
        // CDDA convention (adopted 2026-07-14): plain d-pad up/down are
        // high-frequency verbs (eat/drop); stairs ride the LT layer, which
        // reads as "d-pad moves, LT+d-pad moves vertically". The base
        // entries stay pad-free so LOOK etc. keep the d-pad for the cursor.
        const std::vector<std::pair<std::string, std::string>> stairs = {
            { "LEVEL_UP", "JOY_LT_UP" },
            { "LEVEL_DOWN", "JOY_LT_DOWN" },
        };
        for( const auto &[id, button] : stairs ) {
            INFO( "action id: " << id );
            const auto &base = get_set( bindings, "default", id );
            const auto &mirror = get_set( bindings, "DEFAULTMODE", id );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( mirror.gamepad.contains( button ) );
        }
    }

    SECTION( "LOOK direction overrides keep base keys and extend gamepad" ) {
        // Look mode adds right-stick cursor movement on top of the shared
        // direction bindings (keyboard + d-pad).
        for( const std::string id : {
                 "UP", "DOWN", "LEFT", "RIGHT", "LEFTUP", "RIGHTUP", "LEFTDOWN", "RIGHTDOWN"
             } ) {
            INFO( "action id: " << id );
            const auto &base = get_set( bindings, "default", id );
            const auto &mirror = get_set( bindings, "LOOK", id );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( std::ranges::includes( mirror.gamepad, base.gamepad ) );
        }
    }

    SECTION( "TARGET and OVERMAP direction overrides keep base keys and extend gamepad" ) {
        // The aim / map cursor moves on either stick on top of the shared
        // direction bindings (keyboard + d-pad).
        for( const std::string cat : { "TARGET", "OVERMAP" } ) {
            for( const std::string id : {
                     "UP", "DOWN", "LEFT", "RIGHT", "LEFTUP", "RIGHTUP", "LEFTDOWN", "RIGHTDOWN"
                 } ) {
                INFO( "category: " << cat << " action id: " << id );
                const auto &base = get_set( bindings, "default", id );
                const auto &mirror = get_set( bindings, cat, id );
                CHECK( mirror.keyboard == base.keyboard );
                CHECK( std::ranges::includes( mirror.gamepad, base.gamepad ) );
            }
        }
    }

    SECTION( "CHOOSE_DIRECTION direction overrides keep base keys and extend gamepad" ) {
        // Direction prompts add left-stick selection on top of the shared
        // direction bindings (keyboard + d-pad).
        for( const std::string id : {
                 "UP", "DOWN", "LEFT", "RIGHT", "LEFTUP", "RIGHTUP", "LEFTDOWN", "RIGHTDOWN"
             } ) {
            INFO( "action id: " << id );
            const auto &base = get_set( bindings, "default", id );
            const auto &mirror = get_set( bindings, "CHOOSE_DIRECTION", id );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( std::ranges::includes( mirror.gamepad, base.gamepad ) );
        }
    }

    SECTION( "CHOOSE_DIRECTION pause mirrors DEFAULTMODE pause" ) {
        // The direction prompt's "choose here" copies the gameplay pause
        // keys (and adds A on the pad); directions themselves come from the
        // shared entries via fallback, so they need no mirror.
        const auto &base = get_set( bindings, "DEFAULTMODE", "pause" );
        const auto &mirror = get_set( bindings, "CHOOSE_DIRECTION", "pause" );
        CHECK( mirror.keyboard == base.keyboard );
    }

    SECTION( "yes/no prompt categories bind A to YES and B to their back-out" ) {
        // Convention: A answers yes on every prompt flavor; B goes to
        // whichever option carries ESC (harmless back-out) — NO on plain
        // yes/no prompts, ABORT on salvage-style prompts, QUIT on
        // yes/no/quit prompts (where NO is a real answer, not a back-out).
        const std::vector<std::pair<std::string, std::string>> b_targets = {
            { "YESNO", "NO" },
            { "YESNOQUIT", "QUIT" },
            { "CANCEL_ACTIVITY_OR_IGNORE_QUERY", "NO" },
            { "YES_NO_ALWAYS_NEVER", "NO" },
            { "YN_IGNORE_QUERY", "ABORT" },
        };
        for( const auto &[cat, back_out] : b_targets ) {
            INFO( "category: " << cat );
            CHECK( get_set( bindings, cat, "YES" ).gamepad.contains( "JOY_0" ) );
            CHECK( get_set( bindings, cat, back_out ).gamepad.contains( "JOY_1" ) );
            // CONFIRM must stay keyboard-only here or, being registered
            // before the options, it swallows JOY_0 (A) in query_popup.
            const auto &confirm = get_set( bindings, cat, "CONFIRM" );
            CHECK( confirm.keyboard == get_set( bindings, "default", "CONFIRM" ).keyboard );
            CHECK( confirm.gamepad.empty() );
        }
    }

    SECTION( "VEH_INTERACT tab overrides keep base keys" ) {
        for( const std::string id : { "NEXT_TAB", "PREV_TAB" } ) {
            INFO( "action id: " << id );
            const auto &base = get_set( bindings, "default", id );
            const auto &mirror = get_set( bindings, "VEH_INTERACT", id );
            CHECK( mirror.keyboard == base.keyboard );
            CHECK( mirror.gamepad == base.gamepad );
        }
    }
}
