from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import check_for_updates

settings_bp = Blueprint('settings_bp', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def settings():
    return render_template('settings/settings.html')

@settings_bp.route('/customize')
@login_required
def settings_customize():
    return render_template('settings/settings_customize.html')

@settings_bp.route('/password')
@login_required
def settings_password():
    return render_template('settings/settings_password.html')
