from flask import Blueprint, render_template
from flask_login import login_required
from .models import Batch
from sqlalchemy import func
from datetime import datetime

stats_bp = Blueprint('stats_bp', __name__, url_prefix='/stats')

@stats_bp.route('/')
@login_required
def view_stats():
    # Only include batches with ABV values for the ABV chart
    abv_batches = Batch.query.filter(Batch.abv.isnot(None)).order_by(Batch.start_date.asc()).all()

    batch_names = [b.name for b in abv_batches]
    abv_values = [round(b.abv, 2) for b in abv_batches]

    # Count of batches started over time (e.g. by day)
    batch_counts = (
        Batch.query
        .with_entities(func.date(Batch.start_date).label("date"), func.count().label("count"))
        .filter(Batch.start_date.isnot(None))
        .group_by(func.date(Batch.start_date))
        .order_by(func.date(Batch.start_date))
        .all()
    )

    dates = [row.date.strftime('%Y-%m-%d') for row in batch_counts]
    counts = [row.count for row in batch_counts]

    return render_template(
        'stats.html',
        batch_names=batch_names,
        abv_values=abv_values,
        dates=dates,
        counts=counts
    )
