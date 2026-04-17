# LoanIQ — Loan, Credit Score and Risk Analysis System

A three-tier database application that manages the complete lifecycle of a loan — from customer registration through credit scoring, loan disbursement, EMI collection, default detection, and portfolio risk analysis. The system integrates a PostgreSQL relational database, three scikit-learn machine learning models, and a Streamlit web interface that communicates directly with PostgreSQL via psycopg2.

---

## Project Structure

```
dbmsproject/
├── db/
│   ├── schema.sql          14 tables, constraints, indexes
│   ├── seed.sql            20 customers, 30 loans, full EMI data, 10 defaults
│   └── queries.sql         10 analytical queries
├── ml/
│   ├── models.py           train (run as script) + inference (import)
│   └── models/             saved .pkl files after training
├── app/
│   ├── db_connect.py       all psycopg2 helper functions
│   ├── main.py             home dashboard
│   └── pages/
│       ├── 1_Customer.py
│       ├── 2_Loan_Application.py
│       ├── 3_EMI_Tracker.py
│       ├── 4_Risk_Dashboard.py
│       └── 5_Admin.py
├── setup_db.py             one-shot schema + seed loader
└── requirements.txt
```

---

## Quick Start

```
# 1. Create the database in psql
CREATE DATABASE loandb;

# 2. Load schema and seed data
python setup_db.py

# 3. Train ML models (already done — skip if models/ folder has .pkl files)
python ml/models.py

# 4. Launch the app
streamlit run app/main.py
```

If your PostgreSQL credentials differ from `postgres/postgres/localhost/5432`, set environment variables before running:

```
$env:DB_USER="your_user"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="loandb"
```

---

## Database Design

### Why PostgreSQL?

PostgreSQL is an ACID-compliant relational database. ACID stands for Atomicity, Consistency, Isolation, Durability. This means every transaction either commits fully or rolls back entirely — no partial inserts. This matters for a loan system because inserting a loan record must also insert a status history record and an EMI schedule atomically. PostgreSQL enforces referential integrity through foreign keys, so you cannot insert a loan for a customer who does not exist.

### Entity-Relationship Overview

The system is centred on the `customer` entity. A customer has one income record, one address, and one credit history. A customer may have many credit scores over time (each dated, forming a trend). A customer may take many loans, each of a specific loan type. Each loan generates a fixed EMI schedule. Each EMI may have a repayment record when paid. When EMIs go overdue, a default record is created for the loan, and a penalty is applied to that default.

```
customer
  |-- income_details       (1:1 per customer)
  |-- address_details      (1:1 per customer)
  |-- credit_history       (1:1 per customer, accumulates totals)
  |-- credit_score         (1:many — one entry per scoring event)
       |-- risk_category   (many:1 lookup — Low/Medium/High)
  |-- loan                 (1:many)
       |-- loan_type       (many:1 lookup)
       |-- loan_status_history  (1:many — audit trail)
       |-- guarantor            (1:many — optional)
       |-- emi_schedule         (1:many — one row per month)
            |-- repayment       (1:1 per EMI when paid)
       |-- default_record       (1:1 when loan defaults)
            |-- penalty         (1:1 per default)
```

### Table Descriptions

**customer** — Core entity. Stores name, date of birth, phone (unique), email (unique). The `created_at` timestamp is auto-set. Phone and email have UNIQUE constraints so duplicate registrations fail at the database level.

**income_details** — Stores monthly income, employment type (Salaried/Self-Employed/Business/Retired), and employer name. This is separated from `customer` because income data may be updated independently and belongs to a different concern (financial profile vs personal identity). This follows the principle of separation of concerns in schema design.

**address_details** — Separated for the same reason as income. In production systems, a customer might have multiple addresses (home, office). Separating it preserves that extensibility.

**credit_history** — Aggregated summary: total loans ever taken and total defaults ever recorded. This is denormalised for performance — rather than counting from the `loan` table every time, we increment these counters when a loan is created or a default is recorded. The trade-off is that these must be kept in sync by the application.

**risk_category** — Lookup table mapping score ranges to risk labels. Three rows: Low (751–900), Medium (601–750), High (300–600). By storing this in a table rather than hard-coding it in application logic, an admin can change the thresholds without touching code.

**credit_score** — One row per scoring event per customer. This allows trend analysis over time. The `risk_id` foreign key links to `risk_category` so the risk classification at that point in time is stored alongside the score. The latest score is retrieved using `ORDER BY score_date DESC LIMIT 1`.

**loan_type** — Lookup table for loan products: Home Loan, Personal Loan, Vehicle Loan, Education Loan, Business Loan. Each has a base interest rate and a maximum sanctionable amount. Storing this in a table allows the admin to add new products or adjust rates without code changes.

**loan** — Central fact table for loan transactions. Foreign keys reference `customer` and `loan_type`. `current_status` is a denormalised field (Active/Closed/Defaulted) for quick filtering, while the full audit trail is in `loan_status_history`. `tenure` is in months.

**loan_status_history** — Append-only audit table. Every time a loan's status changes, a new row is inserted with the new status and the date. This preserves the full history of a loan's lifecycle.

**guarantor** — Optional table. A guarantor co-signs a loan and is liable if the borrower defaults. Stored separately because not all loans require guarantors and a loan may have zero or more.

**emi_schedule** — One row per EMI instalment. Generated programmatically at loan disbursement using the EMI formula. Status is one of: Pending, Paid, Overdue. Status starts as Pending and is updated by the application when payment is recorded or when the due date passes without payment.

**repayment** — One row per payment received. Linked to the specific EMI it settles. Records the amount paid, date, and payment mode. Separating this from `emi_schedule` allows partial payments to be recorded and permits multiple payment records per EMI if needed.

**default_record** — Created automatically when a loan has overdue EMIs beyond a threshold. Records the date the default was identified and the number of overdue days. This triggers a penalty.

**penalty** — Records the penalty amount levied for a default. Calculated as 2% of the overdue EMI total per 30-day period. Stored separately from `default_record` so the penalty amount and date can be tracked independently.

### Normalisation

The schema satisfies **Third Normal Form (3NF)**:

- **1NF**: All columns hold atomic values. No repeating groups. Every table has a primary key.
- **2NF**: All non-key attributes are functionally dependent on the full primary key. There are no partial dependencies because all primary keys are single-column surrogates (SERIAL or IDENTITY).
- **3NF**: No transitive dependencies. For example, `risk_level` is not stored in `credit_score` directly — it is stored by reference to `risk_category.risk_id`. The description of a risk level (Low, Medium, High) is not repeated across rows; it is looked up from the `risk_category` table.

The one intentional denormalisation is `credit_history.total_loans` and `credit_history.total_defaults`, which are counters maintained by the application. This is a deliberate trade-off for read performance on the customer profile page, which would otherwise require an aggregation query on every page load.

### Referential Integrity and Constraints

- All foreign keys are declared with `ON DELETE CASCADE` where appropriate (e.g., deleting a customer deletes all their loans, EMI schedules, repayments, defaults, and penalties).
- `loan_amount` has a `CHECK (loan_amount > 0)` constraint.
- `score_value` has a `CHECK (score_value BETWEEN 300 AND 900)` constraint.
- `tenure` has a `CHECK (tenure > 0)` constraint.
- `phone` and `email` in `customer` are declared `UNIQUE`.
- `risk_level` in `risk_category` is declared `UNIQUE`.
- `type_name` in `loan_type` is declared `UNIQUE`.

### Indexes

```sql
CREATE INDEX idx_loan_customer     ON loan(customer_id);
CREATE INDEX idx_emi_loan          ON emi_schedule(loan_id);
CREATE INDEX idx_emi_status        ON emi_schedule(status);
CREATE INDEX idx_credit_score_cust ON credit_score(customer_id);
CREATE INDEX idx_default_loan      ON default_record(loan_id);
CREATE INDEX idx_repayment_emi     ON repayment(emi_id);
```

These indexes exist because the most frequent query patterns are:
- Look up all loans for a customer (index on `loan.customer_id`)
- Look up EMI schedule for a loan (index on `emi_schedule.loan_id`)
- Filter EMIs by status to find overdue ones (index on `emi_schedule.status`)
- Retrieve credit score history for a customer (index on `credit_score.customer_id`)

Without indexes, these would be sequential table scans. With indexes, PostgreSQL uses a B-tree index scan which is O(log n) instead of O(n).

---

## SQL Queries Explained

### Query 1 — Top Defaulters

Uses multiple JOINs to connect `customer → loan → default_record → penalty`. A LATERAL subquery retrieves the most recent credit score for each customer. Results are grouped by customer and ordered by default count and overdue days. This query is used on the Risk Dashboard defaulters table.

### Query 2 — Monthly EMI Collections

Groups repayment rows by month using `TO_CHAR(payment_date, 'YYYY-MM')`. Uses `FILTER` aggregate to split totals by payment mode (Online, UPI). This shows the bank's month-by-month cash inflow from loan repayments.

### Query 3 — Credit Score Trend with Window Function

Uses `AVG() OVER (PARTITION BY customer_id ORDER BY score_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` — a sliding 3-point moving average of credit scores per customer. Also uses `LAG() OVER (PARTITION BY customer_id ORDER BY score_date)` to compute the score change between consecutive dates. Window functions operate on a set of rows relative to the current row without collapsing the result into one row per group (unlike GROUP BY).

### Query 4 — Loan Approval Rate by Loan Type

Uses `COUNT() FILTER (WHERE current_status = 'Active')` — a filtered aggregate that counts only rows matching the condition. Computes the success rate as the percentage of non-defaulted loans per loan type.

### Query 5 — Customers Eligible for New Loan

Uses a LATERAL subquery to get each customer's latest credit score without a correlated subquery in the WHERE clause. Filters on score > 600, zero defaults, and income > Rs.30,000. LATERAL allows the subquery to reference columns from the outer query on a row-by-row basis.

### Query 6 — Risk Portfolio Distribution

Categorises the loan portfolio (total exposure, count) by risk tier. Uses a LATERAL subquery to join each customer to their latest credit score's risk category.

### Query 7 — EMI Status Summary per Loan

For each loan, counts EMIs in each status (Paid, Overdue, Pending) using filtered aggregates. Computes a repayment percentage. Used on the EMI Tracker to show overall loan health.

### Query 8 — Penalty Leaderboard with Window Functions

Uses `RANK() OVER (ORDER BY SUM(penalty_amount) DESC)` to assign a rank by total penalty paid. Uses `DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT default_id) DESC)` to rank by number of defaults. RANK() leaves gaps after ties (1, 2, 2, 4); DENSE_RANK() does not (1, 2, 2, 3).

### Query 9 — Income vs Loan Capacity

Computes the loan-to-annual-income ratio and the EMI-to-monthly-income ratio for each customer. These are standard lending metrics. A high EMI-to-income ratio (above 40–50%) indicates the borrower may be over-leveraged.

### Query 10 — Cumulative Repayment with Window Function

Uses `SUM(monthly_total) OVER (PARTITION BY customer_id ORDER BY month)` — a running total of repayments per customer over time. Subtracts the cumulative repayment from the original loan amount to estimate the outstanding principal. This is an approximation; exact outstanding principal would require amortisation calculation.

---

## Machine Learning Models

### Why ML in a DBMS project?

Banks do not approve loans based on raw data alone. They use scoring models to estimate creditworthiness and default risk. Adding ML demonstrates how a DBMS can serve as a data source for predictive analytics — this is normal in production systems where transaction databases feed ML pipelines.

### Training Data

Because the database has only 30 loans (insufficient for model training), we generate 5,000 synthetic records with realistic distributions. The synthetic data preserves the business logic: high income + no defaults = high score; many defaults + overdue days = high default probability. The models are trained on synthetic data and then applied to real customer data for inference.

### Model 1 — Credit Score Predictor (RandomForestRegressor)

**Inputs**: monthly_income, employment_type (encoded: Business=4, Salaried=3, Self-Employed=2, Retired=1), total_loans, total_defaults, loan_amount, tenure

**Output**: A continuous value between 300 and 900, clipped to this range.

**Algorithm choice**: RandomForest is an ensemble of decision trees. Each tree is trained on a bootstrap sample of the data with a random subset of features. The final prediction is the average across all trees. This reduces overfitting compared to a single decision tree and handles non-linear relationships between income/defaults and the score — relationships that a linear regression would approximate poorly.

**Performance**: MAE ~17 points, R² ~0.92. An MAE of 17 means on average the predicted score is within 17 points of the target — acceptable for a 300–900 range.

### Model 2 — Risk Classifier (RandomForestClassifier)

**Inputs**: score_value, total_defaults, monthly_income, loan_amount

**Output**: Low / Medium / High (matches the `risk_category` table thresholds)

**Algorithm choice**: Same ensemble rationale as the regressor. Because the risk labels are directly derived from the score (Low if score ≥ 751, etc.), and the score is one of the input features, the classifier achieves near-perfect accuracy on the synthetic test set. In a real system, this model would handle cases where the predicted score falls near a boundary and additional features push the classification in one direction.

**Output format**: Returns the class label and the class probabilities (e.g., Low: 0.85, Medium: 0.12, High: 0.03) so the UI can show a confidence breakdown.

### Model 3 — Default Predictor (LogisticRegression)

**Inputs**: score_value, overdue_days, tenure, interest_rate, total_defaults

**Output**: Binary (0 = will not default, 1 = will default) + probability

**Algorithm choice**: Logistic regression models the log-odds of the default event as a linear combination of scaled inputs. It is interpretable (each feature has a coefficient that shows its direction and magnitude of effect) and appropriate when the relationship between features and the binary outcome is approximately log-linear. StandardScaler is applied before training because logistic regression is sensitive to feature scale — income in hundreds of thousands and overdue_days in single digits would dominate each other without scaling.

**class_weight="balanced"**: Because defaults are less frequent than non-defaults, we use balanced class weights so the model does not simply predict "no default" for everything.

### Approval Logic

```
APPROVED  if  predicted_credit_score > 600  AND  default_probability < 0.40
REJECTED  otherwise
```

This mirrors real bank policy: a minimum CIBIL-equivalent score of 600 is a common cutoff, and a 40% default probability is the threshold above which the expected loss exceeds the expected return at most standard interest rates.

---

## EMI Calculation

The Equated Monthly Instalment formula:

```
EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

Where:
  P = principal (loan amount)
  r = monthly interest rate = annual_rate / 12 / 100
  n = tenure in months
```

This formula is derived from the present value of an annuity. At each month, interest accrues on the outstanding principal. The EMI is constant but its composition changes over time — early instalments are mostly interest; later instalments are mostly principal (amortisation schedule). The system stores each EMI at the same amount (`emi_amount`) and does not store the interest/principal split per instalment — that would require a full amortisation table.

---

## Default Detection Logic

The EMI Tracker page calls `mark_overdue_emis()` on every page load. This runs:

```sql
UPDATE emi_schedule
SET status = 'Overdue'
WHERE status = 'Pending' AND due_date < CURRENT_DATE
```

If a loan has overdue EMIs and no existing `default_record`, the application then inserts a default record with the number of overdue days and inserts a penalty:

```
penalty_amount = total_overdue_emi_sum * 0.02 * max(1, overdue_days // 30)
```

The loan's `current_status` is then updated to `Defaulted`, and a row is inserted into `loan_status_history`.

---

## Application Architecture

```
Browser
   |
   v
Streamlit (Python web framework — runs on port 8501)
   |
   +-- app/db_connect.py  (psycopg2 — direct TCP connection to PostgreSQL)
   |        |
   |        v
   |   PostgreSQL (port 5432)
   |
   +-- ml/models.py  (scikit-learn inference — loaded from .pkl files)
```

There is no intermediate API layer (no Flask, no FastAPI). Streamlit pages import `db_connect.py` directly and call helper functions. This is appropriate for a project of this scope. In production, an API layer would be added between the UI and the database to enforce authentication, rate limiting, and input validation.

### Connection Handling

Each database operation opens a new connection, executes the query, commits, and closes the connection. This is safe for a development context but inefficient at scale. Production systems use connection pooling (e.g., PgBouncer or SQLAlchemy's pool) so that connections are reused across requests rather than opened and closed on every query.

### psycopg2 Parameterised Queries

All queries use `%s` placeholders, not string formatting. For example:

```python
cur.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
```

This prevents SQL injection because psycopg2 escapes the value before inserting it into the query string. Never use f-strings or string concatenation to build SQL queries.

---

## Common Professor Questions

**Q: Why 14 tables? Could you design this with fewer?**

Yes, but at the cost of normalisation. For example, `income_details` and `address_details` could be columns in `customer`. But that would mean the `customer` table has ~15 columns, mixing concerns (identity vs financial profile vs location). Normalisation improves maintainability: if address format changes, only `address_details` is affected. It also allows a customer to have multiple addresses in the future without restructuring the `customer` table.

**Q: What is a window function and where do you use it?**

A window function computes a value across a set of rows related to the current row without collapsing them into a group. Unlike GROUP BY which returns one row per group, window functions return one row per input row. We use three: `AVG() OVER` (rolling credit score average in Q3), `LAG() OVER` (score change between dates in Q3), `RANK() OVER` (penalty leaderboard in Q8), `DENSE_RANK() OVER` (default leaderboard in Q8), and `SUM() OVER` (cumulative repayment in Q10).

**Q: What is a LATERAL join and why do you use it?**

A LATERAL subquery can reference columns from the outer query. We use it to retrieve the most recent credit score for each customer in the outer query: `JOIN LATERAL (SELECT risk_id FROM credit_score WHERE customer_id = c.customer_id ORDER BY score_date DESC LIMIT 1) cs ON TRUE`. Without LATERAL, you would need a correlated subquery in the SELECT clause or a ranked subquery (using ROW_NUMBER()) which is more verbose.

**Q: How does the credit score in the ML model relate to the credit score in the database?**

When the ML model predicts a credit score for a loan application, that prediction is written back to the `credit_score` table. The `risk_id` is looked up from `risk_category` based on the predicted score value. This creates a new dated entry in the credit score history, so the customer's score trend on the Customer page updates after each loan application.

**Q: What is the difference between RANK and DENSE_RANK?**

Given scores [100, 100, 80]: RANK assigns [1, 1, 3] — there is no rank 2. DENSE_RANK assigns [1, 1, 2] — no gaps. Use RANK when you want position in an ordered sequence including gaps; use DENSE_RANK when you want the number of distinct values ahead of you.

**Q: Why use RandomForest and not a neural network?**

For tabular data with 6 numerical features and 5,000 samples, RandomForest typically outperforms neural networks because: (1) it does not require feature scaling, (2) it is not sensitive to hyperparameter choice, (3) it trains in seconds rather than minutes, and (4) it generalises well on small datasets where neural networks tend to overfit. Neural networks excel when data volume is large and features are high-dimensional (text, images).

**Q: Why is LogisticRegression used for default prediction instead of RandomForest?**

Logistic regression is interpretable: each coefficient directly shows the direction and relative magnitude of each feature's effect on the default probability. This is important in a financial context where regulators may require an explanation of why a loan application was rejected. RandomForest is a black box — you know it predicts "default" but not why. We also apply `class_weight="balanced"` to handle the imbalanced class distribution (defaults are rare).

**Q: What happens if you try to insert a customer with a phone number that already exists?**

PostgreSQL raises a `UniqueViolationError` (psycopg2 exception code 23505). The transaction is rolled back. The Streamlit form catches this exception and displays an error message to the user. The `UNIQUE` constraint is enforced at the database level — the application does not need to run a SELECT first to check for duplicates.

**Q: What is the ON DELETE CASCADE constraint?**

When a parent row is deleted, all child rows referencing it are automatically deleted. For example, `DELETE FROM customer WHERE customer_id = 5` will also delete that customer's `income_details`, `address_details`, `credit_history`, `credit_score` records, and all their `loan` records — which cascades further to `emi_schedule`, `repayment`, `default_record`, and `penalty`. This prevents orphaned records and maintains referential integrity without requiring the application to manually delete in the correct order.

**Q: What is the purpose of loan_status_history?**

It is an append-only audit table. Every status change (Approved → Active → Defaulted) is recorded with a date. This allows you to reconstruct the full timeline of any loan's history and answer questions like "when exactly did this loan default?" or "how many days between approval and default?". The `current_status` column in `loan` is denormalised for fast filtering; `loan_status_history` is the authoritative source of truth for audit purposes.

---

## Setup Reference

```
pip install -r requirements.txt
python setup_db.py          # creates schema + loads seed data
python ml/models.py         # trains and saves ML models (skip if .pkl files exist)
streamlit run app/main.py   # starts web app at http://localhost:8501
```

### Environment Variables (if not using defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | PostgreSQL host |
| DB_PORT | 5432 | PostgreSQL port |
| DB_NAME | loandb | Database name |
| DB_USER | postgres | PostgreSQL user |
| DB_PASSWORD | postgres | PostgreSQL password |

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `connection refused` | PostgreSQL not running | Start the PostgreSQL service |
| `database "loandb" does not exist` | DB not created | Run `CREATE DATABASE loandb;` in psql |
| `relation does not exist` | Schema not loaded | Run `python setup_db.py` |
| `Model not found` | .pkl files missing | Run `python ml/models.py` |
| `duplicate key value violates unique constraint` | Duplicate phone/email | Use a different phone or email |
| Port 8501 in use | Another Streamlit instance | Run `streamlit run app/main.py --server.port 8502` |
