from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.utils import role_required
from app.models import Yeast, db

yeast_bp = Blueprint("yeast_bp", __name__, url_prefix="/yeasts")

@yeast_bp.route("/")
@login_required
def list_yeasts():
    mead_yeasts = Yeast.query.filter_by(alcohol_type="Mead").all()
    wine_yeasts = Yeast.query.filter_by(alcohol_type="Wine").all()
    beer_yeasts = Yeast.query.filter_by(alcohol_type="Beer").all()
    cider_yeasts = Yeast.query.filter_by(alcohol_type="Hard Cider").all()
    other_yeasts = Yeast.query.filter(
        ~Yeast.alcohol_type.in_(["Mead", "Wine", "Beer", "Hard Cider"]) | (Yeast.alcohol_type == None)
    ).all()
    return render_template("yeasts.html", mead_yeasts=mead_yeasts, wine_yeasts=wine_yeasts,
                           beer_yeasts=beer_yeasts, cider_yeasts=cider_yeasts,
                           other_yeasts=other_yeasts)

@yeast_bp.route("/restore", methods=["POST"])
@login_required
@role_required("admin")
def restore_yeasts():
    default_yeasts = [
    {"name": "Lalvin 71B-1122", "alcohol_type": "Mead", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Moderate", "flocculation": "Low", "attenuation": "70%", "notes": "Fruity esters; smooths acidity."},
    {"name": "Lalvin D47", "alcohol_type": "Mead", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "flocculation": "Medium", "attenuation": "75%", "notes": "Clean fermentation; enhances mouthfeel."},
    {"name": "Lalvin K1V-1116", "alcohol_type": "Mead", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "flocculation": "Low", "attenuation": "75%", "notes": "Strong fermenter; useful for restarting stuck fermentations."},
    {"name": "Lalvin EC-1118", "alcohol_type": "Mead", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "flocculation": "High", "attenuation": "80%", "notes": "Reliable and clean; high alcohol tolerance."},
    {"name": "Lalvin EC-1118", "alcohol_type": "Wine", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "flocculation": "High", "attenuation": "80%", "notes": "Champagne yeast; ferments fast and dry."},
    {"name": "Lalvin RC-212", "alcohol_type": "Wine", "tolerance": "16%", "strength": "Medium", "sweetness_retention": "Medium", "flocculation": "Medium", "attenuation": "75%", "notes": "Great for red wines; enhances tannin and color."},
    {"name": "Lalvin D47", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "flocculation": "Medium", "attenuation": "75%", "notes": "White wine favorite; promotes round mouthfeel."},
    {"name": "Red Star Premier Rouge", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Low", "flocculation": "Medium", "attenuation": "73%", "notes": "Great for full-bodied red wines."},
    {"name": "Lalvin 71B-1122", "alcohol_type": "Wine", "tolerance": "14%", "strength": "Medium", "sweetness_retention": "Moderate", "flocculation": "Low", "attenuation": "70%", "notes": "Best for young reds, softens acidity."},
    {"name": "SafAle US-05", "alcohol_type": "Beer", "tolerance": "10%", "strength": "Medium", "sweetness_retention": "Medium", "flocculation": "Medium", "attenuation": "78%", "notes": "Clean American ale yeast."},
    {"name": "Wyeast 1056 (American Ale)", "alcohol_type": "Beer", "tolerance": "11%", "strength": "Medium", "sweetness_retention": "Low", "flocculation": "Low", "attenuation": "75%", "notes": "Neutral flavor; widely used in APAs and IPAs."},
    {"name": "Nottingham Ale Yeast", "alcohol_type": "Beer", "tolerance": "14%", "strength": "Strong", "sweetness_retention": "Medium", "flocculation": "High", "attenuation": "77%", "notes": "Highly flocculant; great for dry ales and ciders."},
    {"name": "WLP775 English Cider", "alcohol_type": "Hard Cider", "tolerance": "12%", "strength": "Medium", "sweetness_retention": "High", "flocculation": "Medium", "attenuation": "75%", "notes": "Dry and crisp; preserves apple aroma."},
    {"name": "Mangrove Jack's M02", "alcohol_type": "Hard Cider", "tolerance": "12%", "strength": "Medium", "sweetness_retention": "High", "flocculation": "Medium", "attenuation": "72%", "notes": "Smooth and aromatic finish."},
    {"name": "Nottingham Ale Yeast", "alcohol_type": "Hard Cider", "tolerance": "14%", "strength": "Strong", "sweetness_retention": "Medium", "flocculation": "High", "attenuation": "77%", "notes": "Clean ferment; dual-purpose for cider and beer."},
    {"name": "Lalvin EC-1118", "alcohol_type": "Hard Cider", "tolerance": "18%", "strength": "Strong", "sweetness_retention": "Low", "flocculation": "High", "attenuation": "80%", "notes": "Neutral profile; high attenuation."}
]

    added = 0
    for data in default_yeasts:
        if not Yeast.query.filter_by(name=data["name"]).first():
            db.session.add(Yeast(**data))
            added += 1

    db.session.commit()
    flash(f"✅ {added} yeast types restored.", "success")
    return redirect(url_for("routes.yeast_bp.list_yeasts"))

@yeast_bp.route("/add", methods=["POST"])
@login_required
@role_required("admin")
def add_yeast():
    yeast = Yeast(
        name=request.form.get("name"),
        alcohol_type=request.form.get("alcohol_type"),
        tolerance=request.form.get("tolerance"),
        strength=request.form.get("strength"),
        sweetness_retention=request.form.get("sweetness_retention"),
        flocculation=request.form.get("flocculation"),
        attenuation=request.form.get("attenuation"),
        notes=request.form.get("notes")
    )
    db.session.add(yeast)
    db.session.commit()
    flash(f"Yeast '{yeast.name}' added.", "success")
    return redirect(url_for("routes.yeast_bp.list_yeasts"))

@yeast_bp.route("/delete/<int:yeast_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_yeast(yeast_id):
    yeast = Yeast.query.get_or_404(yeast_id)
    db.session.delete(yeast)
    db.session.commit()
    flash(f"Yeast '{yeast.name}' deleted.", "success")
    return redirect(url_for("routes.yeast_bp.list_yeasts"))

@yeast_bp.route("/edit/<int:yeast_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_yeast(yeast_id):
    yeast = Yeast.query.get_or_404(yeast_id)
    if request.method == "POST":
        yeast.name = request.form.get("name")
        yeast.alcohol_type = request.form.get("alcohol_type")
        yeast.tolerance = request.form.get("tolerance")
        yeast.strength = request.form.get("strength")
        yeast.sweetness_retention = request.form.get("sweetness_retention")
        yeast.flocculation = request.form.get("flocculation")
        yeast.attenuation = request.form.get("attenuation")
        yeast.notes = request.form.get("notes")
        db.session.commit()
        flash("Yeast updated.", "success")
        return redirect(url_for("routes.yeast_bp.list_yeasts"))

    return render_template("edit_yeast.html", yeast=yeast)
