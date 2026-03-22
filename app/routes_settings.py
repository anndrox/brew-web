from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import check_for_updates

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

        current_user.theme = theme
        current_user.font_size = font_size
        from .models import db
        db.session.commit()

        flash("Preferences saved.", "success")
        return redirect(url_for('routes.settings_bp.settings_customize'))  # redirects to GET

    return render_template('settings/settings_customize.html')

@settings_bp.route('/password')
@login_required
def settings_password():
    return render_template('settings/settings_password.html')
