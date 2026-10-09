# Calculator formulas and assumptions

Brew-Web calculators are planning estimates, not laboratory measurements or
proof that a bottle is pressure-safe. Version 1.4.1 corrects honey, dilution,
carbonation and hydrometer calculations. Old stored data is not changed. Confirm
results against your ingredients, instrument calibration and fermentation state.

## Units and reference cases

Volumes use US liquid gallons, not Imperial gallons: one gallon is 3.78541 liters
in the application's existing conversion convention. One pound is 0.45359237 kg
and one avoirdupois ounce is 28.349523125 g. Ingredient amounts retain the unit
entered; only the rate denominator changes between per gallon and per liter.
Calculations retain precision until final displayed results are rounded.

| Calculator | Formula or assumption | Reference case |
| --- | --- | --- |
| ABV | `(OG - FG) × 131.25`; simple estimate, not a high-gravity alcohol analysis | 1.100 to 1.010 → 11.81% |
| Honey required and target ABV | `lb = gallons × SG increase × 1000 / 35`; 35 gravity points per lb per gallon | 5 gallons at 1.100 → 14.29 lb / 6.48 kg |
| Sweetness | Same 35-point honey estimate; neglects added honey volume | 5 gallons, 1.000 to 1.010 → 1.43 lb |
| Dilution | Conserve gravity points: `new volume = old volume × (old SG - 1) / (target SG - 1)` | 5 gallons, 1.100 to 1.050 → add 5 gallons water |
| Volume recovery | Honey required for the missing volume at the original gravity; estimated honey displacement at 12 lb/gallon | 4 to 5 gallons at 1.100 → 2.86 lb honey and 0.76 gallons water |
| Carbonation | Residual CO₂ `3.0378 - 0.050062 × T + 0.00026555 × T²`, T in °F; corn sugar `g = liters × max(0, target - residual) × 4 / 0.91` | 5 gallons, 68°F / 20°C, 2.5 volumes → 136.32 g / 4.81 oz |
| Hydrometer correction | Multiply reading by the sample/calibration water-density factor ratio, rather than adding 0.001 per degree | 1.050 at 100°F, calibrated at 60°F → 1.056; at calibration temperature → unchanged |
| Legacy nutrient schedule | 0.8 g/L divided into four additions; existing threshold OG 1.050 | 5 gallons / 18.92705 L → 15.14 g total, 3.79 g per part |

Honey varies; 35 points is a planning assumption consistent with the existing
target-ABV calculator, not a measured extract value for every honey. Recovery and
sweetness estimates neglect some mixing/density effects. Make gradual additions,
measure gravity again, and verify stabilization before backsweetening. Volume
recovery means replacing lost must, not reversing alcohol/fermentation chemistry.
Dilution using gravity points is intended for unfermented must/wort, not alcohol
dilution of a finished beverage.

The hydrometer factor is
`1.00130346 - 0.000134722124*T + 0.00000204052596*T² - 0.00000000232820948*T³`.
Supported sample temperatures are 32–100°F (0–37.78°C), calibration 50–75°F
(10–23.89°C). Cool samples near the instrument's calibration temperature for
better accuracy. Do not use this correction for an alcohol-affected refractometer
or assume a digital hydrometer needs the same correction twice.

Carbonation now asks for the highest representative fermentation/post-fermentation
temperature; older submissions without it default to 68°F / 20°C. It assumes corn
sugar is 91% fermentable and uses the approximate 4 g sucrose/L/CO₂-volume planning
factor. It is not a honey/table-sugar calculator. Supported temperature is
32–86°F (0–30°C) and target at most 3 volumes. Those bounds do not certify bottle
safety. Only package fully fermented beverages in pressure-rated bottles, measure
sugar by weight, and account separately for residual fermentable sugars and any
backsweetening. Cold-crashed, pressurized or unusual fermentations can invalidate
the residual-CO₂ estimate; use an appropriate specialist method in those cases.

The existing nutrient tool is explicitly a **simplified legacy schedule**, not
full tailored TOSNA or a yeast-assimilable nitrogen (YAN) model. It does not factor
in yeast nitrogen demand or nutrient composition. Follow manufacturer guidance
and weigh additions; spoon-volume estimates are approximate. This release does
not silently recalculate previously saved nutrient/calendar entries.

Nonfinite numbers, negative/zero volumes and out-of-range gravity input are
rejected. Lower sweetness targets, non-increasing recovery volumes, dilution to
1.000 or below, and reversed ABV gravities produce no addition recommendation.

## Verification and sources

`tests/test_reliability.py` checks fixed numerical reference cases, rejects invalid
inputs, verifies equal sample/calibration temperatures and checks metric/US unit
equivalence. `tests/test_app.py` verifies form field names, displayed labels and
canonical storage round trips. Expected values were updated to the documented
formulas, not merely to the previous application's answers.

Formula references: [Brewer's Friend residual CO₂ and corn sugar assumptions](https://www.brewersfriend.com/beer-priming-calculator/),
[Brewer's Friend fermentable data](https://www.brewersfriend.com/fermentables/?filter=Sugar),
[National Honey Board cider guidance](https://legacy.bjcp.org/mead/cider.pdf),
and [BrewToolbox hydrometer formula](https://brewtoolbox.com/calculators/hydrometer-temperature-correction).
