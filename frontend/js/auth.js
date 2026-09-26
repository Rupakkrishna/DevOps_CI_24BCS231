/**
 * PBRMS Authentication Handlers
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- LOGIN FORM ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearAlert('alertContainer');

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const submitBtn = document.getElementById('loginSubmitBtn');

            if (!email || !password) {
                showAlert('alertContainer', 'Please fill in both email and password.');
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Signing In...';

                const response = await api.post('/auth/login', { email, password });
                Storage.setToken(response.token);
                Storage.setUser(response);

                // Redirect based on role
                if (response.role === 'admin') {
                    window.location.href = '/admin/dashboard.html';
                } else if (response.role === 'rental_owner') {
                    window.location.href = '/owner/dashboard.html';
                } else {
                    window.location.href = '/user/dashboard.html';
                }
            } catch (err) {
                showAlert('alertContainer', err.message || 'Login failed. Please verify your credentials.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Sign In';
            }
        });
    }

    // --- REGISTRATION FORM (CUSTOMER) ---
    const userRegisterForm = document.getElementById('userRegisterForm');
    if (userRegisterForm) {
        userRegisterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearAlert('userAlertContainer');

            const name = document.getElementById('userName').value.trim();
            const email = document.getElementById('userEmail').value.trim();
            const phone = document.getElementById('userPhone').value.trim();
            const password = document.getElementById('userPassword').value;
            const submitBtn = document.getElementById('userRegisterBtn');

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating Account...';

                const response = await api.post('/auth/register', {
                    name, email, phone, password, role: 'user'
                });

                Storage.setToken(response.token);
                Storage.setUser(response);
                showAlert('userAlertContainer', 'Registration successful! Redirecting to dashboard...', 'success');
                setTimeout(() => {
                    window.location.href = '/user/dashboard.html';
                }, 1000);
            } catch (err) {
                showAlert('userAlertContainer', err.message || 'Registration failed.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Register as Customer';
            }
        });
    }

    // --- REGISTRATION FORM (RENTAL OWNER) ---
    const ownerRegisterForm = document.getElementById('ownerRegisterForm');
    if (ownerRegisterForm) {
        ownerRegisterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearAlert('ownerAlertContainer');

            const name = document.getElementById('ownerName').value.trim();
            const email = document.getElementById('ownerEmail').value.trim();
            const phone = document.getElementById('ownerPhone').value.trim();
            const address = document.getElementById('ownerAddress').value.trim();
            const password = document.getElementById('ownerPassword').value;
            const submitBtn = document.getElementById('ownerRegisterBtn');

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting Registration...';

                const response = await api.post('/auth/register', {
                    name, email, phone, address, password, role: 'rental_owner'
                });

                showAlert('ownerAlertContainer', response.message || 'Registration submitted! Your account requires administrator approval before login.', 'success');
                ownerRegisterForm.reset();
            } catch (err) {
                showAlert('ownerAlertContainer', err.message || 'Owner registration failed.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Register as Rental Owner';
            }
        });
    }
});

// Demo Login Quick-Fill Helper
function fillDemoLogin(role) {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    if (!emailInput || !passwordInput) return;

    if (role === 'admin') {
        emailInput.value = 'admin@pbrms.com';
        passwordInput.value = 'Admin@123';
    } else if (role === 'user') {
        emailInput.value = 'alice@example.com';
        passwordInput.value = 'User@123';
    } else if (role === 'owner') {
        emailInput.value = 'john.bikes@example.com';
        passwordInput.value = 'Owner@123';
    }
}

