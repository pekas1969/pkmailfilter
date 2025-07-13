# pkmailfilter

Ein einfaches Python-Konsolentool zum Verwalten und Anwenden von IMAP-Mailfiltern.

---

## Funktionen

- Verwaltung mehrerer Mail-Accounts (hinzufügen, auflisten, löschen)
- Globale Filter und Account-spezifische Filter (Anzeigen, Hinzufügen, Löschen)
- Filter basierend auf `from`, `subject` oder `body` mit Aktionen wie Verschieben in Ordner oder Löschen (Trash)
- Verschlüsselte Speicherung der Passwörter mit Fernet
- Ausführung der Filter auf die jeweiligen Mail-Accounts
- CLI-Auswahlmenü zur komfortablen Bedienung
- Möglichkeit zur Ausführung der Filter per Kommandozeilenparameter (z.B. für Cronjobs)

---

## Installation

1. Repository klonen:

```bash
git clone https://dein.git.repo.url/pkmailfilter.git
cd pkmailfilter
```

2. Abhängigkeiten installieren:

```bash
pip install cryptography
```

3. (Optional) Fernet-Schlüssel generieren und speichern (wird automatisch erstellt, falls nicht vorhanden):

```bash
python3 pkmailfilter.py
# Beim ersten Start wird automatisch ein Schlüssel unter ~/.config/pkmailfilter/fernet.key angelegt
```

---

## Nutzung

Starte das Programm einfach mit:

```bash
python3 pkmailfilter.py
```

Du erhältst ein Menü mit folgenden Optionen:

- Account hinzufügen, löschen und auflisten
- Globale Filter anzeigen, hinzufügen und löschen
- Account-spezifische Filter anzeigen, hinzufügen und löschen
- Filter ausführen (alle Accounts filtern)

### Passwortspeicherung

Passwörter werden mit Fernet verschlüsselt in der Konfigurationsdatei gespeichert, sodass sie nicht im Klartext auf der Festplatte liegen.

---

## Filter konfigurieren

Filter werden als JSON-Dateien unter `~/.config/pkmailfilter/filters/` abgelegt:

- `global.json` für globale Filter
- `<email>.json` für Account-spezifische Filter

Beispiel für einen Filtereintrag:

```json
[
  {
    "field": "subject",
    "contains": "Rechnung",
    "action": "Ablage/Rechnungen"
  }
]
```

Filter können nach dem Feld `from`, `subject` oder `body` suchen und die Mail in einen Ordner verschieben oder in den Papierkorb legen (`Trash`).

---

## Filter ausführen per Kommandozeile / Cronjob

Das Tool kann die Filter auch direkt per Kommandozeilenargument ausführen, ohne das Menü zu starten:

```bash
python3 pkmailfilter.py --apply
```

### Beispiel Cronjob (alle 30 Minuten):

```bash
*/30 * * * * /usr/bin/python3 /pfad/zu/pkmailfilter/pkmailfilter.py --apply >> /pfad/zu/pkmailfilter/pkmailfilter.log 2>&1
```

**Wichtig:**

- Die Datei `fernet.key` muss vorhanden sein und im gleichen Benutzerkontext wie der Cronjob liegen.
- Die Konfigurationsdateien müssen korrekt angelegt und mit verschlüsselten Passwörtern versehen sein.

---

## Speicherorte

- Accounts und Passwörter: `~/.config/pkmailfilter/accounts.json`
- Filter: `~/.config/pkmailfilter/filters/*.json`
- Fernet-Schlüssel: `~/.config/pkmailfilter/fernet.key`

---

## Fehler & Support

Falls Fehler auftreten:

- Prüfe die JSON-Konfigurationsdateien auf Syntaxfehler.
- Kontrolliere, ob der Fernet-Schlüssel korrekt ist (bei `InvalidToken`-Fehlern).
- Stelle sicher, dass IMAP-Zugangsdaten (Host, Port, Verschlüsselung) stimmen.
- Nutze das Logfile (z.B. Cronjob-Output) zur Fehlersuche.

---

## Screenshots

*Screenshots folgen...*

---

## Lizenz

*Hier deine Lizenz ergänzen*

---

Viel Erfolg und bei Fragen einfach melden!
