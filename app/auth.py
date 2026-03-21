import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User
from sqlalchemy import inspect

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.before_app_request
def require_setup_or_reset():
    from flask import request

    # Skip static assets
    if request.endpoint in ('static',):
        return

    # If no user exists yet, redirect to setup
    if not User.query.first() and request.endpoint != 'auth_bp.setup':
        return redirect(url_for('auth_bp.setup'))

    # If a force_reset flag is present, require reset
    flag_path = os.path.join(current_app.instance_path, 'force_reset.flag')
    if os.path.exists(flag_path):
        allowed_endpoints = ['auth_bp.reset_password', 'auth_bp.login', 'auth_bp.setup', 'static']
        if request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth_bp.reset_password'))

@auth_bp.route('/force-reset', methods=['POST'])
@login_required
def trigger_force_reset():
    if not current_user.is_admin:  # adjust this check if needed
        flash("You are not authorized to do this.", "danger")
        return redirect(url_for("index"))

    flag_path = os.path.join(current_app.instance_path, 'force_reset.flag')
    os.makedirs(current_app.instance_path, exist_ok=True)
    with open(flag_path, 'w') as f:
        f.write('1')

    flash("Forced password reset activated.", "success")
    return redirect(url_for("index"))

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if User.query.first():
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # ✅ new field

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth_bp.setup'))

        user = User(
            username=username,
            is_admin=True,
            role='admin'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Ensure a force reset is NOT pending for fresh setups
        flag_path = os.path.join(current_app.instance_path, 'force_reset.flag')
        if os.path.exists(flag_path):
            os.remove(flag_path)

        login_user(user)
        flash('Admin account created and logged in.', 'success')
        return redirect(url_for('routes.index'))

    return render_template('setup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.index'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    # Reset password even if not logged in (as long as a user exists)
    if not User.query.first():
        return redirect(url_for('auth_bp.setup'))

    user = current_user if current_user.is_authenticated else User.query.first()
    flag_path = os.path.join(current_app.instance_path, 'force_reset.flag')

    if request.method == 'POST':
        new = request.form['new_password']
        confirm = request.form['confirm_password']

        if new != confirm:
            flash('Passwords do not match.', 'error')
        elif len(new) < 6:
            flash('Password too short.', 'error')
        else:
            user.set_password(new)
            db.session.commit()
            # Removing the flag unlocks normal access
            if os.path.exists(flag_path):
                os.remove(flag_path)
            flash('Password changed successfully. Please log in.', 'success')
            return redirect(url_for('auth_bp.login'))

    return render_template('auth/reset_password.html')
