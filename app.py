import os
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask, abort, flash, redirect, render_template, request,
    send_from_directory, url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from constants import DISTRICTS, INDUSTRY_TYPES, OBSERVATION_TYPES, STATUSES, STATUS_DESCRIPTIONS
from db import get_db, init_app as init_db_app, init_db
from seed import seed_database


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def status_slug(value):
    return value.lower().replace(" ", "-")


def format_timestamp(value):
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return value


def report_or_404(report_code):
    report = get_db().execute(
        "SELECT * FROM reports WHERE report_code = ?", (report_code.upper(),)
    ).fetchone()
    if report is None:
        abort(404)
    return report


def get_counts(where="", params=()):
    db = get_db()
    base = f"SELECT status, COUNT(*) count FROM reports {where} GROUP BY status"
    rows = db.execute(base, params).fetchall()
    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row["status"]] = row["count"]
    total_sql = f"SELECT COUNT(*) FROM reports {where}"
    counts["Total"] = db.execute(total_sql, params).fetchone()[0]
    return counts


def validate_report_form(form, image):
    errors = {}
    required = {
        "observation_type": "Select what you observed.",
        "title": "Enter a short title.",
        "description": "Describe what you observed.",
        "district": "Select a Telangana district.",
        "locality": "Enter the locality, industrial area, mandal, or ULB.",
        "address_landmark": "Enter an address or nearby landmark.",
        "incident_date": "Select the incident date.",
        "incident_time": "Enter the approximate incident time.",
    }
    for field, message in required.items():
        if not form.get(field, "").strip():
            errors[field] = message
    if form.get("observation_type") and form.get("observation_type") not in OBSERVATION_TYPES:
        errors["observation_type"] = "Select a valid observation type."
    if form.get("district") and form.get("district") not in DISTRICTS:
        errors["district"] = "Select a valid Telangana district."
    if form.get("industry_type") and form.get("industry_type") not in INDUSTRY_TYPES:
        errors["industry_type"] = "Select a valid industry type."
    if len(form.get("title", "")) > 120:
        errors["title"] = "Keep the title under 120 characters."
    elif form.get("title", "").strip() and len(form.get("title", "").strip()) < 8:
        errors["title"] = "Use at least 8 characters for a clear title."
    if len(form.get("description", "")) > 3000:
        errors["description"] = "Keep the description under 3,000 characters."
    elif form.get("description", "").strip() and len(form.get("description", "").strip()) < 20:
        errors["description"] = "Add at least 20 characters describing what you observed."
    try:
        incident_date = date.fromisoformat(form.get("incident_date", ""))
        if incident_date > date.today():
            errors["incident_date"] = "Incident date cannot be in the future."
    except ValueError:
        if form.get("incident_date"):
            errors["incident_date"] = "Enter a valid incident date."
    if form.get("incident_time") and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", form["incident_time"]):
        errors["incident_time"] = "Enter a valid time."
    lat_text, lng_text = form.get("latitude", "").strip(), form.get("longitude", "").strip()
    if bool(lat_text) != bool(lng_text):
        errors["coordinates"] = "Provide both latitude and longitude, or leave both blank."
    elif lat_text and lng_text:
        try:
            lat, lng = float(lat_text), float(lng_text)
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
        except ValueError:
            errors["coordinates"] = "Enter valid latitude and longitude values."
    if image is None or not image.filename:
        errors["image"] = "Add a JPG, PNG, or WebP image as evidence."
    else:
        filename = secure_filename(image.filename)
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ALLOWED_EXTENSIONS or image.mimetype not in ALLOWED_MIME_TYPES:
            errors["image"] = "Use a JPG, JPEG, PNG, or WebP image."
    return errors


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    root = Path(app.root_path)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "telangana-hackathon-demo-key"),
        DATABASE=str(Path(app.instance_path, "pollution.db")),
        UPLOAD_FOLDER=str(root / "uploads"),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    init_db_app(app)

    @app.template_filter("datetime")
    def datetime_filter(value):
        return format_timestamp(value)

    @app.context_processor
    def inject_globals():
        return {
            "status_slug": status_slug,
            "status_descriptions": STATUS_DESCRIPTIONS,
            "statuses": STATUSES,
        }

    @app.route("/")
    def index():
        recent = get_db().execute("SELECT * FROM reports ORDER BY created_at DESC, id DESC LIMIT 3").fetchall()
        return render_template("index.html", counts=get_counts(), recent=recent)

    @app.route("/report", methods=("GET", "POST"))
    def submit_report():
        errors = {}
        if request.method == "POST":
            image = request.files.get("image")
            errors = validate_report_form(request.form, image)
            if not errors:
                extension = secure_filename(image.filename).rsplit(".", 1)[-1].lower()
                stored_name = f"{uuid4().hex}.{extension}"
                stored_path = Path(app.config["UPLOAD_FOLDER"], stored_name)
                image.save(stored_path)
                db = get_db()
                now = utc_now()
                try:
                    cursor = db.execute(
                        """INSERT INTO reports
                        (title, observation_type, industry_type, description, district, locality,
                         address_landmark, latitude, longitude, industrial_unit_name,
                         assigned_jurisdiction, incident_date, incident_time, image_filename,
                         status, submitter_key, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Reported', 'demo-citizen', ?, ?)""",
                        (request.form["title"].strip(), request.form["observation_type"],
                         request.form.get("industry_type") or None, request.form["description"].strip(),
                         request.form["district"], request.form["locality"].strip(),
                         request.form["address_landmark"].strip(),
                         float(request.form["latitude"]) if request.form.get("latitude", "").strip() else None,
                         float(request.form["longitude"]) if request.form.get("longitude", "").strip() else None,
                         request.form.get("industrial_unit_name", "").strip() or None,
                         request.form["district"], request.form["incident_date"],
                         request.form["incident_time"], stored_name, now, now),
                    )
                    report_id = cursor.lastrowid
                    report_code = f"INC-{datetime.now(timezone.utc).year}-{report_id:04d}"
                    db.execute("UPDATE reports SET report_code = ? WHERE id = ?", (report_code, report_id))
                    db.execute(
                        "INSERT INTO status_history (report_id, status, actor, created_at) VALUES (?, 'Reported', 'Citizen', ?)",
                        (report_id, now),
                    )
                    db.commit()
                except sqlite3.Error:
                    db.rollback()
                    stored_path.unlink(missing_ok=True)
                    app.logger.exception("Could not save report")
                    flash("We could not save the report. Please try again.", "error")
                else:
                    flash(f"Report {report_code} was submitted successfully.", "success")
                    return redirect(url_for("report_detail", report_code=report_code))
        return render_template(
            "report_form.html", errors=errors, districts=DISTRICTS,
            observation_types=OBSERVATION_TYPES, industry_types=INDUSTRY_TYPES,
            today=date.today().isoformat(), form=request.form,
        )

    @app.route("/reports")
    def reports():
        rows = get_db().execute("SELECT * FROM reports ORDER BY created_at DESC, id DESC").fetchall()
        return render_template("reports.html", reports=rows, title="Reported incidents", intro="Public incident register")

    @app.route("/my-reports")
    def my_reports():
        rows = get_db().execute(
            "SELECT * FROM reports WHERE submitter_key = 'demo-citizen' ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return render_template(
            "reports.html", reports=rows, counts=get_counts("WHERE submitter_key = ?", ("demo-citizen",)),
            title="My reports", intro="Demo Citizen workspace", is_mine=True,
        )

    @app.route("/reports/<report_code>")
    def report_detail(report_code):
        report = report_or_404(report_code)
        history = get_db().execute(
            "SELECT * FROM status_history WHERE report_id = ? ORDER BY created_at, id", (report["id"],)
        ).fetchall()
        return render_template("report_detail.html", report=report, history=history)

    @app.route("/authority")
    def authority_dashboard():
        rows = get_db().execute("SELECT * FROM reports ORDER BY created_at DESC, id DESC").fetchall()
        return render_template("authority_dashboard.html", reports=rows, counts=get_counts())

    @app.route("/authority/reports/<report_code>", methods=("GET", "POST"))
    def authority_report(report_code):
        report = report_or_404(report_code)
        errors = {}
        if request.method == "POST":
            status = request.form.get("status", "")
            remark = request.form.get("authority_remark", "").strip()
            action = request.form.get("action_taken", "").strip()
            if status not in STATUSES:
                errors["status"] = "Select a valid status."
            if len(remark) > 1000:
                errors["authority_remark"] = "Keep the public remark under 1,000 characters."
            if len(action) > 1000:
                errors["action_taken"] = "Keep the action under 1,000 characters."
            if status == report["status"] and not remark and not action:
                errors["form"] = "Change the status or add a public response."
            if not errors:
                now = utc_now()
                db = get_db()
                try:
                    current_remark = remark or report["authority_remark"]
                    current_action = action or report["action_taken"]
                    db.execute(
                        "UPDATE reports SET status = ?, authority_remark = ?, action_taken = ?, updated_at = ? WHERE id = ?",
                        (status, current_remark, current_action, now, report["id"]),
                    )
                    db.execute(
                        """INSERT INTO status_history
                        (report_id, status, public_remark, action_taken, actor, created_at)
                        VALUES (?, ?, ?, ?, 'Authority', ?)""",
                        (report["id"], status, remark or None, action or None, now),
                    )
                    db.commit()
                except sqlite3.Error:
                    db.rollback()
                    app.logger.exception("Could not update report")
                    flash("The update could not be saved. Please try again.", "error")
                else:
                    flash(f"{report_code.upper()} updated to {status}.", "success")
                    return redirect(url_for("authority_report", report_code=report_code.upper()))
        history = get_db().execute(
            "SELECT * FROM status_history WHERE report_id = ? ORDER BY created_at, id", (report["id"],)
        ).fetchall()
        return render_template("authority_report.html", report=report, history=history, errors=errors)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "healthy", "service": "Telangana Industrial Pollution Watch"}

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, title="Report or page not found", message="The requested page may have moved, or the report ID may be incorrect."), 404

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(error):
        return render_template("error.html", code=413, title="Image is too large", message="Please upload a JPG, PNG, or WebP image smaller than 8 MB."), 413

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", code=500, title="Something went wrong", message="The request could not be completed. Please try again."), 500

    with app.app_context():
        init_db()
        if not app.config.get("SKIP_SEED", False):
            seed_database(app.config["UPLOAD_FOLDER"])

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
