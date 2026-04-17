-- ============================================================
--  Loan, Credit Score & Risk Analysis System — schema.sql
-- ============================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS penalty CASCADE;
DROP TABLE IF EXISTS default_record CASCADE;
DROP TABLE IF EXISTS repayment CASCADE;
DROP TABLE IF EXISTS emi_schedule CASCADE;
DROP TABLE IF EXISTS guarantor CASCADE;
DROP TABLE IF EXISTS loan_status_history CASCADE;
DROP TABLE IF EXISTS loan CASCADE;
DROP TABLE IF EXISTS loan_type CASCADE;
DROP TABLE IF EXISTS credit_score CASCADE;
DROP TABLE IF EXISTS risk_category CASCADE;
DROP TABLE IF EXISTS credit_history CASCADE;
DROP TABLE IF EXISTS address_details CASCADE;
DROP TABLE IF EXISTS income_details CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

-- ─────────────────────────────────────────
-- 1. customer
-- ─────────────────────────────────────────
CREATE TABLE customer (
    customer_id  SERIAL PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    dob          DATE         NOT NULL,
    phone        VARCHAR(15)  UNIQUE NOT NULL,
    email        VARCHAR(150) UNIQUE NOT NULL,
    created_at   TIMESTAMP    DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- 2. income_details
-- ─────────────────────────────────────────
CREATE TABLE income_details (
    income_id        SERIAL PRIMARY KEY,
    customer_id      INT          NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    monthly_income   NUMERIC(12,2) NOT NULL CHECK (monthly_income > 0),
    employment_type  VARCHAR(50)  NOT NULL,   -- Salaried / Self-Employed / Business / Retired
    company_name     VARCHAR(150)
);

-- ─────────────────────────────────────────
-- 3. address_details
-- ─────────────────────────────────────────
CREATE TABLE address_details (
    address_id  SERIAL PRIMARY KEY,
    customer_id INT         NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    street      VARCHAR(200),
    city        VARCHAR(100),
    zip_code    VARCHAR(10)
);

-- ─────────────────────────────────────────
-- 4. credit_history
-- ─────────────────────────────────────────
CREATE TABLE credit_history (
    history_id     SERIAL PRIMARY KEY,
    customer_id    INT  NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    total_loans    INT  DEFAULT 0,
    total_defaults INT  DEFAULT 0,
    last_updated   DATE DEFAULT CURRENT_DATE
);

-- ─────────────────────────────────────────
-- 5. risk_category
-- ─────────────────────────────────────────
CREATE TABLE risk_category (
    risk_id    SERIAL PRIMARY KEY,
    risk_level VARCHAR(20) UNIQUE NOT NULL,  -- Low / Medium / High / Very High
    min_score  INT NOT NULL,
    max_score  INT NOT NULL
);

-- ─────────────────────────────────────────
-- 6. credit_score
-- ─────────────────────────────────────────
CREATE TABLE credit_score (
    score_id    SERIAL PRIMARY KEY,
    customer_id INT     NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    score_value INT     NOT NULL CHECK (score_value BETWEEN 300 AND 900),
    score_date  DATE    DEFAULT CURRENT_DATE,
    risk_id     INT     REFERENCES risk_category(risk_id)
);

-- ─────────────────────────────────────────
-- 7. loan_type
-- ─────────────────────────────────────────
CREATE TABLE loan_type (
    loan_type_id       SERIAL PRIMARY KEY,
    type_name          VARCHAR(80) UNIQUE NOT NULL,
    base_interest_rate NUMERIC(5,2) NOT NULL,
    max_amount         NUMERIC(14,2) NOT NULL
);

-- ─────────────────────────────────────────
-- 8. loan
-- ─────────────────────────────────────────
CREATE TABLE loan (
    loan_id        SERIAL PRIMARY KEY,
    customer_id    INT           NOT NULL REFERENCES customer(customer_id),
    loan_type_id   INT           NOT NULL REFERENCES loan_type(loan_type_id),
    loan_amount    NUMERIC(14,2) NOT NULL CHECK (loan_amount > 0),
    interest_rate  NUMERIC(5,2)  NOT NULL,
    tenure         INT           NOT NULL CHECK (tenure > 0),   -- months
    current_status VARCHAR(30)   DEFAULT 'Active',  -- Active / Closed / Defaulted
    disbursed_date DATE          DEFAULT CURRENT_DATE
);

-- ─────────────────────────────────────────
-- 9. loan_status_history
-- ─────────────────────────────────────────
CREATE TABLE loan_status_history (
    status_history_id SERIAL PRIMARY KEY,
    loan_id           INT         NOT NULL REFERENCES loan(loan_id) ON DELETE CASCADE,
    status_label      VARCHAR(30) NOT NULL,
    change_date       DATE        DEFAULT CURRENT_DATE
);

-- ─────────────────────────────────────────
-- 10. guarantor
-- ─────────────────────────────────────────
CREATE TABLE guarantor (
    guarantor_id INT         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id      INT         NOT NULL REFERENCES loan(loan_id) ON DELETE CASCADE,
    name         VARCHAR(120) NOT NULL,
    phone        VARCHAR(15),
    relationship VARCHAR(60)
);

-- ─────────────────────────────────────────
-- 11. emi_schedule
-- ─────────────────────────────────────────
CREATE TABLE emi_schedule (
    emi_id     SERIAL PRIMARY KEY,
    loan_id    INT           NOT NULL REFERENCES loan(loan_id) ON DELETE CASCADE,
    due_date   DATE          NOT NULL,
    emi_amount NUMERIC(12,2) NOT NULL,
    status     VARCHAR(15)   DEFAULT 'Pending'  -- Pending / Paid / Overdue
);

-- ─────────────────────────────────────────
-- 12. repayment
-- ─────────────────────────────────────────
CREATE TABLE repayment (
    repayment_id  SERIAL PRIMARY KEY,
    emi_id        INT           NOT NULL REFERENCES emi_schedule(emi_id) ON DELETE CASCADE,
    paid_amount   NUMERIC(12,2) NOT NULL,
    payment_date  DATE          DEFAULT CURRENT_DATE,
    payment_mode  VARCHAR(30)   -- Cash / Online / Cheque / UPI
);

-- ─────────────────────────────────────────
-- 13. default_record
-- ─────────────────────────────────────────
CREATE TABLE default_record (
    default_id   SERIAL PRIMARY KEY,
    loan_id      INT  NOT NULL REFERENCES loan(loan_id) ON DELETE CASCADE,
    default_date DATE DEFAULT CURRENT_DATE,
    overdue_days INT  DEFAULT 0
);

-- ─────────────────────────────────────────
-- 14. penalty
-- ─────────────────────────────────────────
CREATE TABLE penalty (
    penalty_id     SERIAL PRIMARY KEY,
    default_id     INT           NOT NULL REFERENCES default_record(default_id) ON DELETE CASCADE,
    penalty_amount NUMERIC(10,2) NOT NULL,
    penalty_date   DATE          DEFAULT CURRENT_DATE
);

-- ─────────────────────────────────────────
-- Indexes for performance
-- ─────────────────────────────────────────
CREATE INDEX idx_loan_customer     ON loan(customer_id);
CREATE INDEX idx_emi_loan          ON emi_schedule(loan_id);
CREATE INDEX idx_emi_status        ON emi_schedule(status);
CREATE INDEX idx_credit_score_cust ON credit_score(customer_id);
CREATE INDEX idx_default_loan      ON default_record(loan_id);
CREATE INDEX idx_repayment_emi     ON repayment(emi_id);
