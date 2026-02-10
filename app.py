from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 1. Database Configuration
# This creates a file named 'sharednotes.db' in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharednotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. The Database Table (The "Filing Cabinet")
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)

# 3. Create the Database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    # Fetch all saved notes to send to Person A's HTML
    all_notes = Note.query.all()
    return render_template("index.html", notes=all_notes)

@app.route("/add", methods=["POST"])
def add_note():
    # 'note_content' is the ID Person A must use in their HTML
    user_text = request.form.get("note_content")
    if user_text:
        new_note = Note(content=user_text)
        db.session.add(new_note)
        db.session.commit()
    return redirect("/")

@app.route("/delete/<int:note_id>", methods=["POST"]) # <--- ADD THIS HERE
def delete_note(note_id):
    note_to_delete = Note.query.get_or_404(note_id)
    
    try:
        db.session.delete(note_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        return "Error: Could not delete note."
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)