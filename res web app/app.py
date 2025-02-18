import bcrypt
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from config import Config
from models import db, Order, MenuItem, User, OrderItem

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config.from_object(Config) 
print("POSTGRES_HOST:", os.getenv("POSTGRES_HOST"))


# # Configure SQLAlchemy for PostgreSQL
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
#     f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
# )
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)


# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/menu')
def menu():
    try:
        items = MenuItem.query.all()
        return render_template('menu.html', items=items)
    except Exception as e:
        print("Error fetching menu:", e)
        return render_template('menu.html', items=[])

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').encode('utf-8')

        if not username or not password:
            return render_template('admin_login.html', error="Please fill all fields")

        try:
            user = User.query.filter_by(username=username).first()
            if not user or not bcrypt.checkpw(password, user.password.encode('utf-8')):
                return render_template('admin_login.html', error="Invalid credentials")
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return render_template('admin_login.html', error="Database error. Please try again later.")

    return render_template('admin_login.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    try:
        new_order = Order(table_number=data['tableNumber'], total=data['total'])
        db.session.add(new_order)
        db.session.flush()
        for item in data['cart']:
            order_item = OrderItem(order_id=new_order.id, menu_item_id=item['id'], quantity=item['quantity'])
            db.session.add(order_item)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False), 500

@app.route('/test-conn')
def test_conn():
    try:
        db.session.execute(text('SELECT 1'))
        return "Database connection successful!"
    except Exception as e:
        return f"Connection failed: {str(e)}", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
