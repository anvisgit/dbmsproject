-- ============================================================
--  queries.sql — 10 Analytical Queries
-- ============================================================

-- ─── Q1: Top Defaulters (JOINs + ORDER BY) ───────────────────
-- Shows customers with most defaults, their overdue days, and penalty totals
SELECT
    c.customer_id,
    c.name,
    c.phone,
    COUNT(DISTINCT dr.default_id)    AS total_defaults,
    SUM(dr.overdue_days)             AS total_overdue_days,
    COALESCE(SUM(p.penalty_amount),0) AS total_penalty_paid,
    cs.score_value                   AS latest_credit_score
FROM customer c
JOIN loan l         ON l.customer_id   = c.customer_id
JOIN default_record dr ON dr.loan_id  = l.loan_id
LEFT JOIN penalty p    ON p.default_id = dr.default_id
LEFT JOIN LATERAL (
    SELECT score_value
    FROM   credit_score
    WHERE  customer_id = c.customer_id
    ORDER BY score_date DESC
    LIMIT  1
) cs ON TRUE
GROUP BY c.customer_id, c.name, c.phone, cs.score_value
ORDER BY total_defaults DESC, total_overdue_days DESC;

-- ─── Q2: Monthly EMI Collections ─────────────────────────────
-- Total repayments grouped by month
SELECT
    TO_CHAR(r.payment_date, 'YYYY-MM')  AS collection_month,
    COUNT(r.repayment_id)               AS payments_count,
    SUM(r.paid_amount)                  AS total_collected,
    AVG(r.paid_amount)                  AS avg_emi_paid,
    SUM(r.paid_amount) FILTER (WHERE r.payment_mode = 'Online') AS online_collected,
    SUM(r.paid_amount) FILTER (WHERE r.payment_mode = 'UPI')    AS upi_collected
FROM repayment r
GROUP BY collection_month
ORDER BY collection_month;

-- ─── Q3: Credit Score Trend Per Customer (Window Function) ───
-- Running average of credit score over time using window function
SELECT
    c.name,
    cs.score_date,
    cs.score_value,
    ROUND(AVG(cs.score_value) OVER (
        PARTITION BY cs.customer_id
        ORDER BY cs.score_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                AS rolling_avg_score,
    cs.score_value - LAG(cs.score_value) OVER (
        PARTITION BY cs.customer_id ORDER BY cs.score_date
    )                                    AS score_change,
    r.risk_level
FROM credit_score cs
JOIN customer c      ON c.customer_id = cs.customer_id
JOIN risk_category r ON r.risk_id     = cs.risk_id
ORDER BY c.customer_id, cs.score_date;

-- ─── Q4: Loan Approval Rate by Loan Type ─────────────────────
SELECT
    lt.type_name,
    COUNT(l.loan_id)                                             AS total_loans,
    COUNT(l.loan_id) FILTER (WHERE l.current_status = 'Active') AS active_loans,
    COUNT(l.loan_id) FILTER (WHERE l.current_status = 'Closed') AS closed_loans,
    COUNT(l.loan_id) FILTER (WHERE l.current_status = 'Defaulted') AS defaulted_loans,
    ROUND(
        100.0 * COUNT(l.loan_id) FILTER (WHERE l.current_status != 'Defaulted')
        / NULLIF(COUNT(l.loan_id), 0), 2
    )                                                            AS success_rate_pct,
    ROUND(AVG(l.loan_amount), 2)                                 AS avg_loan_amount,
    SUM(l.loan_amount)                                           AS total_disbursed
FROM loan_type lt
LEFT JOIN loan l ON l.loan_type_id = lt.loan_type_id
GROUP BY lt.loan_type_id, lt.type_name
ORDER BY total_disbursed DESC;

-- ─── Q5: Customers Eligible for New Loan ─────────────────────
-- Score > 600, no active defaults, income > 30000
SELECT
    c.customer_id,
    c.name,
    i.monthly_income,
    i.employment_type,
    cs_latest.score_value    AS credit_score,
    rc.risk_level,
    ch.total_defaults,
    COUNT(l.loan_id) FILTER (WHERE l.current_status = 'Active') AS active_loans
FROM customer c
JOIN income_details i ON i.customer_id = c.customer_id
JOIN credit_history ch ON ch.customer_id = c.customer_id
JOIN LATERAL (
    SELECT score_value, risk_id
    FROM   credit_score
    WHERE  customer_id = c.customer_id
    ORDER BY score_date DESC
    LIMIT  1
) cs_latest ON TRUE
JOIN risk_category rc ON rc.risk_id = cs_latest.risk_id
LEFT JOIN loan l ON l.customer_id = c.customer_id
WHERE cs_latest.score_value > 600
  AND ch.total_defaults = 0
  AND i.monthly_income  > 30000
GROUP BY
    c.customer_id, c.name, i.monthly_income, i.employment_type,
    cs_latest.score_value, rc.risk_level, ch.total_defaults
ORDER BY cs_latest.score_value DESC;

-- ─── Q6: Loan Portfolio Risk Distribution ────────────────────
SELECT
    rc.risk_level,
    COUNT(DISTINCT c.customer_id)  AS customer_count,
    COUNT(l.loan_id)               AS loan_count,
    SUM(l.loan_amount)             AS total_exposure,
    ROUND(AVG(l.interest_rate),2)  AS avg_interest_rate
FROM customer c
JOIN LATERAL (
    SELECT risk_id FROM credit_score
    WHERE  customer_id = c.customer_id
    ORDER BY score_date DESC LIMIT 1
) cs ON TRUE
JOIN risk_category rc ON rc.risk_id = cs.risk_id
LEFT JOIN loan l ON l.customer_id = c.customer_id
GROUP BY rc.risk_level
ORDER BY rc.risk_level;

-- ─── Q7: EMI Status Summary per Loan ─────────────────────────
SELECT
    l.loan_id,
    c.name            AS customer_name,
    lt.type_name      AS loan_type,
    l.loan_amount,
    COUNT(e.emi_id)                                        AS total_emis,
    COUNT(e.emi_id) FILTER (WHERE e.status = 'Paid')      AS paid_emis,
    COUNT(e.emi_id) FILTER (WHERE e.status = 'Overdue')   AS overdue_emis,
    COUNT(e.emi_id) FILTER (WHERE e.status = 'Pending')   AS pending_emis,
    ROUND(
        100.0 * COUNT(e.emi_id) FILTER (WHERE e.status = 'Paid')
        / NULLIF(COUNT(e.emi_id), 0), 2
    )                                                      AS repayment_pct
FROM loan l
JOIN customer  c  ON c.customer_id  = l.customer_id
JOIN loan_type lt ON lt.loan_type_id = l.loan_type_id
LEFT JOIN emi_schedule e ON e.loan_id = l.loan_id
GROUP BY l.loan_id, c.name, lt.type_name, l.loan_amount
ORDER BY repayment_pct ASC NULLS LAST;

-- ─── Q8: Penalty Leaderboard with Rank (Window Function) ─────
SELECT
    c.customer_id,
    c.name,
    COUNT(DISTINCT dr.default_id)       AS default_count,
    SUM(p.penalty_amount)               AS total_penalty,
    RANK() OVER (ORDER BY SUM(p.penalty_amount) DESC) AS penalty_rank,
    DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT dr.default_id) DESC) AS default_rank
FROM customer c
JOIN loan l           ON l.customer_id   = c.customer_id
JOIN default_record dr ON dr.loan_id    = l.loan_id
JOIN penalty p         ON p.default_id  = dr.default_id
GROUP BY c.customer_id, c.name
ORDER BY penalty_rank;

-- ─── Q9: Income vs Loan Capacity Analysis ────────────────────
SELECT
    c.customer_id,
    c.name,
    i.monthly_income,
    i.employment_type,
    COALESCE(SUM(l.loan_amount), 0)             AS total_borrowed,
    COALESCE(SUM(l.loan_amount),0) / NULLIF(i.monthly_income * 12, 0) AS loan_to_income_ratio,
    COALESCE(AVG(e.emi_amount), 0)               AS avg_emi,
    ROUND(COALESCE(AVG(e.emi_amount),0) * 100.0 / NULLIF(i.monthly_income,0),2) AS emi_to_income_pct
FROM customer c
JOIN income_details i ON i.customer_id = c.customer_id
LEFT JOIN loan l       ON l.customer_id = c.customer_id AND l.current_status = 'Active'
LEFT JOIN emi_schedule e ON e.loan_id = l.loan_id
GROUP BY c.customer_id, c.name, i.monthly_income, i.employment_type
ORDER BY loan_to_income_ratio DESC NULLS LAST;

-- ─── Q10: Cumulative Repayment vs Outstanding (Window Function)
SELECT
    c.name,
    TO_CHAR(r.payment_date, 'YYYY-MM') AS month,
    SUM(r.paid_amount)                 AS monthly_repayment,
    SUM(SUM(r.paid_amount)) OVER (
        PARTITION BY l.customer_id
        ORDER BY TO_CHAR(r.payment_date, 'YYYY-MM')
    )                                  AS cumulative_repaid,
    l.loan_amount - SUM(SUM(r.paid_amount)) OVER (
        PARTITION BY l.customer_id
        ORDER BY TO_CHAR(r.payment_date, 'YYYY-MM')
    )                                  AS estimated_outstanding
FROM repayment r
JOIN emi_schedule e ON e.emi_id = r.emi_id
JOIN loan l         ON l.loan_id = e.loan_id
JOIN customer c     ON c.customer_id = l.customer_id
GROUP BY c.name, l.customer_id, l.loan_amount, month
ORDER BY c.name, month;
