import bcrypt
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
    "?charset=utf8mb4"
)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

# Routes (updated with SQLAlchemy)
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
            if not user:
                app.logger.warning(f"Login attempt for non-existent user: {username}")
                return render_template('admin_login.html', error="Invalid credentials")

            if bcrypt.checkpw(password, user.password.encode('utf-8')):
                session['admin_logged_in'] = True
                session.permanent = True
                app.logger.info(f"Successful login for admin: {username}")
                return redirect(url_for('admin_dashboard'))
            
            app.logger.warning(f"Failed login attempt for user: {username}")
            return render_template('admin_login.html', error="Invalid credentials")

        except Exception as e:
            app.logger.error(f"Login error for {username}: {str(e)}")
            return render_template('admin_login.html', error="Database error. Please try again later.")

    return render_template('admin_login.html')

@app.route('/admin/orders')
def view_orders():
    try:
        orders = db.session.execute(text("""
            SELECT o.*, SUM(oi.quantity * m.price) AS total 
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            GROUP BY o.id
        """)).mappings().all()
        return render_template('admin_partials/view_orders.html', orders=orders)
    except Exception as e:
        app.logger.error(f"Error fetching orders: {str(e)}")
        return render_template('admin_partials/view_orders.html', orders=[])

@app.route('/admin/menu', methods=['GET', 'POST'])
def manage_menu():
    if request.method == 'POST':
        try:
            new_item = MenuItem(
                name=request.form['name'],
                description=request.form['description'],
                price=float(request.form['price'])
            )
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('manage_menu'))
        except Exception as e:
            app.logger.error(f"Error adding menu item: {str(e)}")
            db.session.rollback()
    
    items = MenuItem.query.all()
    return render_template('admin_partials/menu_management.html', items=items)

@app.route('/admin/employees', methods=['GET', 'POST'])
def manage_employees():
    if request.method == 'POST':
        try:
            new_employee = Employee(
                name=request.form['name'],
                role=request.form['role']
            )
            db.session.add(new_employee)
            db.session.commit()
            return redirect(url_for('manage_employees'))
        except Exception as e:
            app.logger.error(f"Error adding employee: {str(e)}")
            db.session.rollback()
    
    employees = Employee.query.all()
    return render_template('admin_partials/employees.html', employees=employees)

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    try:
        # Create order
        new_order = Order(
            table_number=data['tableNumber'],
            total=data['total']
        )
        db.session.add(new_order)
        db.session.flush()  # To get the order ID
        
        # Add order items
        for item in data['cart']:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item['id'],
                quantity=item['quantity']
            )
            db.session.add(order_item)
        
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        app.logger.error(f"Order error: {str(e)}")
        db.session.rollback()
        return jsonify(success=False), 500

@app.route('/delete-item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        item = MenuItem.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
        return redirect(url_for('manage_menu'))
    except Exception as e:
        app.logger.error(f"Error deleting item: {str(e)}")
        db.session.rollback()
        return redirect(url_for('manage_menu'))

@app.route('/delete-employee/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    try:
        employee = Employee.query.get(emp_id)
        if employee:
            db.session.delete(employee)
            db.session.commit()
        return redirect(url_for('manage_employees'))
    except Exception as e:
        app.logger.error(f"Error deleting employee: {str(e)}")
        db.session.rollback()
        return redirect(url_for('manage_employees'))
    
@app.route('/admin/orders/<int:order_id>')
def view_order(order_id):
    try:
        # Fetch the specific order and associated items
        order = db.session.execute(text("""
            SELECT o.*, SUM(oi.quantity * m.price) AS total 
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items m ON oi.menu_item_id = m.id
            WHERE o.id = :order_id
            GROUP BY o.id
        """), {'order_id': order_id}).mappings().first()

        if not order:
            return "Order not found", 404

        return render_template('admin_partials/view_order_details.html', order=order)
    except Exception as e:
        app.logger.error(f"Error fetching order details: {str(e)}")
        return "Error fetching order details", 500


# Add this temporary route to test connection
@app.route('/test-conn')
def test_conn():
    try:
        db.session.execute(text('SELECT 1'))
        return "Database connection successful!"
    except Exception as e:
        return f"Connection failed: {str(e)}", 500
# Other routes remain similar, just update database interactions

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)