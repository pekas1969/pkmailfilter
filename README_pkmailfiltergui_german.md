# pkmailfiltergui

**pkmailfiltergui** ist eine grafische Benutzeroberfläche (GUI) für das Mailfilter-Kommandozeilen-Tool `pkmailfilter.sh`. Mit dieser Anwendung kannst du deine IMAP-Mailfilter bequem verwalten und ausführen, ohne die Konsole zu benutzen.

---

## Funktionen

- Anzeige und Verwaltung von Mailaccounts
- Bearbeitung globaler und accountbezogener Filter
- Ausführen der Filter über einen Button
- Passwortverschlüsselung mit Fernet (kompatibel mit `pkmailfilter.sh`)
- Arbeitet mit den bestehenden JSON-Konfigurationsdateien
- Einfacher Zugriff auf die Filterverwaltung per GUI

---

## Installation

1. Stelle sicher, dass Python 3.10+ installiert ist.
2. Installiere die benötigten Python-Pakete:

   ```bash
   pip install PyQt6 cryptography
   ```

3. Lege das Skript `pkmailfiltergui.py` in das gleiche Verzeichnis wie `pkmailfilter.sh`.

---

## Nutzung

1. Starte die GUI:

   ```bash
   python pkmailfiltergui.py
   ```

2. Die Anwendung lädt automatisch die Konfigurationsdateien aus dem Standardordner (`~/.config/pkmailfilter/`).
3. Verwalte deine Mailaccounts und Filter bequem per Klick.
4. Klicke auf **Filter ausführen**, um die Filter auf deine Mailaccounts anzuwenden.

---

## Hinweise

- Das Skript `pkmailfilter.sh` muss im gleichen Verzeichnis wie `pkmailfiltergui.py` liegen.
- Die Konfigurationen werden im Ordner `~/.config/pkmailfilter/` erwartet.
- Passwörter werden verschlüsselt gespeichert, um die Sicherheit zu erhöhen.
- Für Fernet-Verschlüsselung wird ein Schlüssel benötigt, den du mit `pkmailfilter.sh` generieren kannst.

---

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

---

## Kontakt

Bei Fragen oder Problemen kannst du mich gerne kontaktieren.

---

**Viel Erfolg beim Filtern deiner Mails!**
