import os
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import random
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key-goes-here'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_BINDS'] = {'shop': 'sqlite:///' + os.path.join(basedir, 'shop.db')}

user_id = 0

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CREATE TABLE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
# db.create_all()

class Products(db.Model):
    __bind_key__ = 'shop'
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    prod = db.Column(db.String(100), unique=True)
    prod_desc = db.Column(db.String(100))
    picture = db.Column(db.String(100))
    price = db.Column(db.Float)

class Cart(db.Model):
    __bind_key__ = 'shop'
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    prod_id = db.Column(db.Integer)
    price = db.Column(db.Integer)
    prod = db.Column(db.String(100))



@app.route('/')
def home():
    with app.app_context():
        # within this block, current_app points to app.
        # print current_app.name
        prods = Products.query.all()

        if current_user.is_authenticated:
            global user_id
            user_id = current_user.id

    return render_template("index.html", logged_in=current_user.is_authenticated, prods=prods)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        global user_id
        user = User.query.filter_by(email=request.form.get('email')).first()
        user_id = user.id
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
    
        user = User.query.filter_by(email=email).first()
        #Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            global user_id
            user = User.query.filter_by(email=request.form.get('email')).first()
            user_id = user.id
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)

@app.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    global user_id
    cart = Cart.query.filter_by(user_id=user_id).all()
    print(cart)
    return render_template("cart.html", logged_in=current_user.is_authenticated, cart=cart)


@app.route('/add/<int:prod_id>', methods=["GET", "POST"])
@login_required
def add(prod_id):
    #lookup price
    prod = Products.query.filter_by(id=prod_id).first()
    price = prod.price
    desc = prod.prod
    global user_id
    print(f'user_id = {user_id}')
    cart = Cart(user_id=user_id, prod_id=prod_id, price=price, prod=desc)
    db.session.add(cart)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/checkout', methods=["GET", "POST"])
@login_required
def checkout():
    global user_id
    Cart.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return render_template("index2.html")


if __name__ == "__main__":
    app.run(debug=True)
