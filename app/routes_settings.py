from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import is_strong_password
from .models import db

settings_bp = Blueprint('settings_bp', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def settings():
    return render_template('settings/settings.html')

@settings_bp.route('/customize', methods=['GET', 'POST'])
@login_required
def settings_customize():
    if request.method == 'POST':
        theme = request.form.get('theme')
        font_size = request.form.get('font_size')

        current_user.theme = theme if theme in {'dark', 'light'} else 'dark'
        current_user.font_size = font_size if font_size in {'14px', '16px', '18px'} else '16px'
        db.session.commit()

        flash("Preferences saved.", "success")
        return redirect(url_for('routes.settings_bp.settings_customize'))  # redirects to GET

    return render_template('settings/settings_customize.html')

@settings_bp.route('/password', methods=['GET', 'POST'])
@login_required
def settings_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        elif not is_strong_password(new_password):
            flash('Use at least 8 characters with upper- and lowercase letters, a number, and a symbol.', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('routes.settings_bp.settings_password'))

    return render_template('settings/settings_password.html')
