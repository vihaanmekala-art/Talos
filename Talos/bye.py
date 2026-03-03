import json
import sqlite3
def create_sql():
    conn = sqlite3.connect('talos.db', check_same_thread=False)
    return conn

def migrate_json_to_sql():
    # 1. Open the old JSON file
    try:
        with open('secret.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("No secret.json found to migrate.")
        return

    # 2. Connect to your new DB
    conn = create_sql()
    cursor = conn.cursor()

    # 3. Loop through the JSON users and insert them
    usernames_dict = data.get('usernames', {})
    
    for username, info in usernames_dict.items():
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, name, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (username, info['name'], info['email'], info['password']))
        except Exception as e:
            print(f"Could not migrate {username}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete! Your users are now in talos.db.")