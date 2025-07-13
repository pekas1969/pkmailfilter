import os
import json
import getpass
import imaplib
from cryptography.fernet import Fernet

CONFIG_DIR = os.path.expanduser("~/.config/pkmailfilter")
ACCOUNTS_FILE = os.path.join(CONFIG_DIR, "accounts.json")
FILTERS_DIR = os.path.join(CONFIG_DIR, "filters")
GLOBAL_FILTER = os.path.join(FILTERS_DIR, "global.json")
KEY_FILE = os.path.join(CONFIG_DIR, "key.key")

def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(FILTERS_DIR, exist_ok=True)

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

fernet = Fernet(load_key())

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

def add_account():
    email = input("E-Mail-Adresse: ")
    host = input("IMAP-Host: ")
    port = int(input("IMAP-Port (z.B. 993): "))
    encryption = input("Verschlüsselung (ssl/starttls/none): ").lower()
    password = getpass.getpass("Passwort: ")

    accounts = load_accounts()
    accounts[email] = {
        "email": email,
        "host": host,
        "port": port,
        "encryption": encryption,
        "password": fernet.encrypt(password.encode()).decode()
    }
    save_accounts(accounts)
    print("Account gespeichert.")

def list_accounts():
    accounts = load_accounts()
    for i, email in enumerate(accounts.keys(), start=1):
        print(f"{i}. {email}")

def delete_account():
    list_accounts()
    accounts = load_accounts()
    email = input("E-Mail-Adresse zum Löschen: ")
    if email in accounts:
        del accounts[email]
        save_accounts(accounts)
        print("Account gelöscht.")
        # zugehörige Filterdatei entfernen
        acc_filter_file = os.path.join(FILTERS_DIR, email.replace("@", "_at_") + ".json")
        if os.path.exists(acc_filter_file):
            os.remove(acc_filter_file)
    else:
        print("Account nicht gefunden.")

def load_filters(account=None):
    if account:
        path = os.path.join(FILTERS_DIR, account.replace("@", "_at_") + ".json")
    else:
        path = GLOBAL_FILTER
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_filters(filters, account=None):
    if account:
        path = os.path.join(FILTERS_DIR, account.replace("@", "_at_") + ".json")
    else:
        path = GLOBAL_FILTER
    with open(path, "w") as f:
        json.dump(filters, f, indent=2)

def list_filters(account=None):
    filters = load_filters(account)
    if not filters:
        print("Keine Filter vorhanden.")
        return
    for i, f in enumerate(filters, start=1):
        print(f"{i}. Wenn '{f['field']}' enthält '{f['contains']}', dann verschiebe nach '{f['action']}'.")

def add_filter(account=None):
    field = input("Feld (from, subject, body): ").lower()
    contains = input("Enthält: ")
    target = input("Zielordner: ")
    filters = load_filters(account)
    filters.append({
        "field": field,
        "contains": contains,
        "action": action
    })
    save_filters(filters, account)
    print("Filter hinzugefügt.")

def delete_filter(account=None):
    filters = load_filters(account)
    list_filters(account)
    try:
        index = int(input("Filternummer zum Löschen: ")) - 1
        if 0 <= index < len(filters):
            filters.pop(index)
            save_filters(filters, account)
            print("Filter gelöscht.")
        else:
            print("Ungültige Nummer.")
    except ValueError:
        print("Bitte eine gültige Zahl eingeben.")

def apply_filters():
    accounts = load_accounts()
    if not accounts:
        print("Keine Accounts vorhanden.")
        return
    for email, settings in accounts.items():
        print(f"Verbinde mit {email}...")
        try:
            password = fernet.decrypt(settings["password"].encode()).decode()
            if settings["encryption"] == "ssl":
                mail = imaplib.IMAP4_SSL(settings["host"], settings["port"])
            else:
                mail = imaplib.IMAP4(settings["host"], settings["port"])
                if settings["encryption"] == "starttls":
                    mail.starttls()
            mail.login(email, password)
            mail.select("INBOX")

            global_filters = load_filters()
            account_filters = load_filters(email)

            all_filters = global_filters + account_filters

            for f in all_filters:
                if f["field"] not in ["from", "subject", "body"]:
                    continue
                search_criterion = f'(TEXT "{f["contains"]}")'
                result, data = mail.search(None, search_criterion)
                if result == "OK":
                    for num in data[0].split():
                        mail.copy(num, f["action"])
                        mail.store(num, "+FLAGS", "\\Deleted")
                    mail.expunge()
            mail.logout()
            print(f"Filter für {email} angewendet.")
        except Exception as e:
            print("Fehler:", e)

def hauptmenue():
    ensure_dirs()
    while True:
        print("\n--- pkmailfilter ---")
        print("1. Account hinzufügen")
        print("2. Accounts auflisten")
        print("3. Account löschen")
        print("4. Globalen Filter anzeigen")
        print("5. Globalen Filter hinzufügen")
        print("6. Globalen Filter löschen")
        print("7. Account-Filter anzeigen")
        print("8. Account-Filter hinzufügen")
        print("9. Account-Filter löschen")
        print("10. Filter ausführen")
        print("0. Beenden")
        choice = input("> ")

        if choice == "1":
            add_account()
        elif choice == "2":
            list_accounts()
        elif choice == "3":
            delete_account()
        elif choice == "4":
            list_filters()
        elif choice == "5":
            add_filter()
        elif choice == "6":
            delete_filter()
        elif choice == "7":
            list_accounts()
            acc = input("Für welchen Account?: ")
            list_filters(acc)
        elif choice == "8":
            list_accounts()
            acc = input("Für welchen Account?: ")
            add_filter(acc)
        elif choice == "9":
            list_accounts()
            acc = input("Für welchen Account?: ")
            delete_filter(acc)
        elif choice == "10":
            apply_filters()
        elif choice == "0":
            break
        else:
            print("Ungültige Eingabe.")

if __name__ == "__main__":
    import sys
    ensure_dirs()
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_filters()
    else:
        hauptmenue()
