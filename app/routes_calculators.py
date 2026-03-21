from flask import Blueprint, render_template, request
from flask_login import login_required
from app.utils import get_unit_preference, gallons_to_liters, liters_to_gallons

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
            units = get_unit_preference()
            original_volume_input = float(request.form['original_volume'])
            original_volume = original_volume_input if units == 'imperial' else liters_to_gallons(original_volume_input)
            original_gravity = float(request.form['original_gravity'])
            target_gravity = float(request.form['target_gravity'])

            if target_gravity >= original_gravity:
                result = "Target gravity must be lower than original gravity."
            else:
                new_volume = (original_volume * original_gravity) / target_gravity
                added_water_gal = new_volume - original_volume
                added_water = round(gallons_to_liters(added_water_gal) if units == 'metric' else added_water_gal, 2)
                unit_label = "liters" if units == 'metric' else "gallons"
                result = f"Add {added_water} {unit_label} of water."
        except:
            result = "Invalid input"
    return render_template("calculators/dilution.html", result=result)

@calculator_bp.route('/volume-recovery', methods=['GET', 'POST'])
@login_required
def calculator_volume_recovery():
    result = None
    if request.method == 'POST':
        try:
            units = get_unit_preference()
            current_volume_input = float(request.form['current_volume'])
            target_volume_input = float(request.form['target_volume'])
            current_volume = current_volume_input if units == 'imperial' else liters_to_gallons(current_volume_input)
            target_volume = target_volume_input if units == 'imperial' else liters_to_gallons(target_volume_input)
            original_gravity = float(request.form['original_gravity'])

            lost_volume = target_volume - current_volume
            gravity_points = original_gravity - 1.0
            honey_per_gallon = 2.7 * gravity_points
            honey_needed = round(honey_per_gallon * lost_volume, 2)
            water_needed_gal = lost_volume - (honey_needed / 12)
            if units == 'metric':
                result = {"honey": round(honey_needed, 2), "water": round(gallons_to_liters(water_needed_gal), 2), "unit": "liters"}
            else:
                result = {"honey": honey_needed, "water": round(water_needed_gal, 2), "unit": "gallons"}
        except:
            result = None
    return render_template("calculators/volume_recovery.html", result=result)

@calculator_bp.route('/honey-needed', methods=['GET', 'POST'])
@login_required
def calculator_honey_needed():
    result = None
    if request.method == 'POST':
        try:
            units = get_unit_preference()
            batch_size_input = float(request.form['batch_size'])
            batch_size = batch_size_input if units == 'imperial' else liters_to_gallons(batch_size_input)
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
            units = get_unit_preference()
            vol_input = float(request.form['gallons'])
            gallons = vol_input if units == 'imperial' else liters_to_gallons(vol_input)
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
            units = get_unit_preference()
            volume_input = float(request.form['volume'])
            volume = volume_input if units == 'imperial' else liters_to_gallons(volume_input)
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
            units = get_unit_preference()
            batch_size_input = float(request.form['batch_size'])
            batch_size = batch_size_input if units == 'imperial' else liters_to_gallons(batch_size_input)
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
            units = get_unit_preference()
            observed = float(request.form['observed'])
            temp_input = float(request.form['temp'])
            temp_f = temp_input if units == 'imperial' else (temp_input * 9/5) + 32
            correction = (temp_f - 60) * 0.001
            corrected = round(observed + correction, 3)
            result = corrected
        except:
            result = None
    return render_template("calculators/temp_correction.html", result=result)
