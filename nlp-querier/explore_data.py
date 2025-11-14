#!/usr/bin/env python3
"""
Quick data explorer to understand the database structure and content.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sqlite_db import SQLiteManager
import pandas as pd

def explore_data():
    """Quick data exploration tool."""
    print("=== Quick Data Explorer ===")
    
    db = SQLiteManager()
    
    print("\n📋 DATABASE OVERVIEW:")
    print("-" * 40)
    
    # Get all tables
    tables_result = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    if tables_result['success']:
        tables = [row['name'] for row in tables_result['rows']]
        print(f"Tables: {', '.join(tables)}")
    
    for table in ['sales', 'customers']:
        print(f"\n📊 TABLE: {table.upper()}")
        print("-" * 40)
        
        # Get table info
        info_result = db.execute_query(f"PRAGMA table_info({table})")
        if info_result['success']:
            print("Columns:")
            for col in info_result['rows']:
                print(f"  - {col['name']} ({col['type']})")
        
        # Get row count
        count_result = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
        if count_result['success']:
            count = count_result['rows'][0]['count']
            print(f"Total rows: {count}")
        
        # Show sample data
        sample_result = db.execute_query(f"SELECT * FROM {table} LIMIT 3")
        if sample_result['success']:
            df = pd.DataFrame(sample_result['rows'])
            print("Sample data:")
            print(df.to_string())
    
    print(f"\n🔢 USEFUL QUERIES TO TEST:")
    print("-" * 40)
    
    useful_queries = [
        ("Total Revenue", "SELECT SUM(total_amount) as total_revenue FROM sales"),
        ("Sales Count by Region", "SELECT region, COUNT(*) as count FROM sales GROUP BY region"),
        ("Top 3 Sales", "SELECT * FROM sales ORDER BY total_amount DESC LIMIT 3"),
        ("Average Sale Amount", "SELECT AVG(total_amount) as avg_sale FROM sales"),
        ("Sales by Product", "SELECT product, SUM(total_amount) as revenue FROM sales GROUP BY product"),
        ("Customer Count", "SELECT COUNT(*) as customer_count FROM customers"),
        ("Latest Sales", "SELECT * FROM sales ORDER BY date DESC LIMIT 5"),
        ("Sales with Customer Info", """
            SELECT s.*, c.name, c.email 
            FROM sales s 
            JOIN customers c ON s.id = c.customer_id 
            LIMIT 5
        """)
    ]
    
    for name, query in useful_queries:
        print(f"\n{name}:")
        print(f"  {query.strip()}")
        
        # Execute and show result
        result = db.execute_query(query.strip())
        if result['success']:
            df = pd.DataFrame(result['rows'])
            if len(df) == 1 and len(df.columns) == 1:
                # Single value result
                print(f"  Result: {df.iloc[0, 0]}")
            elif len(df) <= 5:
                # Small result set
                print(f"  Results ({len(df)} rows):")
                for _, row in df.iterrows():
                    print(f"    {dict(row)}")
            else:
                print(f"  Results: {len(df)} rows (showing first 3)")
                for i, (_, row) in enumerate(df.head(3).iterrows()):
                    print(f"    {dict(row)}")

if __name__ == "__main__":
    explore_data()