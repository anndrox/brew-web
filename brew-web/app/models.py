from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db

class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default='user')
    theme = db.Column(db.String(20), default='dark')
    font_size = db.Column(db.String(10), default='16px')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alcohol_type = db.Column(db.String(20))
    content = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    water_type = db.Column(db.String(50))
    yeast_id = db.Column(db.Integer, db.ForeignKey('yeast.id'))
    yeast = db.relationship('Yeast')

    batches = db.relationship(
        'Batch',
        backref='recipe',
        lazy=True,
        cascade='all, delete-orphan'
    )

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    events = db.relationship('CalendarEvent', backref='batch', lazy=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    fermentation_temp = db.Column(db.String(50))
    initial_gravity = db.Column(db.Float)
    final_gravity = db.Column(db.Float)
    abv = db.Column(db.Float)
    yeast_type = db.Column(db.String(100))
    backsweetened = db.Column(db.Boolean)
    flavor_additions = db.Column(db.Text)
    pectic_used = db.Column(db.Boolean)
    notes = db.Column(db.Text)
    water_type = db.Column(db.String(50))
    alcohol_type = db.Column(db.String(20))
    tosna_total = db.Column(db.Float, comment="Total Fermaid O needed in grams")
    tosna_per_day = db.Column(db.Float, comment="Fermaid O per day over 4 days")
    tosna_enabled = db.Column(db.Boolean, default=False)
    yeast_id = db.Column(db.Integer, db.ForeignKey('yeast.id'))
    yeast = db.relationship('Yeast')

    measurements = db.relationship(
        'Measurement',
        backref='batch',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'))
    title = db.Column(db.String(100), nullable=False)
    start = db.Column(db.Date, nullable=False)
    end = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text)
    all_day = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    note = db.Column(db.Text)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount_per_gallon = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(200))

    recipe = db.relationship('Recipe', backref=db.backref('ingredients', cascade='all, delete-orphan'))

class Yeast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alcohol_type = db.Column(db.String(20), nullable=False)
    tolerance = db.Column(db.String(50))
    strength = db.Column(db.String(50))
    sweetness_retention = db.Column(db.String(50))
    notes = db.Column(db.Text)
    flocculation = db.Column(db.String(50))
    attenuation = db.Column(db.String(10))
    is_default = db.Column(db.Boolean, default=False)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    gravity = db.Column(db.Float)
    ph = db.Column(db.Float)
    temperature = db.Column(db.Float)
    notes = db.Column(db.Text)
    
class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    base_url = db.Column(db.String(255))

