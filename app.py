import os
from datetime import date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_file, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
import mysql.connector

from reports import build_pdf_report, build_excel_report

# ============================================================
# APP CONFIG
# ============================================================
app = Flask(__name__)
# Secret key: reads from an environment variable if set, otherwise generates
# a random one at startup. A random fallback is safer than a hardcoded string,
# but note that sessions will be invalidated every time the app restarts
# unless LOAN_APP_SECRET is set explicitly.
app.secret_key = os.environ.get("LOAN_APP_SECRET") or os.urandom(24).hex()

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads", "receipts")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

csrf = CSRFProtect(app)

# ============================================================
# LOAN PURPOSES (Phase 7 - Purpose Validation)
# ============================================================
# This is the single source of truth for loan purposes AND receipt
# categories. Using the exact same list for both means a receipt either
# matches the loan's purpose exactly, or it doesn't - no guessing needed.
LOAN_PURPOSES = [
    "Education",
    "Medical",
    "Wedding",
    "Home Renovation",
    "Travel",
    "Vehicle",
    "Agriculture",
    "Business",
    "Housing",
    "Consumer Durables",
    "Personal",
]

REMINDER_THRESHOLDS = [
    (21, "Final Reminder"),
    (14, "Reminder 2"),
    (7, "Reminder 1"),
]


# ============================================================
# DATABASE HELPER
# ============================================================
# MySQL password is read from an environment variable so it's never
# committed to code. Set it before running the app, e.g. in PowerShell:
#   $env:MYSQL_PASSWORD="your_real_password"
# Falls back to a placeholder so the app still tells you clearly what's
# missing instead of silently using the wrong password.
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "nila252006")


def get_db():
    """Opens a MySQL connection. Raises a clear error if the DB is unreachable
    so routes can catch it and show a friendly message instead of crashing."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password=MYSQL_PASSWORD,
            database="loan_db",
        )
    except mysql.connector.Error as err:
        raise RuntimeError(f"Database connection failed: {err}") from err


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def reminder_stage(loan_date_value, status):
    """Returns a reminder label if a Pending loan has aged past a threshold (Phase 8)."""
    if status != "Pending" or not loan_date_value:
        return None
    days_pending = (date.today() - loan_date_value).days
    for threshold, label in REMINDER_THRESHOLDS:
        if days_pending >= threshold:
            return label
    return None


# ============================================================
# ACCESS CONTROL DECORATORS (Phase 11)
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session or session.get("role") != "user":
            flash("Please log in to continue.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def officer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session or session.get("role") != "officer":
            flash("Please log in as an officer to continue.")
            return redirect(url_for("officer_login"))
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# HOME
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# GLOBAL ERROR HANDLING (Phase 11)
# ============================================================
@app.errorhandler(RuntimeError)
def handle_db_error(e):
    """Catches DB connection failures raised from get_db() so the user sees
    a friendly page instead of Flask's raw 'Internal Server Error'."""
    return render_template("error.html", message=str(e)), 500


@app.errorhandler(500)
def handle_generic_error(e):
    return render_template("error.html", message="An unexpected error occurred."), 500


# ============================================================
# USER AUTH
# ============================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 3 or len(password) < 6:
            flash("Username must be 3+ chars and password 6+ chars.")
            return render_template("register.html")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            flash("That username is already taken.")
            cursor.close()
            conn.close()
            return render_template("register.html")

        hashed = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users(username, password, role) VALUES(%s, %s, 'user')",
            (username, hashed),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND role='user'", (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password ❌")

    return render_template("login.html")


@app.route("/officer_login", methods=["GET", "POST"])
def officer_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND role='officer'", (username,)
        )
        officer = cursor.fetchone()
        cursor.close()
        conn.close()

        if officer and check_password_hash(officer["password"], password):
            session["user"] = username
            session["role"] = "officer"
            return redirect(url_for("officer_dashboard"))

        return render_template("officer_login.html", error="Invalid officer credentials ❌")

    return render_template("officer_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# UTILIZATION HELPERS (Phase 4)
# ============================================================
def attach_utilization(cursor, loan):
    """Adds used_amount / remaining_amount / utilization_pct / reminder to a loan dict."""
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS used FROM receipts "
        "WHERE loan_id=%s AND status='Verified'",
        (loan["id"],),
    )
    used = float(cursor.fetchone()["used"])
    amount = float(loan["amount"])

    loan["used_amount"] = used
    loan["remaining_amount"] = max(amount - used, 0)
    loan["utilization_pct"] = round((used / amount) * 100, 1) if amount > 0 else 0
    loan["reminder"] = reminder_stage(loan.get("loan_date"), loan.get("status"))
    return loan


# ============================================================
# USER DASHBOARD
# ============================================================
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    search = request.args.get("search")
    if search:
        cursor.execute(
            "SELECT * FROM loans WHERE username=%s AND purpose LIKE %s ORDER BY loan_date DESC",
            (session["user"], "%" + search + "%"),
        )
    else:
        cursor.execute(
            "SELECT * FROM loans WHERE username=%s ORDER BY loan_date DESC",
            (session["user"],),
        )

    loans = cursor.fetchall()
    for loan in loans:
        attach_utilization(cursor, loan)

        cursor.execute(
            "SELECT * FROM receipts WHERE loan_id=%s ORDER BY uploaded_at DESC",
            (loan["id"],),
        )
        loan["receipts"] = cursor.fetchall()

    total_loans = len(loans)
    total_amount = sum(float(l["amount"]) for l in loans)
    total_used = sum(l["used_amount"] for l in loans)
    total_remaining = sum(l["remaining_amount"] for l in loans)
    pending_count = sum(1 for l in loans if l["status"] == "Pending")
    approved_count = sum(1 for l in loans if l["status"] == "Approved")
    rejected_count = sum(1 for l in loans if l["status"] == "Rejected")
    completed_count = sum(1 for l in loans if l["status"] == "Completed")
    verified_receipts = sum(
        1 for l in loans for r in l["receipts"] if r["status"] == "Verified"
    )

    cursor.close()
    conn.close()

    chart_data = {
        "total_amount": total_amount,
        "total_used": total_used,
        "total_remaining": total_remaining,
        "pending_count": pending_count,
        "verified_receipts": verified_receipts,
    }

    return render_template(
        "dashboard.html",
        loans=loans,
        user=session["user"],
        total_loans=total_loans,
        total_amount=total_amount,
        total_used=total_used,
        total_remaining=total_remaining,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        completed_count=completed_count,
        search=search,
        chart_data=chart_data,
    )


# ============================================================
# LOAN CRUD
# ============================================================
@app.route("/loan")
@login_required
def loan_page():
    return render_template("loan.html", user=session["user"], purposes=LOAN_PURPOSES)


@app.route("/add_loan", methods=["POST"])
@login_required
def add_loan():
    amount = request.form["amount"]
    loan_date = request.form["loan_date"]
    purpose = request.form["purpose"].strip()

    if purpose not in LOAN_PURPOSES:
        flash("Please select a valid loan purpose from the list.")
        return redirect(url_for("loan_page"))

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid loan amount.")
        return redirect(url_for("loan_page"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO loans(username, amount, loan_date, purpose, status) "
        "VALUES(%s, %s, %s, %s, 'Pending')",
        (session["user"], amount_val, loan_date, purpose),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Loan added successfully.")
    return redirect(url_for("dashboard"))


@app.route("/edit_loan/<int:loan_id>", methods=["GET", "POST"])
@login_required
def edit_loan(loan_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM loans WHERE id=%s AND username=%s",
        (loan_id, session["user"]),
    )
    loan = cursor.fetchone()
    if not loan:
        cursor.close()
        conn.close()
        abort(404)

    # Only Pending loans can be edited once an officer has started reviewing it
    if request.method == "POST":
        if loan["status"] != "Pending":
            flash("This loan has already been reviewed and can no longer be edited.")
            cursor.close()
            conn.close()
            return redirect(url_for("dashboard"))

        amount = request.form["amount"]
        purpose = request.form["purpose"].strip()
        loan_date_val = request.form.get("loan_date", loan["loan_date"])

        if purpose not in LOAN_PURPOSES:
            flash("Please select a valid loan purpose from the list.")
            cursor.close()
            conn.close()
            return redirect(url_for("edit_loan", loan_id=loan_id))

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid loan amount.")
            cursor.close()
            conn.close()
            return redirect(url_for("edit_loan", loan_id=loan_id))

        cursor.execute(
            "UPDATE loans SET amount=%s, purpose=%s, loan_date=%s "
            "WHERE id=%s AND username=%s",
            (amount_val, purpose, loan_date_val, loan_id, session["user"]),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Loan updated.")
        return redirect(url_for("dashboard"))

    cursor.close()
    conn.close()
    return render_template("edit_loan.html", loan=loan, purposes=LOAN_PURPOSES)


@app.route("/delete_loan/<int:loan_id>")
@login_required
def delete_loan(loan_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM loans WHERE id=%s AND username=%s",
        (loan_id, session["user"]),
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Loan deleted.")
    return redirect(url_for("dashboard"))


# ============================================================
# RECEIPT UPLOAD (Phase 3) + PURPOSE VALIDATION (Phase 7)
# ============================================================
@app.route("/upload_receipt/<int:loan_id>", methods=["GET", "POST"])
@login_required
def upload_receipt(loan_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM loans WHERE id=%s AND username=%s",
        (loan_id, session["user"]),
    )
    loan = cursor.fetchone()
    if not loan:
        cursor.close()
        conn.close()
        abort(404)

    if request.method == "POST":
        file = request.files.get("receipt")
        category = request.form.get("category", "Other")
        amount = request.form.get("amount")

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except (TypeError, ValueError):
            flash("Enter a valid receipt amount.")
            cursor.close()
            conn.close()
            return redirect(url_for("upload_receipt", loan_id=loan_id))

        if not file or file.filename == "":
            flash("Please choose a file to upload.")
            cursor.close()
            conn.close()
            return redirect(url_for("upload_receipt", loan_id=loan_id))

        if not allowed_file(file.filename):
            flash("Invalid file type. Only PNG, JPG, JPEG, PDF allowed.")
            cursor.close()
            conn.close()
            return redirect(url_for("upload_receipt", loan_id=loan_id))

        filename = secure_filename(f"{loan_id}_{session['user']}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Phase 7: flag if the receipt's category doesn't exactly match the
        # loan's purpose - both come from the same LOAN_PURPOSES list, so
        # this is an exact comparison, not a guess.
        needs_review = 1 if category != loan["purpose"] else 0

        cursor.execute(
            "INSERT INTO receipts(loan_id, username, file_path, category, amount, "
            "status, needs_review) VALUES(%s, %s, %s, %s, %s, 'Pending', %s)",
            (loan_id, session["user"], filepath, category, amount_val, needs_review),
        )
        conn.commit()
        cursor.close()
        conn.close()

        if needs_review:
            flash(f"Receipt uploaded, but flagged for officer review "
                  f"(receipt category '{category}' doesn't match loan purpose '{loan['purpose']}').")
        else:
            flash("Receipt uploaded successfully.")
        return redirect(url_for("dashboard"))

    cursor.close()
    conn.close()
    return render_template("upload_receipt.html", loan=loan, purposes=LOAN_PURPOSES)


# ============================================================
# OFFICER PORTAL (Phase 5) + RECEIPT VERIFICATION (Phase 6)
# ============================================================
@app.route("/officer/dashboard")
@officer_required
def officer_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM loans ORDER BY loan_date DESC")
    loans = cursor.fetchall()
    for loan in loans:
        attach_utilization(cursor, loan)
        cursor.execute(
            "SELECT * FROM receipts WHERE loan_id=%s ORDER BY uploaded_at DESC",
            (loan["id"],),
        )
        loan["receipts"] = cursor.fetchall()

    cursor.close()
    conn.close()

    pending_loans = [l for l in loans if l["status"] == "Pending"]
    flagged_receipts = [
        r for l in loans for r in l["receipts"] if r["needs_review"]
    ]

    return render_template(
        "officer_dashboard.html",
        loans=loans,
        pending_loans=pending_loans,
        flagged_receipts=flagged_receipts,
        officer=session["user"],
    )


@app.route("/officer/loan/<int:loan_id>/status", methods=["POST"])
@officer_required
def officer_update_loan_status(loan_id):
    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()

    if new_status not in ("Approved", "Rejected", "Completed", "Pending"):
        flash("Invalid status.")
        return redirect(url_for("officer_dashboard"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE loans SET status=%s, remarks=%s WHERE id=%s",
        (new_status, remarks, loan_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"Loan #{loan_id} marked as {new_status}.")
    return redirect(url_for("officer_dashboard"))


@app.route("/officer/receipt/<int:receipt_id>/status", methods=["POST"])
@officer_required
def officer_update_receipt_status(receipt_id):
    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()

    if new_status not in ("Verified", "Rejected", "Pending"):
        flash("Invalid status.")
        return redirect(url_for("officer_dashboard"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE receipts SET status=%s, remarks=%s WHERE id=%s",
        (new_status, remarks, receipt_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"Receipt #{receipt_id} marked as {new_status}.")
    return redirect(url_for("officer_dashboard"))


# ============================================================
# REPORTS (Phase 10)
# ============================================================
@app.route("/export/pdf")
@login_required
def export_pdf():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM loans WHERE username=%s ORDER BY loan_date DESC",
        (session["user"],),
    )
    loans = cursor.fetchall()
    for loan in loans:
        attach_utilization(cursor, loan)
    cursor.close()
    conn.close()

    filepath = build_pdf_report(session["user"], loans)
    return send_file(filepath, as_attachment=True, download_name="loan_report.pdf")


@app.route("/export/excel")
@login_required
def export_excel():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM loans WHERE username=%s ORDER BY loan_date DESC",
        (session["user"],),
    )
    loans = cursor.fetchall()
    for loan in loans:
        attach_utilization(cursor, loan)
    cursor.close()
    conn.close()

    filepath = build_excel_report(session["user"], loans)
    return send_file(filepath, as_attachment=True, download_name="loan_report.xlsx")


# ============================================================
# RUN APP
# ============================================================
if __name__ == "__main__":
    print("Flask starting...")
    app.run(debug=True)
