from app import db
from app.models import Yeast

yeasts = [
    # Mead
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

for y in yeasts:
    existing = Yeast.query.filter_by(name=y['name']).first()
    if not existing:
        db.session.add(Yeast(**y))

db.session.commit()
print("✅ Yeast data seeded successfully.")
