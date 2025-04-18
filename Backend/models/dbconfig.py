import psycopg2, psycopg2.extras
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
DB_URL = os.getenv("DB_URL")

def db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"Error: {e}")
        return None, None