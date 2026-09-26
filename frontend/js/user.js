/**
 * PBRMS Customer / User Dashboard Logic
 */

let activeRentalTimer = null;
let currentActiveRental = null;
let allStations = [];

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Enforce auth for 'user' role
    if (!checkAuth(['user'])) return;

    const user = Storage.getUser();
    document.getElementById('userNameDisplay').innerText = user.name || 'Customer';

    // 2. Load initial data
    await loadStations();
    await checkActiveRental();
    await loadAvailableBicycles();
    await loadRentalHistory();

    // 3. Setup event listeners
    document.getElementById('stationFilter').addEventListener('change', () => loadAvailableBicycles());
    document.getElementById('typeFilter').addEventListener('change', () => loadAvailableBicycles());
});

// --- LOAD STATIONS ---
async function loadStations() {
    try {
        allStations = await api.get('/stations');
        const stationFilter = document.getElementById('stationFilter');
        const returnStationSelect = document.getElementById('returnStationSelect');

        stationFilter.innerHTML = '<option value="">All Stations</option>';
        returnStationSelect.innerHTML = '<option value="" disabled selected>Select return station...</option>';

        allStations.forEach(s => {
            // Filter dropdown
            stationFilter.innerHTML += `<option value="${s.station_id}">${s.station_name} (${s.available_bicycles} available)</option>`;
            
            // Return dropdown
            const spaceLeft = s.capacity - s.available_bicycles;
            const isFull = spaceLeft <= 0;
            returnStationSelect.innerHTML += `
                <option value="${s.station_id}" ${isFull ? 'disabled' : ''}>
                    ${s.station_name} — [${s.available_bicycles}/${s.capacity} docked, ${spaceLeft} slots free] ${isFull ? '(FULL)' : ''}
                </option>
            `;
        });
    } catch (err) {
        console.error('Failed to load stations:', err);
    }
}

// --- ACTIVE RENTAL WIDGET & LIVE TIMER ---
async function checkActiveRental() {
    try {
        const res = await api.get('/rentals/active');
        const container = document.getElementById('activeRentalContainer');

        if (res && res.rental) {
            currentActiveRental = res.rental;
            renderActiveRentalBanner(res.rental);
            startRentalTimer(res.rental.start_time, res.rental.rental_rate);
        } else {
            currentActiveRental = null;
            if (activeRentalTimer) clearInterval(activeRentalTimer);
            container.innerHTML = '';
        }
    } catch (err) {
        console.error('Failed to check active rental:', err);
    }
}

function renderActiveRentalBanner(rental) {
    const container = document.getElementById('activeRentalContainer');
    container.innerHTML = `
        <div class="active-rental-banner">
            <div class="row align-items-center">
                <div class="col-lg-6 mb-3 mb-lg-0">
                    <span class="badge bg-warning text-dark px-3 py-1 mb-2 fw-semibold">
                        <i class="bi bi-clock-history me-1"></i> ACTIVE RENTAL IN PROGRESS
                    </span>
                    <h3 class="fw-bold text-white mb-1">
                        Bicycle: ${rental.bicycle_number} <span class="badge bg-light text-dark fs-6">${rental.bicycle_type}</span>
                    </h3>
                    <p class="text-light opacity-90 mb-0">
                        <i class="bi bi-geo-alt me-1"></i> Departed from: <strong>${rental.start_station_name || 'Station'}</strong>
                        <span class="ms-3"><i class="bi bi-tag me-1"></i> Rate: <strong>${formatCurrency(rental.rental_rate)}/hr</strong></span>
                    </p>
                </div>
                <div class="col-lg-4 text-center text-lg-start mb-3 mb-lg-0">
                    <small class="text-uppercase text-light opacity-75 fw-semibold d-block">Elapsed Duration</small>
                    <div class="rental-timer text-warning" id="liveTimerDisplay">00:00:00</div>
                    <small class="text-light opacity-90">Estimated Fare: <strong id="liveFareDisplay">${formatCurrency(rental.rental_rate)}</strong> (min 1 hr)</small>
                </div>
                <div class="col-lg-2 text-lg-end text-center">
                    <button class="btn btn-light btn-lg text-danger fw-bold shadow-sm" onclick="openReturnModal()">
                        <i class="bi bi-box-arrow-down-left me-1"></i> Return Bike
                    </button>
                </div>
            </div>
        </div>
    `;
}

function startRentalTimer(startTimeStr, hourlyRate) {
    if (activeRentalTimer) clearInterval(activeRentalTimer);

    const startTime = new Date(startTimeStr).getTime();

    function update() {
        const now = new Date().getTime();
        const diffSeconds = Math.max(0, Math.floor((now - startTime) / 1000));

        const hours = Math.floor(diffSeconds / 3600);
        const minutes = Math.floor((diffSeconds % 3600) / 60);
        const seconds = diffSeconds % 60;

        const pad = (n) => n.toString().padStart(2, '0');
        const timerEl = document.getElementById('liveTimerDisplay');
        if (timerEl) {
            timerEl.innerText = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
        }

        // Live estimated fare (min 1 hr)
        const billableHours = Math.max(1.0, diffSeconds / 3600.0);
        const estimatedFare = billableHours * parseFloat(hourlyRate);
        const fareEl = document.getElementById('liveFareDisplay');
        if (fareEl) {
            fareEl.innerText = formatCurrency(estimatedFare);
        }
    }

    update();
    activeRentalTimer = setInterval(update, 1000);
}

// --- AVAILABLE BICYCLES ---
async function loadAvailableBicycles() {
    const stationId = document.getElementById('stationFilter').value;
    const type = document.getElementById('typeFilter').value;
    const container = document.getElementById('bicyclesList');

    try {
        let url = '/bicycles/available?';
        if (stationId) url += `station_id=${stationId}&`;
        if (type) url += `type=${type}&`;

        const bikes = await api.get(url);

        if (!bikes || bikes.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-bicycle fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No available bicycles match your selection.</p>
                </div>
            `;
            return;
        }

        const hasActive = currentActiveRental !== null;

        container.innerHTML = bikes.map(b => `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm stat-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title fw-bold mb-0">${b.bicycle_number}</h5>
                            <span class="badge bg-light text-primary border border-primary-subtle fw-semibold">
                                ${b.type}
                            </span>
                        </div>
                        <p class="text-muted small mb-2">
                            <i class="bi bi-geo-alt me-1"></i> ${b.station_name}
                        </p>
                        <p class="text-muted small mb-3">
                            <i class="bi bi-person me-1"></i> Owner: ${b.owner_name}
                        </p>
                        <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                            <div>
                                <span class="fs-4 fw-bold text-primary">${formatCurrency(b.rental_rate)}</span>
                                <small class="text-muted">/ hour</small>
                            </div>
                            <button class="btn btn-primary btn-sm px-3" 
                                    onclick="openRentModal(${b.bicycle_id}, '${b.bicycle_number}', '${b.type}', ${b.rental_rate}, '${b.station_name}')"
                                    ${hasActive ? 'disabled title="Return current active rental first"' : ''}>
                                <i class="bi bi-bicycle me-1"></i> Rent Now
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading available bikes:', err);
    }
}

// --- RENT CONFIRMATION MODAL ---
let selectedBikeForRent = null;

function openRentModal(bikeId, bikeNumber, bikeType, rate, stationName) {
    if (currentActiveRental) {
        alert('You already have an active rental in progress. Please return it first.');
        return;
    }

    selectedBikeForRent = bikeId;
    document.getElementById('modalBikeNumber').innerText = bikeNumber;
    document.getElementById('modalBikeType').innerText = bikeType;
    document.getElementById('modalStationName').innerText = stationName;
    document.getElementById('modalRentalRate').innerText = `${formatCurrency(rate)} / hour`;
    document.getElementById('rentAlertContainer').innerHTML = '';

    const modal = new bootstrap.Modal(document.getElementById('rentConfirmModal'));
    modal.show();
}

async function confirmRent() {
    if (!selectedBikeForRent) return;
    const btn = document.getElementById('confirmRentBtn');

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Confirming...';

        await api.post('/rentals', { bicycle_id: selectedBikeForRent });

        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('rentConfirmModal')).hide();

        // Refresh UI
        await checkActiveRental();
        await loadStations();
        await loadAvailableBicycles();
        await loadRentalHistory();
    } catch (err) {
        showAlert('rentAlertContainer', err.message || 'Rental failed.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Confirm Rental';
    }
}

// --- RETURN MODAL ---
function openReturnModal() {
    if (!currentActiveRental) return;

    document.getElementById('returnBikeNumber').innerText = currentActiveRental.bicycle_number;
    document.getElementById('returnDepartedStation').innerText = currentActiveRental.start_station_name || 'Station';
    document.getElementById('returnAlertContainer').innerHTML = '';
    document.getElementById('returnStationSelect').selectedIndex = 0;

    const modal = new bootstrap.Modal(document.getElementById('returnModal'));
    modal.show();
}

async function confirmReturn() {
    if (!currentActiveRental) return;

    const stationSelect = document.getElementById('returnStationSelect');
    const returnStationId = stationSelect.value;
    const btn = document.getElementById('confirmReturnBtn');

    if (!returnStationId) {
        showAlert('returnAlertContainer', 'Please select a destination docking station.');
        return;
    }

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing Return & Payment...';

        const result = await api.post(`/rentals/${currentActiveRental.rental_id}/return`, {
            return_station_id: parseInt(returnStationId)
        });

        // Close return modal
        bootstrap.Modal.getInstance(document.getElementById('returnModal')).hide();

        // Show Fare Receipt Modal
        showReceiptModal(result);

        // Refresh state
        await checkActiveRental();
        await loadStations();
        await loadAvailableBicycles();
        await loadRentalHistory();
    } catch (err) {
        showAlert('returnAlertContainer', err.message || 'Return failed.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Confirm Return & Complete Payment';
    }
}

function showReceiptModal(rental) {
    document.getElementById('receiptBikeNumber').innerText = rental.bicycle_number;
    document.getElementById('receiptDuration').innerText = `${rental.duration} hours`;
    document.getElementById('receiptRate').innerText = `${formatCurrency(rental.rental_rate)}/hr`;
    document.getElementById('receiptFare').innerText = formatCurrency(rental.fare);
    document.getElementById('receiptPaymentStatus').innerHTML = getStatusBadge(rental.payment_status || 'Paid');

    const modal = new bootstrap.Modal(document.getElementById('receiptModal'));
    modal.show();
}

// --- RENTAL HISTORY ---
async function loadRentalHistory() {
    const tableBody = document.getElementById('rentalHistoryTableBody');
    try {
        const rentals = await api.get('/rentals');
        if (!rentals || rentals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No rental history found.</td></tr>';
            return;
        }

        tableBody.innerHTML = rentals.map(r => `
            <tr>
                <td>#${r.rental_id}</td>
                <td><strong>${r.bicycle_number}</strong> <span class="text-muted small">(${r.bicycle_type})</span></td>
                <td>${r.start_station_name || 'N/A'}</td>
                <td>${r.return_station_name || '<span class="badge bg-warning text-dark">Active</span>'}</td>
                <td>${formatDateTime(r.start_time)}</td>
                <td>${r.duration ? `${r.duration} hrs` : '-'}</td>
                <td><strong>${r.fare ? formatCurrency(r.fare) : '-'}</strong></td>
                <td>${getStatusBadge(r.status)}</td>
                <td>${getStatusBadge(r.payment_status || (r.status === 'Active' ? 'Pending' : 'Paid'))}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load rental history:', err);
    }
}

