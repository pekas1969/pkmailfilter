import os
import json
import getpass
import argparse
import imaplib
import email
from email.header import decode_header
from cryptography.fernet import Fernet

CONFIG_DIR = "config"
FILTERS_DIR = "filters"
FERNET_KEY_FILE = os.path.join(CONFIG_DIR, "fernet.key")
ACCOUNTS_FILE = "accounts.json"
GLOBAL_FILTER_FILE = os.path.join(FILTERS_DIR, "global.json")
DEFAULT_FILTER = [
    "contain:from",
    "move_to:Trash",
    "filter:\"Casino.com\""
]


def ensure_directories():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(FILTERS_DIR, exist_ok=True)


def get_fernet():
    if not os.path.exists(FERNET_KEY_FILE):
        key = Fernet.generate_key()
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)


def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)


def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def email_to_filename(email):
    return email.replace("@", "_").replace(".", "_") + ".json"


def create_account():
    f = get_fernet()
    email = input("E-Mail-Adresse: ")
    host = input("IMAP-Host: ")
    port = input("Port [993]: ") or "993"
    encryption = input("Verschlüsselung [SSL]: ") or "SSL"
    password = getpass.getpass("Passwort: ")
    encrypted_pw = f.encrypt(password.encode()).decode()

    account = {
        "email": email,
        "host": host,
        "port": port,
        "encryption": encryption,
        "password": encrypted_pw
    }

    accounts = load_accounts()
    accounts.append(account)
    save_accounts(accounts)

    filename = email_to_filename(email)
    filepath = os.path.join(FILTERS_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump(DEFAULT_FILTER, f, indent=2)
    print("✅ Account wurde gespeichert.")


def delete_account():
    accounts = load_accounts()
    if not accounts:
        print("❌ Keine Accounts vorhanden.")
        return

    print("\n📧 Verfügbare Accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account['email']}")
    choice = input("Wähle einen Account zum Löschen (Zahl): ")
    try:
        index = int(choice) - 1
        removed = accounts.pop(index)
        save_accounts(accounts)
        print("✅ Account gelöscht:", removed['email'])
    except (ValueError, IndexError):
        print("❌ Ungültige Auswahl.")


def list_accounts():
    accounts = load_accounts()
    if not accounts:
        print("❌ Keine Accounts vorhanden.")
        return
    print("\n📧 Verfügbare Accounts:")
    for i, account in enumerate(accounts, 1):
        if isinstance(account, dict) and 'email' in account:
            print(f"{i}. {account['email']}")
        else:
            print(f"{i}. [Ungültiger Eintrag: {account}]")


def show_global_filters():
    if not os.path.exists(GLOBAL_FILTER_FILE):
        print("🌐 Keine globale Filterdatei vorhanden.")
        return
    with open(GLOBAL_FILTER_FILE, "r") as f:
        filters = json.load(f)
    print("\n🌐 Globale Filter:")
    for i in range(0, len(filters), 3):
        try:
            filter_type = filters[i].split(":")[1]
            move_to = filters[i + 1].split(":")[1]
            terms = filters[i + 2].split(":", 1)[1]
            terms_clean = terms.replace('"', '').split(",")
            print(f"{filter_type}: {', '.join(terms_clean)} → {move_to}")
        except:
            continue


def show_account_filters():
    accounts = load_accounts()
    if not accounts:
        print("❌ Keine Accounts vorhanden.")
        return

    print("\n📧 Verfügbare Accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account['email']}")
    choice = input("Wähle einen Account (Zahl): ")

    try:
        index = int(choice) - 1
        account = accounts[index]
    except (ValueError, IndexError):
        print("❌ Ungültige Auswahl.")
        return

    filename = email_to_filename(account["email"])
    path = os.path.join(FILTERS_DIR, filename)
    if not os.path.exists(path):
        print("❌ Keine Filterdatei für diesen Account vorhanden.")
        return

    with open(path, "r") as f:
        raw_filters = json.load(f)

    print(f"\n📂 Filter für {account['email']}:")
    for i in range(0, len(raw_filters), 3):
        try:
            filter_type = raw_filters[i].split(":")[1]
            move_to = raw_filters[i + 1].split(":")[1]
            terms = raw_filters[i + 2].split(":", 1)[1]
            terms_clean = terms.replace('"', '').split(",")
            print(f"{filter_type}: {', '.join(terms_clean)} → {move_to}")
        except Exception as e:
            print("⚠️ Fehler beim Lesen eines Filters:", e)


def apply_filters():
    print("⚙️  Filterausführung gestartet...")
    accounts = load_accounts()
    fernet = get_fernet()

    for account in accounts:
        email_addr = account['email']
        password = fernet.decrypt(account['password_enc'].encode()).decode()

        print(f"🔐 Verbinde mit {email_addr}...")

        try:
            mail = imaplib.IMAP4_SSL(account['host'], int(account['port']))
            mail.login(email_addr, password)
            mail.select("inbox")

            filename = email_to_filename(email_addr)
            filter_path = os.path.join(FILTERS_DIR, filename)
            with open(filter_path, "r") as f:
                filters = json.load(f)

            for i in range(0, len(filters), 3):
                try:
                    condition = filters[i].split(":")[1]
                    action = filters[i + 1].split(":")[1]
                    terms = filters[i + 2].split(":", 1)[1].replace('"', '').split(",")

                    for term in terms:
                        criterion = None
                        if condition == "from":
                            criterion = f'FROM "{term.strip()}"'
                        elif condition == "subject":
                            criterion = f'SUBJECT "{term.strip()}"'
                        elif condition == "body":
                            criterion = f'TEXT "{term.strip()}"'

                        if criterion:
                            status, data = mail.search(None, criterion)
                            if status == 'OK':
                                for num in data[0].split():
                                    mail.store(num, '+X-GM-LABELS', action)
                                    mail.store(num, '+FLAGS', '\\Deleted')
                                    print(f"✉️  E-Mail {num.decode()} → {action}")

                except Exception as e:
                    print("⚠️ Fehler beim Anwenden eines Filters:", e)

            mail.expunge()
            mail.logout()
        except Exception as e:
            print(f"❌ Fehler bei {email_addr}: {e}")


def main():
    ensure_directories()
    fernet = get_fernet()

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--apply", action="store_true", help="Filter jetzt ausführen")
    args = parser.parse_args()

    if args.apply:
        apply_filters()
        return

    if not os.path.exists(GLOBAL_FILTER_FILE):
        with open(GLOBAL_FILTER_FILE, "w") as f:
            json.dump(DEFAULT_FILTER, f, indent=2)

    while True:
        print("\n📥 pkmailfilter2 Menü")
        print("1. Account anlegen")
        print("2. Account löschen")
        print("3. Accounts anzeigen")
        print("4. Globale Filter anzeigen")
        print("5. Account-Filter anzeigen")
        print("6. Filter ausführen")
        print("7. Beenden")
        choice = input("> ")

        if choice == "1":
            create_account()
        elif choice == "2":
            delete_account()
        elif choice == "3":
            list_accounts()
        elif choice == "4":
            show_global_filters()
        elif choice == "5":
            show_account_filters()
        elif choice == "6":
            apply_filters()
        elif choice == "7":
            break
        else:
            print("❌ Ungültige Eingabe.")


if __name__ == "__main__":
    main()
