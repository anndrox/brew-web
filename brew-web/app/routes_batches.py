from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_required
from app.decorators import role_required
from .models import db, Batch, Recipe, Yeast
from datetime import datetime, timedelta
from app.models import CalendarEvent


batches_bp = Blueprint('batches_bp', __name__, url_prefix='/batches')

@batches_bp.route('/')
@login_required
def list_batches():
    mead_batches = Batch.query.filter_by(alcohol_type='Mead').order_by(Batch.start_date.desc()).all()
    wine_batches = Batch.query.filter_by(alcohol_type='Wine').order_by(Batch.start_date.desc()).all()
    beer_batches = Batch.query.filter_by(alcohol_type='Beer').order_by(Batch.start_date.desc()).all()
    cider_batches = Batch.query.filter_by(alcohol_type='Hard Cider').order_by(Batch.start_date.desc()).all()

    other_batches = Batch.query.filter(
        ~Batch.alcohol_type.in_(['Mead', 'Wine', 'Beer', 'Hard Cider']) | (Batch.alcohol_type == None)
    ).order_by(Batch.start_date.desc()).all()

    return render_template(
        'batches.html',
        mead_batches=mead_batches,
        wine_batches=wine_batches,
        beer_batches=beer_batches,
        cider_batches=cider_batches,
        other_batches=other_batches
    )

@batches_bp.route('/<int:batch_id>')
@login_required
def view_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    return render_template('batch_detail.html', batch=batch, timedelta=timedelta)

@batches_bp.route('/<int:batch_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    recipes = Recipe.query.order_by(Recipe.name).all()
    yeasts = Yeast.query.order_by(Yeast.name).all()

    if request.method == 'POST':
        batch.name = request.form.get('name')
        batch.recipe_id = request.form.get('recipe_id') or None
        batch.yeast_id = request.form.get('yeast_id') or None
        batch.start_date = request.form.get('start_date') or None
        batch.end_date = request.form.get('end_date') or None
        batch.batch_size = request.form.get('batch_size') or None

        try:
            batch.initial_gravity = round(float(request.form.get('initial_gravity')), 3)
        except (TypeError, ValueError):
            batch.initial_gravity = None

        try:
            batch.final_gravity = round(float(request.form.get('final_gravity')), 3)
        except (TypeError, ValueError):
            batch.final_gravity = None

        batch.fermentation_temp = request.form.get('fermentation_temp') or None
        batch.water_type = request.form.get('water_type') or None
        batch.yeast_type = request.form.get('yeast_type') or None
        batch.tosna_enabled = 'enable_tosna' in request.form
        batch.backsweetened = 'backsweetened' in request.form
        batch.pectic_used = 'pectic_used' in request.form
        batch.flavor_additions = request.form.get('flavor_additions') or None
        batch.notes = request.form.get('notes') or None

        db.session.commit()
        flash("Batch updated successfully.", "success")
        return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))

    return render_template('edit_batch.html', batch=batch, recipes=recipes, yeasts=yeasts)
    
@batches_bp.route('/<int:batch_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    flash(f"Batch '{batch.name}' deleted successfully.", "success")
    return redirect(url_for('routes.batches_bp.list_batches'))

@batches_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def new_batch():
    recipes = Recipe.query.order_by(Recipe.name).all()
    yeasts = Yeast.query.order_by(Yeast.name).all()
    show_warning = len(recipes) == 0

    if request.method == 'POST':
        recipe_id_raw = request.form.get('recipe_id')
        name = request.form.get('name', '').strip()
        start_date_raw = request.form.get('start_date', '').strip()
        tosna_total = None
        tosna_per_day = None
        tosna_enabled = 'enable_tosna' in request.form

        try:
            recipe_id = int(recipe_id_raw)
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                raise ValueError("Recipe not found.")
        except (TypeError, ValueError):
            flash("A valid recipe must be selected.", "danger")
            return redirect(url_for('routes.batches_bp.new_batch'))

        if not name:
            flash("Batch name is required.", "danger")
            return redirect(url_for('routes.batches_bp.new_batch'))

        if not start_date_raw:
            flash("Start date is required.", "danger")
            return redirect(url_for('routes.batches_bp.new_batch'))

        try:
            start_date = datetime.strptime(start_date_raw, '%Y-%m-%d')
        except ValueError:
            flash("Invalid start date format.", "danger")
            return redirect(url_for('routes.batches_bp.new_batch'))

        # Parse and round floats
        try:
            initial_gravity = round(float(request.form.get('initial_gravity')), 3)
        except (TypeError, ValueError):
            initial_gravity = None

        try:
            final_gravity = round(float(request.form.get('final_gravity')), 3)
        except (TypeError, ValueError):
            final_gravity = None

        try:
            batch_size = float(request.form.get('batch_size'))
        except (TypeError, ValueError):
            batch_size = None

        try:
            fermentation_temp = float(request.form.get('fermentation_temp'))
        except (TypeError, ValueError):
            fermentation_temp = None

        if tosna_enabled and batch_size and initial_gravity and initial_gravity >= 1.050:
            must_liters = batch_size * 3.78541
            tosna_total = round(0.8 * must_liters, 2)
            tosna_per_day = round(tosna_total / 4, 2)
        elif tosna_enabled:
            flash("Could not calculate TOSNA due to missing or invalid values.", "warning")
            tosna_enabled = False

        batch = Batch(
            name=name,
            recipe_id=recipe_id,
            start_date=start_date,
            alcohol_type=recipe.alcohol_type,
            yeast_id=request.form.get('yeast_id') or None,
            tosna_enabled=tosna_enabled,
            tosna_total=tosna_total,
            tosna_per_day=tosna_per_day,
            initial_gravity=initial_gravity,
            final_gravity=final_gravity,
            batch_size=batch_size,
            fermentation_temp=fermentation_temp,
            water_type=request.form.get('water_type') or None,
            yeast_type=request.form.get('yeast_type') or None,
            backsweetened='backsweetened' in request.form,
            pectic_used='pectic_used' in request.form,
            flavor_additions=request.form.get('flavor_additions') or None,
            notes=request.form.get('notes') or None
        )

        db.session.add(batch)
        db.session.commit()
        flash("Batch created successfully.", "success")
        return redirect(url_for('routes.batches_bp.list_batches'))

    return render_template('new_batch.html', recipes=recipes, yeasts=yeasts, show_warning=show_warning)
    
### Calculator additions ###

@batches_bp.route('/batch/<int:batch_id>/tosna', methods=['POST'])
@login_required
def calculate_tosna(batch_id):
    batch = Batch.query.get_or_404(batch_id)

    if not batch.initial_gravity or not batch.batch_size:
        flash("Missing gravity or batch size — cannot calculate TOSNA.", "warning")
        return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))

    if batch.initial_gravity < 1.050:
        flash("OG too low for TOSNA.", "warning")
        return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))

    # Calculate TOSNA
    must_liters = batch.batch_size * 3.78541
    total = round(0.8 * must_liters, 2)
    per_day = round(total / 4, 2)

    # Add to calendar if requested
    if 'add_to_calendar' in request.form:
        base_date = batch.start_date or datetime.utcnow().date()
        for i in range(4):
            event = CalendarEvent(
                title=f"TOSNA Day {i}",
                date=base_date + timedelta(days=i),
                note=f"Add {per_day}g Fermaid O for batch {batch.name}",
                batch_id=batch.id
            )
            db.session.add(event)
        db.session.commit()
        flash("TOSNA schedule added to calendar.", "success")
    else:
        flash(f"TOSNA calculated: {total}g total / {per_day}g per day.", "success")

    return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))
    
### Calendar additions ###

@batches_bp.route('/batch/<int:batch_id>/add-tosna-calendar', methods=['POST'])
@login_required
def add_tosna_to_calendar(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    if not batch.tosna_enabled or not batch.start_date:
        flash("TOSNA schedule not available for this batch.", "warning")
        return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))

    for i in range(4):
        event = CalendarEvent(
            title=f"TOSNA Day {i}",
            start=batch.start_date + timedelta(days=i),  # ✅ corrected here
            note=f"Add {batch.tosna_per_day}g Fermaid O to {batch.name}",
            batch_id=batch.id
        )
        db.session.add(event)

    db.session.commit()
    flash("TOSNA schedule added to calendar.", "success")
    return redirect(url_for('routes.batches_bp.view_batch', batch_id=batch.id))

