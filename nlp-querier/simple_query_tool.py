#!/usr/bin/env python3
"""
Simple SQLite Query Interface for FCFP Database
Perfect for free VS Code usage without extensions
"""

import sqlite3
import pandas as pd

class SimpleQueryTool:
    def __init__(self):
        self.db_path = 'output/fcfp_analytics.db'
        
    def run_query(self, sql):
        """Execute a SQL query and display results nicely"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            print(f"📝 Query: {sql}")
            print("=" * 80)
            
            if len(df) > 0:
                print(f"📊 Results ({len(df)} rows):")
                print(df.to_string(index=False, max_rows=20))
                if len(df) > 20:
                    print(f"... showing first 20 of {len(df)} total rows")
            else:
                print("No results found")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    def show_quick_examples(self):
        """Show some quick example queries"""
        print("🚀 Quick Example Queries for FCFP Database")
        print("=" * 60)
        
        examples = [
            ("1. Count customers by risk segment", 
             "SELECT risk_segment, COUNT(*) as customers FROM dim_account GROUP BY risk_segment"),
             
            ("2. Recent high-value transactions",
             "SELECT txn_id, amount, channel, txn_dt FROM fact_transactions WHERE amount > 5000 ORDER BY txn_dt DESC LIMIT 5"),
             
            ("3. Alerts by risk level",
             "SELECT risk_level, COUNT(*) as alert_count FROM fact_alerts GROUP BY risk_level ORDER BY alert_count DESC"),
             
            ("4. Monthly transaction volume",
             "SELECT strftime('%Y-%m', txn_dt) as month, COUNT(*) as transactions, SUM(amount) as total_amount FROM fact_transactions GROUP BY month ORDER BY month DESC LIMIT 6"),
             
            ("5. High-risk customers with alerts",
             "SELECT c.customer_name, c.segment, COUNT(a.alert_id) as alerts FROM dim_customer c JOIN fact_alerts a ON c.customer_id = a.customer_id WHERE c.segment = 'Corporate' GROUP BY c.customer_id, c.customer_name, c.segment ORDER BY alerts DESC LIMIT 10")
        ]
        
        for desc, sql in examples:
            print(f"\n{desc}:")
            self.run_query(sql)

def main():
    tool = SimpleQueryTool()
    
    print("🏦 FCFP Analytics - Simple Query Tool")
    print("=" * 60)
    print("Choose an option:")
    print("1. Run example queries")
    print("2. Enter custom query")
    print("3. Show table info")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        tool.show_quick_examples()
    elif choice == "2":
        print("\n📝 Enter your SQL query (or 'quit' to exit):")
        while True:
            query = input("SQL> ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if query:
                tool.run_query(query)
    elif choice == "3":
        # Show table structure
        queries = [
            ("Tables Overview", "SELECT name FROM sqlite_master WHERE type='table'"),
            ("Customer table structure", "PRAGMA table_info(dim_customer)"),
            ("Account table structure", "PRAGMA table_info(dim_account)"),
            ("Transaction table structure", "PRAGMA table_info(fact_transactions)"),
            ("Alert table structure", "PRAGMA table_info(fact_alerts)")
        ]
        for desc, sql in queries:
            print(f"\n{desc}:")
            tool.run_query(sql)

if __name__ == "__main__":
    main()