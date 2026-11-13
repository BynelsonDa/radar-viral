"""Shared database configuration for the web app and collector."""
import os
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def connect():
    conn = mysql.connector.connect(host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '3306')), database=os.getenv('DB_NAME', 'radar_viral'),
        user=os.getenv('DB_USER', 'radar'), password=os.getenv('DB_PASSWORD', ''),
        connection_timeout=10)
    conn.cmd_query("SET time_zone = '+00:00'")
    return conn


def initialize():
    conn = connect()
    try:
        with conn.cursor() as cursor:
            schema = Path(__file__).resolve().parents[1] / 'sql/schema.sql'
            for statement in schema.read_text().split(';'):
                statement = statement.strip()
                if statement and not statement.upper().startswith(('CREATE DATABASE', 'USE ')):
                    cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    initialize()
