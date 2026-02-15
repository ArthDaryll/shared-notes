from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timezone
from flask_login import login_user, LoginManager, UserMixin, login_required, current_user


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharednotes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here' # Required for sessions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    members = db.relationship('User', secondary=user_groups, backref=db.backref('groups', lazy='dynamic'))
    notes = db.relationship('Note', backref='group', lazy=True)

class GroupRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    status = db.Column(db.String(20), default='pending')
    user = db.relationship('User', backref='sent_requests')
    group = db.relationship('Group', backref='received_requests')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)


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
    group_id = data.get('group_id')

    if group_id:
        group = Group.query.get(group_id)
        if not group or current_user not in group.members:
            return False

    new_note = Note(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id,
        group_id=group_id
    )
    db.session.add(new_note)
    db.session.commit()

    note_payload = {
        'id': new_note.id,
        'title': new_note.title,
        'content': new_note.content,
        'timestamp': new_note.timestamp.strftime('%d-%m-%Y, %I:%M:%p'),
        'user_id': new_note.user_id,
        'group_id': new_note.group_id
    }

    if group_id:
        emit('note_added', note_payload, to=f'group_{group_id}')
    else:
        emit('note_added', note_payload, to=request.sid)

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

@socketio.on('update_note')
def handle_update_note(data):
    note = Note.query.get(data['id'])

    if note and note.user_id == current_user.id:
        note.title = data['title']
        note.content = data['content']
        note.timestamp = datetime.now(timezone.utc)
        db.session.commit()

        emit('note_updated', {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'timestamp': note.timestamp.strftime('%d-%m-%Y, %I:%M:%p')
        }, broadcast=True)

@socketio.on('create_group')
def handle_create_group(data):
    group_name = data.get('group_name')
    if Group.query.filter_by(name=group_name).first():
        emit('error', {'message': 'Group name already exists'})
        return
    new_group = Group(name=group_name, owner_id=current_user.id)
    new_group.members.append(current_user)
    db.session.add(new_group)
    db.session.commit()

    join_room(f"group_{new_group.id}")
    emit('group_created', {
        'group_id': new_group.id, 
        'group_name': new_group.name
    })

@socketio.on('delete_group')
def handle_delete_group(data):
    group_id = data.get('group_id')
    group = Group.query.get(group_id)
    if not group:
        return
    if group.owner_id != current_user.id:
        emit('error', {'message': 'Only the owner can delete this group'})
        return
    Note.query.filter_by(group_id=group_id).delete()
    GroupRequest.query.filter_by(group_id=group_id).delete()
    db.session.delete(group)
    db.session.commit()

    emit('group_deleted', {'group_id': group_id}, to=f"group_{group_id}")

@socketio.on('leave_group')
def handle_leave_group(data):
    group_id = data.get('group_id')
    group = Group.query.get(group_id)
    if group and current_user in group.members:
        if group.owner_id == current_user.id:
            emit('error', {'message': 'Owner cannot leave. Delete the group instead'})
        else:
            group.members.remove(current_user)
            db.session.commit()
            leave_room(f"group_{group_id}")
            emit('group_left', {'group_id': group_id}, to=f"group_{group_id}")

@socketio.on('switch_group')
def handle_swtich_group(data):
    group_id = data.get('group_id')

    if group_id:
        group = Group.query.get(group_id)
        if not group or current_user not in group.members:
            return False
        join_room(f"group_{group_id}")
        notes = Note.query.filter_by(group_id=group_id).order_by(Note.timestamp.asc()).all
    else:
        notes = Note.query.filter_by(user_id=current_user.id, group_id=None).order_by(Note.timestamp.asc()).all

    notes_data = [{
        'id': note.id,
        'title': note.title,
        'content': note.content',
        'timestamp': note.timestamp.strftime('%d-%m-%Y, %I:%M:%p'),
    } for note in notes]

    emit('load_notes', {'notes': notes_data, 'group_id': group_id})

@socketio.on('join_group_room')
def handle_join_group(data):
    group_id = data.get('group_id')
    room = f'group_{group_id}'
    join_room(room)

@socketio.on('search_groups')
def handle_search(data):
    query = data.get('query', '')
    if len(query) < 2:
        return
    results = Group.query.filter(Group.name.like(f'%{query}%')).all()

    output = []
    for group in results:
        is_member = current_user in group.members
        has_pending = GroupRequest.query.filter_by(
            user_id=current_user.id,
            group_id=group.id,
            status='pending'
        ).first() is not None

        output.append({
            'id': group.id,
            'name': group.name,
            'is_member': is_member,
            'has_pending': has_pending
        })
    emit('search_results', output)

@socketio.on('apply_to_group')
def handle_apply(data):
    group_id = data.get('group_id')
    group = Group.query.get(group_id)
    if not group:
        return
    existing = GroupRequest.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    if not existing:
        new_req = GroupRequest(user_id=current_user.id, group_id=group_id)
        db.session.add(new_req)
        db.session.commit()

        owner_room = f"user_{group.owner_id}"
        emit('new_request_received', {
            'group_name': group.name,
            'user_name': current_user.username
        }, to=owner_room)

@socketio.on('get_pending_requests')
def get_requests():
    owned_groups = Groups.query.filter_by(owner_id=current_user.id).all()
    group_ids = [group.id for group in owned_groups]

    pending = GroupRequest.query.filter(
        GroupRequest.group_id.in_(group_ids),
        GroupRequest.status == 'pending'
    ).all()

    output = [{
        'request_id': request.id,
        'user_name': request.user.username,
        'group_name': request.group.name,
    } for request in pending ]
    emit('pending_requests', output)

@socketio.on('respond_to_request')
def handle_respond(data):
    request_id = data.get('request_id')
    response = data.get('response')
    request = GroupRequest.query.get(request_id)

    if not request or request.user_id != current_user.id:
        return
    if response == 'accept':
        request.status = 'accepted'
        request.group.members.append(request.user)
        db.session.commit()

        emit('application_accepted', {
            'group_id': request.group_id,
            'group_name': request.group.name
        }, to=f"user_{request.user_id}")
    
    else:
        db.session.delete(request)
        db.session.commit()

        emit('application_rejected', {
            'group_name': request.group.name
        }, to=f"user_{request.user_id}")
        
