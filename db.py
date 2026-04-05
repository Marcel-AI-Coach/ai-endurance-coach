import os
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Lädt lokale Umgebungsvariablen aus einer .env-Datei
# Auf Railway ist das meist nicht nötig, schadet aber nicht
load_dotenv()


def get_db_connection():
    """
    Erstellt eine Verbindung zur PostgreSQL-Datenbank.

    Railway stellt meist eine DATABASE_URL als Umgebungsvariable bereit.
    Beispiel:
    postgresql://user:password@host:port/dbname
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL wurde nicht gefunden.")

    conn = connect(database_url, row_factory=dict_row)
    return conn
