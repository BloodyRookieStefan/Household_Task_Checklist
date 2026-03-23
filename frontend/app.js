// ── Application Initialization and Event Handlers ──
(function() {
    'use strict';

    // Initialize dark mode
    const initDarkMode = () => {
        const saved = localStorage.getItem('darkMode');
        if (saved === 'true') {
            document.body.classList.add('dark-mode');
        }
        updateDarkModeButton();
    };

    const updateDarkModeButton = () => {
        const btn = document.getElementById('darkModeToggle');
        if (btn) {
            const isDark = document.body.classList.contains('dark-mode');
            btn.textContent = isDark ? '☀️' : '🌙';
        }
    };

    const toggleDarkMode = () => {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', isDark);
        updateDarkModeButton();
    };

    // API helper function
    const apiCall = (endpoint, data) => {
        return fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) location.reload();
            return data;
        })
        .catch(err => console.error('Error:', err));
    };

    // Task action handlers
    const handleTaskComplete = (btn, user) => {
        const row = btn.closest('tr');
        const { room, task } = row.dataset;
        apiCall('/api/task/complete', { room, task, doneBy: user, dayDate: currentDayDate });
    };

    const handleTaskUncomplete = (btn) => {
        const row = btn.closest('tr');
        const { room, task } = row.dataset;
        apiCall('/api/task/uncomplete', { room, task, dayDate: currentDayDate });
    };

    const handleCompleteAllRooms = (btn, taskKey, user) => {
        const entry = quickTasks[taskKey];
        if (!entry) return;
        
        const rooms = entry.rooms.filter(r => !r.displayDone && !r.locked);
        if (!rooms.length) return;
        
        btn.disabled = true;
        Promise.all(rooms.map(r =>
            apiCall('/api/task/complete', { 
                room: r.room, 
                task: entry.name, 
                doneBy: user, 
                dayDate: currentDayDate 
            })
        ));
    };

    const handleUncompleteAllRooms = (btn, taskKey) => {
        const entry = quickTasks[taskKey];
        if (!entry) return;
        
        const rooms = entry.rooms.filter(r => r.doneBy);
        if (!rooms.length) return;
        
        btn.disabled = true;
        Promise.all(rooms.map(r =>
            apiCall('/api/task/uncomplete', { 
                room: r.room, 
                task: entry.name, 
                dayDate: currentDayDate 
            })
        ));
    };

    // Event delegation for buttons
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;

        const action = btn.dataset.action;
        if (!action) {
            // Dark mode toggle
            if (btn.id === 'darkModeToggle') {
                e.preventDefault();
                toggleDarkMode();
            }
            return;
        }

        e.preventDefault();
        
        switch(action) {
            case 'complete':
                handleTaskComplete(btn, btn.dataset.user);
                break;
            case 'uncomplete':
                handleTaskUncomplete(btn);
                break;
            case 'complete-all':
                handleCompleteAllRooms(btn, btn.dataset.taskKey, btn.dataset.user);
                break;
            case 'uncomplete-all':
                handleUncompleteAllRooms(btn, btn.dataset.taskKey);
                break;
        }
    });

    // Debug feature: Hover + "a" to mark task as done
    if (debugMode) {
        let hoveredTaskRow = null;

        document.addEventListener('mouseover', (e) => {
            const taskRow = e.target.closest('tr.task-row');
            if (taskRow) hoveredTaskRow = taskRow;
        });

        document.addEventListener('mouseout', (e) => {
            const taskRow = e.target.closest('tr.task-row');
            if (taskRow === hoveredTaskRow) hoveredTaskRow = null;
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'a' && hoveredTaskRow && users.length > 0) {
                e.preventDefault();
                
                const { room, task } = hoveredTaskRow.dataset;
                const isDone = hoveredTaskRow.classList.contains('done');
                
                if (isDone) {
                    apiCall('/api/task/uncomplete', { room, task, dayDate: currentDayDate })
                        .then(() => console.log('[DEBUG] Task uncompleted:', room, task));
                } else {
                    const debugUser = users[0];
                    apiCall('/api/task/complete', { 
                        room, task, doneBy: debugUser, dayDate: currentDayDate 
                    }).then(() => console.log('[DEBUG] Task completed by', debugUser, ':', room, task));
                }
            }
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDarkMode);
    } else {
        initDarkMode();
    }
})();
