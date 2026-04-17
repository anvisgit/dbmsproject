import os
import psycopg2
import pandas as pd
from datetime import date

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "loandb"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_df(sql, params=None):
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                try:
                    return cur.fetchone()[0]
                except Exception:
                    return None
    finally:
        conn.close()


def get_all_customers():
    return fetch_df("""
        SELECT c.customer_id, c.name, c.phone, c.email, c.dob,
               i.monthly_income, i.employment_type, i.company_name,
               a.city, a.zip_code
        FROM   customer c
        LEFT JOIN income_details  i ON i.customer_id = c.customer_id
        LEFT JOIN address_details a ON a.customer_id = c.customer_id
        ORDER BY c.customer_id
    """)


def get_customer(customer_id):
    df = fetch_df("""
        SELECT c.customer_id, c.name, c.phone, c.email, c.dob,
               i.monthly_income, i.employment_type, i.company_name,
               a.street, a.city, a.zip_code,
               ch.total_loans, ch.total_defaults
        FROM   customer c
        LEFT JOIN income_details  i  ON i.customer_id  = c.customer_id
        LEFT JOIN address_details a  ON a.customer_id  = c.customer_id
        LEFT JOIN credit_history  ch ON ch.customer_id = c.customer_id
        WHERE  c.customer_id = %s
    """, (customer_id,))
    return None if df.empty else df.iloc[0].to_dict()


def get_customer_credit_scores(customer_id):
    return fetch_df("""
        SELECT cs.score_date, cs.score_value, rc.risk_level
        FROM   credit_score cs
        JOIN   risk_category rc ON rc.risk_id = cs.risk_id
        WHERE  cs.customer_id = %s
        ORDER BY cs.score_date
    """, (customer_id,))


def get_latest_credit_score(customer_id):
    df = fetch_df("""
        SELECT cs.score_value, cs.score_date, rc.risk_level
        FROM   credit_score cs
        JOIN   risk_category rc ON rc.risk_id = cs.risk_id
        WHERE  cs.customer_id = %s
        ORDER BY cs.score_date DESC LIMIT 1
    """, (customer_id,))
    return None if df.empty else df.iloc[0].to_dict()


def insert_customer(name, dob, phone, email, monthly_income, employment_type,
                    company_name, street, city, zip_code):
    cid = execute(
        "INSERT INTO customer (name, dob, phone, email) VALUES (%s,%s,%s,%s) RETURNING customer_id",
        (name, dob, phone, email)
    )
    execute("INSERT INTO income_details (customer_id, monthly_income, employment_type, company_name) VALUES (%s,%s,%s,%s)",
            (cid, monthly_income, employment_type, company_name))
    execute("INSERT INTO address_details (customer_id, street, city, zip_code) VALUES (%s,%s,%s,%s)",
            (cid, street, city, zip_code))
    execute("INSERT INTO credit_history (customer_id, total_loans, total_defaults) VALUES (%s,0,0)", (cid,))
    return cid


def update_customer(customer_id, name, phone, email, dob):
    execute("UPDATE customer SET name=%s, phone=%s, email=%s, dob=%s WHERE customer_id=%s",
            (name, phone, email, dob, customer_id))


def delete_customer(customer_id):
    execute("DELETE FROM customer WHERE customer_id=%s", (customer_id,))


def insert_credit_score(customer_id, score_value):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT risk_id FROM risk_category WHERE %s BETWEEN min_score AND max_score LIMIT 1",
                            (score_value,))
                row = cur.fetchone()
                risk_id = row[0] if row else None
                cur.execute("INSERT INTO credit_score (customer_id, score_value, score_date, risk_id) VALUES (%s,%s,CURRENT_DATE,%s)",
                            (customer_id, score_value, risk_id))
    finally:
        conn.close()


def get_loan_types():
    return fetch_df("SELECT * FROM loan_type ORDER BY loan_type_id")


def insert_loan_type(type_name, base_interest_rate, max_amount):
    execute("INSERT INTO loan_type (type_name, base_interest_rate, max_amount) VALUES (%s,%s,%s)",
            (type_name, base_interest_rate, max_amount))


def update_loan_type(loan_type_id, type_name, base_interest_rate, max_amount):
    execute("UPDATE loan_type SET type_name=%s, base_interest_rate=%s, max_amount=%s WHERE loan_type_id=%s",
            (type_name, base_interest_rate, max_amount, loan_type_id))


def delete_loan_type(loan_type_id):
    execute("DELETE FROM loan_type WHERE loan_type_id=%s", (loan_type_id,))


def get_risk_categories():
    return fetch_df("SELECT * FROM risk_category ORDER BY min_score DESC")


def insert_risk_category(risk_level, min_score, max_score):
    execute("INSERT INTO risk_category (risk_level, min_score, max_score) VALUES (%s,%s,%s)",
            (risk_level, min_score, max_score))


def update_risk_category(risk_id, risk_level, min_score, max_score):
    execute("UPDATE risk_category SET risk_level=%s, min_score=%s, max_score=%s WHERE risk_id=%s",
            (risk_level, min_score, max_score, risk_id))


def delete_risk_category(risk_id):
    execute("DELETE FROM risk_category WHERE risk_id=%s", (risk_id,))


def get_loans_for_customer(customer_id):
    return fetch_df("""
        SELECT l.loan_id, lt.type_name, l.loan_amount, l.interest_rate,
               l.tenure, l.current_status, l.disbursed_date
        FROM   loan l
        JOIN   loan_type lt ON lt.loan_type_id = l.loan_type_id
        WHERE  l.customer_id = %s ORDER BY l.loan_id
    """, (customer_id,))


def get_all_loans():
    return fetch_df("""
        SELECT l.loan_id, c.name AS customer_name, lt.type_name,
               l.loan_amount, l.interest_rate, l.tenure, l.current_status, l.disbursed_date
        FROM   loan l
        JOIN   customer  c  ON c.customer_id   = l.customer_id
        JOIN   loan_type lt ON lt.loan_type_id = l.loan_type_id
        ORDER BY l.loan_id
    """)


def insert_loan(customer_id, loan_type_id, loan_amount, interest_rate, tenure, status="Active"):
    loan_id = execute("""
        INSERT INTO loan (customer_id, loan_type_id, loan_amount, interest_rate, tenure, current_status, disbursed_date)
        VALUES (%s,%s,%s,%s,%s,%s,CURRENT_DATE) RETURNING loan_id
    """, (customer_id, loan_type_id, loan_amount, interest_rate, tenure, status))
    execute("INSERT INTO loan_status_history (loan_id, status_label, change_date) VALUES (%s,'Approved',CURRENT_DATE)", (loan_id,))
    execute("INSERT INTO loan_status_history (loan_id, status_label, change_date) VALUES (%s,%s,CURRENT_DATE)", (loan_id, status))
    execute("UPDATE credit_history SET total_loans=total_loans+1, last_updated=CURRENT_DATE WHERE customer_id=%s",
            (customer_id,))
    return loan_id


def generate_emi_schedule(loan_id, loan_amount, interest_rate, tenure):
    r = interest_rate / 1200.0
    emi = round(loan_amount * r * (1+r)**tenure / ((1+r)**tenure - 1), 2) if r > 0 else round(loan_amount/tenure, 2)
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                today = date.today()
                for i in range(1, tenure + 1):
                    month = today.month + i
                    year  = today.year + (month - 1) // 12
                    month = (month - 1) % 12 + 1
                    try:
                        due = date(year, month, today.day)
                    except ValueError:
                        due = date(year, month, 28)
                    cur.execute("INSERT INTO emi_schedule (loan_id, due_date, emi_amount, status) VALUES (%s,%s,%s,'Pending')",
                                (loan_id, due, emi))
    finally:
        conn.close()


def update_loan_status(loan_id, status):
    execute("UPDATE loan SET current_status=%s WHERE loan_id=%s", (status, loan_id))
    execute("INSERT INTO loan_status_history (loan_id, status_label, change_date) VALUES (%s,%s,CURRENT_DATE)", (loan_id, status))


def get_emi_schedule(loan_id):
    return fetch_df("""
        SELECT e.emi_id, e.due_date, e.emi_amount, e.status,
               COALESCE(r.paid_amount, 0) AS paid_amount,
               r.payment_date, r.payment_mode
        FROM   emi_schedule e
        LEFT JOIN repayment r ON r.emi_id = e.emi_id
        WHERE  e.loan_id = %s ORDER BY e.due_date
    """, (loan_id,))


def get_overdue_emis(loan_id):
    return fetch_df("""
        SELECT emi_id, due_date, emi_amount FROM emi_schedule
        WHERE loan_id=%s AND status='Overdue' ORDER BY due_date
    """, (loan_id,))


def record_payment(emi_id, paid_amount, payment_mode):
    execute("INSERT INTO repayment (emi_id, paid_amount, payment_date, payment_mode) VALUES (%s,%s,CURRENT_DATE,%s)",
            (emi_id, paid_amount, payment_mode))
    execute("UPDATE emi_schedule SET status='Paid' WHERE emi_id=%s", (emi_id,))


def mark_overdue_emis():
    execute("UPDATE emi_schedule SET status='Overdue' WHERE status='Pending' AND due_date < CURRENT_DATE")


def auto_default_overdue(loan_id):
    df = get_overdue_emis(loan_id)
    if df.empty:
        return
    existing = fetch_df("SELECT default_id FROM default_record WHERE loan_id=%s", (loan_id,))
    if not existing.empty:
        return
    overdue_days = int((date.today() - pd.to_datetime(df["due_date"].min()).date()).days)
    default_id   = execute("INSERT INTO default_record (loan_id, default_date, overdue_days) VALUES (%s,CURRENT_DATE,%s) RETURNING default_id",
                           (loan_id, overdue_days))
    total_overdue  = float(df["emi_amount"].sum())
    penalty_amount = round(total_overdue * 0.02 * max(1, overdue_days // 30), 2)
    execute("INSERT INTO penalty (default_id, penalty_amount, penalty_date) VALUES (%s,%s,CURRENT_DATE)",
            (default_id, penalty_amount))
    update_loan_status(loan_id, "Defaulted")


def get_kpis():
    return {
        "total_customers":    int(fetch_df("SELECT COUNT(*) AS c FROM customer")["c"].iloc[0]),
        "active_loans":       int(fetch_df("SELECT COUNT(*) AS c FROM loan WHERE current_status='Active'")["c"].iloc[0]),
        "defaulters":         int(fetch_df("SELECT COUNT(DISTINCT loan_id) AS c FROM default_record")["c"].iloc[0]),
        "penalties_collected":float(fetch_df("SELECT COALESCE(SUM(penalty_amount),0) AS t FROM penalty")["t"].iloc[0]),
    }


def get_loans_by_risk():
    return fetch_df("""
        SELECT COALESCE(rc.risk_level,'Unknown') AS risk_level,
               COUNT(l.loan_id) AS loan_count, SUM(l.loan_amount) AS total_amount
        FROM loan l
        JOIN customer c ON c.customer_id = l.customer_id
        LEFT JOIN LATERAL (
            SELECT risk_id FROM credit_score WHERE customer_id=c.customer_id
            ORDER BY score_date DESC LIMIT 1
        ) cs ON TRUE
        LEFT JOIN risk_category rc ON rc.risk_id = cs.risk_id
        GROUP BY rc.risk_level ORDER BY loan_count DESC
    """)


def get_monthly_repayments():
    return fetch_df("""
        SELECT TO_CHAR(payment_date,'YYYY-MM') AS month,
               SUM(paid_amount) AS total_collected, COUNT(repayment_id) AS payment_count
        FROM repayment GROUP BY month ORDER BY month
    """)


def get_defaulters_table():
    return fetch_df("""
        SELECT c.customer_id, c.name, c.phone, l.loan_id, lt.type_name AS loan_type,
               l.loan_amount, dr.default_date, dr.overdue_days,
               COALESCE(p.penalty_amount,0) AS penalty_amount
        FROM default_record dr
        JOIN loan l       ON l.loan_id       = dr.loan_id
        JOIN customer c   ON c.customer_id   = l.customer_id
        JOIN loan_type lt ON lt.loan_type_id = l.loan_type_id
        LEFT JOIN penalty p ON p.default_id  = dr.default_id
        ORDER BY dr.overdue_days DESC
    """)


def run_raw_sql(sql):
    s = sql.strip().upper()
    if s.startswith("SELECT") or s.startswith("WITH"):
        return fetch_df(sql)
    execute(sql)
    return None


def export_table_csv(table_name):
    allowed = {"customer","income_details","address_details","credit_history","credit_score",
               "loan","loan_type","emi_schedule","repayment","default_record","penalty",
               "guarantor","risk_category","loan_status_history"}
    if table_name not in allowed:
        raise ValueError(f"Table not allowed: {table_name}")
    return fetch_df(f"SELECT * FROM {table_name} ORDER BY 1")
