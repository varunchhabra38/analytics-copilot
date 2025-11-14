# setup_fcfp_database.py
# Financial Compliance and Fraud Prevention (FCFP) Database Setup
# Creates a comprehensive SQLite database with customers, accounts, transactions, and alerts

import sqlite3
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import os

# -------------------------
# CONFIG (edit these only)
# -------------------------
DB_FILE         = "output/fcfp_analytics.db"    # The name of the SQLite database file
N_CUSTOMERS     = 200           # ~200 customers (increased for more analytics data)
ACCTS_PER_C     = (2, 6)        # 2-6 accounts per customer -> ~600-800 accounts total
N_TRANSACTIONS  = 5000          # fact_transactions rows (increased for analytics)
N_ALERTS_TARGET = 800           # fact_alerts target rows

START_DT = date(2024, 1, 1)
END_DT   = date(2025, 11, 30)   # Up to current date

# Category universes - Banking/Financial focus
COUNTRIES_EU   = ["NL","DE","FR","BE","IT","ES","PL","CZ","HU","AT","IE","PT","GR","SK","SI","LU","LT","LV","EE"]
CURRENCIES     = ["EUR","USD","GBP","CHF","JPY"]
CHANNELS       = ["ONLINE","ATM","BRANCH","POS","MOBILE","WIRE"]
SEGMENTS       = ["RETAIL","SME","CORP","PRIVATE"]
KYC_STATUS     = ["PASSED","REVIEW","FAILED","EXPIRED"]
ACC_TYPES      = ["CURRENT","SAVINGS","CREDIT_CARD","BUSINESS","INVESTMENT"]
ACC_STATUS     = ["ACTIVE","DORMANT","CLOSED","SUSPENDED"]
RISK_SEG       = ["LOW","MEDIUM","HIGH","CRITICAL"]
RISK_LEVEL     = ["LOW","MEDIUM","HIGH","CRITICAL"]
ALERT_TYPES    = ["SANCTIONS","TM_RULE","NAME_SCREEN","PEP_MATCH","AML_SUSPICION","LARGE_CASH","FRAUD_PATTERN"]

# Weighted distributions (more realistic banking patterns)
W_SEGMENTS     = [0.75, 0.18, 0.05, 0.02]  # Most retail, some SME, few corporate/private
W_KYC_STATUS   = [0.88, 0.08, 0.03, 0.01]  # Most passed KYC
W_ACC_TYPES    = [0.45, 0.30, 0.15, 0.08, 0.02]  # Current accounts dominant
W_ACC_STATUS   = [0.85, 0.10, 0.04, 0.01]  # Most active accounts
W_ACC_RISKSEG  = [0.65, 0.25, 0.09, 0.01]  # Most low risk
W_CHANNELS     = [0.45, 0.15, 0.10, 0.20, 0.08, 0.02]  # Online and POS dominant
W_ALERT_TYPES  = [0.20, 0.25, 0.15, 0.05, 0.15, 0.10, 0.10]  # Varied alert types

# Correlations / business rules
PEP_RATE                 = 0.015   # 1.5% PEP rate (realistic)
FLAGGED_BASE_RATE        = 0.06    # 6% base flagged transaction probability
FLAGGED_BOOST_HIGH_ACC   = 0.08    # +8% for high-risk accounts
FLAGGED_BOOST_Q4         = 0.03    # +3% in Q4 (holiday activity)
FLAGGED_BOOST_ATM        = 0.02    # +2% for ATM (cash transactions)
FLAGGED_BOOST_WIRE       = 0.05    # +5% for wire transfers
HIGH_RISK_ALERT_BUMP_AMT = 10000.0 # Alerts over €10k more likely HIGH risk

# Seasonality bias months (more financial activity)
SEASONAL_MONTHS = [3, 6, 9, 12]  # Quarter ends
SEASONAL_BIAS_P = 0.20  # 20% of events biased into quarter-end months

# Amount distribution (more realistic banking amounts)
LOGN_MEAN = 4.5  # Higher mean for realistic transaction amounts
LOGN_SIG  = 1.2  # Higher variance
SPIKE_P   = 0.008  # Less frequent but larger spikes
SPIKE_X   = 50.0   # Bigger spikes
AMOUNT_SCALE = 1.0  # Scale factor

# Reproducibility
Faker.seed(42)
random.seed(42)
np.random.seed(42)
fake = Faker(['en_US', 'de_DE', 'fr_FR', 'nl_NL'])  # Multi-locale for European names

print("🏦 FINANCIAL COMPLIANCE AND FRAUD PREVENTION DATABASE SETUP")
print("=" * 70)

# -------------------------
# Part 1: Schema Definition
# -------------------------
def create_database_schema(conn):
    """Creates the financial analytics database tables and indexes."""
    cursor = conn.cursor()

    sql_schema = """
    PRAGMA foreign_keys = ON;

    -- Drop existing tables to start fresh on each run
    DROP TABLE IF EXISTS fact_alerts;
    DROP TABLE IF EXISTS fact_transactions;
    DROP TABLE IF EXISTS dim_account;
    DROP TABLE IF EXISTS dim_customer;
    DROP TABLE IF EXISTS dim_calendar;

    -- Customer Dimension - Core customer information
    CREATE TABLE dim_customer (
      customer_id      TEXT PRIMARY KEY,
      customer_name    TEXT NOT NULL,
      segment          TEXT CHECK (segment IN ('RETAIL','SME','CORP','PRIVATE')) NOT NULL,
      onboarding_dt    DATE NOT NULL,
      kyc_status       TEXT CHECK (kyc_status IN ('PASSED','REVIEW','FAILED','EXPIRED')) NOT NULL,
      is_pep           INTEGER CHECK (is_pep IN (0,1)) NOT NULL,
      residence_country TEXT NOT NULL,
      email            TEXT,
      phone            TEXT,
      date_of_birth    DATE,
      created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Account Dimension - Customer accounts
    CREATE TABLE dim_account (
      account_id    TEXT PRIMARY KEY,
      customer_id   TEXT NOT NULL,
      account_name  TEXT NOT NULL,
      account_type  TEXT CHECK (account_type IN ('CURRENT','SAVINGS','CREDIT_CARD','BUSINESS','INVESTMENT')) NOT NULL,
      opened_dt     DATE NOT NULL,
      status        TEXT CHECK (status IN ('ACTIVE','DORMANT','CLOSED','SUSPENDED')) NOT NULL,
      risk_segment  TEXT CHECK (risk_segment IN ('LOW','MEDIUM','HIGH','CRITICAL')) NOT NULL,
      balance       REAL DEFAULT 0.0,
      currency      TEXT DEFAULT 'EUR',
      FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id)
    );

    -- Calendar Dimension - Time intelligence
    CREATE TABLE dim_calendar (
      dt         DATE PRIMARY KEY,
      day_name   TEXT NOT NULL,
      month      INTEGER NOT NULL,
      month_name TEXT NOT NULL,
      quarter    TEXT NOT NULL,
      year       INTEGER NOT NULL,
      is_weekend INTEGER CHECK (is_weekend IN (0,1)) NOT NULL,
      is_holiday INTEGER CHECK (is_holiday IN (0,1)) DEFAULT 0
    );

    -- Transaction Facts - Core transactional data
    CREATE TABLE fact_transactions (
      txn_id           TEXT PRIMARY KEY,
      customer_id      TEXT NOT NULL,
      account_id       TEXT NOT NULL,
      txn_dt           DATE NOT NULL,
      txn_time         TIME,
      amount           REAL NOT NULL,
      currency         TEXT NOT NULL DEFAULT 'EUR',
      country          TEXT NOT NULL,
      channel          TEXT CHECK (channel IN ('ONLINE','ATM','BRANCH','POS','MOBILE','WIRE')) NOT NULL,
      transaction_type TEXT,
      merchant_name    TEXT,
      is_flagged       INTEGER CHECK (is_flagged IN (0,1)) NOT NULL DEFAULT 0,
      risk_score       REAL,
      created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
      FOREIGN KEY (account_id) REFERENCES dim_account(account_id),
      FOREIGN KEY (txn_dt) REFERENCES dim_calendar(dt)
    );

    -- Alert Facts - Compliance and fraud alerts
    CREATE TABLE fact_alerts (
      alert_id         TEXT PRIMARY KEY,
      customer_id      TEXT NOT NULL,
      account_id       TEXT,
      alert_dt         DATE NOT NULL,
      alert_time       TIME,
      region           TEXT NOT NULL,
      country          TEXT NOT NULL,
      risk_level       TEXT CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')) NOT NULL,
      alert_type       TEXT CHECK (alert_type IN ('SANCTIONS','TM_RULE','NAME_SCREEN','PEP_MATCH','AML_SUSPICION','LARGE_CASH','FRAUD_PATTERN')) NOT NULL,
      alert_status     TEXT DEFAULT 'OPEN',
      txn_count        INTEGER,
      amount           REAL,
      channel          TEXT CHECK (channel IN ('ONLINE','ATM','BRANCH','POS','MOBILE','WIRE')),
      description      TEXT,
      assigned_to      TEXT,
      resolved_dt      DATE,
      created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
      FOREIGN KEY (alert_dt) REFERENCES dim_calendar(dt)
    );

    -- Performance Indexes
    CREATE INDEX idx_transactions_customer_dt ON fact_transactions (customer_id, txn_dt);
    CREATE INDEX idx_transactions_account_dt ON fact_transactions (account_id, txn_dt);
    CREATE INDEX idx_transactions_amount ON fact_transactions (amount);
    CREATE INDEX idx_transactions_channel ON fact_transactions (channel);
    CREATE INDEX idx_transactions_flagged ON fact_transactions (is_flagged);
    
    CREATE INDEX idx_alerts_customer_dt ON fact_alerts (customer_id, alert_dt);
    CREATE INDEX idx_alerts_type_level ON fact_alerts (alert_type, risk_level);
    CREATE INDEX idx_alerts_status ON fact_alerts (alert_status);
    
    CREATE INDEX idx_customers_segment ON dim_customer (segment);
    CREATE INDEX idx_customers_kyc ON dim_customer (kyc_status);
    CREATE INDEX idx_customers_pep ON dim_customer (is_pep);
    
    CREATE INDEX idx_accounts_type ON dim_account (account_type);
    CREATE INDEX idx_accounts_status ON dim_account (status);
    CREATE INDEX idx_accounts_risk ON dim_account (risk_segment);
    """
    
    cursor.executescript(sql_schema)
    print("✅ Database schema and tables created successfully.")
    return True

# -------------------------
# Part 2: Data Generation
# -------------------------
def generate_data():
    """Generates comprehensive financial analytics data."""
    
    # Helper functions
    def rand_date():
        total_days = (END_DT - START_DT).days + 1
        return START_DT + timedelta(days=random.randint(0, total_days - 1))

    def seasonal_date():
        if random.random() < SEASONAL_BIAS_P:
            y = random.choice([2024, 2025])
            m = random.choice(SEASONAL_MONTHS)
            d = random.randint(1, 28)
            try:
                return date(y, m, d)
            except:
                return rand_date()
        return rand_date()

    def wchoice(items, weights):
        return random.choices(items, weights=weights, k=1)[0]

    def quarter_of(dt: date) -> str:
        return f"Q{((dt.month - 1)//3) + 1}"
        
    def generate_merchant_name():
        merchants = [
            "Amazon", "Google", "Apple", "Microsoft", "Netflix", "Spotify", 
            "Uber", "Airbnb", "McDonald's", "Starbucks", "Shell", "BP",
            "Albert Heijn", "IKEA", "H&M", "Zara", "MediaMarkt", "Bol.com",
            "ING Bank", "ABN AMRO", "Rabobank", "KLM", "NS", "PostNL"
        ]
        return random.choice(merchants)

    # Generate Calendar Dimension
    print("📅 Generating calendar dimension...")
    cal_days = pd.date_range(START_DT, END_DT, freq="D").date
    cal_data = []
    for d in cal_days:
        cal_data.append({
            "dt": d,
            "day_name": d.strftime("%A"),
            "month": d.month,
            "month_name": d.strftime("%B"),
            "quarter": quarter_of(d),
            "year": d.year,
            "is_weekend": 1 if d.weekday() >= 5 else 0,
            "is_holiday": 0  # Simplified - could add holiday logic
        })
    df_cal = pd.DataFrame(cal_data)

    # Generate Customer Dimension
    print("👥 Generating customer dimension...")
    customers = []
    for i in range(N_CUSTOMERS):
        segment = wchoice(SEGMENTS, W_SEGMENTS)
        onboarding_dt = START_DT - timedelta(days=random.randint(30, 2190))  # 0-6 years ago
        
        customers.append({
            "customer_id": f"CUST-{i:05d}",
            "customer_name": fake.name(),
            "segment": segment,
            "onboarding_dt": onboarding_dt,
            "kyc_status": wchoice(KYC_STATUS, W_KYC_STATUS),
            "is_pep": int(random.random() < PEP_RATE),
            "residence_country": random.choice(COUNTRIES_EU),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85)
        })
    
    df_cust = pd.DataFrame(customers)

    # Generate Account Dimension
    print("🏧 Generating account dimension...")
    accounts = []
    for _, customer in df_cust.iterrows():
        n_accts = random.randint(*ACCTS_PER_C)
        for j in range(n_accts):
            account_type = wchoice(ACC_TYPES, W_ACC_TYPES)
            opened_dt = customer["onboarding_dt"] + timedelta(days=random.randint(0, 365*2))
            
            # Generate realistic balances based on account type and segment
            if account_type == "SAVINGS":
                balance = random.uniform(1000, 50000)
            elif account_type == "CURRENT":
                balance = random.uniform(500, 15000)
            elif account_type == "BUSINESS":
                balance = random.uniform(10000, 500000)
            elif account_type == "INVESTMENT":
                balance = random.uniform(5000, 1000000)
            else:  # CREDIT_CARD
                balance = random.uniform(-5000, 0)
                
            accounts.append({
                "account_id": f"ACC-{customer['customer_id'].split('-')[1]}-{j:02d}",
                "customer_id": customer["customer_id"],
                "account_name": f"{account_type} Account {j+1}",
                "account_type": account_type,
                "opened_dt": opened_dt,
                "status": wchoice(ACC_STATUS, W_ACC_STATUS),
                "risk_segment": wchoice(RISK_SEG, W_ACC_RISKSEG),
                "balance": round(balance, 2),
                "currency": wchoice(CURRENCIES, [0.85, 0.08, 0.05, 0.015, 0.005])
            })
    
    df_acct = pd.DataFrame(accounts)

    # Generate Transaction Facts
    print("💳 Generating transaction facts...")
    active_acct_ids = df_acct[df_acct["status"] == "ACTIVE"]["account_id"].values
    if len(active_acct_ids) == 0:
        active_acct_ids = df_acct["account_id"].values  # Fallback to all accounts
    
    cust_for_acct = dict(zip(df_acct["account_id"], df_acct["customer_id"]))
    risk_for_acct = dict(zip(df_acct["account_id"], df_acct["risk_segment"]))
    type_for_acct = dict(zip(df_acct["account_id"], df_acct["account_type"]))

    # Get valid date range from calendar
    valid_dates = df_cal["dt"].values
    
    txn_types = ["PAYMENT", "WITHDRAWAL", "DEPOSIT", "TRANSFER", "PURCHASE", "REFUND", "FEE"]
    
    txn_rows = []
    for i in range(N_TRANSACTIONS):
        aid = random.choice(active_acct_ids)
        txn_dt = seasonal_date()
        
        # Ensure date exists in calendar
        if txn_dt not in valid_dates:
            txn_dt = random.choice(valid_dates)
        
        # Generate amount based on account type and transaction type
        base = np.random.lognormal(mean=LOGN_MEAN, sigma=LOGN_SIG)
        if random.random() < SPIKE_P: 
            base *= SPIKE_X
        
        # Adjust by account type
        account_type = type_for_acct[aid]
        if account_type == "BUSINESS":
            base *= 3  # Business accounts have larger transactions
        elif account_type == "INVESTMENT":
            base *= 5  # Investment accounts have largest transactions
            
        amount = round(base * AMOUNT_SCALE, 2)
        
        channel = wchoice(CHANNELS, W_CHANNELS)
        txn_type = random.choice(txn_types)
        
        # Calculate flagging probability
        p_flag = FLAGGED_BASE_RATE
        if risk_for_acct[aid] == "HIGH": 
            p_flag += FLAGGED_BOOST_HIGH_ACC
        elif risk_for_acct[aid] == "CRITICAL":
            p_flag += FLAGGED_BOOST_HIGH_ACC * 1.5
        if quarter_of(txn_dt) == "Q4": 
            p_flag += FLAGGED_BOOST_Q4
        if channel == "ATM": 
            p_flag += FLAGGED_BOOST_ATM
        elif channel == "WIRE":
            p_flag += FLAGGED_BOOST_WIRE
        
        is_flagged = int(random.random() < p_flag)
        risk_score = random.uniform(0.1, 0.9) if not is_flagged else random.uniform(0.7, 1.0)
        
        txn_rows.append({
            "txn_id": f"TXN-{i:07d}",
            "customer_id": cust_for_acct[aid],
            "account_id": aid,
            "txn_dt": txn_dt,
            "txn_time": fake.time(),
            "amount": amount,
            "currency": wchoice(CURRENCIES, [0.85, 0.08, 0.05, 0.015, 0.005]),
            "country": random.choice(COUNTRIES_EU),
            "channel": channel,
            "transaction_type": txn_type,
            "merchant_name": generate_merchant_name() if random.random() < 0.6 else None,
            "is_flagged": is_flagged,
            "risk_score": round(risk_score, 3)
        })
    
    df_txn = pd.DataFrame(txn_rows)

    # Generate Alert Facts
    print("🚨 Generating alert facts...")
    alerts = []
    
    # Generate alerts from flagged transactions
    flagged = df_txn[df_txn["is_flagged"] == 1]
    grp = flagged.groupby(["customer_id","txn_dt","channel"], sort=False)
    seq = 0
    
    for (cid, adt, ch), g in grp:
        # Ensure alert date exists in calendar
        if adt not in valid_dates:
            adt = random.choice(valid_dates)
            
        total_amt = float(g["amount"].sum())
        
        # Determine risk level based on amount
        if total_amt >= HIGH_RISK_ALERT_BUMP_AMT:
            rlevel = wchoice(RISK_LEVEL, [0.10, 0.20, 0.40, 0.30])  # More high/critical risk
        else:
            rlevel = wchoice(RISK_LEVEL, [0.50, 0.30, 0.15, 0.05])  # More low/medium risk
            
        atype = wchoice(ALERT_TYPES, W_ALERT_TYPES)
        
        # Get related account
        related_accounts = df_acct[df_acct["customer_id"] == cid]["account_id"].values
        related_account = random.choice(related_accounts) if len(related_accounts) > 0 else None
        
        alert_status = random.choice(["OPEN", "INVESTIGATING", "CLOSED", "FALSE_POSITIVE"])
        assigned_analysts = ["John Smith", "Sarah Johnson", "Mike Chen", "Lisa Anderson", "David Brown"]
        
        alerts.append({
            "alert_id": f"ALT-{seq:07d}",
            "customer_id": cid,
            "account_id": related_account,
            "alert_dt": adt,
            "alert_time": fake.time(),
            "region": "EU",
            "country": random.choice(COUNTRIES_EU),
            "risk_level": rlevel,
            "alert_type": atype,
            "alert_status": alert_status,
            "txn_count": int(g.shape[0]),
            "amount": round(total_amt, 2),
            "channel": ch,
            "description": f"{atype} alert triggered for {g.shape[0]} transactions totaling €{total_amt:,.2f}",
            "assigned_to": random.choice(assigned_analysts) if random.random() < 0.7 else None,
            "resolved_dt": adt + timedelta(days=random.randint(1, 30)) if alert_status in ["CLOSED", "FALSE_POSITIVE"] else None
        })
        seq += 1

    # Generate additional standalone alerts to reach target
    while len(alerts) < N_ALERTS_TARGET:
        cid = random.choice(df_cust["customer_id"].values)
        alert_dt = seasonal_date()
        
        # Ensure date exists in calendar
        if alert_dt not in valid_dates:
            alert_dt = random.choice(valid_dates)
            
        amt = float(np.random.lognormal(LOGN_MEAN, LOGN_SIG) * AMOUNT_SCALE * random.uniform(0.5, 3.0))
        
        # Get related account
        related_accounts = df_acct[df_acct["customer_id"] == cid]["account_id"].values
        related_account = random.choice(related_accounts) if len(related_accounts) > 0 else None
        
        atype = wchoice(ALERT_TYPES, [0.30, 0.20, 0.15, 0.10, 0.15, 0.05, 0.05])
        rlevel = wchoice(RISK_LEVEL, [0.45, 0.35, 0.15, 0.05])
        alert_status = random.choice(["OPEN", "INVESTIGATING", "CLOSED", "FALSE_POSITIVE"])
        assigned_analysts = ["John Smith", "Sarah Johnson", "Mike Chen", "Lisa Anderson", "David Brown"]
        
        alerts.append({
            "alert_id": f"ALT-{seq:07d}",
            "customer_id": cid,
            "account_id": related_account,
            "alert_dt": alert_dt,
            "alert_time": fake.time(),
            "region": "EU", 
            "country": random.choice(COUNTRIES_EU),
            "risk_level": rlevel,
            "alert_type": atype,
            "alert_status": alert_status,
            "txn_count": random.randint(1, 5),
            "amount": round(amt, 2),
            "channel": wchoice(CHANNELS, W_CHANNELS),
            "description": f"{atype} alert - automated detection",
            "assigned_to": random.choice(assigned_analysts) if random.random() < 0.7 else None,
            "resolved_dt": alert_dt + timedelta(days=random.randint(1, 30)) if alert_status in ["CLOSED", "FALSE_POSITIVE"] else None
        })
        seq += 1
    
    df_alert = pd.DataFrame(alerts)

    print("✅ Comprehensive financial analytics data generated successfully.")
    print(f"   📊 Generated {len(df_cust):,} customers")
    print(f"   🏧 Generated {len(df_acct):,} accounts") 
    print(f"   💳 Generated {len(df_txn):,} transactions")
    print(f"   🚨 Generated {len(df_alert):,} alerts")
    print(f"   📅 Generated {len(df_cal):,} calendar records")
    
    return df_cust, df_acct, df_cal, df_txn, df_alert

# -------------------------
# Part 3: Main Execution
# -------------------------
def main():
    """Main function to orchestrate FCFP database creation and data population."""
    print("🚀 Starting Financial Compliance and Fraud Prevention database setup...\n")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Establish connection to the SQLite database
    conn = sqlite3.connect(DB_FILE)
    print(f"📁 Database file: {DB_FILE}")

    try:
        # 1. Create the database schema
        print("\n🔧 Creating database schema...")
        create_database_schema(conn)

        # 2. Generate the synthetic data
        print("\n📊 Generating financial analytics data...")
        df_cust, df_acct, df_cal, df_txn, df_alert = generate_data()

        # 3. Insert data into the database tables
        print("\n💾 Inserting data into database tables...")
        
        # Insert in order of dependencies
        df_cal.to_sql("dim_calendar", conn, if_exists="append", index=False)
        print("   ✅ Calendar dimension inserted")
        
        df_cust.to_sql("dim_customer", conn, if_exists="append", index=False)
        print("   ✅ Customer dimension inserted")
        
        df_acct.to_sql("dim_account", conn, if_exists="append", index=False)
        print("   ✅ Account dimension inserted")
        
        df_txn.to_sql("fact_transactions", conn, if_exists="append", index=False)
        print("   ✅ Transaction facts inserted")
        
        df_alert.to_sql("fact_alerts", conn, if_exists="append", index=False)
        print("   ✅ Alert facts inserted")

        # 4. Generate summary statistics
        print("\n📈 Database Summary Statistics:")
        print("=" * 50)
        
        cursor = conn.cursor()
        
        # Customer stats
        cursor.execute("SELECT segment, COUNT(*) FROM dim_customer GROUP BY segment ORDER BY COUNT(*) DESC")
        print("👥 Customers by Segment:")
        for segment, count in cursor.fetchall():
            print(f"   {segment}: {count:,}")
            
        # Account stats  
        cursor.execute("SELECT account_type, COUNT(*) FROM dim_account GROUP BY account_type ORDER BY COUNT(*) DESC")
        print("\n🏧 Accounts by Type:")
        for acc_type, count in cursor.fetchall():
            print(f"   {acc_type}: {count:,}")
            
        # Transaction stats
        cursor.execute("SELECT channel, COUNT(*) FROM fact_transactions GROUP BY channel ORDER BY COUNT(*) DESC")
        print("\n💳 Transactions by Channel:")
        for channel, count in cursor.fetchall():
            print(f"   {channel}: {count:,}")
            
        cursor.execute("SELECT SUM(amount), AVG(amount), COUNT(*) FROM fact_transactions")
        total_amt, avg_amt, txn_count = cursor.fetchone()
        print(f"\n💰 Transaction Totals:")
        print(f"   Total Amount: €{total_amt:,.2f}")
        print(f"   Average Amount: €{avg_amt:,.2f}")
        print(f"   Total Transactions: {txn_count:,}")
        
        # Alert stats
        cursor.execute("SELECT alert_type, COUNT(*) FROM fact_alerts GROUP BY alert_type ORDER BY COUNT(*) DESC")
        print("\n🚨 Alerts by Type:")
        for alert_type, count in cursor.fetchall():
            print(f"   {alert_type}: {count:,}")
            
        cursor.execute("SELECT risk_level, COUNT(*) FROM fact_alerts GROUP BY risk_level ORDER BY COUNT(*) DESC")
        print("\n⚠️  Alerts by Risk Level:")
        for risk_level, count in cursor.fetchall():
            print(f"   {risk_level}: {count:,}")

        print(f"\n🎉 SUCCESS! Financial Compliance database '{DB_FILE}' is ready for analytics!")
        print("\n📋 Sample Analytics Queries to Try:")
        print("   • 'Who are the top 5 customers by transaction volume?'")
        print("   • 'Show high-risk alerts from the last 30 days'")
        print("   • 'What is the total transaction amount by channel?'")
        print("   • 'Which countries have the most flagged transactions?'")
        print("   • 'Show PEP customers with suspicious activity'")
        print("   • 'What are the transaction patterns by customer segment?'")

    except Exception as e:
        print(f"\n❌ An error occurred during database setup: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print(f"\n🔒 Database connection closed.")

if __name__ == "__main__":
    main()