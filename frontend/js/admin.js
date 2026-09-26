/**
 * PBRMS Admin Dashboard Logic
 */

let allStations = [];
let allOwners = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!checkAuth(['admin'])) return;

    const user = Storage.getUser();
    document.getElementById('adminNameDisplay').innerText = user.name || 'Administrator';

    // Load metrics and tabs data
    await loadMetrics();
    await loadOwners();
    await loadStations();
    await loadBicycles();
    await loadUsers();
    await loadRentals();
    await loadPayments();
});

// --- METRICS ---
async function loadMetrics() {
    try {
        const data = await api.get('/admin/dashboard');

        // Users
        document.getElementById('metricUsers').innerText = data.users.total_customers;
        document.getElementById('metricOwners').innerText = data.users.total_owners;
        document.getElementById('metricPendingOwners').innerText = data.users.pending_owner_approvals;
        if (data.users.pending_owner_approvals > 0) {
            document.getElementById('pendingAlert').classList.remove('d-none');
            document.getElementById('pendingCountText').innerText = data.users.pending_owner_approvals;
        } else {
            document.getElementById('pendingAlert').classList.add('d-none');
        }

        // Bicycles
        document.getElementById('metricTotalBikes').innerText = data.bicycles.total;
        document.getElementById('metricAvailBikes').innerText = data.bicycles.available;
        document.getElementById('metricRentedBikes').innerText = data.bicycles.rented;
        document.getElementById('metricMaintBikes').innerText = data.bicycles.maintenance;

        // Stations & Rentals
        document.getElementById('metricStations').innerText = data.stations.total;
        document.getElementById('metricActiveRentals').innerText = data.rentals.active;
        document.getElementById('metricRevenue').innerText = formatCurrency(data.payments.total_revenue);
    } catch (err) {
        console.error('Failed to load admin metrics:', err);
    }
}

// --- RENTAL OWNERS MANAGEMENT ---
async function loadOwners() {
    const tableBody = document.getElementById('ownersTableBody');
    try {
        allOwners = await api.get('/admin/owners');
        if (!allOwners || allOwners.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No rental owners registered.</td></tr>';
            return;
        }

        tableBody.innerHTML = allOwners.map(o => {
            let actions = '';
            if (o.approval_status === 'Pending') {
                actions = `
                    <button class="btn btn-sm btn-success me-1" onclick="setOwnerStatus(${o.owner_id}, 'Approved')">
                        <i class="bi bi-check-lg"></i> Approve
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="setOwnerStatus(${o.owner_id}, 'Rejected')">
                        <i class="bi bi-x-lg"></i> Reject
                    </button>
                `;
            } else if (o.approval_status === 'Approved') {
                actions = `
                    <button class="btn btn-sm btn-outline-danger" onclick="setOwnerStatus(${o.owner_id}, 'Rejected')">
                        <i class="bi bi-ban"></i> Revoke
                    </button>
                `;
            } else {
                actions = `
                    <button class="btn btn-sm btn-outline-success" onclick="setOwnerStatus(${o.owner_id}, 'Approved')">
                        <i class="bi bi-check-lg"></i> Re-Approve
                    </button>
                `;
            }

            return `
                <tr>
                    <td>#${o.owner_id}</td>
                    <td><strong>${o.name}</strong></td>
                    <td>${o.email}</td>
                    <td>${o.phone || '-'}</td>
                    <td><small class="text-muted">${o.address || '-'}</small></td>
                    <td>${getStatusBadge(o.approval_status)}</td>
                    <td class="text-end">${actions}</td>
                </tr>
            `;
        }).join('');

        // Populate owner dropdown in bike modal
        populateBikeOwnerSelect();
    } catch (err) {
        console.error('Failed to load owners:', err);
    }
}

async function setOwnerStatus(ownerId, status) {
    if (!confirm(`Are you sure you want to set this owner to '${status}'?`)) return;

    try {
        await api.post(`/admin/owners/${ownerId}/status`, { status });
        await loadMetrics();
        await loadOwners();
    } catch (err) {
        alert(err.message || 'Failed to update owner status.');
    }
}

// --- DOCKING STATIONS MANAGEMENT ---
async function loadStations() {
    const tableBody = document.getElementById('stationsTableBody');
    try {
        allStations = await api.get('/stations');
        if (!allStations || allStations.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No stations found.</td></tr>';
            return;
        }

        tableBody.innerHTML = allStations.map(s => `
            <tr>
                <td>#${s.station_id}</td>
                <td><strong>${s.station_name}</strong></td>
                <td><i class="bi bi-geo-alt text-muted me-1"></i>${s.location}</td>
                <td>${s.capacity}</td>
                <td>
                    <span class="badge ${s.available_bicycles > 0 ? 'bg-success' : 'bg-danger'}">
                        ${s.available_bicycles} Available
                    </span>
                </td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditStationModal(${s.station_id}, '${s.station_name}', '${s.location}', ${s.capacity})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteStation(${s.station_id})">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');

        // Update station dropdowns in bike modal
        populateBikeStationSelect();
    } catch (err) {
        console.error('Failed to load stations:', err);
    }
}

function openAddStationModal() {
    document.getElementById('stationModalTitle').innerText = 'Add New Docking Station';
    document.getElementById('stationIdInput').value = '';
    document.getElementById('stationNameInput').value = '';
    document.getElementById('stationLocationInput').value = '';
    document.getElementById('stationCapacityInput').value = '10';
    clearAlert('stationAlertContainer');

    new bootstrap.Modal(document.getElementById('stationModal')).show();
}

function openEditStationModal(id, name, loc, cap) {
    document.getElementById('stationModalTitle').innerText = 'Edit Docking Station';
    document.getElementById('stationIdInput').value = id;
    document.getElementById('stationNameInput').value = name;
    document.getElementById('stationLocationInput').value = loc;
    document.getElementById('stationCapacityInput').value = cap;
    clearAlert('stationAlertContainer');

    new bootstrap.Modal(document.getElementById('stationModal')).show();
}

async function saveStation() {
    const id = document.getElementById('stationIdInput').value;
    const name = document.getElementById('stationNameInput').value.trim();
    const loc = document.getElementById('stationLocationInput').value.trim();
    const cap = document.getElementById('stationCapacityInput').value;
    const btn = document.getElementById('saveStationBtn');

    if (!name || !loc || !cap) {
        showAlert('stationAlertContainer', 'Please fill in all required fields.');
        return;
    }

    try {
        btn.disabled = true;
        if (id) {
            await api.put(`/stations/${id}`, { station_name: name, location: loc, capacity: parseInt(cap) });
        } else {
            await api.post('/stations', { station_name: name, location: loc, capacity: parseInt(cap) });
        }

        bootstrap.Modal.getInstance(document.getElementById('stationModal')).hide();
        await loadMetrics();
        await loadStations();
    } catch (err) {
        showAlert('stationAlertContainer', err.message || 'Failed to save station.');
    } finally {
        btn.disabled = false;
    }
}

async function deleteStation(id) {
    if (!confirm('Are you sure you want to delete this station? Ensure no bicycles are currently docked.')) return;

    try {
        await api.delete(`/stations/${id}`);
        await loadMetrics();
        await loadStations();
    } catch (err) {
        alert(err.message || 'Failed to delete station.');
    }
}

// --- BICYCLES MANAGEMENT ---
async function loadBicycles() {
    const tableBody = document.getElementById('bicyclesTableBody');
    try {
        const bikes = await api.get('/bicycles');
        if (!bikes || bikes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No bicycles registered.</td></tr>';
            return;
        }

        tableBody.innerHTML = bikes.map(b => `
            <tr>
                <td>#${b.bicycle_id}</td>
                <td><strong>${b.bicycle_number}</strong></td>
                <td><span class="badge bg-light text-dark border">${b.type}</span></td>
                <td>${getStatusBadge(b.status)}</td>
                <td>${formatCurrency(b.rental_rate)}/hr</td>
                <td>${b.station_name || '<em class="text-muted">None (In Transit)</em>'}</td>
                <td>${b.owner_name || 'Owner #' + b.owner_id}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditBikeModal(${b.bicycle_id}, '${b.type}', ${b.rental_rate}, '${b.status}', ${b.station_id || 'null'})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteBike(${b.bicycle_id})" ${b.status === 'Rented' ? 'disabled title="Cannot delete rented bike"' : ''}>
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load bicycles:', err);
    }
}

function populateBikeOwnerSelect() {
    const sel = document.getElementById('bikeOwnerSelect');
    if (!sel) return;
    sel.innerHTML = '<option value="" disabled selected>Select Owner...</option>';
    allOwners.filter(o => o.approval_status === 'Approved').forEach(o => {
        sel.innerHTML += `<option value="${o.owner_id}">${o.name} (${o.email})</option>`;
    });
}

function populateBikeStationSelect() {
    const sel = document.getElementById('bikeStationSelect');
    if (!sel) return;
    sel.innerHTML = '<option value="">None / Storage</option>';
    allStations.forEach(s => {
        sel.innerHTML += `<option value="${s.station_id}">${s.station_name} (${s.available_bicycles}/${s.capacity})</option>`;
    });
}

function openAddBikeModal() {
    document.getElementById('bikeModalTitle').innerText = 'Add New Bicycle';
    document.getElementById('bikeIdInput').value = '';
    document.getElementById('bikeNumberInput').value = '';
    document.getElementById('bikeNumberInput').disabled = false;
    document.getElementById('bikeTypeSelect').value = 'City';
    document.getElementById('bikeRateInput').value = '5.00';
    document.getElementById('bikeStatusSelect').value = 'Available';
    document.getElementById('bikeOwnerContainer').classList.remove('d-none');
    clearAlert('bikeAlertContainer');

    populateBikeOwnerSelect();
    populateBikeStationSelect();
    new bootstrap.Modal(document.getElementById('bikeModal')).show();
}

function openEditBikeModal(id, type, rate, status, stationId) {
    document.getElementById('bikeModalTitle').innerText = 'Edit Bicycle';
    document.getElementById('bikeIdInput').value = id;
    document.getElementById('bikeNumberInput').value = 'Locked';
    document.getElementById('bikeNumberInput').disabled = true;
    document.getElementById('bikeTypeSelect').value = type;
    document.getElementById('bikeRateInput').value = rate;
    document.getElementById('bikeStatusSelect').value = status;
    document.getElementById('bikeOwnerContainer').classList.add('d-none');
    clearAlert('bikeAlertContainer');

    populateBikeStationSelect();
    if (stationId) {
        document.getElementById('bikeStationSelect').value = stationId;
    } else {
        document.getElementById('bikeStationSelect').value = '';
    }

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
            const ownerId = document.getElementById('bikeOwnerSelect').value;
            if (!bikeNumber || !ownerId) {
                showAlert('bikeAlertContainer', 'Bicycle Number and Owner are required.');
                btn.disabled = false;
                return;
            }
            await api.post('/bicycles', {
                bicycle_number: bikeNumber,
                type,
                rental_rate: parseFloat(rate),
                owner_id: parseInt(ownerId),
                status,
                station_id: stationId ? parseInt(stationId) : null
            });
        }

        bootstrap.Modal.getInstance(document.getElementById('bikeModal')).hide();
        await loadMetrics();
        await loadBicycles();
        await loadStations();
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
        await loadMetrics();
        await loadBicycles();
        await loadStations();
    } catch (err) {
        alert(err.message || 'Failed to delete bicycle.');
    }
}

// --- CUSTOMERS LIST ---
async function loadUsers() {
    const tableBody = document.getElementById('usersTableBody');
    try {
        const users = await api.get('/admin/users');
        if (!users || users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No registered customers.</td></tr>';
            return;
        }

        tableBody.innerHTML = users.map(u => `
            <tr>
                <td>#${u.user_id}</td>
                <td><strong>${u.name}</strong></td>
                <td>${u.email}</td>
                <td>${u.phone || '-'}</td>
                <td>${formatDateTime(u.created_at)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load users:', err);
    }
}

// --- RENTALS LOG ---
async function loadRentals() {
    const tableBody = document.getElementById('rentalsTableBody');
    try {
        const rentals = await api.get('/rentals');
        if (!rentals || rentals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No rental records found.</td></tr>';
            return;
        }

        tableBody.innerHTML = rentals.map(r => `
            <tr>
                <td>#${r.rental_id}</td>
                <td><strong>${r.user_name}</strong> <small class="text-muted">(${r.user_email})</small></td>
                <td>${r.bicycle_number} <span class="badge bg-light text-dark">${r.bicycle_type}</span></td>
                <td>${r.start_station_name || '-'}</td>
                <td>${r.return_station_name || '<span class="badge bg-warning text-dark">Active</span>'}</td>
                <td>${formatDateTime(r.start_time)}</td>
                <td>${r.duration ? `${r.duration} hrs` : '-'}</td>
                <td><strong>${r.fare ? formatCurrency(r.fare) : '-'}</strong></td>
                <td>${getStatusBadge(r.status)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load rentals:', err);
    }
}

// --- PAYMENTS LEDGER ---
async function loadPayments() {
    const tableBody = document.getElementById('paymentsTableBody');
    try {
        const payments = await api.get('/payments');
        if (!payments || payments.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No payment records found.</td></tr>';
            return;
        }

        tableBody.innerHTML = payments.map(p => `
            <tr>
                <td>#${p.payment_id}</td>
                <td>Rental #${p.rental_id}</td>
                <td>${p.user_name}</td>
                <td><strong>${p.bicycle_number}</strong></td>
                <td><strong class="text-success">${formatCurrency(p.amount)}</strong></td>
                <td>${getStatusBadge(p.status)}</td>
                <td>${formatDateTime(p.payment_date || p.created_at)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load payments:', err);
    }
}

