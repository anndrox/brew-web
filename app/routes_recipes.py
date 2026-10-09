import math
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app.models import db, Recipe, Ingredient, Yeast
from app.utils import (
    get_unit_preference,
    per_gallon_to_per_liter,
    per_liter_to_per_gallon,
    role_required,
    sanitize_instructions,
)

recipes_bp = Blueprint("recipes_bp", __name__)


def _submitted_recipe(units):
    """Validate every remaining row before mutating the existing recipe."""
    name = (request.form.get('name') or '').strip()
    if not name or len(name) > 100:
        abort(400, 'Recipe name must contain 1–100 characters.')
    yeast_id = request.form.get('yeast_id') or None
    if yeast_id:
        try:
            yeast_id = int(yeast_id)
        except ValueError:
            abort(400, 'Invalid yeast selection.')
        db.get_or_404(Yeast, yeast_id)
    indices = sorted({int(match.group(1)) for key in request.form
                      if (match := re.fullmatch(r'ingredient_(?:name|amount|unit|note)_(\d+)', key))})
    ingredients = []
    for i in indices:
        row = {field: (request.form.get(f'ingredient_{field}_{i}') or '').strip()
               for field in ('name', 'amount', 'unit', 'note')}
        if not any(row.values()):
            continue  # Empty optional row, not an end-of-list sentinel.
        try:
            amount = float(row['amount'])
        except ValueError:
            abort(400, 'Each ingredient needs a finite nonnegative amount.')
        if (not row['name'] or len(row['name']) > 100 or not row['unit']
                or len(row['unit']) > 20 or len(row['note']) > 200
                or not math.isfinite(amount) or amount < 0):
            abort(400, 'Invalid ingredient row; existing ingredients were not changed.')
        ingredients.append({'name': row['name'], 'unit': row['unit'], 'note': row['note'],
                            'amount_per_gallon': per_liter_to_per_gallon(amount)
                            if units == 'metric' else amount})
    return name, yeast_id, ingredients

@recipes_bp.route('/recipes')
@login_required
def recipes():
    return redirect(url_for('routes.index'))

@recipes_bp.route('/recipes/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def new_recipe():
    if request.method == 'POST':
        units = get_unit_preference()
        name, yeast_id, ingredients = _submitted_recipe(units)
        content = sanitize_instructions(request.form.get('content', ''))

        recipe = Recipe(
            name=name,
            content=content,
            alcohol_type=request.form.get('alcohol_type') or None,
            water_type=request.form.get('water_type') or None,
            yeast_id=yeast_id
        )
        db.session.add(recipe)
        db.session.flush()

        for fields in ingredients:
            db.session.add(Ingredient(recipe_id=recipe.id, **fields))

        db.session.commit()
        flash("New recipe with ingredients added.", "success")
        return redirect(url_for('routes.index'))

    yeasts = Yeast.query.order_by(Yeast.name).all()
    units = get_unit_preference()
    display_unit = 'liter' if units == 'metric' else 'gallon'
    return render_template('new_recipe.html', yeasts=yeasts, unit_preference=units, display_unit=display_unit)

@recipes_bp.route('/recipes/<int:recipe_id>')
@login_required
def view_recipe(recipe_id):
    recipe = db.get_or_404(Recipe, recipe_id)
    units = get_unit_preference()
    target_batch = request.args.get('target_batch', type=float, default=1)
    if not math.isfinite(target_batch) or target_batch <= 0:
        abort(400, 'Batch size must be positive and finite.')
    display_unit = 'liter' if units == 'metric' else 'gallon'

    ingredients_view = []
    for ing in recipe.ingredients:
        unit_label = ing.unit or ''
        # The denominator changes (per gallon -> per liter), not the ingredient's
        # numerator unit. A quantity labelled gallons must remain gallons.
        if units == 'metric':
            unrounded = per_gallon_to_per_liter(ing.amount_per_gallon or 0)
            base_amount = round(unrounded, 2)
            scaled_amount = round(unrounded * target_batch, 2)
        else:
            base_amount = ing.amount_per_gallon or 0
            scaled_amount = round(base_amount * target_batch, 2)

        ingredients_view.append({
            "name": ing.name,
            "note": ing.note,
            "base_amount": base_amount,
            "scaled_amount": scaled_amount,
            "unit_label": unit_label
        })

    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        target_batch=target_batch,
        unit_preference=units,
        display_unit=display_unit,
        ingredients_view=ingredients_view
    )

@recipes_bp.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit_recipe(recipe_id):
    recipe = db.get_or_404(Recipe, recipe_id)
    if request.method == 'POST':
        units = get_unit_preference()
        name, yeast_id, ingredients = _submitted_recipe(units)
        recipe.name = name
        recipe.content = sanitize_instructions(request.form.get('content', ''))
        recipe.alcohol_type = request.form.get('alcohol_type') or None
        recipe.water_type = request.form.get('water_type') or None
        recipe.yeast_id = yeast_id

        Ingredient.query.filter_by(recipe_id=recipe.id).delete()

        for fields in ingredients:
            db.session.add(Ingredient(recipe_id=recipe.id, **fields))

        db.session.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('routes.recipes_bp.view_recipe', recipe_id=recipe.id))

    yeasts = Yeast.query.order_by(Yeast.name).all()
    units = get_unit_preference()
    display_unit = 'liter' if units == 'metric' else 'gallon'
    return render_template(
        'edit_recipe.html',
        recipe=recipe,
        yeasts=yeasts,
        unit_preference=units,
        display_unit=display_unit,
        per_gallon_to_per_liter=per_gallon_to_per_liter,
    )


@recipes_bp.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_recipe(recipe_id):
    recipe = db.get_or_404(Recipe, recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash(f'Recipe \"{recipe.name}\" was deleted.', 'success')
    return redirect(url_for('routes.index'))
