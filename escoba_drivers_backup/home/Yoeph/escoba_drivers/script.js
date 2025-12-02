document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const loginContainer = document.getElementById('loginContainer');
    const dashboardContainer = document.getElementById('dashboardContainer');
    const activationContainer = document.getElementById('activationContainer');

    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const submitBtn = document.querySelector('.btn-primary');

    const newAccountLink = document.querySelector('.new-account');
    const backToLoginLink = document.querySelector('.back-to-login');
    const driverSelect = document.getElementById('driverSelect');

    const calcBtn = document.querySelector('.btn-danger'); // Calcular Siguiente button
    const addReinforcementBtn = document.querySelector('.btn-outline'); // Añadir Refuerzo button
    const currentEscobaEl = document.getElementById('currentEscoba');
    const reinforcementsListEl = document.getElementById('reinforcementsList');
    const addDriverBtn = document.querySelector('.btn-blue-sm'); // Nuevo Conductor button

    // Data (Mock Database)
    // Exposed globally for testing
    window.driversData = [
        { name: 'JAVI', lastSeen: '2025-11-18', status: 'Asuntos', type: 'asuntos', registrationDate: '2025-01-01', daysOff: ['Jueves', 'Viernes'], phone: '' },
        { name: 'ANTONIO', lastSeen: '2025-11-22', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Domingo', 'Lunes'], phone: '' },
        { name: 'SALVA', lastSeen: '2025-11-23', status: 'Vacaciones', type: 'vacaciones', registrationDate: '2025-01-01', daysOff: ['Lunes', 'Martes'], phone: '' },
        { name: 'JOAN', lastSeen: '2025-11-24', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Jueves', 'Viernes'], phone: '' },
        { name: 'KEVIN', lastSeen: '2025-11-25', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Miércoles', 'Jueves'], phone: '' },
        { name: 'CEMAL', lastSeen: '2025-11-26', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Miércoles', 'Jueves'], phone: '' },
        { name: 'NOUH', lastSeen: '2025-11-28', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Lunes', 'Martes'], phone: '' },
        { name: 'KENNEDY', lastSeen: '2025-11-29', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Jueves', 'Viernes'], phone: '' },
        { name: 'KADA', lastSeen: '2025-11-30', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Lunes', 'Martes'], phone: '' },
        { name: 'ANDY', lastSeen: '2025-12-01', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Jueves', 'Viernes'], phone: '' },
        { name: 'YOEPH', lastSeen: '2025-11-27', status: 'Activo', type: 'active', registrationDate: '2025-01-01', daysOff: ['Martes', 'Miércoles'], phone: '' },
        { name: 'HAYDAR', lastSeen: 'NUNCA', status: 'Asuntos', type: 'asuntos', registrationDate: '2025-01-01', daysOff: ['Lunes', 'Martes'], phone: '' }
    ];

    let currentSessionAssigned = []; // Track assigned drivers in current session

    // Navigation
    newAccountLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginContainer.classList.add('hidden');
        activationContainer.classList.remove('hidden');
        document.body.style.background = '#f0f2f5';
        document.querySelector('.background-animation').style.display = 'none';
        populateDriverSelect();
    });

    backToLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        activationContainer.classList.add('hidden');
        loginContainer.classList.remove('hidden');
        document.body.style.background = ''; // Reset to gradient
        document.querySelector('.background-animation').style.display = 'block';
    });

    // Login Logic
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const username = emailInput.value.trim().toLowerCase();
        const authorizedUsers = ['ana', 'ramon', 'jimmy'];

        const originalBtnText = submitBtn.querySelector('span').innerText;
        submitBtn.querySelector('span').innerText = 'Verificando...';
        submitBtn.style.opacity = '0.8';
        submitBtn.disabled = true;

        setTimeout(() => {
            if (authorizedUsers.includes(username)) {
                loginContainer.classList.add('hidden');
                dashboardContainer.classList.remove('hidden');
                document.body.style.background = '#f0f2f5';
                document.querySelector('.background-animation').style.display = 'none';
                initializeDashboard();
            } else {
                alert('Usuario no autorizado. Solo Ana, Ramon y Jimmy tienen acceso.');
                submitBtn.querySelector('span').innerText = originalBtnText;
                submitBtn.style.opacity = '1';
                submitBtn.disabled = false;
            }
        }, 800);
    });

    // Activation Logic
    function populateDriverSelect() {
        if (driverSelect.options.length > 1) return;
        window.driversData.forEach(driver => {
            const option = document.createElement('option');
            option.value = driver.name;
            option.textContent = driver.name;
            driverSelect.appendChild(option);
        });
    }

    document.getElementById('activationForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const selectedDriver = driverSelect.value;
        const phone = document.getElementById('actPhone').value;
        const daysOff = Array.from(document.querySelectorAll('input[name="day"]:checked')).map(cb => cb.value);

        const driverIndex = window.driversData.findIndex(d => d.name === selectedDriver);
        if (driverIndex !== -1) {
            window.driversData[driverIndex].phone = phone;
            window.driversData[driverIndex].daysOff = daysOff;
            window.driversData[driverIndex].status = 'Activo';
            window.driversData[driverIndex].type = 'active';
        }

        alert(`Cuenta activada para ${selectedDriver}.\nTeléfono: ${phone}\nDías libres: ${daysOff.join(', ')}`);

        activationContainer.classList.add('hidden');
        loginContainer.classList.remove('hidden');
        document.body.style.background = '';
        document.querySelector('.background-animation').style.display = 'block';
    });

    // Dashboard Logic
    function initializeDashboard() {
        renderDrivers();
    }

    // Helper: Get Next Driver
    function getNextDriver(excludeNames = []) {
        const today = new Date();
        const daysOfWeek = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
        const dayName = daysOfWeek[today.getDay()];

        // 1. Filter Candidates
        const candidates = window.driversData.filter(driver => {
            // Must be Active
            if (driver.status !== 'Activo') return false;
            // Must not be their fixed day off
            if (driver.daysOff.includes(dayName)) return false;
            // Must not be already assigned
            if (excludeNames.includes(driver.name)) return false;

            return true;
        });

        if (candidates.length === 0) return null;

        // 2. Sort Candidates
        candidates.sort((a, b) => {
            const aNever = a.lastSeen === 'NUNCA';
            const bNever = b.lastSeen === 'NUNCA';

            // Priority 1: Never served comes first
            if (aNever && !bNever) return -1;
            if (!aNever && bNever) return 1;

            // Priority 2: If both never served, oldest registration date wins
            if (aNever && bNever) {
                return new Date(a.registrationDate) - new Date(b.registrationDate);
            }

            // Priority 3: If both served, oldest lastSeen date wins
            return new Date(a.lastSeen) - new Date(b.lastSeen);
        });

        return candidates[0];
    }

    window.sendWhatsApp = function (name, phone, isReinforcement = false) {
        if (!phone) {
            alert(`Se ha asignado a ${name}, pero no tiene teléfono registrado.`);
            return;
        }

        // Updated Message Format: "Hola [Name]. Hoy te toca ESCOBA"
        const message = isReinforcement
            ? `Hola ${name}. Hoy te toca ESCOBA (Refuerzo).`
            : `Hola ${name}. Hoy te toca ESCOBA.`;

        const url = `https://wa.me/${phone.replace(/\s+/g, '').replace('+', '')}?text=${encodeURIComponent(message)}`;

        // Open in new tab
        window.open(url, '_blank');
    }

    // Escoba Calculation Logic
    // Exposed globally for testing
    window.calculateEscoba = function (isAuto = false) {
        const todayStr = new Date().toISOString().split('T')[0];

        // Check if already calculated today (for auto mode)
        if (isAuto && localStorage.getItem('lastEscobaCalculation') === todayStr) {
            return;
        }

        const winner = getNextDriver([]);

        if (!winner) {
            if (!isAuto) alert('No hay conductores disponibles (Todos están de baja, vacaciones o es su día libre).');
            return;
        }

        // Reset Session
        currentSessionAssigned = [winner.name];
        reinforcementsListEl.innerHTML = ''; // Clear reinforcements

        // Update UI
        currentEscobaEl.innerText = winner.name;

        // Update Data (Mock)
        window.driversData.forEach(d => d.isBroom = false);
        const winnerIndex = window.driversData.findIndex(d => d.name === winner.name);
        window.driversData[winnerIndex].isBroom = true;

        renderDrivers();

        // Save calculation date
        localStorage.setItem('lastEscobaCalculation', todayStr);

        // WhatsApp / Notification
        if (winner.phone) {
            if (isAuto) {
                console.log(`Auto-assigned: ${winner.name}. Showing notification.`);
                const notification = document.createElement('div');
                notification.id = 'autoCalcNotification'; // ID for testing
                notification.style.cssText = 'position:fixed;top:20px;right:20px;background:#25D366;color:white;padding:15px;border-radius:5px;z-index:1000;box-shadow:0 2px 5px rgba(0,0,0,0.2);cursor:pointer;';
                notification.innerHTML = `🧹 Escoba asignada a <strong>${winner.name}</strong><br><small>Click para enviar WhatsApp</small>`;
                notification.onclick = () => window.sendWhatsApp(winner.name, winner.phone);
                document.body.appendChild(notification);
            } else {
                window.sendWhatsApp(winner.name, winner.phone);
            }
        } else {
            if (!isAuto) alert(`Se ha asignado la escoba a ${winner.name}.\n(Este conductor no tiene teléfono registrado)`);
        }
    }

    calcBtn.addEventListener('click', () => window.calculateEscoba(false));

    // Auto-Calculation Check (Every minute)
    // Exposed globally for testing
    window.checkAutoCalculation = function () {
        const now = new Date();
        // Check if it's past 3:00 AM
        if (now.getHours() >= 3) {
            const todayStr = now.toISOString().split('T')[0];
            const lastCalc = localStorage.getItem('lastEscobaCalculation');

            if (lastCalc !== todayStr) {
                console.log('Running auto-calculation for 3 AM...');
                window.calculateEscoba(true);
            }
        }
    }

    // Run check on load and every 60 seconds
    window.checkAutoCalculation();
    setInterval(window.checkAutoCalculation, 60000);

    // Add Reinforcement Logic
    addReinforcementBtn.addEventListener('click', () => {
        // Ensure main escoba is assigned first
        if (currentSessionAssigned.length === 0) {
            alert('Primero debes calcular la Escoba del Día.');
            return;
        }

        const reinforcement = getNextDriver(currentSessionAssigned);

        if (!reinforcement) {
            alert('No hay más conductores disponibles para refuerzo.');
            return;
        }

        // Add to session
        currentSessionAssigned.push(reinforcement.name);

        // Update UI
        const reinforcementEl = document.createElement('div');
        reinforcementEl.className = 'reinforcement-item';
        reinforcementEl.innerHTML = `<span class="reinforcement-tag">REFUERZO</span> ${reinforcement.name}`;
        reinforcementsListEl.appendChild(reinforcementEl);

        // WhatsApp
        window.sendWhatsApp(reinforcement.name, reinforcement.phone, true);
    });

    // Edit/Add Driver Logic
    const editModal = document.getElementById('editDriverModal');
    const closeModal = document.querySelector('.close-modal');
    const editForm = document.getElementById('editDriverForm');
    let isEditing = false;
    let editingOriginalName = '';

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            editModal.classList.add('hidden');
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === editModal) {
            editModal.classList.add('hidden');
        }
    });

    // Open Modal for New Driver
    addDriverBtn.addEventListener('click', () => {
        isEditing = false;
        editingOriginalName = '';

        document.getElementById('modalTitle').innerText = 'Nuevo Conductor';
        document.getElementById('editName').value = '';
        document.getElementById('editPhone').value = '';
        document.getElementById('editLastSeen').value = '';
        document.getElementById('editStatus').value = 'Activo';
        document.querySelectorAll('input[name="editDay"]').forEach(cb => cb.checked = false);

        editModal.classList.remove('hidden');
    });

    // Open Modal for Edit
    window.openEditModal = function (driverName) {
        const driver = window.driversData.find(d => d.name === driverName);
        if (!driver) return;

        isEditing = true;
        editingOriginalName = driver.name;

        document.getElementById('modalTitle').innerText = 'Editar Conductor';
        document.getElementById('editDriverOriginalName').value = driver.name;
        document.getElementById('editName').value = driver.name;
        document.getElementById('editPhone').value = driver.phone || '';
        document.getElementById('editLastSeen').value = driver.lastSeen === 'NUNCA' ? '' : driver.lastSeen;
        document.getElementById('editStatus').value = driver.status;

        document.querySelectorAll('input[name="editDay"]').forEach(cb => cb.checked = false);
        driver.daysOff.forEach(day => {
            const cb = document.querySelector(`input[name="editDay"][value="${day}"]`);
            if (cb) cb.checked = true;
        });

        editModal.classList.remove('hidden');
    };

    // Delete Driver
    window.deleteDriver = function (driverName) {
        if (confirm(`¿Estás seguro de que quieres eliminar a ${driverName}?`)) {
            window.driversData = window.driversData.filter(d => d.name !== driverName);
            renderDrivers();
        }
    };

    if (editForm) {
        editForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const newName = document.getElementById('editName').value.toUpperCase();
            const newPhone = document.getElementById('editPhone').value;
            const newLastSeen = document.getElementById('editLastSeen').value || 'NUNCA';
            const newStatus = document.getElementById('editStatus').value;
            const newDaysOff = Array.from(document.querySelectorAll('input[name="editDay"]:checked')).map(cb => cb.value);

            // Map status to type for styling
            const typeMap = {
                'Activo': 'active',
                'Vacaciones': 'vacaciones',
                'Baja': 'baja',
                'Asuntos': 'asuntos'
            };
            const newType = typeMap[newStatus] || 'inactive';

            if (isEditing) {
                const driverIndex = window.driversData.findIndex(d => d.name === editingOriginalName);
                if (driverIndex !== -1) {
                    window.driversData[driverIndex].name = newName;
                    window.driversData[driverIndex].phone = newPhone;
                    window.driversData[driverIndex].lastSeen = newLastSeen;
                    window.driversData[driverIndex].daysOff = newDaysOff;
                    window.driversData[driverIndex].status = newStatus;
                    window.driversData[driverIndex].type = newType;
                }
            } else {
                // Add New Driver
                window.driversData.push({
                    name: newName,
                    lastSeen: newLastSeen,
                    status: newStatus,
                    type: newType,
                    registrationDate: new Date().toISOString().split('T')[0],
                    daysOff: newDaysOff,
                    phone: newPhone
                });
            }

            editModal.classList.add('hidden');
            renderDrivers();
        });
    }

    function renderDrivers() {
        const grid = document.getElementById('driversGrid');
        grid.innerHTML = window.driversData.map(driver => `
            <div class="driver-card" style="${driver.isBroom ? 'border: 2px solid #28a745; background: #f0fff4;' : ''}">
                <div class="driver-info">
                    <h3>${driver.name}</h3>
                    <p>Última vez: ${driver.lastSeen}</p>
                    <p style="font-size: 0.8em; color: #666;">${driver.daysOff.join(', ') || 'Sin días libres'}</p>
                    ${driver.phone ? `<p style="font-size: 0.8em; color: #007bff;">📱 ${driver.phone}</p>` : ''}
                </div>
                <div class="driver-status">
                    <span class="status-badge status-${driver.type}">${driver.status}</span>
                    ${driver.isBroom ? '<span class="icon-broom">🧹</span>' : ''}
                    <div class="card-actions">
                        <button class="btn-icon" onclick="openEditModal('${driver.name}')" title="Editar">📅</button>
                        <button class="btn-icon-delete" onclick="deleteDriver('${driver.name}')" title="Eliminar">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Input animations removed as per user request
});
