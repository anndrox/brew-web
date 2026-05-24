import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db, oauth
from .models import User

auth_bp = Blueprint('auth_bp', __name__)


def oidc_enabled():
    config = current_app.config
    return all([
        config.get('OIDC_ENABLED'),
        config.get('OIDC_DISCOVERY_URL'),
        config.get('OIDC_CLIENT_ID'),
        config.get('OIDC_CLIENT_SECRET'),
    ])


def local_login_enabled():
    return not current_app.config.get('DISABLE_LOCAL_LOGIN', False)


def oidc_client():
    client = oauth.create_client('authentik')
    if client is None:
        oauth.register(
            name='authentik',
            server_metadata_url=current_app.config['OIDC_DISCOVERY_URL'],
            client_id=current_app.config['OIDC_CLIENT_ID'],
            client_secret=current_app.config['OIDC_CLIENT_SECRET'],
            client_kwargs={'scope': current_app.config['OIDC_SCOPES']},
        )
        client = oauth.create_client('authentik')
    return client


def map_role(groups):
    group_set = {group for group in groups if group}
    admin_groups = set(current_app.config.get('OIDC_ADMIN_GROUPS', []))
    editor_groups = set(current_app.config.get('OIDC_EDITOR_GROUPS', []))

    if admin_groups & group_set:
        return 'admin', True
    if editor_groups & group_set:
        return 'editor', False
    return 'viewer', False


def unique_username(candidate):
    base = (candidate or 'brew-user').strip() or 'brew-user'
    username = base
    suffix = 1
    while User.query.filter_by(username=username).first():
        suffix += 1
        username = f'{base}-{suffix}'
    return username


def sync_oidc_user(claims):
    username_claim = current_app.config.get('OIDC_USERNAME_CLAIM', 'preferred_username')
    email_claim = current_app.config.get('OIDC_EMAIL_CLAIM', 'email')
    name_claim = current_app.config.get('OIDC_NAME_CLAIM', 'name')
    groups_claim = current_app.config.get('OIDC_GROUPS_CLAIM', 'groups')

    subject = claims.get('sub')
    email = claims.get(email_claim)
    preferred_username = claims.get(username_claim) or email or subject
    display_name = claims.get(name_claim) or preferred_username
    groups = claims.get(groups_claim) or []
    if isinstance(groups, str):
        groups = [group.strip() for group in groups.split(',') if group.strip()]

    role, is_admin = map_role(groups)
    first_user = User.query.count() == 0
    if first_user:
        role, is_admin = 'admin', True

    user = None
    if subject:
        user = User.query.filter_by(oidc_subject=subject).first()
    if user is None and email:
        user = User.query.filter_by(email=email).first()
    if user is None and preferred_username:
        user = User.query.filter_by(username=preferred_username).first()

    if user is None:
        user = User(
            username=unique_username(preferred_username),
            auth_source='oidc',
        )

    user.oidc_subject = subject
    user.email = email
    user.display_name = display_name
    user.auth_source = 'oidc'
    user.role = role
    user.is_admin = is_admin
    user.last_login_at = datetime.utcnow()
    if not user.username:
        user.username = unique_username(preferred_username)

    db.session.add(user)
    db.session.commit()
    return user

@auth_bp.before_app_request
def require_setup_or_reset():
    from flask import request

    # Skip static assets
    if request.endpoint in ('static', 'health'):
        return

    # If no user exists yet, redirect to setup
    if not User.query.first() and not oidc_enabled() and request.endpoint != 'auth_bp.setup':
        return redirect(url_for('auth_bp.setup'))

    # If a force_reset flag is present, require reset
    flag_path = os.path.join(current_app.instance_path, 'force_reset.flag')
    if os.path.exists(flag_path) and local_login_enabled():
        allowed_endpoints = ['auth_bp.reset_password', 'auth_bp.login', 'auth_bp.setup', 'auth_bp.oidc_login', 'auth_bp.oidc_callback', 'static']
        if request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth_bp.reset_password'))

@auth_bp.route('/force-reset', methods=['POST'])
@login_required
def trigger_force_reset():
    if not local_login_enabled():
        flash('Password resets are disabled while OIDC SSO is enabled.', 'warning')
        return redirect(url_for('routes.admin_bp.admin_settings'))

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
    if oidc_enabled():
        return render_template('setup.html')

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
    if oidc_enabled() and not local_login_enabled():
        return render_template('login.html')

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


@auth_bp.route('/oidc/login')
def oidc_login():
    if not oidc_enabled():
        return redirect(url_for('auth_bp.login'))

    redirect_uri = url_for('auth_bp.oidc_callback', _external=True)
    return oidc_client().authorize_redirect(redirect_uri)


@auth_bp.route('/oidc/callback')
def oidc_callback():
    if not oidc_enabled():
        return redirect(url_for('auth_bp.login'))

    token = oidc_client().authorize_access_token()
    claims = token.get('userinfo')
    if not claims:
        claims = oidc_client().userinfo()

    user = sync_oidc_user(claims)
    login_user(user)
    flash('Signed in with Authentik.', 'success')
    return redirect(url_for('routes.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if not local_login_enabled():
        flash('Local password login is disabled.', 'warning')
        return redirect(url_for('auth_bp.login'))

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
