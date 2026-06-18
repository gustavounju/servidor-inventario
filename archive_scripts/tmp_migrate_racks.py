from database.db_core import init_db
print("Running init_db to apply migrations and seed racks...")
init_db()
print("Done.")
