from flask_sqlalchemy import SQLAlchemy

# Create a global SQLAlchemy instance to avoid circular imports.
# The Flask app will initialize it via db.init_app(app).
db = SQLAlchemy()

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cards = db.relationship("Card", backref="deck", cascade="all, delete")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    rarity = db.Column(db.String(20))
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    xp = db.Column(db.Integer)
    level = db.Column(db.Integer)
    streak = db.Column(db.Integer)
    last_study = db.Column(db.String(20))
    combo = db.Column(db.Integer, default=0)
