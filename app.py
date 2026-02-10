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

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/delete/<int:note_id>")
def delete_note(note_id):
    # 1. Look into the 'Note' table for a specific row matching the ID
    note_to_delete = Note.query.get_or_404(note_id)
    
    try:
        # 2. Mark that specific row for removal
        db.session.delete(note_to_delete)
        # 3. Save the changes to the .db file
        db.session.commit()
        # 4. Go back to the main list
        return redirect("/")
    except:
        return "Error: Could not delete note."