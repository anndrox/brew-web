import os
import subprocess
import glob
import threading
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_file, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import ProgrammingError
from .models import db, User, AppSettings
from app.decorators import role_required
from app.utils import is_strong_password, check_for_updates, read_import_status_file
from datetime import datetime
import re

BACKUP_FOLDER = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_FOLDER, exist_ok=True)
IMPORT_STATUS_PATH = None

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/settings/admin')

@admin_bp.route('/')
@login_required
@role_required('admin')
def admin_settings():
    users = User.query.order_by(User.username).all()
    try:
        settings = AppSettings.query.first() or AppSettings()
    except ProgrammingError:
        # Likely missing new columns on restored backup; patch and retry once
        db.session.execute("ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';")
        db.session.commit()
        settings = AppSettings.query.first() or AppSettings()
    if not settings.unit_preference:
        settings.unit_preference = 'imperial'
    update_info = check_for_updates()
    backups = sorted(
        [f for f in os.listdir(BACKUP_FOLDER) if f.endswith(".sql")],
        reverse=True
    )
    import_status = _read_import_status()
    return render_template('settings/admin.html', users=users, settings=settings, update_info=update_info, backups=backups, import_status=import_status)

@admin_bp.route('/update-base-url', methods=['POST'])
@login_required
@role_required('admin')
def update_base_url():
    settings = AppSettings.query.first() or AppSettings()
    settings.base_url = request.form.get('base_url')
    unit_pref = request.form.get('unit_preference') or settings.unit_preference or 'imperial'
    settings.unit_preference = unit_pref if unit_pref in ('imperial', 'metric') else 'imperial'
    db.session.add(settings)
    db.session.commit()
    flash('Base URL updated.', 'success')
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/create-user', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('routes.admin_bp.admin_settings'))

    if not is_strong_password(password):
        flash('Weak password.', 'danger')
        return redirect(url_for('routes.admin_bp.admin_settings'))

    hashed = generate_password_hash(password)
    user = User(username=username, password_hash=hashed, role=role)
    db.session.add(user)
    db.session.commit()
    flash('User created.', 'success')
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    if user_id == current_user.id:
        flash("Cannot delete your own account.", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/update-password/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('password')
    user.set_password(new_pw)
    db.session.commit()
    flash("Password updated.", "success")
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/create-backup', methods=['POST'])
@login_required
@role_required('admin')
def create_backup():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"brewweb_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_FOLDER, filename)

    try:
        with open(backup_path, "w") as f:
            subprocess.run([
                "pg_dump",
                "-h", "db",
                "-U", "brewuser",
                "-d", "brewweb",
                "--no-owner",
                "--no-privileges",
                "--inserts"
            ], check=True, env={"PGPASSWORD": "brewpass"}, stdout=f)

        flash("New backup created successfully.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Backup failed: {e}", "danger")

    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/download-backup/<filename>')
@login_required
@role_required('admin')
def download_backup(filename):
    path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(path):
        flash("Backup file not found.", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))
    return send_file(path, as_attachment=True)

@admin_bp.route('/delete-backup/<filename>', methods=['POST'])
@login_required
@role_required('admin')
def delete_backup(filename):
    path = os.path.join(BACKUP_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        flash(f"{filename} deleted.", "success")
    else:
        flash("File not found.", "danger")
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/export-db')
@login_required
@role_required('admin')
def export_db():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"brewweb_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_FOLDER, filename)

    try:
        with open(backup_path, "w") as f_out:
            subprocess.run([
                "pg_dump",
                "-h", "db",
                "-U", "brewuser",
                "-d", "brewweb",
                "--no-owner",
                "--no-privileges",
                "--inserts",
                "--quote-all-identifiers"  # 👈 ensures "User" is preserved
            ], check=True, env={"PGPASSWORD": "brewpass"}, stdout=f_out)

        flash("Export completed successfully.", "success")
        return send_file(backup_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        flash(f"Export failed: {e}", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/import-db', methods=['POST'])
@login_required
@role_required('admin')
def import_db():
    file = request.files.get("backup_file")
    if not file:
        flash("No file selected.", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))

    filename = secure_filename(file.filename)
    if not filename.endswith(".sql"):
        flash("Invalid file format. Expected .sql", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))

    temp_path = os.path.join(BACKUP_FOLDER, filename)
    file.save(temp_path)

    try:
        _write_import_status("running", "Import started; this may take ~30s.")
        _start_background_import(temp_path)
        flash("Import started in background. You will be redirected to status.", "info")
    except Exception as e:
        _write_import_status("error", f"Failed to start import: {e}")
        flash(f"Import failed: {e}", "danger")

    return redirect(url_for('routes.admin_bp.import_status_page'))

@admin_bp.route('/import-status')
def import_status():
    status = _read_import_status()
    return jsonify(status or {"status": "idle", "message": "No import running"})

@admin_bp.route('/import-status/page')
@login_required
@role_required('admin')
def import_status_page():
    status = _read_import_status() or {"status": "idle", "message": "No import running"}
    return render_template('settings/import_status.html', import_status=status)

@admin_bp.route('/import-status/clear', methods=['POST'])
@login_required
@role_required('admin')
def clear_import_status():
    _clear_import_status()
    flash("Import status cleared.", "info")
    return redirect(url_for('routes.admin_bp.admin_settings'))

# ---- import helpers ----
def _start_background_import(sql_path):
    app = current_app._get_current_object()

    def worker():
        with app.app_context():
            env = os.environ.copy()
            env["PGPASSWORD"] = env.get("PGPASSWORD", "brewpass")
            try:
                _write_import_status("running", "Dropping schema…")
                subprocess.run(
                    ["psql", "-h", "db", "-U", "brewuser", "-d", "brewweb", "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"],
                    check=True,
                    env=env,
                )
                _write_import_status("running", "Importing SQL…")
                import_run = subprocess.run(
                    ["psql", "-h", "db", "-U", "brewuser", "-d", "brewweb", "-f", sql_path],
                    check=False,
                    env=env,
                )
                if import_run.returncode != 0:
                    _write_import_status("running", f"Import completed with return code {import_run.returncode}; continuing…")
                _write_import_status("running", "Applying schema fixes…")
                _apply_schema_fixes(env)
                _write_import_status("running", "Seeding yeast data…")
                subprocess.run(["flask", "seed-yeasts"], check=False, env=env, cwd=os.getcwd())
                _write_import_status("success", "Import completed and schema fixed.")
            except subprocess.CalledProcessError as e:
                _write_import_status("error", f"Import failed: {e}")
            except Exception as e:
                _write_import_status("error", f"Unexpected error: {e}")

    threading.Thread(target=worker, daemon=True).start()


def _write_import_status(status, message):
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
        path = os.path.join(current_app.instance_path, "import_status.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "status": status,
                "message": message,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }, f)
    except Exception:
        pass

def _read_import_status():
    return read_import_status_file()

def _clear_import_status():
    try:
        path = os.path.join(current_app.instance_path, "import_status.json")
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def _latest_local_revision():
    # Look for migrations in /app/migrations/versions
    base_dir = os.path.abspath(os.path.join(current_app.root_path, ".."))
    versions_path = os.path.join(base_dir, "migrations", "versions")
    try:
        entries = sorted([f for f in os.listdir(versions_path) if f.endswith(".py")])
        if not entries:
            return None
        revs = [re.split(r"[_\.]", f)[0] for f in entries]
        return revs[-1] if revs else None
    except Exception:
        return None

def _stamp_head_with_fallback(env):
    try:
        subprocess.run(["flask", "db", "stamp", "head"], check=True, env=env, cwd=os.getcwd())
        return
    except Exception:
        pass
    # Fallback: manually set alembic_version to local latest revision or known revision id
    rev = _latest_local_revision() or "d00abd51392a"
    try:
        db.session.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL);")
        db.session.execute("DELETE FROM alembic_version;")
        db.session.execute("INSERT INTO alembic_version (version_num) VALUES (:rev)", {"rev": rev})
        db.session.commit()
    except Exception:
        db.session.rollback()

def _apply_schema_fixes(env):
    commands = []
    # Create tables if missing
    commands.extend([
        """
        CREATE TABLE IF NOT EXISTS yeast (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            alcohol_type VARCHAR(20) NOT NULL,
            tolerance VARCHAR(50),
            strength VARCHAR(50),
            sweetness_retention VARCHAR(50),
            notes TEXT,
            flocculation VARCHAR(50),
            attenuation VARCHAR(10),
            is_default BOOLEAN DEFAULT FALSE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS recipe (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            alcohol_type VARCHAR(20),
            content TEXT,
            created_date TIMESTAMP,
            instructions TEXT,
            notes TEXT,
            water_type VARCHAR(50),
            yeast_id INTEGER REFERENCES yeast(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS batch (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER REFERENCES recipe(id),
            name VARCHAR(100) NOT NULL,
            start_date TIMESTAMP,
            end_date TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            username VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(512) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            role VARCHAR(50) DEFAULT 'user',
            theme VARCHAR(20) DEFAULT 'dark',
            font_size VARCHAR(10) DEFAULT '16px'
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ingredient (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER REFERENCES recipe(id),
            name VARCHAR(100) NOT NULL,
            amount_per_gallon FLOAT,
            unit VARCHAR(20),
            note VARCHAR(200)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS measurement (
            id SERIAL PRIMARY KEY,
            batch_id INTEGER REFERENCES batch(id),
            date TIMESTAMP,
            gravity FLOAT,
            ph FLOAT,
            temperature FLOAT,
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS calendar_event (
            id SERIAL PRIMARY KEY,
            batch_id INTEGER REFERENCES batch(id),
            title VARCHAR(100) NOT NULL,
            start DATE NOT NULL,
            "end" DATE,
            description TEXT,
            all_day BOOLEAN DEFAULT TRUE,
            created_by INTEGER REFERENCES "user"(id),
            note TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            id SERIAL PRIMARY KEY,
            base_url VARCHAR(255),
            unit_preference VARCHAR(10) DEFAULT 'imperial'
        );
        """
    ])
    # Add/patch columns to match current models
    commands.extend([
        "ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';",
        "ALTER TABLE recipe ADD COLUMN IF NOT EXISTS yeast_id INTEGER;",
        "ALTER TABLE recipe ADD CONSTRAINT IF NOT EXISTS recipe_yeast_id_fkey FOREIGN KEY (yeast_id) REFERENCES yeast(id);",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS batch_size FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS fermentation_temp VARCHAR(50);",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS initial_gravity FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS final_gravity FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS abv FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS yeast_type VARCHAR(100);",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS backsweetened BOOLEAN;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS flavor_additions TEXT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS pectic_used BOOLEAN;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS notes TEXT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS water_type VARCHAR(50);",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS alcohol_type VARCHAR(20);",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS tosna_total FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS tosna_per_day FLOAT;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS tosna_enabled BOOLEAN;",
        "ALTER TABLE batch ADD COLUMN IF NOT EXISTS yeast_id INTEGER;",
        "ALTER TABLE batch ADD CONSTRAINT IF NOT EXISTS batch_yeast_id_fkey FOREIGN KEY (yeast_id) REFERENCES yeast(id);",
        "ALTER TABLE ingredient ADD COLUMN IF NOT EXISTS amount_per_gallon FLOAT;",
        "ALTER TABLE ingredient ADD COLUMN IF NOT EXISTS unit VARCHAR(20);",
        "ALTER TABLE ingredient ADD COLUMN IF NOT EXISTS note VARCHAR(200);",
        "ALTER TABLE measurement ADD COLUMN IF NOT EXISTS ph FLOAT;",
        "ALTER TABLE measurement ADD COLUMN IF NOT EXISTS temperature FLOAT;"
    ])

    for cmd in commands:
        subprocess.run(
            ["psql", "-h", "db", "-U", "brewuser", "-d", "brewweb", "-c", cmd],
            check=False,
            env=env,
        )
