import sqlite3
import json

conn = sqlite3.connect('inventario.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get schema for PCs, users and tasks tables
tables = ['pcs', 'users', 'usuarios', 'tareas', 'tasks']
for table in tables:
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
    row = cursor.fetchone()
    if row:
        print(f"--- Table: {row['name']} ---")
        print(row['sql'])

