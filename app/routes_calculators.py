import math

from flask import Blueprint, render_template, request, abort
from flask_login import login_required
from app.utils import c_to_f, get_unit_preference, gallons_to_liters, liters_to_gallons

calculator_bp = Blueprint('calculator_bp', __name__, url_prefix='/calculator')
HONEY_POINTS_PER_POUND_GALLON = 35.0
POUND_TO_KG = 0.45359237
OUNCE_TO_GRAMS = 28.349523125


@calculator_bp.before_request
def validate_numeric_inputs():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key == 'csrf_token' or value == '':
                continue
            try:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError
                if key in {'volume', 'batch_volume', 'batch_size', 'current_volume', 'target_volume', 'original_volume'} and number <= 0:
                    raise ValueError
                if key in {'og', 'fg', 'target_fg', 'reading', 'starting_gravity', 'original_gravity', 'target_gravity', 'current_gravity'} and not 0.900 <= number <= 1.300:
                    raise ValueError
                if key in {'target_abv', 'target_co2'} and number < 0:
                    raise ValueError
            except ValueError:
                abort(400, 'Enter finite values in the supported range; volumes must be positive.')


def honey_pounds(volume_gallons, sg_increase):
    if sg_increase < 0:
        raise ValueError('Target gravity must not be lower than current gravity.')
    pounds = volume_gallons * sg_increase * 1000 / HONEY_POINTS_PER_POUND_GALLON
    if not math.isfinite(pounds):
        raise ValueError('Amount exceeds the supported numeric range.')
    return pounds


def hydrometer_correction(reading, sample_f, calibration_f):
    if not 32 <= sample_f <= 100 or not 50 <= calibration_f <= 75:
        raise ValueError('Cool the sample; supported sample range is 32–100°F and calibration 50–75°F.')
    def density_factor(temp):
        return 1.00130346 - 0.000134722124 * temp + 0.00000204052596 * temp**2 - 0.00000000232820948 * temp**3
    return reading * density_factor(sample_f) / density_factor(calibration_f)

@calculator_bp.route('/')
@login_required
def calculator_index():
    return render_template("calculators/index.html")

@calculator_bp.route('/abv', methods=['GET', 'POST'])
@login_required
def calculator_abv():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            og = float(request.form['og'])
            fg = float(request.form['fg'])
            if og < fg:
                raise ValueError('Final gravity must not be higher than original gravity.')
            result = round((og - fg) * 131.25, 2)
        except (KeyError, TypeError, ValueError):
            result = None
    return render_template("calculators/abv.html", result=result, unit_preference=units)

@calculator_bp.route('/abv-target', methods=['GET', 'POST'])
@login_required
def calculator_abv_target():
    """Estimate how much honey to add to reach a target ABV."""
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            batch_input = float(request.form['volume'])
            batch_gal = batch_input if units == 'imperial' else liters_to_gallons(batch_input)
            current_sg = float(request.form['current_gravity'])
            target_abv = float(request.form['target_abv'])
            target_fg = float(request.form.get('target_fg') or 1.000)

            target_og = (target_abv / 131.25) + target_fg
            added_points = target_og - current_sg

            if added_points <= 0:
                result = {"error": "Target ABV is not higher than current potential."}
            else:
                # Honey adds ~35 points per pound per gallon
                pounds_needed = honey_pounds(batch_gal, added_points)
                if units == 'metric':
                    result = {
                        "amount": round(pounds_needed * POUND_TO_KG, 2),
                        "unit": "kg",
                        "target_og": round(target_og, 3)
                    }
                else:
                    result = {
                        "amount": round(pounds_needed, 2),
                        "unit": "lb",
                        "target_og": round(target_og, 3)
                    }
        except Exception:
            result = {"error": "Invalid input"}
    return render_template("calculators/abv_target.html", result=result, unit_preference=units)

@calculator_bp.route('/dilution', methods=['GET', 'POST'])
@login_required
def calculator_dilution():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            original_volume_input = float(request.form['original_volume'])
            original_volume = original_volume_input if units == 'imperial' else liters_to_gallons(original_volume_input)
            original_gravity = float(request.form['original_gravity'])
            target_gravity = float(request.form['target_gravity'])

            if target_gravity >= original_gravity or target_gravity <= 1:
                result = "Target gravity must be above 1.000 and lower than original gravity."
            else:
                new_volume = original_volume * (original_gravity - 1) / (target_gravity - 1)
                added_water_gal = new_volume - original_volume
                added_water = round(gallons_to_liters(added_water_gal) if units == 'metric' else added_water_gal, 2)
                unit_label = "liters" if units == 'metric' else "gallons"
                result = f"Add {added_water} {unit_label} of water."
        except (KeyError, TypeError, ValueError):
            result = "Invalid input"
    return render_template("calculators/dilution.html", result=result, unit_preference=units)

@calculator_bp.route('/volume-recovery', methods=['GET', 'POST'])
@login_required
def calculator_volume_recovery():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            current_volume_input = float(request.form['current_volume'])
            target_volume_input = float(request.form['target_volume'])
            current_volume = current_volume_input if units == 'imperial' else liters_to_gallons(current_volume_input)
            target_volume = target_volume_input if units == 'imperial' else liters_to_gallons(target_volume_input)
            original_gravity = float(request.form['original_gravity'])

            lost_volume = target_volume - current_volume
            gravity_points = original_gravity - 1.0
            if lost_volume <= 0 or gravity_points < 0:
                raise ValueError('Target volume must be higher; gravity must be at least 1.000.')
            honey_needed = honey_pounds(lost_volume, gravity_points)
            water_needed_gal = lost_volume - (honey_needed / 12)
            if units == 'metric':
                result = {
                    "honey": round(honey_needed * POUND_TO_KG, 2),
                    "water": round(gallons_to_liters(water_needed_gal), 2),
                    "unit": "liters",
                    "honey_unit": "kg"
                }
            else:
                result = {
                    "honey": round(honey_needed, 2),
                    "water": round(water_needed_gal, 2),
                    "unit": "gallons",
                    "honey_unit": "lb"
                }
        except (KeyError, TypeError, ValueError):
            result = None
    return render_template("calculators/volume_recovery.html", result=result, unit_preference=units)

@calculator_bp.route('/honey-needed', methods=['GET', 'POST'])
@login_required
def calculator_honey_needed():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            batch_size_input = float(request.form['volume'])
            batch_size = batch_size_input if units == 'imperial' else liters_to_gallons(batch_size_input)
            target_og = float(request.form['target_gravity'])
            gravity_points = target_og - 1.0
            honey_lb = honey_pounds(batch_size, gravity_points)
            if units == 'metric':
                result = {"amount": round(honey_lb * POUND_TO_KG, 2), "unit": "kg"}
            else:
                result = {"amount": round(honey_lb, 2), "unit": "lb"}
        except (KeyError, TypeError, ValueError):
            result = "Invalid input"
    return render_template("calculators/honey_required.html", result=result, unit_preference=units)

@calculator_bp.route('/sweetness', methods=['GET', 'POST'])
@login_required
def calculator_sweetness():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            vol_input = float(request.form['batch_volume'])
            gallons = vol_input if units == 'imperial' else liters_to_gallons(vol_input)
            target_sg = float(request.form['target_gravity'])
            current_sg = float(request.form['current_gravity'])

            delta = target_sg - current_sg
            honey_lb = honey_pounds(gallons, delta)
            if units == 'metric':
                result = {"amount": round(honey_lb * POUND_TO_KG, 2), "unit": "kg"}
            else:
                result = {"amount": round(honey_lb, 2), "unit": "lb"}
        except (KeyError, TypeError, ValueError):
            result = None
    return render_template("calculators/sweetness.html", result=result, unit_preference=units)

@calculator_bp.route('/carbonation', methods=['GET', 'POST'])
@login_required
def calculator_carbonation():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            volume_input = float(request.form['volume'])
            volume = volume_input if units == 'imperial' else liters_to_gallons(volume_input)
            co2 = float(request.form['target_co2'])
            temperature = float(request.form.get('temperature') or (20 if units == 'metric' else 68))
            temperature_f = c_to_f(temperature) if units == 'metric' else temperature
            if not 32 <= temperature_f <= 86 or co2 > 3:
                raise ValueError('Use 32–86°F and at most 3 CO₂ volumes; check bottle rating separately.')
            residual = 3.0378 - 0.050062 * temperature_f + 0.00026555 * temperature_f**2
            # 4 g sucrose/L/CO2 volume; corn sugar is assumed 91% fermentable.
            sugar_grams = gallons_to_liters(volume) * max(0, co2 - residual) * 4 / 0.91
            if units == 'metric':
                result = {"amount": round(sugar_grams, 2), "unit": "grams"}
            else:
                result = {"amount": round(sugar_grams / OUNCE_TO_GRAMS, 2), "unit": "oz"}
        except (KeyError, TypeError, ValueError):
            result = "Invalid input"
    return render_template("calculators/carbonation.html", result=result, unit_preference=units)

@calculator_bp.route('/tosna', methods=['GET', 'POST'])
@login_required
def calculator_tosna():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            batch_size_input = float(request.form['batch_size'])
            batch_size = batch_size_input if units == 'imperial' else liters_to_gallons(batch_size_input)
            starting_gravity = float(request.form['starting_gravity'])

            if starting_gravity < 1.050:
                result = "OG too low for TOSNA."
            else:
                must_liters = gallons_to_liters(batch_size)
                total = round(0.8 * must_liters, 2)
                per_day = round(total / 4, 2)
                result = type('TOSNAResult', (object,), {"total": total, "per_day": per_day})()
        except Exception as e:
            result = "Invalid input"
            print("TOSNA error:", e)

    return render_template("calculators/tosna.html", result=result, unit_preference=units)

@calculator_bp.route('/temp-correction', methods=['GET', 'POST'])
@login_required
def calculator_temp_correction():
    result = None
    units = get_unit_preference()
    if request.method == 'POST':
        try:
            observed = float(request.form['reading'])
            sample_temp = float(request.form['sample_temp'])
            calibration_temp = float(request.form['calibration_temp'])
            if units == 'metric':
                sample_temp = c_to_f(sample_temp)
                calibration_temp = c_to_f(calibration_temp)
            corrected = round(hydrometer_correction(observed, sample_temp, calibration_temp), 3)
            result = corrected
        except (KeyError, TypeError, ValueError):
            result = None
    return render_template("calculators/temp_correction.html", result=result, unit_preference=units)
