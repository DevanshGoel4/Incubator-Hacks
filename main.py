from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin
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

# Artwork Model
class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)


# Ownership Model
class Ownership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('owned_artworks', lazy=True))
    artwork = db.relationship('Artwork', backref=db.backref('owners', lazy=True))

# Initialize Flask-Admin
admin = Admin(app, name='My Admin', template_mode='bootstrap3')


# Add views for the models
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Artwork, db.session))
admin.add_view(ModelView(Ownership, db.session))

# Assigning the ownership of art
def assign_ownership(user_id, artwork_id):
    ownership = Ownership(user_id=user_id, artwork_id=artwork_id)
    db.session.add(ownership)
    db.session.commit()

# Transferring the ownership to someone else
def transfer_ownership(artwork_id, new_user_id):
    existing_ownership = Ownership.query.filter_by(artwork_id=artwork_id, user_id=new_user_id).first()
    if not existing_ownership:
        ownership = Ownership(user_id=new_user_id, artwork_id=artwork_id)
        db.session.add(ownership)
        db.session.commit()

# Making sure they have the artwork
def get_owned_artworks(user_id):
    return Artwork.query.join(Ownership).filter(Ownership.user_id == user_id).all()

# Routes
@app.route('/')
def home():
    if "username" in session:
        artworks = Artwork.query.all()
        return render_template('dashboard.html', artworks=artworks)
    return render_template('homepage.html')
    


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/cat')
def cat():
    return render_template('cat.html')

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
    
    # Fetch all artworks to pass to the template
    artworks = Artwork.query.all()
    return render_template('dashboard.html', artworks=artworks, i=4)

# My Art
@app.route('/myart')
def myart():
    user = User.query.filter_by(username=session.get('username')).first()
    if user:
        user_id = user.id
        owned_artworks = Ownership.query.filter_by(user_id=user_id).all()
        
        # Get the actual artworks from ownership
        artworks = [ownership.artwork for ownership in owned_artworks]

        return render_template('myart.html', artworks=artworks, username=user.username, message=displaymessage)

# Dynamic welcome messages
messagelist = ["Welcome, ", "Hope you’re well, ", "Let’s get cooking, "]
displaymessage = random.choice(messagelist)

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Route for transferring ownership
@app.route('/assign_ownership/<int:user_id>/<int:artwork_id>', methods=['POST'])
def assign(user_id, artwork_id):
    assign_ownership(user_id, artwork_id)

@app.route('/transfer_ownership/<int:artwork_id>/<int:new_user_id>', methods=['POST'])
def transfer(artwork_id, new_user_id):
    transfer_ownership(artwork_id, new_user_id)

# After clicking buy button
@app.route('/buy/<int:artwork_id>')
def buy_art(artwork_id):
    user = User.query.filter_by(username=session['username']).first()
    
    if user:
        buyer_id = user.id
        transfer_ownership(artwork_id, buyer_id)
        print(f"Ownership transferred: User ID {buyer_id} now owns Artwork ID {artwork_id}")
        return redirect(url_for('myart'))

    print("No user found in session.")
    return redirect(url_for('home'))

if __name__ in "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)