#!/usr/bin/env python3
"""
Simple test for transaction behavior queries without full agent workflow.
"""

import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_transaction_queries():
    """Test transaction behavior queries directly against the database."""
    
    db_path = "output/fcfp_analytics.db"
    
    queries = [
        {
            "name": "Average transaction amount by channel for high-risk customers",
            "sql": """
                SELECT 
                    ft.channel,
                    ROUND(AVG(ft.amount), 2) as avg_amount,
                    COUNT(ft.txn_id) as transaction_count
                FROM fact_transactions ft
                JOIN dim_customer dc ON ft.customer_id = dc.customer_id
                JOIN dim_account da ON ft.account_id = da.account_id
                WHERE UPPER(da.risk_segment) = 'HIGH'
                GROUP BY ft.channel
                ORDER BY avg_amount DESC
            """
        },
        {
            "name": "Online vs Branch/ATM transaction behavior",
            "sql": """
                SELECT 
                    ft.channel,
                    COUNT(ft.txn_id) as transaction_count,
                    ROUND(AVG(ft.amount), 2) as avg_amount,
                    ROUND(AVG(ft.risk_score), 2) as avg_risk_score,
                    SUM(CASE WHEN ft.is_flagged = 1 THEN 1 ELSE 0 END) as flagged_count,
                    ROUND(
                        CAST(SUM(CASE WHEN ft.is_flagged = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ft.txn_id), 
                        2
                    ) as flagged_percentage
                FROM fact_transactions ft
                GROUP BY ft.channel
                ORDER BY transaction_count DESC
            """
        },
        {
            "name": "Country with highest flagged transaction ratio",
            "sql": """
                SELECT 
                    ft.country,
                    COUNT(ft.txn_id) as total_transactions,
                    SUM(CASE WHEN ft.is_flagged = 1 THEN 1 ELSE 0 END) as flagged_transactions,
                    ROUND(
                        CAST(SUM(CASE WHEN ft.is_flagged = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ft.txn_id), 
                        2
                    ) as flagged_percentage
                FROM fact_transactions ft
                WHERE ft.country IS NOT NULL AND ft.country != ''
                GROUP BY ft.country
                HAVING COUNT(ft.txn_id) >= 10  -- Only countries with meaningful transaction volume
                ORDER BY flagged_percentage DESC, total_transactions DESC
            """
        }
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        
        for i, query_info in enumerate(queries, 1):
            logger.info(f"\n🔍 TEST QUERY {i}: {query_info['name']}")
            logger.info("-" * 60)
            
            try:
                df = pd.read_sql_query(query_info['sql'], conn)
                
                logger.info(f"✅ Query executed successfully")
                logger.info(f"📊 Results: {len(df)} rows")
                
                if len(df) > 0:
                    logger.info(f"📝 Columns: {list(df.columns)}")
                    logger.info(f"📋 Sample results:")
                    for idx, row in df.head(3).iterrows():
                        logger.info(f"  Row {idx+1}: {dict(row)}")
                    if len(df) > 3:
                        logger.info(f"  ... ({len(df)-3} more rows)")
                else:
                    logger.info("📋 No results returned")
                    
            except Exception as e:
                logger.error(f"❌ Query failed: {e}")
        
        conn.close()
        logger.info("\n🏁 Transaction behavior queries test completed")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_transaction_queries()