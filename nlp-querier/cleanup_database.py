import sqlite3

# Connect to database
conn = sqlite3.connect('output/fcfp_analytics.db')
cursor = conn.cursor()

print("🧹 Cleaning up FCFP Analytics Database...")
print("=" * 50)

# Remove the test tables that don't belong
test_tables = ['customers', 'sales']

for table in test_tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✅ Removed test table: {table}")
    except Exception as e:
        print(f"❌ Error removing {table}: {e}")

# Commit changes
conn.commit()

# Verify the cleanup
print("\n📊 Remaining tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    if table_name != 'sqlite_sequence':  # Skip system table
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  • {table_name:<20} ({count:,} rows)")

conn.close()
print("\n🎯 Database cleanup completed! Now contains only FCFP data.")