from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Recipe, Ingredient, Yeast
from app.utils import role_required

recipes_bp = Blueprint("recipes_bp", __name__)

@recipes_bp.route('/recipes')
@login_required
def recipes():
    return redirect(url_for('routes.recipes_bp.index'))

@recipes_bp.route('/')
@login_required
def index():
    mead_recipes = Recipe.query.filter_by(alcohol_type='Mead').order_by(Recipe.name.asc()).all()
    wine_recipes = Recipe.query.filter_by(alcohol_type='Wine').order_by(Recipe.name.asc()).all()
    beer_recipes = Recipe.query.filter_by(alcohol_type='Beer').order_by(Recipe.name.asc()).all()
    other_recipes = Recipe.query.filter(Recipe.alcohol_type == None).order_by(Recipe.name.asc()).all()
    return render_template('index.html', mead_recipes=mead_recipes, wine_recipes=wine_recipes,
                           beer_recipes=beer_recipes, other_recipes=other_recipes)

@recipes_bp.route('/recipes/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def new_recipe():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        batch_size = int(request.form['batch_size'])

        recipe = Recipe(
            name=name,
            content=content,
            alcohol_type=request.form.get('alcohol_type') or None,
            water_type=request.form.get('water_type') or None,
            yeast_id=request.form.get('yeast_id') or None  # ✅ yeast_id is here
        )
        db.session.add(recipe)
        db.session.flush()

        i = 0
        while True:
            name_key = f"ingredient_name_{i}"
            if not request.form.get(name_key):
                break
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name=request.form.get(name_key),
                amount_per_gallon=float(request.form.get(f"ingredient_amount_{i}") or 0),
                unit=request.form.get(f"ingredient_unit_{i}"),
                note=request.form.get(f"ingredient_note_{i}") or ""
            )
            db.session.add(ingredient)
            i += 1

        db.session.commit()
        flash("New recipe with ingredients added.", "success")
        return redirect(url_for('routes.recipes_bp.index'))

    yeasts = Yeast.query.order_by(Yeast.name).all()
    return render_template('new_recipe.html', yeasts=yeasts)

@recipes_bp.route('/recipes/<int:recipe_id>')
@login_required
def view_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    target_batch = request.args.get('target_batch', type=int, default=1)
    return render_template('recipe_detail.html', recipe=recipe, target_batch=target_batch)

@recipes_bp.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if request.method == 'POST':
        recipe.name = request.form['name']
        recipe.content = request.form['content']
        recipe.alcohol_type = request.form.get('alcohol_type') or None
        recipe.water_type = request.form.get('water_type') or None
        recipe.yeast_id = request.form.get('yeast_id') or None

        Ingredient.query.filter_by(recipe_id=recipe.id).delete()

        i = 0
        while True:
            name_key = f"ingredient_name_{i}"
            if not request.form.get(name_key):
                break
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name=request.form.get(name_key),
                amount_per_gallon=float(request.form.get(f"ingredient_amount_{i}") or 0),
                unit=request.form.get(f"ingredient_unit_{i}"),
                note=request.form.get(f"ingredient_note_{i}") or ""
            )
            db.session.add(ingredient)
            i += 1

        db.session.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('routes.recipes_bp.view_recipe', recipe_id=recipe.id))

    yeasts = Yeast.query.order_by(Yeast.name).all()
    return render_template('edit_recipe.html', recipe=recipe, yeasts=yeasts)


@recipes_bp.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash(f'Recipe \"{recipe.name}\" was deleted.', 'success')
    return redirect(url_for('routes.recipes_bp.index'))
