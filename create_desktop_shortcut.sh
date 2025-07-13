#!/bin/bash

# Absoluten Pfad ermitteln
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/pkmailfiltergui.py"
DESKTOP_FILE_NAME="pkmailfiltergui.desktop"
DESKTOP_LOCAL="$HOME/.local/share/applications/$DESKTOP_FILE_NAME"
DESKTOP_HERE="$SCRIPT_DIR/$DESKTOP_FILE_NAME"

# Prüfen, ob die Datei existiert
if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "Fehler: $SCRIPT_PATH nicht gefunden!"
  exit 1
fi

# Python-Interpreter ermitteln
PYTHON_EXEC="$(command -v python3)"

# Desktop-Datei erstellen
cat > "$DESKTOP_HERE" <<EOF
[Desktop Entry]
Type=Application
Name=PKMailFilter GUI
Exec=$PYTHON_EXEC "$SCRIPT_PATH"
Icon=internet-mail
Terminal=false
Categories=Network;Email;Internet;
StartupNotify=true
EOF

# Kopie ins lokale Anwendungen-Menü
cp "$DESKTOP_HERE" "$DESKTOP_LOCAL"
chmod +x "$DESKTOP_HERE" "$DESKTOP_LOCAL"

echo "Desktop-Verknüpfung erstellt:"
echo "- Lokal: $DESKTOP_HERE"
echo "- Anwendungsmenü: $DESKTOP_LOCAL"
