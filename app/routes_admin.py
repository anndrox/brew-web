import os
import subprocess
import threading
import json
import tempfile
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_file, send_from_directory, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from .models import db, User, AppSettings
from app.decorators import role_required
from app.utils import is_strong_password, check_for_updates, read_import_status_file
from datetime import UTC, datetime

BACKUP_FOLDER = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_FOLDER, exist_ok=True)
IMPORT_STATUS_PATH = None
_import_lock = threading.Lock()


def _postgres_env():
    env = os.environ.copy()
    env['PGPASSWORD'] = db.engine.url.password or ''
    env['PGCONNECT_TIMEOUT'] = '5'
    return env


def _postgres_command(tool):
    url = db.engine.url
    if url.get_backend_name() != 'postgresql':
        abort(400, 'PostgreSQL backup tools require a PostgreSQL database.')
    return [tool, '-h', url.host or 'localhost', '-p', str(url.port or 5432),
            '-U', url.username or '', '-d', url.database or '']


def _backup_path(filename):
    safe_name = secure_filename(filename)
    if safe_name != filename or not safe_name.endswith(('.sql', '.dump')):
        abort(400)
    return safe_name, os.path.join(BACKUP_FOLDER, safe_name)

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/settings/admin')

@admin_bp.route('/')
@login_required
@role_required('admin')
def admin_settings():
    users = User.query.order_by(User.username).all()
    settings = AppSettings.query.first() or AppSettings()
    if not settings.unit_preference:
        settings.unit_preference = 'imperial'
    update_info = check_for_updates()
    backups = sorted(
        [f for f in os.listdir(BACKUP_FOLDER) if f.endswith((".sql", ".dump"))],
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
    if role == 'viewer':
        role = 'user'  # Historical UI label; both remain read-only.

    if role not in {'admin', 'editor', 'user'}:
        flash('Invalid role.', 'danger')
        return redirect(url_for('routes.admin_bp.admin_settings'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('routes.admin_bp.admin_settings'))

    if not is_strong_password(password):
        flash('Use at least 8 characters with upper- and lowercase letters, a number, and a symbol.', 'danger')
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

    user = db.get_or_404(User, user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/update-password/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_password(user_id):
    user = db.get_or_404(User, user_id)
    new_pw = request.form.get('password')
    if not is_strong_password(new_pw):
        flash('Use at least 8 characters with upper- and lowercase letters, a number, and a symbol.', 'danger')
        return redirect(url_for('routes.admin_bp.admin_settings'))
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
            subprocess.run(_postgres_command('pg_dump') + [
                "--no-owner",
                "--no-privileges",
                "--inserts"
            ], check=True, env=_postgres_env(), stdout=f)

        flash("New backup created successfully.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Backup failed: {e}", "danger")

    return redirect(url_for('routes.admin_bp.admin_settings'))

@admin_bp.route('/download-backup/<filename>')
@login_required
@role_required('admin')
def download_backup(filename):
    safe_name, path = _backup_path(filename)
    if not os.path.exists(path):
        flash("Backup file not found.", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))
    return send_from_directory(BACKUP_FOLDER, safe_name, as_attachment=True)

@admin_bp.route('/delete-backup/<filename>', methods=['POST'])
@login_required
@role_required('admin')
def delete_backup(filename):
    safe_name, path = _backup_path(filename)
    if os.path.exists(path):
        os.remove(path)
        flash(f"{safe_name} deleted.", "success")
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
            subprocess.run(_postgres_command('pg_dump') + [
                "--no-owner",
                "--no-privileges",
                "--inserts",
                "--quote-all-identifiers"  # 👈 ensures "User" is preserved
            ], check=True, env=_postgres_env(), stdout=f_out)

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
    if not filename.endswith((".sql", ".dump")):
        flash("Invalid file format. Expected .sql or .dump from pg_dump.", "danger")
        return redirect(url_for('routes.admin_bp.admin_settings'))

    if not _import_lock.acquire(blocking=False):
        flash("An import is already running.", "danger")
        return redirect(url_for('routes.admin_bp.import_status_page'))

    try:
        # Do not overwrite the owner's existing backup with an upload.
        with tempfile.NamedTemporaryFile(dir=BACKUP_FOLDER, prefix='import-',
                                         suffix=os.path.splitext(filename)[1], delete=False) as upload:
            temp_path = upload.name
            file.save(upload)
        _write_import_status("running", "Import started; this may take ~30s.")
        _start_background_import(temp_path)
        flash("Import started in background. You will be redirected to status.", "info")
    except Exception as e:
        if _import_lock.locked():
            _import_lock.release()
        _write_import_status("error", f"Failed to start import: {e}")
        flash(f"Import failed: {e}", "danger")

    return redirect(url_for('routes.admin_bp.import_status_page'))

@admin_bp.route('/import-status')
@login_required
@role_required('admin')
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
    if (_read_import_status() or {}).get('status') == 'running':
        flash("Cannot clear status while an import is running.", "danger")
        return redirect(url_for('routes.admin_bp.import_status_page'))
    _clear_import_status()
    flash("Import status cleared.", "info")
    return redirect(url_for('routes.admin_bp.admin_settings'))

# ---- import helpers ----
def _start_background_import(sql_path):
    app = current_app._get_current_object()

    def worker():
        with app.app_context():
            try:
                _write_import_status("running", "Validating and restoring backup transactionally…")
                from app.database import restore_backup
                restore_backup(sql_path, db.engine)
                db.session.remove()
                _write_import_status("success", "Import committed; schema and administrator verified. Sign in using the restored account.")
            except Exception:
                db.session.rollback()
                app.logger.exception("Database restore failed; transaction rolled back")
                _write_import_status("error", "Restore failed and was rolled back. Original database retained; check the local application log.")
            finally:
                try:
                    os.remove(sql_path)
                finally:
                    _import_lock.release()

    try:
        threading.Thread(target=worker, daemon=True).start()
    except Exception:
        _import_lock.release()
        raise
def _write_import_status(status, message):
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
        path = os.path.join(current_app.instance_path, "import_status.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "status": status,
                "message": message,
                "updated_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
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
