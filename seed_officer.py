import mysql.connector
from werkzeug.security import generate_password_hash

OFFICER_USERNAME = "officer1"
OFFICER_PASSWORD = "Officer@123"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nila252006",   # change this to your real MySQL password
    database="loan_db",
)
cursor = conn.cursor()

cursor.execute("SELECT id FROM users WHERE username=%s", (OFFICER_USERNAME,))
if cursor.fetchone():
    print(f"Officer '{OFFICER_USERNAME}' already exists — nothing to do.")
else:
    hashed = generate_password_hash(OFFICER_PASSWORD)
    cursor.execute(
        "INSERT INTO users(username, password, role) VALUES(%s, %s, 'officer')",
        (OFFICER_USERNAME, hashed),
    )
    conn.commit()
    print(f"Officer account created -> username: {OFFICER_USERNAME}  password: {OFFICER_PASSWORD}")

cursor.close()
conn.close()