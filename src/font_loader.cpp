#include "font_loader.h"

#include <algorithm>

void ensure_unifont_loaded( std::vector<std::string> &font_list )
{
    if( !std::ranges::contains( font_list, "unifont" ) ) {
        font_list.emplace_back( PATH_INFO::fontdir() + "unifont.ttf" );
    }
}

void ensure_promptfont_loaded( std::vector<std::string> &font_list )
{
    const auto is_promptfont = []( const std::string & entry ) {
        return entry.find( "promptfont" ) != std::string::npos;
    };
    if( !std::ranges::any_of( font_list, is_promptfont ) ) {
        // First place: the glyph lookup walks fonts in order and the
        // subset provides nothing but the controller codepoints, some of
        // which (e.g. U+21D0-U+21D3 arrows) the main font would otherwise
        // claim.
        font_list.insert( font_list.begin(), PATH_INFO::fontdir() + "promptfont.ttf" );
    }
}

void font_loader::load_throws( const std::string &path )
{
    try {
        cata_ifstream stream = std::move( cata_ifstream().mode( cata_ios_mode::binary ).open( path ) );
        JsonIn json( *stream );
        JsonObject config = json.get_object();
        if( config.has_string( "typeface" ) ) {
            typeface.emplace_back( config.get_string( "typeface" ) );
        } else {
            config.read( "typeface", typeface );
        }
        if( config.has_string( "map_typeface" ) ) {
            map_typeface.emplace_back( config.get_string( "map_typeface" ) );
        } else {
            config.read( "map_typeface", map_typeface );
        }
        if( config.has_string( "overmap_typeface" ) ) {
            overmap_typeface.emplace_back( config.get_string( "overmap_typeface" ) );
        } else {
            config.read( "overmap_typeface", overmap_typeface );
        }

        ensure_unifont_loaded( typeface );
        ensure_unifont_loaded( map_typeface );
        ensure_unifont_loaded( overmap_typeface );

        // UI font only: map/overmap glyph symbols (mapgen palettes use
        // codepoints in the same arrows range) must stay untouched.
        ensure_promptfont_loaded( typeface );

    } catch( const std::exception &err ) {
        throw std::runtime_error( std::string( "loading font settings from " ) + path + " failed: " +
                                  err.what() );
    }
}

void font_loader::load()
{
    const std::string user_fontconfig = PATH_INFO::user_fontconfig();
    const std::string fontconfig = PATH_INFO::fontconfig();
    bool try_user = true;
    if( !file_exist( user_fontconfig ) ) {
        if( !copy_file( fontconfig, user_fontconfig ) ) {
            try_user = false;
            DebugLog( DL::Error, DC::SDL ) << "failed to create user font config file "
                                           << user_fontconfig;
        }
    }
    if( try_user ) {
        font_loader copy = *this;
        try {
            load_throws( user_fontconfig );
            return;
        } catch( const std::exception &e ) {
            DebugLog( DL::Error, DC::SDL ) << e.what();
        }
        *this = copy;
    }
    try {
        load_throws( fontconfig );
    } catch( const std::exception &e ) {
        DebugLog( DL::Error, DC::SDL ) << e.what();
        abort();
    }
}
