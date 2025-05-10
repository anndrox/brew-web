from flask import Blueprint, render_template, request
from flask_login import login_required

calculator_bp = Blueprint('calculator_bp', __name__, url_prefix='/calculator')

@calculator_bp.route('/')
@login_required
def calculator_index():
    return render_template("calculators/index.html")

@calculator_bp.route('/abv', methods=['GET', 'POST'])
@login_required
def calculator_abv():
    result = None
    if request.method == 'POST':
        try:
            og = float(request.form['og'])
            fg = float(request.form['fg'])
            result = round((og - fg) * 131.25, 2)
        except:
            result = None
    return render_template("calculators/abv.html", result=result)

@calculator_bp.route('/dilution', methods=['GET', 'POST'])
@login_required
def calculator_dilution():
    result = None
    if request.method == 'POST':
        try:
            original_volume = float(request.form['original_volume'])
            original_gravity = float(request.form['original_gravity'])
            target_gravity = float(request.form['target_gravity'])

            if target_gravity >= original_gravity:
                result = "Target gravity must be lower than original gravity."
            else:
                new_volume = (original_volume * original_gravity) / target_gravity
                added_water = round(new_volume - original_volume, 2)
                result = f"Add {added_water} gallons of water."
        except:
            result = "Invalid input"
    return render_template("calculators/dilution.html", result=result)

@calculator_bp.route('/volume-recovery', methods=['GET', 'POST'])
@login_required
def calculator_volume_recovery():
    result = None
    if request.method == 'POST':
        try:
            current_volume = float(request.form['current_volume'])
            target_volume = float(request.form['target_volume'])
            original_gravity = float(request.form['original_gravity'])

            lost_volume = target_volume - current_volume
            gravity_points = original_gravity - 1.0
            honey_per_gallon = 2.7 * gravity_points
            honey_needed = round(honey_per_gallon * lost_volume, 2)
            water_needed = round(lost_volume - (honey_needed / 12), 2)
            result = {"honey": honey_needed, "water": water_needed}
        except:
            result = None
    return render_template("calculators/volume_recovery.html", result=result)

@calculator_bp.route('/honey-needed', methods=['GET', 'POST'])
@login_required
def calculator_honey_needed():
    result = None
    if request.method == 'POST':
        try:
            batch_size = float(request.form['batch_size'])
            target_og = float(request.form['target_og'])
            gravity_points = target_og - 1.0
            honey = round(batch_size * gravity_points * 2.7, 2)
            result = honey
        except:
            result = "Invalid input"
    return render_template("calculators/honey_needed.html", result=result)

@calculator_bp.route('/sweetness', methods=['GET', 'POST'])
@login_required
def calculator_sweetness():
    result = None
    if request.method == 'POST':
        try:
            gallons = float(request.form['gallons'])
            target_sg = float(request.form['target_sg'])
            current_sg = float(request.form['current_sg'])

            delta = target_sg - current_sg
            honey = round(gallons * delta * 2.7, 2)
            result = honey
        except:
            result = None
    return render_template("calculators/sweetness.html", result=result)

@calculator_bp.route('/carbonation', methods=['GET', 'POST'])
@login_required
def calculator_carbonation():
    result = None
    if request.method == 'POST':
        try:
            volume = float(request.form['volume'])
            co2 = float(request.form['co2'])
            sugar = round(volume * (co2 - 0.85) * 0.5, 2)
            result = sugar
        except:
            result = "Invalid input"
    return render_template("calculators/carbonation.html", result=result)

@calculator_bp.route('/tosna', methods=['GET', 'POST'])
@login_required
def calculator_tosna():
    result = None
    if request.method == 'POST':
        try:
            batch_size = float(request.form['batch_size'])
            starting_gravity = float(request.form['starting_gravity'])

            if starting_gravity < 1.050:
                result = "OG too low for TOSNA."
            else:
                must_liters = batch_size * 3.78541
                total = round(0.8 * must_liters, 2)
                per_day = round(total / 4, 2)
                result = type('TOSNAResult', (object,), {"total": total, "per_day": per_day})()
        except Exception as e:
            result = "Invalid input"
            print("TOSNA error:", e)

    return render_template("calculators/tosna.html", result=result)

@calculator_bp.route('/temp-correction', methods=['GET', 'POST'])
@login_required
def calculator_temp_correction():
    result = None
    if request.method == 'POST':
        try:
            observed = float(request.form['observed'])
            temp = float(request.form['temp'])
            correction = (temp - 60) * 0.001
            corrected = round(observed + correction, 3)
            result = corrected
        except:
            result = None
    return render_template("calculators/temp_correction.html", result=result)
