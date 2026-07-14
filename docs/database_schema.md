# Database Schema

**Database name:** `loan_db`
**Engine:** MySQL

## Table: `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | Unique user ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login identifier |
| password | VARCHAR(255) | NOT NULL | Hashed password (Werkzeug PBKDF2, never plain text) |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | `'user'` (customer) or `'officer'` |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation time |

## Table: `loans`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | Unique loan ID |
| username | VARCHAR(50) | FK → users(username), NOT NULL | Loan owner |
| amount | DECIMAL(12,2) | NOT NULL | Sanctioned loan amount |
| purpose | VARCHAR(100) | NOT NULL | One of the fixed loan purposes (Education, Medical, Wedding, etc.) |
| loan_date | DATE | NOT NULL | Date the loan was applied for |
| status | VARCHAR(20) | DEFAULT 'Pending' | Pending / Approved / Rejected / Completed |
| remarks | VARCHAR(255) | NULLABLE | Officer's note explaining their decision |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

## Table: `receipts`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | Unique receipt ID |
| loan_id | INT | FK → loans(id), NOT NULL | Which loan this receipt is proof for |
| username | VARCHAR(50) | FK → users(username), NOT NULL | Uploader |
| file_path | VARCHAR(255) | NOT NULL | Path to the uploaded file on disk |
| category | VARCHAR(50) | NOT NULL | Category selected at upload (same fixed list as loan purposes) |
| amount | DECIMAL(12,2) | NOT NULL | Amount this receipt accounts for |
| status | VARCHAR(20) | DEFAULT 'Pending' | Pending / Verified / Rejected |
| needs_review | TINYINT(1) | DEFAULT 0 | Auto-set to 1 if `category` ≠ the loan's `purpose` |
| remarks | VARCHAR(255) | NULLABLE | Officer's note on this receipt |
| uploaded_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Upload time |

## Relationships
- `loans.username` → `users.username` (ON DELETE CASCADE)
- `receipts.loan_id` → `loans.id` (ON DELETE CASCADE)
- `receipts.username` → `users.username` (ON DELETE CASCADE)

## Full SQL

```sql
CREATE DATABASE IF NOT EXISTS loan_db;
USE loan_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    loan_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    remarks VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE receipts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    needs_review TINYINT(1) NOT NULL DEFAULT 0,
    remarks VARCHAR(255) DEFAULT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
