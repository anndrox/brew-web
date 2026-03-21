from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from .models import db, Batch, CalendarEvent
from app.decorators import role_required
from app import csrf  # For csrf.exempt

calendar_bp = Blueprint('calendar_bp', __name__)

@calendar_bp.route('/calendar', endpoint='calendar')
@login_required
def calendar():
    return render_template("calendar.html")

@calendar_bp.route('/api/calendar-events')
@login_required
def calendar_events():
    batches = Batch.query.all()
    custom_events = CalendarEvent.query.all()
    events = []

    for b in batches:
        if b.start_date:
            events.append({
                "title": f"Start: {b.name}",
                "start": b.start_date.strftime("%Y-%m-%d"),
                "allDay": True,
                "description": "Batch Start",
                "custom": False,
                "type": "batch"
            })
        if b.end_date:
            events.append({
                "title": f"Bottle: {b.name}",
                "start": b.end_date.strftime("%Y-%m-%d"),
                "allDay": True,
                "description": "Batch Bottling",
                "custom": False,
                "type": "batch"
            })

    for e in custom_events:
        events.append({
            "id": e.id,
            "title": e.title,
            "start": e.start.strftime("%Y-%m-%d"),
            "end": e.end.strftime("%Y-%m-%d") if e.end else None,
            "allDay": e.all_day,
            "description": e.description,
            "custom": True,
            "type": "custom"
        })

    return jsonify(events)

@calendar_bp.route('/calendar-event', methods=['POST'])
@csrf.exempt
@login_required
@role_required('admin', 'editor')
def create_calendar_event():
    data = request.get_json()
    event = CalendarEvent(
        title=data.get('title'),
        start=datetime.strptime(data.get('start'), '%Y-%m-%d'),
        end=datetime.strptime(data.get('end'), '%Y-%m-%d') if data.get('end') else None,
        description=data.get('description'),
        all_day=True,
        created_by=current_user.id
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(success=True)

@calendar_bp.route('/calendar-event/<int:event_id>', methods=['PUT'])
@csrf.exempt
@login_required
@role_required('admin', 'editor')
def update_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    data = request.get_json()
    event.title = data.get('title')
    event.start = datetime.strptime(data.get('start'), '%Y-%m-%d')
    event.end = datetime.strptime(data.get('end'), '%Y-%m-%d') if data.get('end') else None
    event.description = data.get('description')
    db.session.commit()
    return jsonify(success=True)

@calendar_bp.route('/calendar-event/<int:event_id>', methods=['DELETE'])
@csrf.exempt
@login_required
@role_required('admin')
def delete_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify(success=True)
