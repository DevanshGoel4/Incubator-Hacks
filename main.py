from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import random
import secrets

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25), unique = True, nullable = False)
    password_hash = db.Column(db.String(150), nullable = False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Dynamic welcome messages
messagelist = ["Welcome, ", "Hope you’re well, ", "Let’s get cooking, ", "Let’s learn about your skin, "]
displaymessage = random.choice(messagelist)

# Routes
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template('homepage.html')

@app.route('/index')
def index():
    return render_template('index.html')

# Login
@app.route("/login", methods =["POST"])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    if not user:
        error = 'User does not exist!'
        return render_template('index.html', error=error)
    else:
        error = 'Incorrect username or password.'
        return render_template('index.html', error=error)

# Register
@app.route("/register", methods =["POST"])
def register():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if not username:
        error = 'Username cannot be empty!'
        return render_template('index.html', error=error)

    if user:
        error = 'User already exists!'
        return render_template('index.html', error=error)
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))


# Dashboard
@app.route('/dashboard')
def dashboard():
    if "username" not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', message=displaymessage, i=4)


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))



if __name__ in "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)