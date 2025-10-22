from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random, datetime, math

app = Flask(__name__)
app.secret_key = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///study.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy()

from models import db as models_db, Deck, Card, Player

# Ensure the models' db and this module's db are the same instance
db = models_db
db.init_app(app)

# ---------- UTILITIES ---------- #
def get_player():
    player = Player.query.first()
    if not player:
        player = Player(username="You", xp=0, level=1, streak=0, last_study=str(datetime.date.today()))
        db.session.add(player)
        db.session.commit()
    return player

def add_xp(player, amount):
    player.xp += amount
    next_lvl = int(100 * (1.5 ** (player.level - 1)))
    if player.xp >= next_lvl:
        player.level += 1
        player.xp -= next_lvl
    db.session.commit()

# Inject the current player into all templates (for navbar/header usage)
@app.context_processor
def inject_player():
    try:
        return {"player": get_player()}
    except Exception:
        # During first-time migrations or errors before DB ready
        return {"player": None}

# Ensure tables exist when the module is imported (e.g., via `flask run`)
with app.app_context():
    try:
        db.create_all()
        # Ensure legacy DBs have new columns
        with db.engine.begin() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(player)"))]
            if 'combo' not in cols:
                conn.execute(text("ALTER TABLE player ADD COLUMN combo INTEGER DEFAULT 0"))
    except Exception:
        # If DB backend not ready or migrations used elsewhere, ignore
        pass

# ---------- ROUTES ---------- #
@app.route("/")
def index():
    decks = Deck.query.all()
    player = get_player()
    return render_template("index.html", decks=decks, player=player)

@app.route("/deck/create", methods=["POST"])
def create_deck():
    deck = Deck(name=request.form["name"])
    db.session.add(deck)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/deck/<int:deck_id>")
def view_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    return render_template("deck.html", deck=deck)

@app.route("/deck/<int:deck_id>/add", methods=["POST"])
def add_card(deck_id):
    rarities = ["Common", "Rare", "Epic", "Legendary"]
    rarity = random.choices(rarities, weights=[70,20,8,2])[0]
    card = Card(deck_id=deck_id,
                question=request.form["question"],
                answer=request.form["answer"],
                rarity=rarity)
    db.session.add(card)
    db.session.commit()
    return redirect(url_for("view_deck", deck_id=deck_id))

@app.route("/study/<int:deck_id>")
def study(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if not deck.cards:
        return redirect(url_for("view_deck", deck_id=deck_id))
    card = random.choice(deck.cards)
    return render_template("study.html", deck=deck, card=card)

@app.route("/answer/<int:card_id>", methods=["POST"])
def answer(card_id):
    card = Card.query.get_or_404(card_id)
    player = get_player()
    user_answer = request.form["answer"].strip().lower()
    correct = user_answer == card.answer.strip().lower()

    today = str(datetime.date.today())
    if player.last_study != today:
        player.streak += 1
        player.last_study = today

    # combo multiplier base logic
    combo_multiplier = 1 + (player.combo * 0.1)

    if correct:
        player.combo += 1
        rarity_xp = {"Common":10, "Rare":20, "Epic":35, "Legendary":50}[card.rarity]
        xp_gain = int(rarity_xp * combo_multiplier)
        add_xp(player, xp_gain)
        feedback = "correct"
        show_answer = False
        combo_active = True
    else:
        player.xp = max(0, player.xp - 5)
        player.combo = 0
        feedback = "wrong"
        show_answer = True
        combo_active = False

    db.session.commit()

    return render_template(
        "study.html",
        deck=card.deck,
        card=card,
        feedback=feedback,
        show_answer=show_answer,
        combo_active=combo_active,
        combo=player.combo
    )

@app.route("/leaderboard")
def leaderboard():
    players = Player.query.order_by(Player.level.desc(), Player.xp.desc()).all()
    return render_template("leaderboard.html", players=players)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
