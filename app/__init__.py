from flask import Flask, redirect, url_for, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils import check_for_updates, get_unit_preference
from config import Config
from markupsafe import Markup, escape
import traceback, os, logging, click
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
            return render_template("errors/import_wait.html"), 503

    @app.before_request
    def guard_import_in_progress():
        from app.utils import read_import_status_file
        allowed = {
            'routes.admin_bp.import_status',
            'routes.admin_bp.import_status_page',
            'routes.admin_bp.import_db',
            'routes.admin_bp.admin_settings',
            'static'
        }
        if request.endpoint in allowed:
            return
        status = read_import_status_file()
        if status and status.get("status") == "running":
            return render_template("errors/import_wait.html"), 503

    @app.context_processor
    def inject_theme():
        if current_user.is_authenticated:
            return {"theme": current_user.theme}
        return {"theme": "dark"}

    @app.context_processor
    def inject_units():
        return {"unit_preference": get_unit_preference()}

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

    from flask.cli import with_appcontext
    @app.cli.command("seed-yeasts")
    @with_appcontext
    def seed_yeasts():
        from app.models import Yeast, db

        if Yeast.query.first():
            print("ℹ️ Yeast table already contains data.")
            return

        default_yeasts = [
            {"name": "Lalvin 71B-1122", "alcohol_type": "Mead", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Moderate", "notes": "Fruity esters; smooths acidity."},
            {"name": "Lalvin D47", "alcohol_type": "Mead", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "notes": "Clean fermentation; enhances mouthfeel."},
            {"name": "Lalvin K1V-1116", "alcohol_type": "Mead", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "notes": "Strong fermenter; useful for restarting stuck fermentations."},
            {"name": "Lalvin EC-1118", "alcohol_type": "Mead", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "notes": "Reliable and clean; high alcohol tolerance."},
            {"name": "Lalvin EC-1118", "alcohol_type": "Wine", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "notes": "Champagne yeast; ferments fast and dry."},
            {"name": "Lalvin RC-212", "alcohol_type": "Wine", "tolerance": "16%", "strength": "Medium", "sweetness_retention": "Medium", "notes": "Great for red wines; enhances tannin and color."},
            {"name": "Lalvin D47", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "notes": "White wine favorite; promotes round mouthfeel."},
            {"name": "Red Star Premier Rouge", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "notes": "Great for full-bodied red wines."},
            {"name": "Lalvin 71B-1122", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Moderate", "notes": "Best for young reds, softens acidity."},
            {"name": "SafAle US-05", "alcohol_type": "Beer", "tolerance": "10%", "strength": "Medium", "sweetness_retention": "Medium", "notes": "Clean American ale yeast with low esters."},
            {"name": "Wyeast 1056 (American Ale)", "alcohol_type": "Beer", "tolerance": "11%", "strength": "Medium", "sweetness_retention": "Low", "notes": "Neutral flavor; widely used in APAs and IPAs."},
            {"name": "Nottingham Ale Yeast", "alcohol_type": "Beer", "tolerance": "14%", "strength": "Strong", "sweetness_retention": "Medium", "notes": "Highly flocculant; great for dry ales and ciders."},
            {"name": "WLP775 English Cider", "alcohol_type": "Hard Cider", "tolerance": "12%", "strength": "Medium", "sweetness_retention": "High", "notes": "Dry and crisp; preserves apple aroma."},
            {"name": "Mangrove Jack's M02", "alcohol_type": "Hard Cider", "tolerance": "12%", "strength": "Medium", "sweetness_retention": "High", "notes": "Smooth and aromatic finish."},
            {"name": "Nottingham Ale Yeast", "alcohol_type": "Hard Cider", "tolerance": "14%", "strength": "Strong", "sweetness_retention": "Medium", "notes": "Clean ferment; dual-purpose for cider and beer."},
            {"name": "Lalvin EC-1118", "alcohol_type": "Hard Cider", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "notes": "Neutral profile; high attenuation."}
        ]

        for data in default_yeasts:
            db.session.add(Yeast(**data, is_default=True))
        db.session.commit()
        print("✅ Yeast table seeded.")

    app.cli.add_command(seed_yeasts)

    return app
