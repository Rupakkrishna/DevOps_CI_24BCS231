import json

def test_user_registration(client):
    """Test 1: User / Customer registration."""
    payload = {
        'name': 'Charlie Chaplin',
        'email': 'charlie@test.com',
        'phone': '1234567899',
        'password': 'Password@123',
        'role': 'user'
    }
    response = client.post('/api/auth/register', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['email'] == 'charlie@test.com'
    assert data['role'] == 'user'
    assert 'token' in data

    # Test duplicate email rejection
    dup_res = client.post('/api/auth/register', json=payload)
    assert dup_res.status_code == 400
    assert 'already registered' in dup_res.get_json()['error']

def test_rental_owner_registration(client):
    """Test Owner registration requiring approval."""
    payload = {
        'name': 'Speedy Bikes',
        'email': 'speedy@test.com',
        'phone': '9876543210',
        'address': '777 Ocean Ave',
        'password': 'Password@123',
        'role': 'rental_owner'
    }
    response = client.post('/api/auth/register', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['approval_status'] == 'Pending'
    assert 'pending' in data['message'].lower()

def test_login_success(client):
    """Test 2: Successful login for customer, admin, and approved owner."""
    # 1. Customer login
    res = client.post('/api/auth/login', json={'email': 'user1@test.com', 'password': 'User@123'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['role'] == 'user'
    assert 'token' in data

    # 2. Admin login
    res_admin = client.post('/api/auth/login', json={'email': 'admin@test.com', 'password': 'Admin@123'})
    assert res_admin.status_code == 200
    assert res_admin.get_json()['role'] == 'admin'

    # 3. Approved Owner login
    res_owner = client.post('/api/auth/login', json={'email': 'owner1@test.com', 'password': 'Owner@123'})
    assert res_owner.status_code == 200
    assert res_owner.get_json()['role'] == 'rental_owner'

def test_invalid_login(client):
    """Test 3: Invalid login handling."""
    # Wrong password
    res = client.post('/api/auth/login', json={'email': 'user1@test.com', 'password': 'WrongPassword'})
    assert res.status_code == 401
    assert 'Invalid email or password' in res.get_json()['error']

    # Non-existent email
    res_no_user = client.post('/api/auth/login', json={'email': 'ghost@test.com', 'password': 'User@123'})
    assert res_no_user.status_code == 401

    # Pending owner login attempt (must be blocked)
    res_pending = client.post('/api/auth/login', json={'email': 'owner2@test.com', 'password': 'Owner@123'})
    assert res_pending.status_code == 401
    assert 'pending approval' in res_pending.get_json()['error'].lower()

def test_unauthorized_endpoint_access(client, user1_token):
    """Test 11: Unauthorized endpoint access & RBAC enforcement."""
    # 1. Accessing admin endpoint without token -> 401
    res_no_token = client.get('/api/admin/dashboard')
    assert res_no_token.status_code == 401

    # 2. Accessing admin endpoint with normal user token -> 403 Forbidden
    headers = {'Authorization': f'Bearer {user1_token}'}
    res_forbidden = client.get('/api/admin/dashboard', headers=headers)
    assert res_forbidden.status_code == 403
    assert 'Access forbidden' in res_forbidden.get_json()['error']

    # 3. Customer attempting to add station -> 403 Forbidden
    res_post_station = client.post('/api/stations', json={'station_name': 'Hacker Station', 'location': 'Nowhere', 'capacity': 5}, headers=headers)
    assert res_post_station.status_code == 403

