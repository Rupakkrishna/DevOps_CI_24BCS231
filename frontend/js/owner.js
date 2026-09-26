/**
 * PBRMS Rental Owner Dashboard Logic
 */

let allStations = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!checkAuth(['rental_owner'])) return;

    const user = Storage.getUser();
    document.getElementById('ownerNameDisplay').innerText = user.name || 'Rental Owner';

    await loadStations();
    await loadOwnerBicycles();
    await loadOwnerRentals();
});

// --- LOAD STATIONS ---
async function loadStations() {
    try {
        allStations = await api.get('/stations');
        const sel = document.getElementById('bikeStationSelect');
        if (!sel) return;
        sel.innerHTML = '<option value="">None / Storage</option>';
        allStations.forEach(s => {
            sel.innerHTML += `<option value="${s.station_id}">${s.station_name} (${s.available_bicycles}/${s.capacity})</option>`;
        });
    } catch (err) {
        console.error('Failed to load stations:', err);
    }
}

// --- LOAD OWNER BICYCLES ---
async function loadOwnerBicycles() {
    const tableBody = document.getElementById('bicyclesTableBody');
    const user = Storage.getUser();

    try {
        const bikes = await api.get(`/bicycles?owner_id=${user.user_id}`);
        
        let total = bikes.length;
        let available = 0;
        let rented = 0;
        let maintenance = 0;

        bikes.forEach(b => {
            if (b.status === 'Available') available++;
            else if (b.status === 'Rented') rented++;
            else if (b.status === 'Maintenance') maintenance++;
        });

        document.getElementById('statTotalOwned').innerText = total;
        document.getElementById('statAvailable').innerText = available;
        document.getElementById('statRented').innerText = rented;
        document.getElementById('statMaintenance').innerText = maintenance;

        if (!bikes || bikes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">You have not registered any bicycles yet. Click "Add Bicycle" to start!</td></tr>';
            return;
        }

        tableBody.innerHTML = bikes.map(b => `
            <tr>
                <td><strong>${b.bicycle_number}</strong></td>
                <td><span class="badge bg-light text-dark border">${b.type}</span></td>
                <td>${getStatusBadge(b.status)}</td>
                <td>${formatCurrency(b.rental_rate)}/hr</td>
                <td>${b.station_name || '<em class="text-muted">None (In Transit / Storage)</em>'}</td>
                <td><small class="text-muted">${formatDateTime(b.created_at)}</small></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditBikeModal(${b.bicycle_id}, '${b.type}', ${b.rental_rate}, '${b.status}', ${b.station_id || 'null'})">
                        <i class="bi bi-pencil me-1"></i> Edit / Assign
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteBike(${b.bicycle_id})" ${b.status === 'Rented' ? 'disabled title="Cannot delete rented bike"' : ''}>
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load owner bicycles:', err);
    }
}

// --- ADD / EDIT BICYCLE ---
function openAddBikeModal() {
    document.getElementById('bikeModalTitle').innerText = 'Register New Bicycle';
    document.getElementById('bikeIdInput').value = '';
    document.getElementById('bikeNumberInput').value = '';
    document.getElementById('bikeNumberInput').disabled = false;
    document.getElementById('bikeTypeSelect').value = 'City';
    document.getElementById('bikeRateInput').value = '5.00';
    document.getElementById('bikeStatusSelect').value = 'Available';
    document.getElementById('bikeStationSelect').value = '';
    clearAlert('bikeAlertContainer');

    new bootstrap.Modal(document.getElementById('bikeModal')).show();
}

function openEditBikeModal(id, type, rate, status, stationId) {
    document.getElementById('bikeModalTitle').innerText = 'Update Bicycle & Station Assignment';
    document.getElementById('bikeIdInput').value = id;
    document.getElementById('bikeNumberInput').value = 'Locked';
    document.getElementById('bikeNumberInput').disabled = true;
    document.getElementById('bikeTypeSelect').value = type;
    document.getElementById('bikeRateInput').value = rate;
    document.getElementById('bikeStatusSelect').value = status;
    document.getElementById('bikeStationSelect').value = stationId ? stationId : '';
    clearAlert('bikeAlertContainer');

    new bootstrap.Modal(document.getElementById('bikeModal')).show();
}

async function saveBicycle() {
    const id = document.getElementById('bikeIdInput').value;
    const type = document.getElementById('bikeTypeSelect').value;
    const rate = document.getElementById('bikeRateInput').value;
    const status = document.getElementById('bikeStatusSelect').value;
    const stationId = document.getElementById('bikeStationSelect').value;
    const btn = document.getElementById('saveBikeBtn');

    try {
        btn.disabled = true;
        if (id) {
            await api.put(`/bicycles/${id}`, {
                type,
                rental_rate: parseFloat(rate),
                status,
                station_id: stationId ? parseInt(stationId) : null
            });
        } else {
            const bikeNumber = document.getElementById('bikeNumberInput').value.trim();
            if (!bikeNumber) {
                showAlert('bikeAlertContainer', 'Bicycle Number is required.');
                btn.disabled = false;
                return;
            }
            await api.post('/bicycles', {
                bicycle_number: bikeNumber,
                type,
                rental_rate: parseFloat(rate),
                status,
                station_id: stationId ? parseInt(stationId) : null
            });
        }

        bootstrap.Modal.getInstance(document.getElementById('bikeModal')).hide();
        await loadStations();
        await loadOwnerBicycles();
    } catch (err) {
        showAlert('bikeAlertContainer', err.message || 'Failed to save bicycle.');
    } finally {
        btn.disabled = false;
    }
}

async function deleteBike(id) {
    if (!confirm('Are you sure you want to delete this bicycle?')) return;

    try {
        await api.delete(`/bicycles/${id}`);
        await loadStations();
        await loadOwnerBicycles();
    } catch (err) {
        alert(err.message || 'Failed to delete bicycle.');
    }
}

// --- RENTAL ACTIVITY FOR OWNED BICYCLES ---
async function loadOwnerRentals() {
    const tableBody = document.getElementById('rentalsTableBody');
    try {
        const rentals = await api.get('/rentals');
        if (!rentals || rentals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No rental history for your bicycles yet.</td></tr>';
            return;
        }

        let totalEarnings = 0;
        tableBody.innerHTML = rentals.map(r => {
            if (r.fare && r.status === 'Completed') totalEarnings += parseFloat(r.fare);
            return `
                <tr>
                    <td>#${r.rental_id}</td>
                    <td><strong>${r.bicycle_number}</strong> <span class="badge bg-light text-dark">${r.bicycle_type}</span></td>
                    <td>${r.user_name}</td>
                    <td>${formatDateTime(r.start_time)}</td>
                    <td>${r.duration ? `${r.duration} hrs` : '-'}</td>
                    <td><strong>${r.fare ? formatCurrency(r.fare) : '-'}</strong></td>
                    <td>${getStatusBadge(r.status)}</td>
                    <td>${getStatusBadge(r.payment_status || 'Paid')}</td>
                </tr>
            `;
        }).join('');

        document.getElementById('statTotalEarnings').innerText = formatCurrency(totalEarnings);
    } catch (err) {
        console.error('Failed to load owner rentals:', err);
    }
}

