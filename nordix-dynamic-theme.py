#!/usr/bin/env python3
##=========================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later               #
 # Copyright (c) 2025 Jimmy Källhagen                      #
 # Part of Yggdrasil - Nordix desktop environment          #
##=========================================================##

import subprocess
import os
import json
import time
import argparse
from pathlib import Path

THEME_NAME = "nordix-dynamic-theme"


# pacman -Q plasma-integration
###################################################################################
####################################################################################
## ORGINAL AWWW
#def get_current_wallpaper():
#    try:
#        result = subprocess.run(['awww', 'query'], capture_output=True, text=True, check=True)
#        for line in result.stdout.split('\n'):
#            if 'image:' in line:
#                wallpaper = line.split('image: ')[1].strip()
#                return wallpaper
#    except subprocess.CalledProcessError as e:
#        print(f"Error running awww: {e}")
#        return None
#    return None
###################################################################################
###################################################################################

# TEST AWWW AND MPVPAPER 

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

    return None


######################################################################################
######################################################################################


def hex_to_rgb(hex_color):
    """Convert '#RRGGBB' to (R, G, B) tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_str(rgb):
    """Convert (R, G, B) tuple to 'R,G,B' string for KDE .colors format."""
    return f"{rgb[0]},{rgb[1]},{rgb[2]}"

def clamp_rgb(rgb):
    """Clamp RGB values to 0-255 range."""
    return tuple(max(0, min(255, v)) for v in rgb)

def offset_rgb(base, delta):
    """Offset all RGB channels by a fixed amount."""
    return clamp_rgb(tuple(base[i] + delta for i in range(3)))

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
def mix_rgb(a, b, ratio):
    """Mix two RGB colors. ratio=0 returns a, ratio=1 returns b."""
    return clamp_rgb(tuple(
        int(a[i] * (1 - ratio) + b[i] * ratio)
        for i in range(3)
    ))


def generate_qt_colors(colors):
    """Generate derived colors by mixing bg with fg/black,
    matching the GTK adw-gtk3-dark template exactly.

    GTK template uses:
      view_bg     = mix(bg, black, 0.15)
      headerbar   = mix(bg, fg,    0.40)
      sidebar     = mix(bg, fg,    0.30)
      card        = mix(bg, fg,    0.20)
    """
    bg = mix_rgb(colors['background'], colors['foreground'], 0.05)  # lyft bg 5% mot fg
    fg = colors['foreground']
    black = (0, 0, 0)
    return {
        'view_bg':     mix_rgb(bg, black, 0.15),   # content area, slightly darker
        'view_alt':    mix_rgb(bg, black, 0.08),   # zebra stripe
        'raised':      mix_rgb(bg, fg, 0.20),      # sidebar — matches GTK sidebar_bg
        'hover':       mix_rgb(bg, fg, 0.40),      # headerbar / hover — matches GTK headerbar_bg
        'wm_active':   mix_rgb(bg, fg, 0.30),
        'wm_inactive': bg,
    }
def build_color_sections(colors, derived):
    """Build the KDE color sections as a string.
    Used by both .colors and kdeglobals to avoid duplication."""
    bg = colors['background']
    fg = colors['foreground']
    raised = derived['raised']

    # Shorthand for foreground colors (same across all sections)
    c1  = rgb_str(colors['color1'])   # accent / red
    c2  = rgb_str(colors['color2'])   # success / green
    c3  = rgb_str(colors['color3'])   # warning / yellow
    c4  = rgb_str(colors['color4'])   # link / blue
    c5  = rgb_str(colors['color5'])   # visited / purple
    c8  = rgb_str(colors['color8'])   # inactive / muted
    c9  = rgb_str(colors['color9'])   # bright red
    fgs = rgb_str(fg)                 # foreground normal

    # Button:       raised / raised        (Alternate=raised for hover-ish)
    # Complementary: raised / bg
    # Header:       bg / raised            (Alt=bg, Norm=raised)
    # Header[Inact]: raised / bg           (swapped from active)
    # Selection:    accent-alt / accent
    # Tooltip:      bg / raised
    # View:         view-alt / view        (darkest level)
    # Window:       raised / bg            (Alt=raised, Norm=bg)

    return f"""\
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
Color={c8}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={rgb_str(derived['hover'])}
BackgroundNormal={rgb_str(raised)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Complementary]
BackgroundAlternate={rgb_str(raised)}
BackgroundNormal={rgb_str(bg)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Header]
BackgroundAlternate={rgb_str(bg)}
BackgroundNormal={rgb_str(raised)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Header][Inactive]
BackgroundAlternate={rgb_str(raised)}
BackgroundNormal={rgb_str(bg)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Selection]
BackgroundAlternate={c4}
BackgroundNormal={c1}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={fgs}
ForegroundInactive={c8}
ForegroundLink={c3}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Tooltip]
BackgroundAlternate={rgb_str(bg)}
BackgroundNormal={rgb_str(raised)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:View]
BackgroundAlternate={rgb_str(derived['view_alt'])}
BackgroundNormal={rgb_str(derived['view_bg'])}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[Colors:Window]
BackgroundAlternate={rgb_str(bg)}
BackgroundNormal={rgb_str(raised)}
DecorationFocus={c1}
DecorationHover={c1}
ForegroundActive={c1}
ForegroundInactive={c8}
ForegroundLink={c4}
ForegroundNegative={c9}
ForegroundNeutral={c3}
ForegroundNormal={fgs}
ForegroundPositive={c2}
ForegroundVisited={c5}

[General]
ColorScheme=~/.themes/nordix-dynamic-theme/qt/nordix-dynamic.colors
Name=nordix-dynamic-theme
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground={rgb_str(derived['wm_active'])}
activeBlend={fgs}
activeForeground={fgs}
inactiveBackground={rgb_str(derived['wm_inactive'])}
inactiveBlend={c8}
inactiveForeground={c8}
"""


def write_qt_colors_file(colors, derived):
    """Write the .colors file for hyprqt6engine."""
    header = """\
##================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later      #
 # Copyright (c) 2025 Jimmy Källhagen             #
 # Part of Yggdrasil - Nordix desktop environment #
##================================================##

# Nordix Dynamic Theme - KDE/Qt Color Scheme
# Auto-generated by nordix-dynamic-theme.py from pywal colors.

"""
    return header + build_color_sections(colors, derived)


def write_kdeglobals_file(colors, derived):
    """Write kdeglobals — same colors plus KDE-specific settings."""
    content = build_color_sections(colors, derived)

    # Append KDE-specific sections that only belong in kdeglobals
    content += """
[Icons]
Theme=Cosmic

[General]
ColorScheme=~/.themes/nordix-dynamic-theme/qt/nordix-dynamic.colors
Name=nordix-dynamic-theme
shadeSortColumn=true
font=Comfortaa,11,-1,5,50,0,0,0,0,0
fixed=Maple Mono,11,-1,5,50,0,0,0,0,0
menuFont=Comfortaa,11,-1,5,50,0,0,0,0,0
toolBarFont=Comfortaa,11,-1,5,50,0,0,0,0,0
widgetStyle=Breeze

[WM]
activeFont=Comfortaa,11,-1,5,50,0,0,0,0,0

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
"""
    return content


def generate_qt_theme_files():
    """Load pywal colors, compute blended values, write .colors and kdeglobals
    directly to their final locations."""
    colors = load_pywal_colors()
    if not colors:
        print("Could not load pywal colors — skipping Qt theme generation")
        return False

    derived = generate_qt_colors(colors)
    home = Path.home()

    # Write .colors file directly where hyprqt6engine.conf reads it
    qt_dir = home / ".themes" / THEME_NAME / "qt"
    qt_dir.mkdir(parents=True, exist_ok=True)
    colors_file = qt_dir / "nordix-dynamic.colors"
    colors_file.write_text(write_qt_colors_file(colors, derived))
    print(f"Qt color scheme written: {colors_file}")

    # Write kdeglobals directly to ~/.config/kdeglobals
    config_dir = home / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    kdeglobals_file = config_dir / "kdeglobals"
    if kdeglobals_file.is_symlink():
        kdeglobals_file.unlink()
    kdeglobals_file.write_text(write_kdeglobals_file(colors, derived))
    print(f"kdeglobals written: {kdeglobals_file}")

    return True


def create_theme_symlinks():
    home = Path.home()

    # --- GTK3 ---
    gtk3_source = home / ".cache/wal/nordix-dynamic-gtk-theme.css"
    gtk3_dir = home / ".themes" / THEME_NAME / "gtk-3.0"
    gtk3_dir.mkdir(parents=True, exist_ok=True)
    link_gtk3 = gtk3_dir / "gtk.css"
    if link_gtk3.exists() or link_gtk3.is_symlink():
        link_gtk3.unlink()
    link_gtk3.symlink_to(gtk3_source)

    # --- GTK4 / libadwaita ---
    gtk4_source = home / ".cache/wal/nordix-dynamic-libadwaita-theme.css"
    gtk4_dir = home / ".config/gtk-4.0"
    gtk4_dir.mkdir(parents=True, exist_ok=True)
    link_gtk4 = gtk4_dir / "libadwaita-tweaks.css"
    if link_gtk4.exists() or link_gtk4.is_symlink():
        link_gtk4.unlink()
    link_gtk4.symlink_to(gtk4_source)

    # Qt .colors and kdeglobals are written directly by generate_qt_theme_files()

    print("Symbolic links created (GTK3 + GTK4/libadwaita)")


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
        print("Failed to get wallpaper from awww")
        return

    print(f"Applying pywal to: {wallpaper}")
    print(f"Using backend: {args.backend}")

    wal_cmd = [
        'wal',
        '-a', str(args.alpha),
        '--saturate', str(args.saturate),
        '--contrast', str(args.contrast),
        '--cols16', str(args.cols16),
        '-i', wallpaper,
        '-n'
    ]

    if args.backend != 'wal':
        wal_cmd.extend(['--backend', args.backend])

    try:
        subprocess.run(wal_cmd, check=True)
        print("Pywal ran successfully")
    except subprocess.CalledProcessError as e:
        print(f"Pywal failed: {e}")
        return

    time.sleep(0.1)

    generate_qt_theme_files()

    create_theme_symlinks()

    subprocess.Popen(['pywalfox', 'update'])

    apply_gtk_theme()
    print("Nordix Dynamic Themes is applied!")

if __name__ == "__main__":
    main()
