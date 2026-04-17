timport os, sys, psycopg2

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "loandb"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SCHEMA_SQL = os.path.join(BASE_DIR, "db", "schema.sql")
SEED_SQL   = os.path.join(BASE_DIR, "db", "seed.sql")

def run_file(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        conn.cursor().execute(f.read())
    conn.commit()
    print(f"  OK  {os.path.basename(path)}")

def main():
    print("\nLoanIQ — Database Setup\n")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Cannot connect: {e}\n"
              "  1. Start PostgreSQL\n"
              "  2. CREATE DATABASE loandb;\n"
              "  3. Set DB_USER / DB_PASSWORD env vars if non-default")
        sys.exit(1)

    run_file(conn, SCHEMA_SQL)
    run_file(conn, SEED_SQL)

    print("\nRow counts:")
    tables = ["customer","income_details","address_details","credit_history","risk_category",
              "credit_score","loan_type","loan","loan_status_history","guarantor",
              "emi_schedule","repayment","default_record","penalty"]
    with conn.cursor() as cur:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t:<25} {cur.fetchone()[0]:>5}")
    conn.close()
    print("\nDone. Run:  streamlit run app/main.py\n")

if __name__ == "__main__":
    main()
