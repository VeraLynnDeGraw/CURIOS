#!/usr/bin/env bash

# CURIOS Terminal Control Center
# Operates on the installation containing this script.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CURIOS_URL="http://127.0.0.1:8765"

pause() {
    echo
    read -rp "Press Enter to return to the menu..."
}

header() {
    clear
    echo "======================================"
    echo "           CURIOS CONTROL"
    echo "======================================"
    echo
}

check_running() {
    if command -v curl >/dev/null 2>&1; then
        if curl -fsS --max-time 2 "$CURIOS_URL/api/health" >/dev/null 2>&1; then
            echo "CURIOS is responding at $CURIOS_URL"
        else
            echo "CURIOS is not responding at $CURIOS_URL"
        fi
    else
        python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=2)' >/dev/null 2>&1 \
            && echo "CURIOS is responding at $CURIOS_URL" \
            || echo "CURIOS is not responding at $CURIOS_URL"
    fi
}

while true; do
    header

    echo " APPLICATION"
    echo "  1. Start CURIOS"
    echo "  2. Open CURIOS in browser"
    echo "  3. Check running status"
    echo
    echo " DIAGNOSTICS"
    echo "  4. Verify Python modules"
    echo "  5. Verify JavaScript"
    echo "  6. Inspect project files"
    echo "  7. Show application information"
    echo
    echo " REFERENCE"
    echo "  8. Display command reference"
    echo "  9. Show CURIOS address"
    echo
    echo "  0. Exit"
    echo
    echo "======================================"

    read -rp "Select an option: " choice

    case "$choice" in
        1)
            echo
            echo "Starting CURIOS..."
            echo "Press Ctrl+C to shut it down and return here."
            cd "$PROJECT_DIR" || exit 1
            python -m curios
            pause
            ;;
        2)
            echo "Opening CURIOS with its dedicated browser profile..."
            PROFILE="$HOME/.local/share/curios/browser-profile"
            mkdir -p "$PROFILE"

            if command -v firefox >/dev/null 2>&1; then
                firefox --no-remote --profile "$PROFILE" \
                    --new-window "$CURIOS_URL" >/dev/null 2>&1 &
                echo "Firefox launch requested."
            elif command -v chromium >/dev/null 2>&1; then
                chromium --user-data-dir="$PROFILE" \
                    --no-first-run --new-window "$CURIOS_URL" >/dev/null 2>&1 &
                echo "Chromium launch requested."
            elif command -v chromium-browser >/dev/null 2>&1; then
                chromium-browser --user-data-dir="$PROFILE" \
                    --no-first-run --new-window "$CURIOS_URL" >/dev/null 2>&1 &
                echo "Chromium launch requested."
            elif command -v google-chrome >/dev/null 2>&1; then
                google-chrome --user-data-dir="$PROFILE" \
                    --no-first-run --new-window "$CURIOS_URL" >/dev/null 2>&1 &
                echo "Chrome launch requested."
            else
                echo "No supported browser found."
                echo "Open this address manually:"
                echo "$CURIOS_URL"
            fi
            pause
            ;;
        3)
            echo
            check_running
            pause
            ;;
        4)
            echo
            cd "$PROJECT_DIR" || exit 1
            if python -m py_compile curios/*.py; then
                echo "Python verification passed."
            else
                echo "Python verification failed."
            fi
            pause
            ;;
        5)
            echo
            cd "$PROJECT_DIR" || exit 1
            if command -v node >/dev/null 2>&1; then
                node --check web/app.js
                if [ $? -eq 0 ]; then
                    echo "JavaScript verification passed."
                else
                    echo "JavaScript verification failed."
                fi
            else
                echo "Node.js is not installed."
            fi
            pause
            ;;
        6)
            echo
            cd "$PROJECT_DIR" || exit 1
            find . -maxdepth 2 -type f \
                ! -name '*.backup' ! -name '*.before-*' | sort
            pause
            ;;
        7)
            echo
            echo "Project: CURIOS"
            echo "Directory: $PROJECT_DIR"
            echo "Python: $(python --version 2>&1)"
            echo "Node: $(node --version 2>/dev/null || echo 'Not installed')"
            echo "Address: $CURIOS_URL"
            pause
            ;;
        8)
            echo
            cd "$PROJECT_DIR" || exit 1
            cat commands.txt
            pause
            ;;
        9)
            echo
            echo "CURIOS local address:"
            echo "$CURIOS_URL"
            pause
            ;;
        0)
            echo
            echo "CURIOS Control Center closed."
            exit 0
            ;;
        *)
            echo
            echo "Invalid selection."
            pause
            ;;
    esac
done
