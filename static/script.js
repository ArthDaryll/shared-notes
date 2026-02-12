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

    // 2. Handle Cancel
    cancelBtn.addEventListener('click', () => {
        deleteModal.style.display = 'none';
        noteIdToDelete = null;
    });

    // 3. Handle Confirm
    confirmBtn.addEventListener('click', () => {
        if (noteIdToDelete) {
            socket.emit('delete_note', { id: noteIdToDelete });
            deleteModal.style.display = 'none';
            noteIdToDelete = null;
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
        <div id="note-${data.id}" class="notes">
            <div class="note-header" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 25px;">
                <h3>${data.title}</h3>
                <div class="note-action">
                    <button class="rewrite"><img src="/static/png/Ball Point Pen.png"></button>
                    <button class="delete" onclick="deleteNote(${data.id})"><img src="/static/png/delete.png"></button>
                </div>
            </div>
            <hr>
            <p class="Note-Content">${data.content}</p>
            <span class="Time" style="margin-top: auto; padding: 20px;">Updated: ${data.timestamp}</span>
        </div>`;
    
    // Insert the note into the now-existing container
    if (container) {
        container.insertAdjacentHTML('afterbegin', newNoteHtml);
    } else {
        // Fallback: if structure is missing, refresh to let Jinja rebuild it
        location.reload();
    }
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