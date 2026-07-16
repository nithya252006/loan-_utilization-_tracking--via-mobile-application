# Testing Report

This document summarizes the testing performed on the Loan Utilization
Tracking System across authentication, loan management, receipt handling,
officer workflows, and deployment.

## Test Environment
- **Local:** Windows, Python 3.13, MySQL 8.4 (localhost)
- **Production:** Render (hosting) + Aiven (managed MySQL, SSL-required)
- **Browsers tested:** Chrome (desktop + mobile)

## 1. Authentication

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 1.1 | Register with valid details | Enter username (3+ chars), password (6+ chars) | Account created, redirected to login | As expected | ✅ Pass |
| 1.2 | Register with duplicate username | Register using an already-taken username | Flash message: "username already taken" | As expected | ✅ Pass |
| 1.3 | Register with short password | Enter password under 6 characters | Rejected with validation message | As expected | ✅ Pass |
| 1.4 | Login with correct credentials | Valid username + password | Redirected to dashboard | As expected | ✅ Pass |
| 1.5 | Login with wrong password | Valid username, wrong password | "Invalid username or password" shown | As expected | ✅ Pass |
| 1.6 | Officer login via customer form | Officer credentials on `/login` | Rejected (role filter excludes officers) | As expected | ✅ Pass |
| 1.7 | Officer login via `/officer_login` | Correct officer credentials | Redirected to officer dashboard | As expected | ✅ Pass |
| 1.8 | Access dashboard without login | Visit `/dashboard` directly, logged out | Redirected to `/login` | As expected | ✅ Pass |
| 1.9 | Password storage check | Inspect `users` table after registration | Password stored as salted hash, not plain text | As expected | ✅ Pass |

## 2. Loan Management

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 2.1 | Add loan with valid data | Fill amount, purpose (dropdown), date | Loan created with status "Pending" | As expected | ✅ Pass |
| 2.2 | Add loan with invalid amount | Enter 0 or negative amount | Rejected with validation message | As expected | ✅ Pass |
| 2.3 | Edit loan while Pending | Change amount/purpose/date | Loan updated successfully | As expected | ✅ Pass |
| 2.4 | Edit loan after Approved/Rejected | Attempt to edit a decided loan | Blocked with "already reviewed" message | As expected | ✅ Pass |
| 2.5 | Delete own loan | Delete a loan belonging to logged-in user | Loan removed from dashboard | As expected | ✅ Pass |
| 2.6 | Access another user's loan by ID | Manually change loan ID in edit URL | 404 / access denied (query scoped to `username`) | As expected | ✅ Pass |
| 2.7 | Search loans by purpose | Search "Education" | Only matching loans shown | As expected | ✅ Pass |

## 3. Receipt Upload & Purpose Validation

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 3.1 | Upload valid receipt (matching category) | Purpose = Education, category = Education | Uploaded, `needs_review = 0` | As expected | ✅ Pass |
| 3.2 | Upload mismatched receipt | Purpose = Wedding, category = Education | Uploaded, flagged `needs_review = 1` | As expected | ✅ Pass |
| 3.3 | Upload invalid file type | Upload a `.exe` or `.docx` file | Rejected: "Invalid file type" | As expected | ✅ Pass |
| 3.4 | Upload oversized file | Upload file over 5MB | Rejected by `MAX_CONTENT_LENGTH` | As expected | ✅ Pass |
| 3.5 | Upload with missing amount | Submit form without amount | Rejected with validation message | As expected | ✅ Pass |

## 4. Utilization Calculation

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 4.1 | Utilization with no receipts | New loan, no uploads | Used = 0, Remaining = full amount, 0% | As expected | ✅ Pass |
| 4.2 | Utilization with unverified receipt | Upload receipt, don't verify | Used amount unchanged (Pending receipts excluded) | As expected | ✅ Pass |
| 4.3 | Utilization after officer verifies | Officer marks receipt "Verified" | Used amount increases, % recalculates | As expected | ✅ Pass |
| 4.4 | Remaining amount floor | Verified receipts exceed loan amount | Remaining clamped to 0, not negative | As expected | ✅ Pass |

## 5. Officer Portal

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 5.1 | View all loans across users | Log in as officer | All customers' loans visible | As expected | ✅ Pass |
| 5.2 | Approve a Pending loan | Click Approve + optional remark | Status → Approved, buttons update | As expected | ✅ Pass |
| 5.3 | Reject a Pending loan | Click Reject + remark | Status → Rejected, action buttons hidden, shows "Decision final" | As expected | ✅ Pass |
| 5.4 | Verify a receipt | Click ✅ on a Pending receipt | Receipt status → Verified | As expected | ✅ Pass |
| 5.5 | Reject a receipt | Click ❌ on a Pending receipt | Receipt status → Rejected | As expected | ✅ Pass |
| 5.6 | View flagged receipts | Upload a mismatched receipt | Appears under "⚠ Needs Officer Review" | As expected | ✅ Pass |
| 5.7 | Customer accessing officer routes | Log in as customer, visit `/officer/dashboard` | Redirected to officer login | As expected | ✅ Pass |

## 6. Reports

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 6.1 | Export PDF | Click "Export PDF" on dashboard | PDF downloads with loan table + totals + date | As expected | ✅ Pass |
| 6.2 | Export Excel | Click "Export Excel" on dashboard | XLSX downloads with same data | As expected | ✅ Pass |

## 7. Security

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 7.1 | Submit form without CSRF token | Strip hidden CSRF field, submit | Request rejected by Flask-WTF | As expected | ✅ Pass |
| 7.2 | SQL injection attempt | Enter `' OR '1'='1` in login username | Rejected — parameterized queries prevent injection | As expected | ✅ Pass |
| 7.3 | Direct file path guessing | Guess a receipt file URL for another user | File not linked anywhere in their UI (no discovery vector); direct path guessing still possible since uploads are served statically — noted as a known limitation | Static files are technically reachable if the exact filename is known | ⚠️ Noted limitation |

## 8. Deployment

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 8.1 | Homepage loads on live URL | Visit Render deployment link | Landing page renders correctly | As expected | ✅ Pass |
| 8.2 | Local MySQL vs Aiven (prod) switch | Compare env-var-driven `get_db()` locally vs deployed | Same code connects to correct DB in each environment | As expected | ✅ Pass |
| 8.3 | Missing environment variables | Deploy without DB env vars set | Falls back to `localhost` and fails clearly via custom error page | As expected (confirms fallback behavior is safe, not silent) | ✅ Pass |

## Summary

- **Total test cases:** 30
- **Passed:** 29
- **Known limitations noted:** 1 (static file paths for uploaded receipts are not individually access-controlled beyond not being linked in another user's UI)

All core functionality — authentication, loan CRUD, receipt upload, purpose
validation, utilization tracking, the officer approval workflow, and
reporting — has been manually tested end-to-end and works as intended
across both local and deployed environments.
