var socket = io();

function addNote() {
    const input = document.getElementById('note-content');
    const content = input.value;
    if (content) {
        socket.emit('add_note', {content: content});
        input.value = ''; 
    }
}

function deleteNote(id) {
    socket.emit('delete_note', {id: id});
}

// Receiving updates
socket.on('note_added', function(data) {
    const ul = document.getElementById('notes-container');
    ul.innerHTML += `
        <li id="note-${data.id}" style="margin-bottom: 10px;">
            ${data.content} 
            <button onclick="deleteNote(${data.id})" style="color: red; margin-left: 10px; cursor: pointer;">
                Delete
            </button>
        </li>`;
});

socket.on('note_deleted', function(data) {
    const element = document.getElementById(`note-${data.id}`);
    if (element) {
        element.remove();
    }
});