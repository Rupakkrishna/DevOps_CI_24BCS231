import json

def test_bicycle_rental_lifecycle(client, user1_token):
    """Test 5: Bicycle rental updates status to Rented and decrements station count."""
    headers = {'Authorization': f'Bearer {user1_token}'}

    # Station 1 initially has 2 available bikes
    s1_before = client.get('/api/stations/1').get_json()
    assert s1_before['available_bicycles'] == 2

    # User 1 rents TEST-101 (id 1)
    res = client.post('/api/rentals', json={'bicycle_id': 1}, headers=headers)
    assert res.status_code == 201
    rental = res.get_json()
    assert rental['status'] == 'Active'
    assert rental['bicycle_id'] == 1

    # Verify bicycle status changed to Rented
    bike = client.get('/api/bicycles/1').get_json()
    assert bike['status'] == 'Rented'
    assert bike['station_id'] is None

    # Verify station count decremented from 2 to 1
    s1_after = client.get('/api/stations/1').get_json()
    assert s1_after['available_bicycles'] == 1

def test_prevent_double_rental(client, user1_token, user2_token):
    """Test 6: Prevent two users from renting the same bicycle simultaneously."""
    headers1 = {'Authorization': f'Bearer {user1_token}'}
    headers2 = {'Authorization': f'Bearer {user2_token}'}

    # User 1 rents TEST-102 (id 2)
    res1 = client.post('/api/rentals', json={'bicycle_id': 2}, headers=headers1)
    assert res1.status_code == 201

    # User 2 attempts to rent the same bicycle TEST-102
    res2 = client.post('/api/rentals', json={'bicycle_id': 2}, headers=headers2)
    assert res2.status_code == 400
    assert 'not available' in res2.get_json()['error'].lower() or 'already rented' in res2.get_json()['error'].lower()

def test_return_bicycle(client, user1_token):
    """Test 7: Return bicycle, calculate fare, update status, and record payment."""
    headers = {'Authorization': f'Bearer {user1_token}'}

    # Rent TEST-101
    res_rent = client.post('/api/rentals', json={'bicycle_id': 1}, headers=headers)
    rental_id = res_rent.get_json()['rental_id']

    # Station 2 currently has 0 available bikes (capacity 2)
    s2_before = client.get('/api/stations/2').get_json()
    assert s2_before['available_bicycles'] == 0

    # Return bike to Station 2
    res_return = client.post(f'/api/rentals/{rental_id}/return', json={'return_station_id': 2}, headers=headers)
    assert res_return.status_code == 200
    returned = res_return.get_json()

    # Verify rental is Completed
    assert returned['status'] == 'Completed'
    assert returned['return_station_id'] == 2
    assert returned['duration'] is not None
    assert returned['fare'] is not None
    assert returned['payment_status'] == 'Paid'

    # Verify bicycle is Available again at Station 2
    bike = client.get('/api/bicycles/1').get_json()
    assert bike['status'] == 'Available'
    assert bike['station_id'] == 2

    # Verify Station 2 available count incremented to 1
    s2_after = client.get('/api/stations/2').get_json()
    assert s2_after['available_bicycles'] == 1

def test_return_bicycle_capacity_limit(client, user1_token, admin_token):
    """Test station capacity prevention upon return."""
    u_headers = {'Authorization': f'Bearer {user1_token}'}
    a_headers = {'Authorization': f'Bearer {admin_token}'}

    # Station 2 has capacity 2. Add 2 bikes directly to fill it to capacity
    client.post('/api/bicycles', json={
        'bicycle_number': 'FILL-1', 'type': 'City', 'rental_rate': 5.0, 'owner_id': 1, 'station_id': 2, 'status': 'Available'
    }, headers=a_headers)
    client.post('/api/bicycles', json={
        'bicycle_number': 'FILL-2', 'type': 'City', 'rental_rate': 5.0, 'owner_id': 1, 'station_id': 2, 'status': 'Available'
    }, headers=a_headers)

    s2 = client.get('/api/stations/2').get_json()
    assert s2['available_bicycles'] == 2
    assert s2['capacity'] == 2

    # Rent bike TEST-101 from Station 1
    res_rent = client.post('/api/rentals', json={'bicycle_id': 1}, headers=u_headers)
    rental_id = res_rent.get_json()['rental_id']

    # Attempt to return to full Station 2
    res_return = client.post(f'/api/rentals/{rental_id}/return', json={'return_station_id': 2}, headers=u_headers)
    assert res_return.status_code == 400
    assert 'capacity' in res_return.get_json()['error'].lower()

