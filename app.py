from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharednotes.db'
socketio = SocketIO(app, cors_allowed_origins="*") # Allows ngrok connections
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)

@app.route("/")
def home():
    notes = Note.query.all()
    return render_template("index.html", notes=notes)

# This handles "Add" in real-time
@socketio.on('add_note')
def handle_add_note(data):
    new_note = Note(content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    # Broadcast to EVERYONE connected
    emit('note_added', {'id': new_note.id, 'content': new_note.content}, broadcast=True)

# This handles "Delete" in real-time
@socketio.on('delete_note')
def handle_delete_note(data):
    note = Note.query.get(data['id'])
    if note:
        db.session.delete(note)
        db.session.commit()
        emit('note_deleted', {'id': data['id']}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)