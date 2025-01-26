from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)

# Konfigurasi
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# Inisialisasi database dan modul tambahan
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin' atau 'user'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    order_details = db.Column(db.Text, nullable=False)  # Simpan sebagai JSON string
    total_payment = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def home():
    if current_user.role == "admin":
        # Ambil data pesanan untuk ditampilkan di dashboard
        total_orders = Order.query.count()
        total_revenue = db.session.query(db.func.sum(Order.total_payment)).scalar() or 0
        total_customers = User.query.filter_by(role='user').count()
        average_rating = 4.5  # Misalkan kita memiliki rating tetap untuk contoh ini
        recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()
        
        return render_template("Dashboard.html", total_orders=total_orders, total_revenue=total_revenue,
                               total_customers=total_customers, average_rating=average_rating,
                               recent_orders=recent_orders)
    else:
        return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f"Selamat datang, {user.role.capitalize()}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Login gagal. Periksa username dan password.", "danger")
    return render_template("login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))
    # Ambil data pesanan untuk ditampilkan di dashboard
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_payment)).scalar() or 0
    total_customers = User.query.filter_by(role='user').count()
    average_rating = 4.5  # Misalkan kita memiliki rating tetap untuk contoh ini
    recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()
    
    return render_template("Dashboard.html", total_orders=total_orders, total_revenue=total_revenue,
                           total_customers=total_customers, average_rating=average_rating,
                           recent_orders=recent_orders)

@app.route("/user")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/submit_order", methods=["POST"])
@login_required
def submit_order():
    data = request.get_json()  # Terima data dalam format JSON
    try:
        # Parsing data
        customer_name = data.get("customerName")
        customer_phone = data.get("customerPhone")
        customer_address = data.get("customerAddress")
        order_details = data.get("orderDetails")  # String JSON dari frontend
        
        # Ambil total pembayaran dari form
        total_pembayaran = data.get('orderTotal', '0')
        # Hapus format yang tidak valid
        total_pembayaran = total_pembayaran.replace(',', '').strip()
        total_pembayaran = float(total_pembayaran)

        # Simpan ke database
        new_order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            order_details=order_details,
            total_payment=total_pembayaran,
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"success": True, "message": "Pesanan berhasil disimpan."}), 201
    except ValueError:
        return jsonify({"success": False, "message": "Gagal menyimpan pesanan: Total pembayaran tidak valid"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Tambahkan admin jika belum ada
        if not User.query.filter_by(username="admin").first():
            hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
            admin_user = User(username="admin", password=hashed_password, role="admin")
            db.session.add(admin_user)

        # Tambahkan pembeli (user) jika belum ada
        if not User.query.filter_by(username="user").first():
            hashed_password = bcrypt.generate_password_hash("user123").decode("utf-8")
            buyer_user = User(username="user", password=hashed_password, role="user")
            db.session.add(buyer_user)

        db.session.commit()

    app.run(debug=True)
