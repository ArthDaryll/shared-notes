from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
from flask_login import login_user, LoginManager, UserMixin, login_required, current_user


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharednotes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here' # Required for sessions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    #notes = db.relationship('Note', backref='author', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required # Ensure user is logged in
def home():
    # Only get notes for the current user
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.asc()).all()
    return render_template("index.html", notes=notes)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"
            
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            login_user(user)
            return redirect(url_for("home"))
        return "Invalid Credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@socketio.on('add_note')
def handle_add_note(data):
    new_note = Note(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()

    emit('note_added', {
        'id': new_note.id, 
        'title': new_note.title, 
        'content': new_note.content,
        'timestamp': new_note.timestamp.strftime('%d-%m-%Y, %I:%M:%p')  
    })

@socketio.on('delete_note')
def handle_delete_note(data):
    note = Note.query.get(data['id'])
    if note:
        db.session.delete(note)
        db.session.commit()
        emit('note_deleted', {'id': data['id']}, broadcast=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Ensures tables are created
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)