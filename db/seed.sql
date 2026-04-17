-- ============================================================
--  seed.sql — Realistic seed data
-- ============================================================

-- ─── Risk Categories ─────────────────────────────────────────
INSERT INTO risk_category (risk_level, min_score, max_score) VALUES
  ('Low',       751, 900),
  ('Medium',    601, 750),
  ('High',      300, 600);

-- ─── Loan Types ──────────────────────────────────────────────
INSERT INTO loan_type (type_name, base_interest_rate, max_amount) VALUES
  ('Home Loan',         7.50,  10000000.00),
  ('Personal Loan',    12.00,    500000.00),
  ('Vehicle Loan',      9.00,   2000000.00),
  ('Education Loan',    8.50,   1500000.00),
  ('Business Loan',    14.00,   5000000.00);

-- ─── Customers (20) ──────────────────────────────────────────
INSERT INTO customer (name, dob, phone, email) VALUES
  ('Aarav Sharma',     '1990-03-15', '9876543210', 'aarav.sharma@email.com'),
  ('Priya Patel',      '1985-07-22', '9876543211', 'priya.patel@email.com'),
  ('Rohit Verma',      '1978-11-08', '9876543212', 'rohit.verma@email.com'),
  ('Sneha Gupta',      '1992-05-30', '9876543213', 'sneha.gupta@email.com'),
  ('Karan Mehta',      '1988-09-14', '9876543214', 'karan.mehta@email.com'),
  ('Anita Joshi',      '1995-01-25', '9876543215', 'anita.joshi@email.com'),
  ('Vikram Singh',     '1975-12-03', '9876543216', 'vikram.singh@email.com'),
  ('Pooja Nair',       '1998-06-18', '9876543217', 'pooja.nair@email.com'),
  ('Suresh Kumar',     '1982-04-07', '9876543218', 'suresh.kumar@email.com'),
  ('Deepa Reddy',      '1993-08-29', '9876543219', 'deepa.reddy@email.com'),
  ('Amit Choudhary',   '1987-10-11', '9876543220', 'amit.choudhary@email.com'),
  ('Kavita Rao',       '1991-02-14', '9876543221', 'kavita.rao@email.com'),
  ('Rajesh Tiwari',    '1980-07-19', '9876543222', 'rajesh.tiwari@email.com'),
  ('Sunita Bose',      '1996-11-22', '9876543223', 'sunita.bose@email.com'),
  ('Manoj Pandey',     '1983-03-05', '9876543224', 'manoj.pandey@email.com'),
  ('Ritu Agarwal',     '1994-09-16', '9876543225', 'ritu.agarwal@email.com'),
  ('Sanjay Mishra',    '1977-05-28', '9876543226', 'sanjay.mishra@email.com'),
  ('Geeta Kapoor',     '1989-12-10', '9876543227', 'geeta.kapoor@email.com'),
  ('Nikhil Bansal',    '1997-04-03', '9876543228', 'nikhil.bansal@email.com'),
  ('Meena Iyer',       '1984-08-25', '9876543229', 'meena.iyer@email.com');

-- ─── Income Details ──────────────────────────────────────────
INSERT INTO income_details (customer_id, monthly_income, employment_type, company_name) VALUES
  ( 1,  85000, 'Salaried',     'Infosys Ltd'),
  ( 2,  60000, 'Salaried',     'TCS'),
  ( 3, 120000, 'Self-Employed', 'Verma Consultancy'),
  ( 4,  45000, 'Salaried',     'Wipro'),
  ( 5,  95000, 'Salaried',     'HCL Technologies'),
  ( 6,  35000, 'Salaried',     'Accenture'),
  ( 7, 200000, 'Business',     'Singh Enterprises'),
  ( 8,  30000, 'Salaried',     'Cognizant'),
  ( 9,  75000, 'Salaried',     'Tech Mahindra'),
  (10,  55000, 'Salaried',     'IBM India'),
  (11, 110000, 'Self-Employed', 'Choudhary & Co.'),
  (12,  48000, 'Salaried',     'Capgemini'),
  (13, 150000, 'Business',     'Tiwari Traders'),
  (14,  28000, 'Salaried',     'Mphasis'),
  (15,  90000, 'Self-Employed', 'Pandey Solutions'),
  (16,  52000, 'Salaried',     'Oracle India'),
  (17, 180000, 'Business',     'Mishra Industries'),
  (18,  65000, 'Salaried',     'SAP India'),
  (19,  25000, 'Salaried',     'Startupville'),
  (20,  70000, 'Salaried',     'HDFC Bank');

-- ─── Address Details ─────────────────────────────────────────
INSERT INTO address_details (customer_id, street, city, zip_code) VALUES
  ( 1, '12 MG Road',           'Bengaluru',  '560001'),
  ( 2, '45 Linking Road',      'Mumbai',     '400050'),
  ( 3, '7 Civil Lines',        'Delhi',      '110054'),
  ( 4, '23 Park Street',       'Kolkata',    '700016'),
  ( 5, '89 Banjara Hills',     'Hyderabad',  '500034'),
  ( 6, '34 Nagar Road',        'Pune',       '411001'),
  ( 7, '56 Race Course Road',  'Coimbatore', '641018'),
  ( 8, '11 Fort Kochi',        'Kochi',      '682001'),
  ( 9, '78 Anna Nagar',        'Chennai',    '600040'),
  (10, '90 Jubilee Hills',     'Hyderabad',  '500033'),
  (11, '15 Vaishali Nagar',    'Jaipur',     '302021'),
  (12, '28 Residency Road',    'Bengaluru',  '560025'),
  (13, '6 Hazratganj',         'Lucknow',    '226001'),
  (14, '19 Salt Lake',         'Kolkata',    '700091'),
  (15, '44 MP Nagar',          'Bhopal',     '462011'),
  (16, '3 Gomti Nagar',        'Lucknow',    '226010'),
  (17, '77 Ring Road',         'Surat',      '395002'),
  (18, '22 Sector 15',         'Gurugram',   '122001'),
  (19, '5 Andheri West',       'Mumbai',     '400058'),
  (20, '38 Adyar',             'Chennai',    '600020');

-- ─── Credit History ──────────────────────────────────────────
INSERT INTO credit_history (customer_id, total_loans, total_defaults, last_updated) VALUES
  ( 1, 3, 0, '2025-12-01'),
  ( 2, 2, 0, '2025-11-15'),
  ( 3, 5, 1, '2025-12-10'),
  ( 4, 1, 0, '2025-10-20'),
  ( 5, 4, 0, '2025-12-05'),
  ( 6, 2, 1, '2025-09-30'),
  ( 7, 6, 0, '2025-12-15'),
  ( 8, 1, 1, '2025-08-22'),
  ( 9, 3, 0, '2025-11-28'),
  (10, 2, 0, '2025-12-08'),
  (11, 4, 1, '2025-11-05'),
  (12, 1, 0, '2025-10-18'),
  (13, 5, 2, '2025-12-12'),
  (14, 2, 2, '2025-07-14'),
  (15, 3, 0, '2025-12-01'),
  (16, 2, 0, '2025-11-22'),
  (17, 7, 1, '2025-12-14'),
  (18, 2, 0, '2025-10-30'),
  (19, 1, 1, '2025-09-05'),
  (20, 3, 0, '2025-12-10');

-- ─── Credit Scores ───────────────────────────────────────────
-- Multiple score entries per customer to show trend
INSERT INTO credit_score (customer_id, score_value, score_date, risk_id) VALUES
  ( 1, 810, '2025-06-01', 1), ( 1, 820, '2025-09-01', 1), ( 1, 835, '2025-12-01', 1),
  ( 2, 720, '2025-06-01', 2), ( 2, 730, '2025-09-01', 2), ( 2, 745, '2025-12-01', 2),
  ( 3, 650, '2025-06-01', 2), ( 3, 630, '2025-09-01', 2), ( 3, 610, '2025-12-01', 2),
  ( 4, 780, '2025-06-01', 1), ( 4, 790, '2025-09-01', 1), ( 4, 800, '2025-12-01', 1),
  ( 5, 855, '2025-06-01', 1), ( 5, 860, '2025-09-01', 1), ( 5, 875, '2025-12-01', 1),
  ( 6, 540, '2025-06-01', 3), ( 6, 520, '2025-09-01', 3), ( 6, 505, '2025-12-01', 3),
  ( 7, 890, '2025-06-01', 1), ( 7, 885, '2025-09-01', 1), ( 7, 895, '2025-12-01', 1),
  ( 8, 430, '2025-06-01', 3), ( 8, 410, '2025-09-01', 3), ( 8, 390, '2025-12-01', 3),
  ( 9, 760, '2025-06-01', 1), ( 9, 770, '2025-09-01', 1), ( 9, 775, '2025-12-01', 1),
  (10, 710, '2025-06-01', 2), (10, 715, '2025-09-01', 2), (10, 720, '2025-12-01', 2),
  (11, 640, '2025-06-01', 2), (11, 620, '2025-09-01', 2), (11, 605, '2025-12-01', 2),
  (12, 800, '2025-06-01', 1), (12, 810, '2025-09-01', 1), (12, 815, '2025-12-01', 1),
  (13, 480, '2025-06-01', 3), (13, 460, '2025-09-01', 3), (13, 440, '2025-12-01', 3),
  (14, 350, '2025-06-01', 3), (14, 330, '2025-09-01', 3), (14, 310, '2025-12-01', 3),
  (15, 840, '2025-06-01', 1), (15, 845, '2025-09-01', 1), (15, 850, '2025-12-01', 1),
  (16, 700, '2025-06-01', 2), (16, 710, '2025-09-01', 2), (16, 720, '2025-12-01', 2),
  (17, 760, '2025-06-01', 1), (17, 755, '2025-09-01', 2), (17, 750, '2025-12-01', 2),
  (18, 790, '2025-06-01', 1), (18, 795, '2025-09-01', 1), (18, 800, '2025-12-01', 1),
  (19, 400, '2025-06-01', 3), (19, 380, '2025-09-01', 3), (19, 360, '2025-12-01', 3),
  (20, 740, '2025-06-01', 2), (20, 755, '2025-09-01', 1), (20, 765, '2025-12-01', 1);

-- ─── Loans (30) ──────────────────────────────────────────────
INSERT INTO loan (customer_id, loan_type_id, loan_amount, interest_rate, tenure, current_status, disbursed_date) VALUES
  ( 1, 1, 5000000, 7.50, 240, 'Active',    '2023-01-10'),
  ( 1, 2,  200000, 12.00, 24, 'Closed',    '2022-06-15'),
  ( 2, 2,  150000, 12.50, 18, 'Active',    '2024-02-20'),
  ( 3, 5, 1000000, 14.50, 60, 'Active',    '2023-07-01'),
  ( 3, 3,  800000,  9.25, 48, 'Defaulted', '2022-01-15'),
  ( 4, 4,  700000,  8.75, 60, 'Active',    '2024-01-05'),
  ( 5, 1, 8000000,  7.75, 300,'Active',    '2021-06-10'),
  ( 5, 3, 1200000,  9.00, 60, 'Active',    '2023-03-22'),
  ( 6, 2,  300000, 13.00, 36, 'Defaulted', '2022-09-18'),
  ( 7, 1, 9000000,  7.50, 360,'Active',    '2020-11-05'),
  ( 7, 5, 3000000, 13.50, 84, 'Active',    '2023-05-15'),
  ( 8, 2,  250000, 14.50, 24, 'Defaulted', '2023-02-10'),
  ( 9, 3,  900000,  9.00, 48, 'Active',    '2024-03-12'),
  (10, 2,  180000, 12.00, 18, 'Active',    '2024-05-01'),
  (11, 5,  500000, 15.00, 36, 'Defaulted', '2022-08-20'),
  (11, 2,  350000, 13.50, 30, 'Active',    '2024-01-30'),
  (12, 1, 4500000,  7.75, 240,'Active',    '2023-08-15'),
  (13, 2,  400000, 14.00, 36, 'Defaulted', '2022-04-10'),
  (13, 5, 2000000, 15.50, 60, 'Defaulted', '2021-11-20'),
  (14, 2,  200000, 15.00, 24, 'Defaulted', '2023-06-05'),
  (15, 1, 6000000,  7.50, 300,'Active',    '2022-09-01'),
  (15, 3, 1500000,  9.25, 60, 'Active',    '2024-02-18'),
  (16, 4,  600000,  8.75, 48, 'Active',    '2024-04-10'),
  (17, 5, 4000000, 14.00, 84, 'Active',    '2021-05-25'),
  (17, 1, 7500000,  7.50, 360,'Active',    '2020-08-12'),
  (18, 2,  250000, 12.00, 24, 'Active',    '2024-06-01'),
  (19, 2,  150000, 15.50, 18, 'Defaulted', '2023-09-10'),
  (20, 3,  700000,  9.00, 42, 'Active',    '2024-01-20'),
  ( 2, 4,  500000,  8.75, 48, 'Active',    '2023-11-15'),
  ( 9, 4,  800000,  8.50, 60, 'Active',    '2022-07-08');

-- ─── Loan Status History ─────────────────────────────────────
INSERT INTO loan_status_history (loan_id, status_label, change_date) VALUES
  ( 1, 'Approved',   '2023-01-10'),
  ( 1, 'Active',     '2023-01-10'),
  ( 2, 'Approved',   '2022-06-15'),
  ( 2, 'Active',     '2022-06-15'),
  ( 2, 'Closed',     '2024-06-15'),
  ( 3, 'Approved',   '2024-02-20'),
  ( 3, 'Active',     '2024-02-20'),
  ( 4, 'Approved',   '2023-07-01'),
  ( 4, 'Active',     '2023-07-01'),
  ( 5, 'Approved',   '2022-01-15'),
  ( 5, 'Active',     '2022-01-15'),
  ( 5, 'Defaulted',  '2023-09-15'),
  ( 6, 'Approved',   '2024-01-05'),
  ( 6, 'Active',     '2024-01-05'),
  ( 9, 'Approved',   '2022-09-18'),
  ( 9, 'Active',     '2022-09-18'),
  ( 9, 'Defaulted',  '2023-06-18'),
  (12, 'Approved',   '2023-02-10'),
  (12, 'Active',     '2023-02-10'),
  (12, 'Defaulted',  '2024-02-10'),
  (15, 'Approved',   '2022-08-20'),
  (15, 'Active',     '2022-08-20'),
  (15, 'Defaulted',  '2023-08-20'),
  (18, 'Approved',   '2022-04-10'),
  (18, 'Active',     '2022-04-10'),
  (18, 'Defaulted',  '2023-04-10'),
  (19, 'Approved',   '2021-11-20'),
  (19, 'Active',     '2021-11-20'),
  (19, 'Defaulted',  '2023-05-20'),
  (20, 'Approved',   '2023-06-05'),
  (20, 'Active',     '2023-06-05'),
  (20, 'Defaulted',  '2024-04-05'),
  (27, 'Approved',   '2023-09-10'),
  (27, 'Active',     '2023-09-10'),
  (27, 'Defaulted',  '2024-06-10');

-- ─── Guarantors ──────────────────────────────────────────────
INSERT INTO guarantor (loan_id, name, phone, relationship) VALUES
  ( 1, 'Sundar Sharma',   '9811001001', 'Father'),
  ( 4, 'Ramesh Verma',    '9811001002', 'Spouse'),
  ( 7, 'Lalita Singh',    '9811001003', 'Mother'),
  (10, 'Prithvi Singh',   '9811001004', 'Father'),
  (12, 'Anil Nair',       '9811001005', 'Brother'),
  (17, 'Vinod Kumar',     '9811001006', 'Friend'),
  (21, 'Harish Pandey',   '9811001007', 'Spouse'),
  (24, 'Kaveri Mishra',   '9811001008', 'Mother'),
  (25, 'Subroto Mishra',  '9811001009', 'Father'),
  (30, 'Padma Reddy',     '9811001010', 'Spouse');

-- ─── EMI Schedules (generate for active/all loans) ───────────
-- Loan 1: Home Loan, 5000000 @ 7.5%, 240 months, from 2023-01-10
-- Monthly EMI ≈ 40280
DO $$
DECLARE
  v_loan_id   INT;
  v_loan_amount NUMERIC;
  v_rate      NUMERIC;
  v_tenure    INT;
  v_start     DATE;
  v_emi       NUMERIC;
  v_r         NUMERIC;
  i           INT;
  v_due       DATE;
  v_status    VARCHAR;
  rec         RECORD;
BEGIN
  FOR rec IN
    SELECT loan_id, loan_amount, interest_rate, tenure, disbursed_date
    FROM   loan
    ORDER BY loan_id
  LOOP
    v_loan_id     := rec.loan_id;
    v_loan_amount := rec.loan_amount;
    v_rate        := rec.interest_rate / 1200.0;   -- monthly rate
    v_tenure      := LEAST(rec.tenure, 12);         -- seed only first 12 EMIs per loan
    v_start       := rec.disbursed_date;

    -- EMI formula: P*r*(1+r)^n / ((1+r)^n - 1)
    IF v_rate = 0 THEN
      v_emi := ROUND(v_loan_amount / rec.tenure, 2);
    ELSE
      v_emi := ROUND(
        v_loan_amount * v_rate * POWER(1 + v_rate, rec.tenure)
        / (POWER(1 + v_rate, rec.tenure) - 1), 2);
    END IF;

    FOR i IN 1..v_tenure LOOP
      v_due := v_start + (i || ' months')::INTERVAL;

      -- Determine status based on date and loan status
      IF v_due < '2025-01-01' THEN
        v_status := 'Paid';
      ELSIF v_due < CURRENT_DATE THEN
        v_status := 'Overdue';
      ELSE
        v_status := 'Pending';
      END IF;

      INSERT INTO emi_schedule (loan_id, due_date, emi_amount, status)
      VALUES (v_loan_id, v_due, v_emi, v_status);
    END LOOP;
  END LOOP;
END $$;

-- ─── Repayments (for all Paid EMIs) ──────────────────────────
INSERT INTO repayment (emi_id, paid_amount, payment_date, payment_mode)
SELECT
  e.emi_id,
  e.emi_amount,
  e.due_date + INTERVAL '2 days',
  (ARRAY['Online','UPI','Cheque','Cash'])[1 + (e.emi_id % 4)]
FROM emi_schedule e
WHERE e.status = 'Paid';

-- ─── Default Records (10 defaults) ───────────────────────────
INSERT INTO default_record (loan_id, default_date, overdue_days) VALUES
  ( 5, '2023-09-15',  92),
  ( 9, '2023-06-18',  75),
  (12, '2024-02-10',  45),
  (15, '2023-08-20', 120),
  (18, '2023-04-10',  60),
  (19, '2023-05-20', 180),
  (20, '2024-04-05',  30),
  (27, '2024-06-10',  55),
  (13, '2023-10-15',  85),
  (14, '2024-01-22',  40);

-- ─── Penalties ───────────────────────────────────────────────
INSERT INTO penalty (default_id, penalty_amount, penalty_date) VALUES
  (1, 12500.00, '2023-10-01'),
  (2,  8750.00, '2023-07-05'),
  (3,  5600.00, '2024-02-25'),
  (4, 15000.00, '2023-09-05'),
  (5,  7200.00, '2023-04-25'),
  (6, 22500.00, '2023-06-10'),
  (7,  3800.00, '2024-04-20'),
  (8,  6900.00, '2024-06-25'),
  (9, 10500.00, '2023-11-01'),
  (10, 5000.00, '2024-02-08');
