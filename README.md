# 💰 Loan Utilization Tracking System

A web application that lets bank customers apply for loans, upload proof
of how the loan amount was spent, and lets a bank officer review, verify,
and approve or reject both loans and receipts — with automatic tracking of
how much of each loan has actually been utilized.

> **Note:** This is a **web application**, accessible via any browser
> (including mobile browsers, thanks to a responsive layout) — not a
> native/installable mobile app.

## 🔗 Live Demo
[https://loan-utilization-tracking-via-mobile-g9zu.onrender.com](https://loan-utilization-tracking-via-mobile-g9zu.onrender.com)

> ⚠️ Hosted on free-tier services (Render + Aiven). If it's been idle a
> while, the first load may take up to a minute to wake up.

## ✨ Features

- 🔐 Customer registration/login with hashed passwords
- 💵 Full loan CRUD (add, edit, delete, view) with status tracking
- 📎 Receipt upload with category tagging
- 📊 Automatic utilization calculation (used amount, remaining amount, %)
- 🏦 Separate officer portal — approve/reject loans, verify/reject receipts
- ⚠️ Automatic purpose-vs-category mismatch flagging for officer review
- ⏰ Reminder system for loans pending review too long
- 📈 Dashboard charts (Chart.js)
- 📄 Export loan history as PDF or Excel
- 🛡️ CSRF protection, SQL-injection-safe queries, session-based access control

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (Chart.js) |
| Backend | Python (Flask) |
| Database | MySQL (Aiven, managed cloud instance) |
| Hosting | Render |
| Security | Werkzeug password hashing, Flask-WTF (CSRF) |
| Reporting | ReportLab (PDF), openpyxl (Excel) |

## 📁 Project Structure

```
├── app.py                  # Main Flask app (all routes)
├── reports.py               # PDF / Excel report generation
├── seed_officer.py          # Creates the first officer login
├── schema.sql                # Database schema
├── requirements.txt
├── docs/                     # Project documentation
│   ├── project-details.md
│   ├── use-case-diagram.md
│   ├── er-diagram.md
│   ├── database-schema.md
│   ├── design-review.md
│   └── testing-report.md
├── static/
│   ├── css/style.css
│   └── uploads/receipts/
└── templates/
    ├── index.html, login.html, register.html, officer_login.html
    ├── dashboard.html, officer_dashboard.html
    ├── loan.html, edit_loan.html, upload_receipt.html
    └── error.html
```

## 🚀 Setup & Run Locally

1. **Clone the repo**
   ```
   git clone https://github.com/nithya252006/loan-_utilization-_tracking--via-mobile-application.git
   cd loan-_utilization-_tracking--via-mobile-application
   ```

2. **Create a virtual environment & install dependencies**
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the database**
   ```
   mysql -u root -p < schema.sql
   ```

4. **Set environment variables**
   ```
   $env:MYSQL_PASSWORD="your_mysql_password"
   ```

5. **Create the officer account**
   ```
   python seed_officer.py
   ```

6. **Run the app**
   ```
   python app.py
   ```
   Visit `http://127.0.0.1:5000`

## ☁️ Deployment

Deployed on **Render**, using **Aiven** for a free managed MySQL database.
Configuration is entirely environment-variable driven (`MYSQL_HOST`,
`MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `MYSQL_SSL`,
`LOAN_APP_SECRET`), so the same codebase runs locally against a local
MySQL instance or in production against Aiven, with no code changes.

## 📚 Documentation

Full project documentation — including the use case diagram, ER diagram,
database schema, design review, and testing report — is available in the
[`docs/`](./docs) folder.

## 👤 Roles

- **Customer** — registers, applies for loans, uploads receipts, tracks utilization
- **Officer** — logs in separately (`/officer_login`), reviews and decides on loan/receipt submissions

## 🔒 Security Highlights

- Passwords hashed with salted PBKDF2 (never stored in plain text)
- CSRF tokens on every form
- Parameterized SQL queries (no injection risk)
- Every query scoped to the logged-in user — no cross-account data access
- File uploads restricted by type and size

## 📄 License

This project was built for academic purposes.