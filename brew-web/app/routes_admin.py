import os
import subprocess
import glob
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from .models import db, User, AppSettings
from app.decorators import role_required
from app.utils import is_strong_password, check_for_updates
from datetime import datetime

BACKUP_FOLDER = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_FOLDER, exist_ok=True)

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/settings/admin')

@admin_bp.route('/')
@login_required
@role_required('admin')
def admin_settings():
    users = User.query.order_by(User.username).all()
    settings = AppSettings.query.first() or AppSettings()
    update_info = check_for_updates()
    backups = sorted(
        [f for f in os.listdir(BACKUP_FOLDER) if f.endswith(".sql")],
        reverse=True
    )
    return render_template('settings/admin.html', users=users, settings=settings, update_info=update_info, backups=backups)

@admin_bp.route('/update-base-url', methods=['POST'])
@login_required
@role_required('admin')
def update_base_url():
    settings = AppSettings.query.first() or AppSettings()
    settings.base_url = request.form.get('base_url')
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

@admin_bp.route('/import-status')
def import_status():
    try:
        result = db.session.execute("SELECT 1 FROM user LIMIT 1")
        return "✅ User table exists. You may now use the app."
    except Exception:
        return "⏳ Still waiting for import to complete..."

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
        subprocess.Popen([
            "bash", "-c",
            f'psql -h db -U brewuser -d brewweb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" && psql -h db -U brewuser -d brewweb -f "{temp_path}"'
        ], env={"PGPASSWORD": "brewpass"})

        flash("Import started. Please wait 20–30 seconds, then refresh the app.", "info")

    except Exception as e:
        flash(f"Import failed: {e}", "danger")

    return redirect(url_for('routes.admin_bp.admin_settings'))


