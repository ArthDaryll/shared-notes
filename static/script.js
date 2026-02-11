var socket = io();

function toggleModal() {
    const modal = document.getElementById('note-modal');
    modal.classList.toggle('hidden');
    if (!modal.classList.contains('hidden')) {
        document.getElementById('note-content').focus();
    }
}

function addNote() {
    const input = document.getElementById('note-content');
    if (input.value.trim()) {
        socket.emit('add_note', {content: input.value});
        input.value = '';
    }
}

function deleteNote(id) {
    socket.emit('delete_note', {id: id});
}

socket.on('note_added', function(data) {
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.classList.add('hidden');
    
    const ul = document.getElementById('notes-container');
    const newNoteHtml = `
        <li id="note-${data.id}" class="bg-zinc-900/50 border border-zinc-800 p-6 rounded-2xl flex flex-col justify-between min-h-[160px] group hover:border-yellow-500/40 transition-all hover:shadow-2xl hover:shadow-yellow-500/5">
            <p class="text-zinc-200 leading-relaxed">${data.content}</p>
            <div class="flex justify-end mt-4">
                <button onclick="deleteNote(${data.id})" class="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all text-xs font-bold uppercase tracking-widest">
                    Delete
                </button>
            </div>
        </li>`;
    ul.insertAdjacentHTML('afterbegin', newNoteHtml);
});

socket.on('note_deleted', function(data) {
    const el = document.getElementById(`note-${data.id}`);
    if (el) el.remove();
    
    const container = document.getElementById('notes-container');
    if (container.children.length === 0) {
        document.getElementById('empty-state').classList.remove('hidden');
    }
});