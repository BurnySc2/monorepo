const drop_zone = document.getElementById('drop-zone') as HTMLDivElement | null;
const file_input = document.getElementById('replays') as HTMLInputElement | null;

const prevent_defaults = (e: Event) => {
    e.preventDefault();
    e.stopPropagation();
};

if (!drop_zone || !file_input) {
    console.error('Required elements not found');
} else {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event_name => {
        document.body.addEventListener(event_name, prevent_defaults, false);
    });

    // Highlight drop zone when dragging files over
    ['dragenter', 'dragover'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault();
            drop_zone.classList.add('border-blue-500', 'bg-blue-100');
        }, false);
    });

    ['dragleave', 'drop'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault();
            drop_zone.classList.remove('border-blue-500', 'bg-blue-100');
        }, false);
    });

    // Handle dropped files
    drop_zone.addEventListener('drop', (e: DragEvent) => {
        e.preventDefault();
        const dt = e.dataTransfer;
        if (!dt) return;

        const files = dt.files;
        if (!files) return;

        // Add files to existing file input
        if (file_input.files && file_input.files.length > 0) {
            const new_files = Array.from(file_input.files).concat(Array.from(files));
            const data_transfer = new DataTransfer();
            new_files.forEach(file => data_transfer.items.add(file));
            file_input.files = data_transfer.files;
        } else {
            file_input.files = files;
        }
    });
}

const main = (): void => {
    console.log("Replay pack builder initialized");
};
