from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, current_user, login_required
from .models import db, Recipe, Measurement, Batch, Ingredient, User
from datetime import datetime
from app import limiter
from app.utils import role_required

routes = Blueprint("routes", __name__, url_prefix="/app")

# === AUTH ===
@routes.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if not User.query.first():
        return redirect(url_for('routes.setup'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('routes.index'))
        else:
            time.sleep(1)  # delays brute-force timing analysis
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('routes.login'))

# === INDEX ===
@routes.route('/')
@login_required
def index():
    mead_recipes = Recipe.query.filter_by(alcohol_type='Mead').order_by(Recipe.name.asc()).all()
    wine_recipes = Recipe.query.filter_by(alcohol_type='Wine').order_by(Recipe.name.asc()).all()
    beer_recipes = Recipe.query.filter_by(alcohol_type='Beer').order_by(Recipe.name.asc()).all()
    other_recipes = Recipe.query.filter(Recipe.alcohol_type == None).order_by(Recipe.name.asc()).all()
    return render_template(
        'index.html',
        mead_recipes=mead_recipes,
        wine_recipes=wine_recipes,
        beer_recipes=beer_recipes,
        other_recipes=other_recipes
    )

# === MEASUREMENTS ===
@routes.route('/measurements/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def new_measurement():
    batches = Batch.query.all()
    selected_id = request.args.get('batch_id', type=int)

    if request.method == 'POST':
        try:
            measurement = Measurement(
                batch_id=int(request.form['batch_id']),
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                gravity=float(request.form['gravity']) if request.form['gravity'] else None,
                ph=float(request.form['ph']) if request.form['ph'] else None,
                temperature=float(request.form['temperature']) if request.form['temperature'] else None,
                notes=request.form['notes']
            )
            db.session.add(measurement)
            db.session.commit()
            flash("Measurement added.", "success")
            return redirect(url_for('routes.batches_bp.view_batch', batch_id=measurement.batch_id))
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    return render_template('new_measurement.html', batches=batches, selected_id=selected_id)

@routes.route('/measurements/<int:measurement_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_measurement(measurement_id):
    measurement = Measurement.query.get_or_404(measurement_id)
    batch_id = measurement.batch_id
    db.session.delete(measurement)
    db.session.commit()
    flash("Measurement deleted successfully.", "success")
    return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch_id))

# === Modular Blueprints ===
from .routes_admin import admin_bp
from .routes_batches import batches_bp
from .routes_calculators import calculator_bp
from .routes_calendar import calendar_bp
from .routes_recipes import recipes_bp
from .routes_settings import settings_bp
from .routes_stats import stats_bp
from .routes_yeast import yeast_bp

routes.register_blueprint(admin_bp)
routes.register_blueprint(batches_bp)
routes.register_blueprint(calculator_bp)
routes.register_blueprint(calendar_bp)
routes.register_blueprint(recipes_bp)
routes.register_blueprint(settings_bp)
routes.register_blueprint(stats_bp)
routes.register_blueprint(yeast_bp)