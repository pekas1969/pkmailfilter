import os
import json
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QInputDialog
)
from PyQt6.QtCore import QSettings
from cryptography.fernet import Fernet

CONFIG_DIR = os.path.expanduser("~/.config/pkmailfilter")
KEY_FILE = os.path.join(CONFIG_DIR, "key.key")
fernet = None


def load_or_create_key():
    global fernet
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    fernet = Fernet(key)


def get_fernet():
    global fernet
    if fernet is None:
        load_or_create_key()
    return fernet


def decrypt_password(enc):
    try:
        return get_fernet().decrypt(enc.encode()).decode()
    except Exception:
        return "[Ungültig oder nicht entschlüsselbar]"


def encrypt_password(pw):
    return get_fernet().encrypt(pw.encode()).decode()


def account_filter_filename(account):
    return account.replace("@", "_").replace(".", "_") + ".json"


class PKMailFilterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        load_or_create_key()
        self.setWindowTitle("PKMailFilter GUI")
        self.base_path = ""
        self.accounts = {}
        self.global_data = []
        self.settings = QSettings("pkmailfilter", "gui")

        self.init_path_dialog()
        self.init_ui()

    def init_path_dialog(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Konfigurationspfad wählen")
        last_path = self.settings.value("lastPath", "")
        if last_path:
            dialog.setDirectory(last_path)
        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self.base_path = paths[0]
                self.settings.setValue("lastPath", self.base_path)
            else:
                QMessageBox.critical(self, "Fehler", "Kein Pfad gewählt.")
                exit(1)
        else:
            exit(0)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Account-Liste
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.display_account_filters)
        main_layout.addWidget(QLabel("Mailaccounts"))
        main_layout.addWidget(self.account_list)

        # Account Buttons
        acc_btns = QHBoxLayout()
        btn_add = QPushButton("Account hinzufügen")
        btn_edit = QPushButton("Account bearbeiten")
        btn_delete = QPushButton("Account löschen")
        btn_add.clicked.connect(self.add_account)
        btn_edit.clicked.connect(self.edit_account)
        btn_delete.clicked.connect(self.delete_account)
        acc_btns.addWidget(btn_add)
        acc_btns.addWidget(btn_edit)
        acc_btns.addWidget(btn_delete)
        main_layout.addLayout(acc_btns)

        # Globale Filter Liste
        self.global_filter_list = QListWidget()
        main_layout.addWidget(QLabel("Globale Filter (global.json)"))
        main_layout.addWidget(self.global_filter_list)

        # Globale Filter Buttons
        global_btns = QHBoxLayout()
        add_global_btn = QPushButton("Globalen Filter hinzufügen")
        add_global_btn.clicked.connect(self.add_global_filter)
        edit_global_btn = QPushButton("Globalen Filter bearbeiten")
        edit_global_btn.clicked.connect(self.edit_global_filter)
        del_global_btn = QPushButton("Globalen Filter löschen")
        del_global_btn.clicked.connect(self.delete_global_filter)
        global_btns.addWidget(add_global_btn)
        global_btns.addWidget(edit_global_btn)
        global_btns.addWidget(del_global_btn)
        main_layout.addLayout(global_btns)

        # Account-spezifische Filter Liste
        self.account_filter_list = QListWidget()
        main_layout.addWidget(QLabel("Account-Filter"))
        main_layout.addWidget(self.account_filter_list)

        # Account Filter Buttons
        account_filter_btns = QHBoxLayout()
        add_account_btn = QPushButton("Account-Filter hinzufügen")
        add_account_btn.clicked.connect(self.add_account_filter)
        edit_account_btn = QPushButton("Account-Filter bearbeiten")
        edit_account_btn.clicked.connect(self.edit_account_filter)
        del_account_btn = QPushButton("Account-Filter löschen")
        del_account_btn.clicked.connect(self.delete_account_filter)
        account_filter_btns.addWidget(add_account_btn)
        account_filter_btns.addWidget(edit_account_btn)
        account_filter_btns.addWidget(del_account_btn)
        main_layout.addLayout(account_filter_btns)

        # Speichern & Filter Ausführen Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_all)
        btn_layout.addWidget(save_btn)

        run_btn = QPushButton("Filter ausführen (extern)")
        run_btn.clicked.connect(self.run_external_filter)
        btn_layout.addWidget(run_btn)

        main_layout.addLayout(btn_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.load_data()

    def load_data(self):
        acc_path = os.path.join(self.base_path, "accounts.json")
        try:
            with open(acc_path, 'r') as f:
                self.accounts = json.load(f)
            self.account_list.itemClicked.disconnect()
            self.account_list.clear()
            for email in self.accounts:
                self.account_list.addItem(email)
            self.account_list.itemClicked.connect(self.display_account_filters)
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Laden", str(e))

        try:
            gpath = os.path.join(self.base_path, "filters", "global.json")
            with open(gpath, 'r') as f:
                self.global_data = json.load(f)
            self.global_filter_list.clear()
            for entry in self.global_data:
                self.global_filter_list.addItem(f"{entry['field']} enthält '{entry['contains']}' → {entry['action']}")
        except Exception:
            self.global_data = []

    def display_account_filters(self, item):
        account = item.text()
        filename = account_filter_filename(account)
        filter_path = os.path.join(self.base_path, "filters", filename)
        try:
            with open(filter_path, 'r') as f:
                self.current_account_filters = json.load(f)
        except FileNotFoundError:
            self.current_account_filters = []
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Laden der Filter", str(e))
            self.current_account_filters = []

        self.account_filter_list.clear()
        for entry in self.current_account_filters:
            self.account_filter_list.addItem(f"{entry['field']} enthält '{entry['contains']}' → {entry['action']}")

    # Globale Filterfunktionen
    def add_global_filter(self):
        field, ok1 = QInputDialog.getText(self, "Feld", "Filterfeld:")
        if not ok1:
            return
        contains, ok2 = QInputDialog.getText(self, "Enthält", "Suchbegriff:")
        if not ok2:
            return
        action, ok3 = QInputDialog.getText(self, "Aktion", "Zielordner:")
        if not ok3:
            return
        self.global_data.append({"field": field, "contains": contains, "action": action})
        self.global_filter_list.addItem(f"{field} enthält '{contains}' → {action}")

    def edit_global_filter(self):
        item = self.global_filter_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Filter ausgewählt", "Bitte wähle zuerst einen globalen Filter aus.")
            return
        index = self.global_filter_list.row(item)
        filter_data = self.global_data[index]

        field, ok1 = QInputDialog.getText(self, "Feld bearbeiten", "Filterfeld:", text=filter_data["field"])
        if not ok1:
            return
        contains, ok2 = QInputDialog.getText(self, "Enthält bearbeiten", "Suchbegriff:", text=filter_data["contains"])
        if not ok2:
            return
        action, ok3 = QInputDialog.getText(self, "Aktion bearbeiten", "Zielordner:", text=filter_data["action"])
        if not ok3:
            return

        self.global_data[index] = {"field": field, "contains": contains, "action": action}
        self.global_filter_list.item(index).setText(f"{field} enthält '{contains}' → {action}")

    def delete_global_filter(self):
        item = self.global_filter_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Filter ausgewählt", "Bitte wähle zuerst einen globalen Filter aus.")
            return
        index = self.global_filter_list.row(item)
        if QMessageBox.question(self, "Löschen", "Diesen globalen Filter wirklich löschen?") != QMessageBox.StandardButton.Yes:
            return
        self.global_data.pop(index)
        self.global_filter_list.takeItem(index)

    # Account-Filterfunktionen
    def add_account_filter(self):
        if not hasattr(self, "current_account_filters"):
            QMessageBox.warning(self, "Kein Account ausgewählt", "Bitte wähle zuerst einen Account aus.")
            return
        field, ok1 = QInputDialog.getText(self, "Feld", "Filterfeld:")
        if not ok1:
            return
        contains, ok2 = QInputDialog.getText(self, "Enthält", "Suchbegriff:")
        if not ok2:
            return
        action, ok3 = QInputDialog.getText(self, "Aktion", "Zielordner:")
        if not ok3:
            return
        self.current_account_filters.append({"field": field, "contains": contains, "action": action})
        self.account_filter_list.addItem(f"{field} enthält '{contains}' → {action}")

    def edit_account_filter(self):
        item = self.account_filter_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Filter ausgewählt", "Bitte wähle zuerst einen Account-Filter aus.")
            return
        index = self.account_filter_list.row(item)
        filter_data = self.current_account_filters[index]

        field, ok1 = QInputDialog.getText(self, "Feld bearbeiten", "Filterfeld:", text=filter_data["field"])
        if not ok1:
            return
        contains, ok2 = QInputDialog.getText(self, "Enthält bearbeiten", "Suchbegriff:", text=filter_data["contains"])
        if not ok2:
            return
        action, ok3 = QInputDialog.getText(self, "Aktion bearbeiten", "Zielordner:", text=filter_data["action"])
        if not ok3:
            return

        self.current_account_filters[index] = {"field": field, "contains": contains, "action": action}
        self.account_filter_list.item(index).setText(f"{field} enthält '{contains}' → {action}")

    def delete_account_filter(self):
        item = self.account_filter_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Filter ausgewählt", "Bitte wähle zuerst einen Account-Filter aus.")
            return
        index = self.account_filter_list.row(item)
        if QMessageBox.question(self, "Löschen", "Diesen Account-Filter wirklich löschen?") != QMessageBox.StandardButton.Yes:
            return
        self.current_account_filters.pop(index)
        self.account_filter_list.takeItem(index)

    # Accountverwaltung
    def add_account(self):
        email, ok = QInputDialog.getText(self, "Account hinzufügen", "E-Mail Adresse:")
        if not ok or not email:
            return
        if email in self.accounts:
            QMessageBox.warning(self, "Account existiert", "Dieser Account existiert bereits.")
            return
        host, ok = QInputDialog.getText(self, "Host", "IMAP Host:")
        if not ok:
            return
        port, ok = QInputDialog.getInt(self, "Port", "IMAP Port:", value=993, min=1, max=65535)
        if not ok:
            return
        ssl_types = ["ssl", "starttls", "none"]
        ssl, ok = QInputDialog.getItem(self, "Verschlüsselung", "Wähle Verschlüsselung", ssl_types, editable=False)
        if not ok:
            return
        password, ok = QInputDialog.getText(self, "Passwort", "Passwort:", echo=QInputDialog.EchoMode.Password)
        if not ok:
            return
        password_confirm, ok = QInputDialog.getText(self, "Passwort bestätigen", "Passwort bestätigen:", echo=QInputDialog.EchoMode.Password)
        if not ok or password != password_confirm:
            QMessageBox.warning(self, "Fehler", "Passwörter stimmen nicht überein.")
            return

        self.accounts[email] = {
            "host": host,
            "port": port,
            "ssl": ssl,
            "password": encrypt_password(password)
        }
        self.account_list.addItem(email)

    def edit_account(self):
        item = self.account_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Account ausgewählt", "Bitte wähle zuerst einen Account aus.")
            return
        email = item.text()
        acc = self.accounts[email]

        host, ok = QInputDialog.getText(self, "Host bearbeiten", "IMAP Host:", text=acc["host"])
        if not ok:
            return
        port, ok = QInputDialog.getInt(self, "Port bearbeiten", "IMAP Port:", value=acc["port"], min=1, max=65535)
        if not ok:
            return
        ssl_types = ["ssl", "starttls", "none"]
        ssl, ok = QInputDialog.getItem(self, "Verschlüsselung bearbeiten", "Wähle Verschlüsselung", ssl_types, current=ssl_types.index(acc["ssl"]), editable=False)
        if not ok:
            return
        password, ok = QInputDialog.getText(self, "Passwort bearbeiten", "Passwort (leer lassen für unverändert):", echo=QInputDialog.EchoMode.Password)
        if not ok:
            return
        if password:
            password_confirm, ok = QInputDialog.getText(self, "Passwort bestätigen", "Passwort bestätigen:", echo=QInputDialog.EchoMode.Password)
            if not ok or password != password_confirm:
                QMessageBox.warning(self, "Fehler", "Passwörter stimmen nicht überein.")
                return
            acc["password"] = encrypt_password(password)

        acc["host"] = host
        acc["port"] = port
        acc["ssl"] = ssl

        self.accounts[email] = acc
        QMessageBox.information(self, "Erfolg", f"Account {email} wurde aktualisiert.")

    def delete_account(self):
        item = self.account_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Kein Account ausgewählt", "Bitte wähle zuerst einen Account aus.")
            return
        email = item.text()
        if QMessageBox.question(self, "Löschen", f"Account {email} wirklich löschen?") != QMessageBox.StandardButton.Yes:
            return
        del self.accounts[email]
        self.account_list.takeItem(self.account_list.row(item))
        # Filterdatei löschen
        fname = os.path.join(self.base_path, "filters", account_filter_filename(email))
        if os.path.exists(fname):
            os.remove(fname)
        self.account_filter_list.clear()

    # Speichern aller Änderungen
    def save_all(self):
        try:
            acc_path = os.path.join(self.base_path, "accounts.json")
            with open(acc_path, 'w') as f:
                json.dump(self.accounts, f, indent=4)

            gpath = os.path.join(self.base_path, "filters", "global.json")
            with open(gpath, 'w') as f:
                json.dump(self.global_data, f, indent=4)

            # Account-Filter speichern
            for email in self.accounts:
                fname = os.path.join(self.base_path, "filters", account_filter_filename(email))
                if email == self.account_list.currentItem().text() and hasattr(self, "current_account_filters"):
                    filters_to_save = self.current_account_filters
                else:
                    # Falls Filter schon geladen sind, nicht überschreiben
                    filters_to_save = []
                    try:
                        with open(fname, 'r') as f:
                            filters_to_save = json.load(f)
                    except Exception:
                        filters_to_save = []
                with open(fname, 'w') as f:
                    json.dump(filters_to_save, f, indent=4)

            QMessageBox.information(self, "Gespeichert", "Alle Daten wurden gespeichert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Speichern", str(e))

    # Ausführung des externen Filterskript im Unterprozess
    def run_external_filter(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cli_path = os.path.join(script_dir, "pkmailfilter.py")
        base_path = self.base_path

        try:
            proc = subprocess.run(
                [sys.executable, cli_path, "--apply", base_path],
                capture_output=True,
                text=True,
                check=True
            )
            QMessageBox.information(self, "Filter angewendet", proc.stdout)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Fehler bei Filterausführung", e.stderr)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PKMailFilterGUI()
    window.show()
    sys.exit(app.exec())
