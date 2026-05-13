/bin/bash
##================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later      #
 # Copyright (c) 2025- The Nordix Authors         #
 # Part of Yggdrasil - Nordix desktop environment #
##================================================##
# Randomly cycles wallpapers using waypaper at a set interval.

PID_FILE="/tmp/nordix-wallpaper-loop.pid"
CONFIG_FILE="$HOME/.config/nordix/nordix-theme/nordix-wallpaper-loop.conf"

# --- Defaults ---
STATE=active
TIME_SEC=180
SKIP_FULLSCREEN=true
SKIP_MEDIA=true

create_default_config() {
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << 'CONF'
##================================================##
 # SPDX-License-Identifier: GPL-3.0-or-later      #
 # Copyright (c) 2025- The Nordix Authors         #
 # Part of Yggdrasil - Nordix desktop environment #
##================================================##

# nordix-wallpaper-loop configuration
# Location: ~/.config/nordix/nordix-theme/nordix-wallpaper-loop.conf

# Start or stop the wallpaper loop
# Values: active | inactive
STATE=active

# Seconds between wallpaper changes
TIME_SEC=180

# Skip wallpaper change when a fullscreen window is detected
# Values: true | false
SKIP_FULLSCREEN=true

# Skip wallpaper change when a video or game window is detected (via contentType)
# Values: true | false
SKIP_MEDIA=true
CONF
    echo "Created default config: $CONFIG_FILE"
}

# --- Create config if it doesn't exist, then load it ---
[[ ! -f "$CONFIG_FILE" ]] && create_default_config
source "$CONFIG_FILE"

# --- CLI argument overrides config STATE ---
[[ -n "$1" ]] && STATE="$1"
[[ -n "$2" ]] && TIME_SEC="$2"

# ------------------------------------------------

show_help() {
    echo "Usage: nordix-wallpaper-loop [active|inactive] [TIME]"
    echo ""
    echo "Automatically change wallpaper at a set interval using waypaper."
    echo "Config: $CONFIG_FILE"
    echo ""
    echo "  active      Start the wallpaper loop"
    echo "  inactive    Stop the wallpaper loop"
    echo ""
    echo "  TIME    Seconds between wallpaper changes (overrides config, default: 180)"
    echo ""
    echo "Examples:"
    echo "  nordix-wallpaper-loop active 60      Change every 60 seconds"
    echo "  nordix-wallpaper-loop active 300     Change every 5 minutes"
    echo "  nordix-wallpaper-loop active         Use interval from config"
    echo "  nordix-wallpaper-loop inactive       Stop the loop"
    echo "  nordix-wallpaper-loop                Use STATE from config"
}

fullscreen_running() {
    hyprctl clients -j | jq -e '.[] | select(.fullscreen > 0)' > /dev/null 2>&1
}

media_running() {
    hyprctl clients -j | jq -e '.[] | select(.contentType == "video" or .contentType == "game")' > /dev/null 2>&1
}

should_skip() {
    [[ "$SKIP_FULLSCREEN" == "true" ]] && fullscreen_running && return 0
    [[ "$SKIP_MEDIA" == "true" ]] && media_running && return 0
    return 1
}

start_loop() {
    if ! [[ "$TIME_SEC" =~ ^[0-9]+$ ]]; then
        echo "Error: TIME_SEC must be a number (seconds)"
        echo ""
        show_help
        exit 1
    fi

    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Nordix Wallpaper Loop is already running (PID $(cat "$PID_FILE"))"
        exit 1
    fi

    echo "Nordix Wallpaper Loop — starting, changing every ${TIME_SEC}s"
    echo "  Skip fullscreen : $SKIP_FULLSCREEN"
    echo "  Skip media/game : $SKIP_MEDIA"

    (
        while true; do
            should_skip || waypaper --random
            sleep "$TIME_SEC"
        done
    ) &

    echo $! > "$PID_FILE"
    echo "Started (PID $!)"
}

stop_loop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Nordix Wallpaper Loop is not running (no PID file found)"
        exit 1
    fi

    local PID
    PID=$(cat "$PID_FILE")

    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Nordix Wallpaper Loop stopped (PID $PID)"
    else
        echo "Process $PID not found, cleaning up PID file"
        rm -f "$PID_FILE"
        exit 1
    fi
}

case "$STATE" in
    active)
        start_loop
        ;;
    inactive)
        stop_loop
        ;;
    -h|--help)
        show_help
        ;;
    *)
        echo "Error: unknown STATE '${STATE}' — must be active or inactive"
        echo ""
        show_help
        exit 1
        ;;
esac
