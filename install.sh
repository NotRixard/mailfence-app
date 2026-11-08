#!/usr/bin/env bash
# Installs the Mailfence wrapper as a proper desktop app (user-level, no sudo).
set -e
cd "$(dirname "$0")"

BIN="$HOME/.local/bin/mailfence-app"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS="$HOME/.local/share/applications"

rm -f "$HOME/.local/share/applications/dev.local.Mailfence.desktop" "$ICONS/dev.local.Mailfence.svg"
install -Dm755 mailfence-app.py "$BIN"
install -Dm644 io.github.NotRixard.MailfenceApp.svg "$ICONS/io.github.NotRixard.MailfenceApp.svg"

mkdir -p "$APPS"
cat > "$APPS/io.github.NotRixard.MailfenceApp.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Mailfence
Comment=Mailfence desktop wrapper
Exec=$BIN
Icon=io.github.NotRixard.MailfenceApp
Categories=Network;Email;
StartupWMClass=io.github.NotRixard.MailfenceApp
Terminal=false
EOF

update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Done. Look for 'Mailfence' in your app launcher."
