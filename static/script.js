var socket = io();

let noteIdToDelete = null; // Temporary storage for the ID

// 1. Open Modal instead of browser alert
function deleteNote(noteId) {
    noteIdToDelete = noteId;
    document.getElementById('deleteModal').style.display = 'flex';
}

document.addEventListener('DOMContentLoaded', () => {
    const deleteModal = document.getElementById('deleteModal');
    const confirmBtn = document.getElementById('confirmDelete');
    const cancelBtn = document.getElementById('cancelDelete');

    document.getElementById('rewrite-btn').onclick = enterEditMode;
    document.getElementById('cancel-btn').onclick = () => { 
        exitEditMode();
    }
    document.getElementById('save-btn').onclick = saveChanges;

    document.getElementById('closeButton').onclick = () => {
        document.querySelector('.big-holder').style.display = 'none';
        currentOpenNoteId = null;
    };

    document.getElementById('delete-btn-modal').onclick = () => {
        if (currentOpenNoteId) {
            deleteNote(currentOpenNoteId);
        }
    };

    cancelBtn.addEventListener('click', () => {
        deleteModal.style.display = 'none';
        noteIdToDelete = null;
    });

    confirmBtn.addEventListener('click', () => {
        if (noteIdToDelete) {
            socket.emit('delete_note', { id: noteIdToDelete });
            deleteModal.style.display = 'none';

            document.querySelector('.big-holder').style.display = 'none';

            noteIdToDelete = null;
            currentOpenNoteId = null;
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const newNoteBtn = document.querySelector('.New-note');
    const createNoteContainer = document.querySelector('.createNote');
    const cancelBtn = document.querySelector('.cancelButton');
    const noteForm = document.querySelector('#noteForm');

    newNoteBtn.addEventListener('click', () => {
        createNoteContainer.style.display = (createNoteContainer.style.display === 'block') ? 'none' : 'block';
    });

    cancelBtn.addEventListener('click', () => {
        createNoteContainer.style.display = 'none';
    });
    noteForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const titleValue = document.querySelector('#fname').value;
        const contentValue = document.querySelector('#content').value;

        socket.emit('add_note', {
            title: titleValue, 
            content: contentValue
        });
        
        this.reset();
        createNoteContainer.style.display = 'none';
    });
});

let originalTitle = "";
let originalContent = "";

function enterEditMode() {
    const titleEl = document.getElementById('titleText');
    const contentEl = document.getElementById('contentText');

    originalTitle = titleEl.innerText;
    originalContent = contentEl.innerText;

    titleEl.innerHTML = `<input type="text" id="edit-title-input" class="modal-input" value="${originalTitle}">`;
    contentEl.innerHTML = `<textarea id="edit-content-textarea" class="modal-textarea">${originalContent}</textarea>`;

    document.getElementById('rewrite-btn').style.display = 'none';
    document.getElementById('delete-btn-modal').style.display = 'none';
    document.getElementById('save-btn').style.display = 'inline-block';
    document.getElementById('cancel-btn').style.display = 'inline-block';
    document.getElementById('line').style.display = 'none';
}

function exitEditMode(save = false) {
    const titleEl = document.getElementById('titleText');
    const contentEl = document.getElementById('contentText');

    if (!save) {
        titleEl.innerText = originalTitle;
        contentEl.innerText = originalContent;
    } else {
        titleEl.innerText = document.getElementById('edit-title-input').value;
        contentEl.innerText = document.getElementById('edit-content-textarea').value;
    }

    const line = document.getElementById('line');
    if (line) line.style.display = 'block';

    document.getElementById('rewrite-btn').style.display = 'inline-block';
    document.getElementById('delete-btn-modal').style.display = 'inline-block';
    document.getElementById('save-btn').style.display = 'none';
    document.getElementById('cancel-btn').style.display = 'none';
}

function saveChanges() {
    const titleInput = document.getElementById('edit-title-input');
    const contentInput = document.getElementById('edit-content-textarea');

    if (titleInput && contentInput) {
        const newTitle = titleInput.value;
        const newContent = contentInput.value;

        socket.emit('update_note', {
            id: currentOpenNoteId,
            title: newTitle,
            content: newContent
        });
        exitEditMode(true);
    }
}

let currentOpenNoteId = null;

function openFullNote(id) {
    currentOpenNoteId = id;
    const noteCard = document.getElementById(`note-${id}`);

    const title = noteCard.querySelector('.note-title-source').innerText;
    const content = noteCard.querySelector('.note-body-source').innerText;
    const time = noteCard.querySelector('.note-time-source').innerText;

    originalTitle = title;
    originalContent = content;

    document.getElementById('titleText').innerText = title;
    document.getElementById('contentText').innerText = content;
    document.getElementById('upToDate').innerText = time;

    document.querySelector('.big-holder').style.display = 'block';
    
    // 5. Ensure buttons are reset to view mode
    document.getElementById('rewrite-btn').style.display = 'inline-block';
    document.getElementById('delete-btn-modal').style.display = 'inline-block';
    document.getElementById('save-btn').style.display = 'none';
    document.getElementById('cancel-btn').style.display = 'none';
    
    exitEditMode();
}

socket.on('note_added', function(data) {
    let container = document.querySelector('.note-holder');
    const emptyState = document.querySelector('.stack-wrapper');

    // If "No notes yet" is visible, we must create the note-holder first
    if (emptyState) {
        // Replace the entire empty state area with a fresh note-holder
        emptyState.outerHTML = `<div class="note-holder"></div>`;
        container = document.querySelector('.note-holder');
    }

    const newNoteHtml = `
        <div id="note-${data.id}" class="notes" onclick="openFullNote(${data.id})">
                <h3 class="note-title-source">${data.title}</h3>
                <div class="note-action">
                    <button class="delete" onclick="deleteNote(${data.id})"><img src="/static/png/delete.png"></button>
                </div>
            <hr>
            <p class="Note-Content note-body-source">${data.content}</p>
            <span class="Time note-time-source" style="margin-top: auto; padding: 20px;">Updated: ${data.timestamp}</span>
        </div>`;
    
    // Insert the note into the now-existing container
    container.insertAdjacentHTML('beforeend', newNoteHtml);
});

socket.on('note_deleted', function(data) {
    const el = document.getElementById(`note-${data.id}`);
    if (el) el.remove();
    
    const container = document.querySelector('.note-holder');
    if (container && container.children.length === 0) {
        location.reload();

        container.innerHTML = `
            <div class="stack-wrapper">
                <div class="body-bar">
                    <img src="/static/png/haha.png" class="body-logo">
                    <h2>No notes yet</h2>
                    <p id="create">Click "New Note" to create your first note</p>
                </div>
            </div>`;
    }
});

socket.on('note_updated', function(data) {
    const noteCard = document.getElementById(`note-${data.id}`);

    if (noteCard) {
        noteCard.querySelector('.note-body-source').innerText = data.content;
        noteCard.querySelector('.note-time-source').innerText = `Updated: ${data.timestamp}`;
        noteCard.querySelector('.note-title-source').innerText = data.title;
    }

    const modalTime = document.getElementById('upToDate');
    if (modalTime) {
        modalTime.innerText = "Updated: " + data.timestamp;
    }
    exitEditMode(true);
});

socket.on('load_notes', function(data) {
    // 1. Find or reset the container
    let container = document.querySelector('.note-holder');
    const emptyState = document.querySelector('.stack-wrapper');

    // 2. If there are no notes in the new group, show the empty state
    if (data.notes.length === 0) {
        const dashboard = document.querySelector('.dashboard-content'); // Or your main parent
        dashboard.innerHTML = `
            <div class="stack-wrapper">
                <img src="/static/png/empty.png">
                <p>No notes in this group yet.</p>
            </div>`;
        return;
    }

    // 3. If notes exist, ensure we have a note-holder and clear it
    if (emptyState) {
        emptyState.outerHTML = `<div class="note-holder"></div>`;
        container = document.querySelector('.note-holder');
    } else if (container) {
        container.innerHTML = ''; // Wipe old notes from previous group
    }

    // 4. Loop through and add each note using your exact HTML template
    data.notes.forEach(note => {
        const noteHtml = `
            <div id="note-${note.id}" class="notes" onclick="openFullNote(${note.id})">
                    <h3 class="note-title-source">${note.title}</h3>
                    <div class="note-action">
                        <button class="delete" onclick="deleteNote(${note.id})"><img src="/static/png/delete.png"></button>
                    </div>
                <hr>
                <p class="Note-Content note-body-source">${note.content}</p>
                <span class="Time note-time-source" style="margin-top: auto; padding: 20px;">Updated: ${note.timestamp}</span>
            </div>`;
        container.insertAdjacentHTML('beforeend', noteHtml);
    });
});