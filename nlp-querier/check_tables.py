import sqlite3

# Connect to database
conn = sqlite3.connect('output/fcfp_analytics.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in fcfp_analytics.db:")
print("=" * 40)

for table in tables:
    table_name = table[0]
    # Get row count for each table
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  • {table_name:<20} ({count:,} rows)")

# Check a few sample records from customers and sales to see what they contain
print("\n" + "=" * 40)
print("Sample from 'customers' table:")
try:
    cursor.execute("SELECT * FROM customers LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row}")
except Exception as e:
    print(f"  Error: {e}")

print("\nSample from 'sales' table:")
try:
    cursor.execute("SELECT * FROM sales LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()