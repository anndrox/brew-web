from flask import Flask, redirect, url_for, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils import check_for_updates
from config import Config
from markupsafe import Markup, escape
import traceback
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(get_remote_address)
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'
    csrf.init_app(app)

    from .models import User

    @app.route('/')
    def root():
        return redirect('/app/')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def require_setup():
        allowed = {'auth_bp.setup', 'static'}

        if request.endpoint is None or request.endpoint in allowed:
            return

        try:
            if not User.query.first():
                return redirect(url_for("auth_bp.setup"))
        except Exception:
            # Table likely doesn't exist yet during import
            return render_template("errors/import_wait.html"), 503

    @app.context_processor
    def inject_theme():
        if current_user.is_authenticated:
            return {"theme": current_user.theme}
        return {"theme": "dark"}

    @app.context_processor
    def inject_globals():
        return {
            "app_version": Config.VERSION,
            "update_info": check_for_updates()
        }

    @app.template_filter('nl2br')
    def nl2br_filter(s):
        return Markup('<br>'.join(escape(s).splitlines()))

    from .routes_calculators import calculator_bp
    app.register_blueprint(calculator_bp)

    from . import routes
    app.register_blueprint(routes.routes)

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # --- Logging Setup ---
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/brewweb.log', maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info('✅ Application startup')
    app.logger.info(f'✅ Brew Web v{Config.VERSION} started')

    # --- Error Handlers ---
    def log_error_and_render(error, template, code):
        user = getattr(current_user, 'username', 'anonymous')
        app.logger.warning(f"{code} ERROR: {error} (User: {user}, IP: {request.remote_addr})", exc_info=True)
        return render_template(template, error=error), code

    @app.errorhandler(400)
    def bad_request(error):
        return log_error_and_render(error, "errors/400.html", 400)

    @app.errorhandler(403)
    def forbidden(error):
        return log_error_and_render(error, "errors/403.html", 403)

    @app.errorhandler(404)
    def not_found(error):
        return log_error_and_render(error, "errors/404.html", 404)

    @app.errorhandler(500)
    def internal_error(error):
        return log_error_and_render(error, "errors/500.html", 500)

    return app
