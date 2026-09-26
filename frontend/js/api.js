/**
 * PBRMS Frontend API & Utility Module
 */

const API_BASE = '/api';

// Auth Token Storage
const Storage = {
    getToken: () => localStorage.getItem('pbrms_token'),
    setToken: (token) => localStorage.setItem('pbrms_token', token),
    removeToken: () => localStorage.removeItem('pbrms_token'),
    getUser: () => {
        try {
            return JSON.parse(localStorage.getItem('pbrms_user'));
        } catch {
            return null;
        }
    },
    setUser: (user) => localStorage.setItem('pbrms_user', JSON.stringify(user)),
    removeUser: () => localStorage.removeItem('pbrms_user'),
    clear: () => {
        localStorage.removeItem('pbrms_token');
        localStorage.removeItem('pbrms_user');
    }
};

// Centralized Fetch Client
const api = {
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = Storage.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            let data = null;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                // If unauthorized on protected routes, redirect to login
                if (response.status === 401 && !window.location.pathname.includes('login.html')) {
                    Storage.clear();
                    window.location.href = '/login.html';
                }
                const errorMsg = data && data.error ? data.error : (data && data.message ? data.message : `HTTP Error ${response.status}`);
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// UI Helper Functions
function showAlert(containerId, message, type = 'danger') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
}

function clearAlert(containerId) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = '';
}

function formatCurrency(amount) {
    const num = parseFloat(amount || 0);
    return `$${num.toFixed(2)}`;
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

function getStatusBadge(status) {
    const s = (status || '').toLowerCase();
    if (s === 'available') {
        return `<span class="badge badge-available"><i class="bi bi-check-circle me-1"></i>Available</span>`;
    } else if (s === 'rented') {
        return `<span class="badge badge-rented"><i class="bi bi-bicycle me-1"></i>Rented</span>`;
    } else if (s === 'maintenance') {
        return `<span class="badge badge-maintenance"><i class="bi bi-wrench me-1"></i>Maintenance</span>`;
    } else if (s === 'inactive') {
        return `<span class="badge badge-inactive"><i class="bi bi-dash-circle me-1"></i>Inactive</span>`;
    } else if (s === 'active') {
        return `<span class="badge bg-primary">Active</span>`;
    } else if (s === 'completed') {
        return `<span class="badge bg-success">Completed</span>`;
    } else if (s === 'paid') {
        return `<span class="badge badge-paid">Paid</span>`;
    } else if (s === 'pending') {
        return `<span class="badge badge-pending">Pending</span>`;
    } else if (s === 'rejected' || s === 'failed') {
        return `<span class="badge badge-failed">${status}</span>`;
    } else {
        return `<span class="badge bg-secondary">${status}</span>`;
    }
}

function checkAuth(requiredRoles = []) {
    const token = Storage.getToken();
    const user = Storage.getUser();

    if (!token || !user) {
        window.location.href = '/login.html';
        return false;
    }

    if (requiredRoles.length > 0 && !requiredRoles.includes(user.role)) {
        alert('Access denied: Unauthorized role.');
        // Redirect to appropriate dashboard
        if (user.role === 'admin') window.location.href = '/admin/dashboard.html';
        else if (user.role === 'rental_owner') window.location.href = '/owner/dashboard.html';
        else window.location.href = '/user/dashboard.html';
        return false;
    }

    return true;
}

function logout() {
    Storage.clear();
    window.location.href = '/login.html';
}

