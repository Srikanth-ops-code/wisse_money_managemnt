from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal, InvalidOperation
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "wise-demo-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///wise_demo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

MICRO_SAVINGS_RATE = Decimal("0.02")  # Demo setting: 2% of each pot top-up

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("25000.00"))
    vault_balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("750.00"))
    external_balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("12000.00"))
    external_bank_name = db.Column(db.String(100), nullable=False, default="Demo External Bank")
    external_linked = db.Column(db.Boolean, nullable=False, default=False)

class Pot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    icon = db.Column(db.String(12), default="◎")
    color = db.Column(db.String(20), default="teal")
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # top-up, spending, external, savings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def money(value):
    try:
        amount = Decimal(str(value))
        if amount <= 0:
            raise ValueError
        return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Enter a valid amount greater than zero.")

def get_wallet():
    return Wallet.query.first()

def seed_data():
    if not Wallet.query.first():
        db.session.add(Wallet())
    if Pot.query.count() == 0:
        db.session.add_all([
            Pot(name="Travel", icon="✈", color="blue", balance=Decimal("3500.00")),
            Pot(name="Food", icon="☕", color="orange", balance=Decimal("1800.00")),
            Pot(name="Shopping", icon="◇", color="purple", balance=Decimal("2400.00")),
            Pot(name="Groceries", icon="⌂", color="green", balance=Decimal("2200.00")),
        ])
    if Transaction.query.count() == 0:
        db.session.add_all([
            Transaction(description="Monthly travel allocation", category="Travel", amount=Decimal("3500.00"), kind="top-up"),
            Transaction(description="Food budget allocation", category="Food", amount=Decimal("1800.00"), kind="top-up"),
            Transaction(description="Grocery shopping", category="Groceries", amount=Decimal("640.00"), kind="spending"),
            Transaction(description="Save Vault contribution", category="Save Vault", amount=Decimal("750.00"), kind="savings"),
        ])
    db.session.commit()

@app.context_processor
def inject_globals():
    wallet = get_wallet()
    pots = Pot.query.all()
    allocated = sum((p.balance for p in pots), Decimal("0.00"))
    available = (wallet.main_balance - allocated - wallet.vault_balance) if wallet else Decimal("0.00")
    return {"wallet": wallet, "pots": pots, "allocated": allocated, "available": available,
            "vault_rate": int(MICRO_SAVINGS_RATE * 100)}

@app.route("/")
def dashboard():
    wallet = get_wallet()
    pots = Pot.query.order_by(Pot.name).all()
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(7).all()
    total_spent = sum((t.amount for t in Transaction.query.filter_by(kind="spending").all()), Decimal("0.00"))
    return render_template("dashboard.html", pots=pots, transactions=transactions, total_spent=total_spent)

@app.route("/pots/<int:pot_id>/topup", methods=["POST"])
def topup_pot(pot_id):
    pot = Pot.query.get_or_404(pot_id)
    try:
        amount = money(request.form.get("amount"))
        wallet = get_wallet()
        savings = (amount * MICRO_SAVINGS_RATE).quantize(Decimal("0.01"))
        total_needed = amount
        current_available = wallet.main_balance - sum((p.balance for p in Pot.query.all()), Decimal("0.00")) - wallet.vault_balance
        if amount > current_available:
            flash("Not enough available balance in your main account.", "error")
            return redirect(url_for("dashboard"))
        pot.balance += amount - savings
        wallet.vault_balance += savings
        db.session.add(Transaction(description=f"Added money to {pot.name}", category=pot.name, amount=amount-savings, kind="top-up"))
        if savings > 0:
            db.session.add(Transaction(description=f"{vault_rate_label()} micro-savings from {pot.name}", category="Save Vault", amount=savings, kind="savings"))
        db.session.commit()
        flash(f"₹{amount:,.2f} allocated to {pot.name}; ₹{savings:,.2f} moved to Save Vault.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("dashboard"))

def vault_rate_label():
    return f"{int(MICRO_SAVINGS_RATE * 100)}%"

@app.route("/pots/<int:pot_id>/spend", methods=["POST"])
def spend_from_pot(pot_id):
    pot = Pot.query.get_or_404(pot_id)
    try:
        amount = money(request.form.get("amount"))
        description = (request.form.get("description") or f"{pot.name} purchase").strip()[:120]
        if amount > pot.balance:
            flash(f"Not enough money in your {pot.name} pot.", "error")
            return redirect(url_for("dashboard"))
        pot.balance -= amount
        db.session.add(Transaction(description=description, category=pot.name, amount=amount, kind="spending"))
        db.session.commit()
        flash(f"₹{amount:,.2f} spent from {pot.name}.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("dashboard"))

@app.route("/pots/create", methods=["POST"])
def create_pot():
    name = (request.form.get("name") or "").strip().title()
    if not name or len(name) > 60:
        flash("Enter a pot name (up to 60 characters).", "error")
        return redirect(url_for("dashboard"))
    if Pot.query.filter(db.func.lower(Pot.name) == name.lower()).first():
        flash("A pot with that name already exists.", "error")
        return redirect(url_for("dashboard"))
    Pot(name=name, icon="◎", color="teal", balance=Decimal("0.00"))
    db.session.add(Pot(name=name, icon="◎", color="teal", balance=Decimal("0.00")))
    db.session.commit()
    flash(f"{name} pot created.", "success")
    return redirect(url_for("dashboard"))

@app.route("/external", methods=["GET", "POST"])
def external():
    wallet = get_wallet()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "link":
            wallet.external_linked = True
            db.session.commit()
            flash("Demo external account linked. No real bank connection was made.", "success")
        elif action == "transfer":
            try:
                amount = money(request.form.get("amount"))
                if not wallet.external_linked:
                    raise ValueError("Link the demo external account first.")
                if amount > wallet.external_balance:
                    raise ValueError("Insufficient demo external account balance.")
                wallet.external_balance -= amount
                wallet.main_balance += amount
                db.session.add(Transaction(description="Funds added from external demo account", category="External transfer", amount=amount, kind="external"))
                db.session.commit()
                flash(f"₹{amount:,.2f} moved from the demo external account to WISE.", "success")
            except ValueError as e:
                flash(str(e), "error")
        return redirect(url_for("external"))
    return render_template("external.html", wallet=wallet)

@app.route("/insights")
def insights():
    pots = Pot.query.all()
    spent_by_category = {}
    for t in Transaction.query.filter_by(kind="spending").all():
        spent_by_category[t.category] = spent_by_category.get(t.category, Decimal("0.00")) + t.amount
    total_spent = sum(spent_by_category.values(), Decimal("0.00"))
    return render_template("insights.html", pots=pots, spent_by_category=spent_by_category, total_spent=total_spent)

@app.route("/bank-growth")
def bank_growth():
    wallet = get_wallet()
    active_demo_users = 10000
    assumed_incremental_balance = Decimal("5000.00")
    illustrative_deposits = active_demo_users * assumed_incremental_balance
    return render_template("bank_growth.html", active_demo_users=active_demo_users,
                           assumed_incremental_balance=assumed_incremental_balance,
                           illustrative_deposits=illustrative_deposits, wallet=wallet)

@app.route("/reset-demo", methods=["POST"])
def reset_demo():
    db.drop_all()
    db.create_all()
    seed_data()
    flash("Demo data has been reset.", "success")
    return redirect(url_for("dashboard"))

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)
