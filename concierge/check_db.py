import sqlite3
import os

# Get the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the SQLite database file within the concierge folder
db_path = os.path.join(script_dir,  'fitness_wellness.db')
# Debug print statements
print(f"Script directory: {script_dir}")
print(f"Database path: {db_path}")


def print_table_data(cursor, table_name):
    print(f"\nData from {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Print data from all relevant tables
tables = ['workouts', 'meals', 'mental_health', 'goals']
for table in tables:
    print_table_data(cursor, table)

# Close the database connection
conn.close()
