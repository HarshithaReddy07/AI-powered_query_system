import os
import pyodbc

# Use env vars only — no host or passwords in the repo
server = os.environ.get("MSSQL_SERVER")
database = os.environ.get("MSSQL_DATABASE")
username = os.environ.get("MSSQL_USERNAME")
password = os.environ.get("MSSQL_PASSWORD")
missing = [n for n, v in [
    ("MSSQL_SERVER", server),
    ("MSSQL_DATABASE", database),
    ("MSSQL_USERNAME", username),
    ("MSSQL_PASSWORD", password),
] if not v]
if missing:
    print("Set:", ", ".join(missing))
    print("Example: export MSSQL_SERVER=yourhost MSSQL_DATABASE=football_db MSSQL_USERNAME=admin MSSQL_PASSWORD=...")
    exit(1)

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")
    row = cursor.fetchone()
    print("Connected to:", row[0])
    conn.close()
except Exception as e:
    print("Connection failed:", e)
    err = str(e).lower()
    if "login failed" in err or "18456" in err:
        print("\n→ Authentication failed: check username and password for your RDS instance.")
        print("  In AWS RDS console: your DB’s master username and the password you set.")