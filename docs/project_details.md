# Project Details

## Project Title
Loan Utilization Tracking System

> **Important note on platform:** this is a **web application** — accessed
> through a web browser (desktop or mobile) — not a native/installable
> mobile app. It is built with HTML, CSS, JavaScript, and Flask (Python),
> and is mobile-responsive (the layout adapts to phone screens via CSS
> media queries), but it does not use Android/iOS/Flutter/React Native.
> Any reference to "mobile" in the original project title refers to
> browser-based access from a mobile device, not a downloadable app.

## Objective
To build a web application that allows bank customers to apply for loans,
upload proof of how the loan amount was spent (receipts), and allows a bank
officer to review, verify, and approve or reject both loans and receipts —
while automatically tracking how much of each loan has been utilized.

## Problem Statement
Traditional loan tracking has no easy way to verify whether a borrower is
using loan funds for the purpose they were sanctioned for. This project
digitizes that process: customers submit loans and receipts online, and the
system automatically flags cases where the receipt doesn't match the
declared loan purpose, so an officer can review it before approving further
disbursement.

## Scope
- Customer-facing portal: register, login, apply for loans, upload receipts,
  track utilization, download reports
- Officer-facing portal: separate login, review all loans/receipts, approve/
  reject with remarks
- Automatic utilization calculation (used amount, remaining amount, % used)
- Automatic purpose-vs-category mismatch flagging
- Reminder system for loans pending review too long
- Exportable PDF/Excel reports

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (Chart.js for graphs) |
| Backend | Python (Flask) |
| Database | MySQL |
| Security | Werkzeug password hashing, Flask-WTF (CSRF protection) |
| Reporting | ReportLab (PDF), openpyxl (Excel) |

## Modules
1. **User Module** — Registration, login, logout, session management
2. **Loan Module** — Add / edit / delete / view loans, status tracking
3. **Receipt Module** — Upload receipts, category tagging, file validation
4. **Utilization Module** — Auto-calculates used / remaining / utilization %
5. **Officer Module** — Separate portal to approve/reject loans and receipts
6. **Purpose Validation Module** — Flags receipts that don't match the
   declared loan purpose
7. **Reminder Module** — Flags loans pending review beyond set thresholds
8. **Reporting Module** — PDF and Excel export of loan history

## Target Users
- **Customers** — individuals applying for and tracking their loans
- **Bank Officers** — staff reviewing and approving/rejecting loan
  applications and utilization proof

## Assumptions & Limitations
- This is a web application accessed via browser (including mobile
  browsers, since the UI is responsive) — not a native/installable mobile app
- Single bank/single branch context — no multi-bank or multi-branch logic
- Officer accounts are seeded manually (not self-registered) for security
