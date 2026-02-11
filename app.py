from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharednotes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here' # Required for sessions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    notes = Note.query.all()
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
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@socketio.on('add_note')
def handle_add_note(data):
    new_note = Note(content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    emit('note_added', {'id': new_note.id, 'content': new_note.content}, broadcast=True)

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