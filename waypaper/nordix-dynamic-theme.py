#!/usr/bin/env python3
##===================================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later                         #
 # Copyright (c) 2025 Jimmy Källhagen                                #
 # Part of Yggdrasil - Nordix desktop environment                    #
 # Nordix and Yggdrasil are registered trademarks of Jimmy Källhagen # 
##===================================================================##

import subprocess
import os
import json
import time
import argparse
from pathlib import Path

THEME_NAME = "nordix-dynamic-theme"
"""
def get_current_wallpaper():
    try:
        result = subprocess.run(['swww', 'query'], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if 'image:' in line:
                wallpaper = line.split('image: ')[1].strip()
                return wallpaper
    except subprocess.CalledProcessError as e:
        print(f"Error running swww: {e}")
        return None
    return None
"""
def get_current_wallpaper():
    # 1. First try whith awww
    try:
        result = subprocess.run(['awww', 'query'], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if 'image:' in line:
                wallpaper = line.split('image: ')[1].strip()
                if os.path.exists(wallpaper):
                    return wallpaper
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass # Move on to mpvpaper if awww fails

    # 2. If awww didn't give anything, check mpvpaper via ps
    try:
        # Gets the full command for the running mpvpaper process
        cmd = ["ps", "aux"]
        ps_result = subprocess.run(cmd, capture_output=True, text=True).stdout

        for line in ps_result.splitlines():
            if 'mpvpaper' in line and not 'grep' in line:

         # We look for the last part of the string which is often the path
         # Based on your previous ps aux the path is last after the '*'
                parts = line.split()
                for part in reversed(parts):
                    if '/' in part and os.path.exists(part):
                        return part
    except Exception as e:
        print(f"Error searching for mpvpaper: {e}")
# ==========================================================================
# Qt color generation — matches the GTK mix() logic
# ==========================================================================
# GTK uses mix(background, foreground, N%) and mix(background, black, N%)
# to create visual hierarchy. KDE .colors has no mix() so we compute the
# blended RGB values here and write them directly.
#
# The percentages below mirror the GTK3/GTK4 templates exactly:
#   headerbar_bg = mix(bg, fg, 0.30)   — 30% foreground into background
#   sidebar_bg   = mix(bg, fg, 0.30)
#   card_bg      = mix(bg, fg, 0.20)
#   dialog_bg    = mix(bg, fg, 0.25)
#   view_bg      = mix(bg, black, 0.15) — 15% black into background
# ==========================================================================

def hex_to_rgb(hex_color):
    """Convert '#RRGGBB' to (R, G, B) tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_str(rgb):
    """Convert (R, G, B) tuple to 'R,G,B' string for KDE .colors format."""
    return f"{rgb[0]},{rgb[1]},{rgb[2]}"

def mix_rgb(color1, color2, amount):
    """Mix two RGB tuples. amount=0.3 means 30% of color2 blended into color1.
    This matches GTK's mix(color1, color2, amount) behavior."""
    return tuple(
        int(color1[i] + (color2[i] - color1[i]) * amount)
        for i in range(3)
    )

def clamp_rgb(rgb):
    """Clamp RGB values to 0-255 range."""
    return tuple(max(0, min(255, v)) for v in rgb)

def load_pywal_colors():
    """Load pywal's generated colors from ~/.cache/wal/colors.json."""
    colors_file = Path.home() / ".cache/wal/colors.json"
    if not colors_file.exists():
        print(f"Error: {colors_file} not found")
        return None
    with open(colors_file) as f:
        data = json.load(f)
    
    colors = {}
    colors['background'] = hex_to_rgb(data['special']['background'])
    colors['foreground'] = hex_to_rgb(data['special']['foreground'])
    for i in range(16):
        colors[f'color{i}'] = hex_to_rgb(data['colors'][f'color{i}'])
    
    return colors

def generate_qt_colors(colors):
    """Generate the derived colors that match GTK's mix() logic."""
    bg = colors['background']
    fg = colors['foreground']
    black = (0, 0, 0)
    
    derived = {}
    
    # Match GTK template: mix(background, foreground, N%)
    derived['headerbar_bg']   = clamp_rgb(mix_rgb(bg, fg, 0.30))  # headerbar
    derived['sidebar_bg']     = clamp_rgb(mix_rgb(bg, fg, 0.30))  # sidebar
    derived['card_bg']        = clamp_rgb(mix_rgb(bg, fg, 0.20))  # cards/popover
    derived['dialog_bg']      = clamp_rgb(mix_rgb(bg, fg, 0.25))  # dialogs
    derived['sidebar_back']   = clamp_rgb(mix_rgb(bg, fg, 0.22))  # sidebar backdrop
    
    # Match GTK template: mix(background, black, 0.15)
    derived['view_bg']        = clamp_rgb(mix_rgb(bg, black, 0.15))  # view/input areas
    
    # Slightly lighter variant for alternating rows
    derived['view_alt']       = clamp_rgb(mix_rgb(bg, fg, 0.08))
    
    # Button: between card and headerbar — subtle elevation above window
    derived['button_bg']      = clamp_rgb(mix_rgb(bg, fg, 0.15))
    
    # Hover state: brighter than button
    derived['hover_bg']       = clamp_rgb(mix_rgb(bg, fg, 0.25))
    
    return derived


def write_qt_colors_file(colors, derived):
    """Write the .colors file with computed blended values."""
    bg = colors['background']
    fg = colors['foreground']
    
    content = f"""\
##===================================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later                         #
 # Copyright (c) 2025 Jimmy Källhagen                                #
 # Part of Yggdrasil - Nordix desktop environment                    #
 # Nordix and Yggdrasil are registered trademarks of Jimmy Källhagen # 
##===================================================================##

# ==========================================================================
# Nordix Dynamic Theme — KDE/Qt Color Scheme
# ==========================================================================
# Auto-generated by nordix-dynamic-theme.py from pywal colors.
# Colors are computed with the same mix() ratios as the GTK3/GTK4 templates
# to ensure visual consistency across all toolkits.
# ==========================================================================

[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={rgb_to_str(colors['color8'])}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={rgb_to_str(derived['hover_bg'])}
BackgroundNormal={rgb_to_str(derived['button_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Complementary]
BackgroundAlternate={rgb_to_str(derived['sidebar_back'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Header]
BackgroundAlternate={rgb_to_str(bg)}
BackgroundNormal={rgb_to_str(derived['headerbar_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Header][Inactive]
BackgroundAlternate={rgb_to_str(derived['sidebar_back'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Selection]
BackgroundAlternate={rgb_to_str(colors['color4'])}
BackgroundNormal={rgb_to_str(colors['color1'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(fg)}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color3'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Tooltip]
BackgroundAlternate={rgb_to_str(bg)}
BackgroundNormal={rgb_to_str(derived['dialog_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:View]
BackgroundAlternate={rgb_to_str(derived['view_alt'])}
BackgroundNormal={rgb_to_str(derived['view_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Window]
BackgroundAlternate={rgb_to_str(derived['card_bg'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[General]
ColorScheme=NordixDynamic
Name=Nordix Dynamic
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground={rgb_to_str(derived['headerbar_bg'])}
activeBlend={rgb_to_str(fg)}
activeForeground={rgb_to_str(fg)}
inactiveBackground={rgb_to_str(bg)}
inactiveBlend={rgb_to_str(colors['color8'])}
inactiveForeground={rgb_to_str(colors['color8'])}
"""
    return content


def write_kdeglobals_file(colors, derived):
    """Write kdeglobals with computed blended values — same color sections
    as .colors but with additional KDE-specific sections."""
    bg = colors['background']
    fg = colors['foreground']
    
    content = f"""\
[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={rgb_to_str(colors['color8'])}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={rgb_to_str(derived['hover_bg'])}
BackgroundNormal={rgb_to_str(derived['button_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Complementary]
BackgroundAlternate={rgb_to_str(derived['sidebar_back'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Header]
BackgroundAlternate={rgb_to_str(bg)}
BackgroundNormal={rgb_to_str(derived['headerbar_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Header][Inactive]
BackgroundAlternate={rgb_to_str(derived['sidebar_back'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Selection]
BackgroundAlternate={rgb_to_str(colors['color4'])}
BackgroundNormal={rgb_to_str(colors['color1'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(fg)}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color3'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Tooltip]
BackgroundAlternate={rgb_to_str(bg)}
BackgroundNormal={rgb_to_str(derived['dialog_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:View]
BackgroundAlternate={rgb_to_str(derived['view_alt'])}
BackgroundNormal={rgb_to_str(derived['view_bg'])}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[Colors:Window]
BackgroundAlternate={rgb_to_str(derived['card_bg'])}
BackgroundNormal={rgb_to_str(bg)}
DecorationFocus={rgb_to_str(colors['color1'])}
DecorationHover={rgb_to_str(colors['color1'])}
ForegroundActive={rgb_to_str(colors['color1'])}
ForegroundInactive={rgb_to_str(colors['color8'])}
ForegroundLink={rgb_to_str(colors['color4'])}
ForegroundNegative={rgb_to_str(colors['color9'])}
ForegroundNeutral={rgb_to_str(colors['color3'])}
ForegroundNormal={rgb_to_str(fg)}
ForegroundPositive={rgb_to_str(colors['color2'])}
ForegroundVisited={rgb_to_str(colors['color5'])}

[General]
ColorScheme=NordixDynamic
Name=Nordix Dynamic
shadeSortColumn=true

[Icons]
Theme=breeze-dark

[KDE]
contrast=4
widgetStyle=Breeze

[KFileDialog Settings]
Allow Expansion=false
Automatically select filename extension=true
Breadcrumb Navigation=true
Decoration position=2
Show Full Path=false
Show Inline Previews=true
Show Preview=false
Show Speedbar=true
Show hidden files=false
Sort by=Name
Sort directories first=true
Sort hidden files last=false
Sort reversed=false
Speedbar Width=173
View Style=DetailTree

[WM]
activeBackground={rgb_to_str(derived['headerbar_bg'])}
activeBlend={rgb_to_str(fg)}
activeForeground={rgb_to_str(fg)}
inactiveBackground={rgb_to_str(bg)}
inactiveBlend={rgb_to_str(colors['color8'])}
inactiveForeground={rgb_to_str(colors['color8'])}
"""
    return content


def generate_qt_theme_files():
    """Load pywal colors, compute blended values, write .colors and kdeglobals."""
    colors = load_pywal_colors()
    if not colors:
        print("Could not load pywal colors — skipping Qt theme generation")
        return False
    
    derived = generate_qt_colors(colors)
    
    cache_dir = Path.home() / ".cache/wal"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Write .colors file (for hyprqt6engine)
    colors_content = write_qt_colors_file(colors, derived)
    colors_file = cache_dir / "nordix-dynamic.colors"
    colors_file.write_text(colors_content)
    print(f"Qt color scheme written: {colors_file}")
    
    # Write kdeglobals (for Qt5 apps and KDE fallback)
    kdeglobals_content = write_kdeglobals_file(colors, derived)
    kdeglobals_file = cache_dir / "kdeglobals"
    kdeglobals_file.write_text(kdeglobals_content)
    print(f"kdeglobals written: {kdeglobals_file}")
    
    return True


def create_theme_symlinks():
    home = Path.home()

    # --- GTK3 ---
    # Pywal generates ~/.cache/wal/nordix-dynamic-gtk-theme.css from the template.
    # We symlink it as gtk.css into the theme directory so gsettings can pick it up.
    gtk3_source = home / ".cache/wal/nordix-dynamic-gtk-theme.css"
    gtk3_dir = home / ".themes" / THEME_NAME / "gtk-3.0"
    gtk3_dir.mkdir(parents=True, exist_ok=True)
    link_gtk3 = gtk3_dir / "gtk.css"
    if link_gtk3.exists() or link_gtk3.is_symlink():
        link_gtk3.unlink()
    link_gtk3.symlink_to(gtk3_source)

    # --- GTK4 / libadwaita ---
    # Pywal generates ~/.cache/wal/nordix-dynamic-libadwaita-theme.css from the template.
    # We symlink it as libadwaita-tweaks.css so libadwaita picks it up.
    gtk4_source = home / ".cache/wal/nordix-dynamic-libadwaita-theme.css"
    gtk4_dir = home / ".config/gtk-4.0"
    gtk4_dir.mkdir(parents=True, exist_ok=True)
    link_gtk4 = gtk4_dir / "libadwaita-tweaks.css"
    if link_gtk4.exists() or link_gtk4.is_symlink():
        link_gtk4.unlink()
    link_gtk4.symlink_to(gtk4_source)

    # --- Qt / KDE color scheme ---
    # Generated by generate_qt_theme_files() with computed blend values.
    # We symlink it into the theme directory. hyprqt6engine.conf points here.
    qt_source = home / ".cache/wal/nordix-dynamic.colors"
    qt_dir = home / ".themes" / THEME_NAME / "qt"
    qt_dir.mkdir(parents=True, exist_ok=True)
    link_qt = qt_dir / "nordix-dynamic.colors"
    if link_qt.exists() or link_qt.is_symlink():
        link_qt.unlink()
    link_qt.symlink_to(qt_source)

    # --- kdeglobals ---
    # Generated by generate_qt_theme_files() with same computed blend values.
    # Many Qt apps (especially Qt5) read ~/.config/kdeglobals for colors.
    kdeglobals_source = home / ".cache/wal/kdeglobals"
    kdeglobals_link = home / ".config/kdeglobals"
    if kdeglobals_link.exists() or kdeglobals_link.is_symlink():
        kdeglobals_link.unlink()
    kdeglobals_link.symlink_to(kdeglobals_source)

    print("Symbolic links created (GTK3 + GTK4/libadwaita + Qt .colors + kdeglobals)")



def apply_gtk_theme():
    try:
        subprocess.run([
            'gsettings', 'set', 
            'org.gnome.desktop.interface', 
            'gtk-theme', 
            THEME_NAME
        ], check=True)
        print("GTK theme applied with gsettings")
    except subprocess.CalledProcessError as e:
        print(f"Failed to apply theme: {e}")


def main():
    parser = argparse.ArgumentParser(description='Apply pywal colors from current wallpaper')
    parser.add_argument('-b', '--backend', 
                       default='fast-colorthief',
                       choices=['haishoku', 'colorthief', 'fast-colorthief', 'colorz', 'wal'],
                       help='Color backend to use (default: haishoku)')
    parser.add_argument('--cols16', 
                       default='foxify-lighten',
                       choices=['darken', 'lighten', 'dual', 'foxify-darken', 'foxify-lighten'],
                       help='16-color generation mode (default: foxify-lighten)')
    parser.add_argument('-a', '--alpha', type=float, default=0.5,
                       help='Terminal background transparency (default: 0.9)')
    parser.add_argument('-s', '--saturate', type=float, default=0.9,
                       help='Color saturation (default: 0.9)')
    parser.add_argument('-c', '--contrast', type=float, default=0.3,
                       help='Color contrast (default: 0.9)')
    parser.add_argument('-w', '--wait', type=int, default=4,
                       help='Seconds to wait for wallpaper to apply (default: 4)')
    
    args = parser.parse_args()
    
    time.sleep(args.wait)
    
    wallpaper = get_current_wallpaper()
    if not wallpaper:
        print("Failed to get wallpaper from swww")
        return
    
    print(f"Applying pywal to: {wallpaper}")
    print(f"Using backend: {args.backend}")
    
    # Build wal command
    wal_cmd = [
        'wal',
        '-a', str(args.alpha),
        '--saturate', str(args.saturate),
        '--contrast', str(args.contrast),
        '--cols16', str(args.cols16),
        '-i', wallpaper,
        '-n'
    ]
    
    # Add backend (only if not the default 'wal' backend)
    if args.backend != 'wal':
        wal_cmd.extend(['--backend', args.backend])
    
    try:
        subprocess.run(wal_cmd, check=True)
        print("Pywal ran successfully")
    except subprocess.CalledProcessError as e:
        print(f"Pywal failed: {e}")
        return
    
    time.sleep(0.1)
    
    # Generate Qt theme files with computed blend values (replaces pywal template)
    generate_qt_theme_files()
    
    create_theme_symlinks()
    
    subprocess.Popen(['pywalfox', 'update'])
    
    apply_gtk_theme()
    subprocess.run(['hyprctl', 'reload'], capture_output=True)
    print("Hyprland config reloaded (Qt theme refresh)")
    print("Nordix Dynamic Themes is applied!")
    
if __name__ == "__main__":
    main()
