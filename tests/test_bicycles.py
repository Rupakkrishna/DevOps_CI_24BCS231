import json

def test_bicycle_availability(client):
    """Test 4: Available bicycle search returns ONLY Available bicycles."""
    res = client.get('/api/bicycles/available')
    assert res.status_code == 200
    bikes = res.get_json()

    # In conftest: TEST-101 and TEST-102 are Available; TEST-103 is Maintenance; TEST-104 is Inactive
    bike_numbers = [b['bicycle_number'] for b in bikes]
    assert 'TEST-101' in bike_numbers
    assert 'TEST-102' in bike_numbers
    assert 'TEST-103' not in bike_numbers
    assert 'TEST-104' not in bike_numbers

    for b in bikes:
        assert b['status'] == 'Available'

def test_bicycle_status_transition(client, owner_token):
    """Test 9: Bicycle status transitions (Available -> Maintenance -> Available)."""
    headers = {'Authorization': f'Bearer {owner_token}'}

    # 1. Update TEST-101 to Maintenance
    res = client.put('/api/bicycles/1', json={'status': 'Maintenance'}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()['status'] == 'Maintenance'

    # Verify it disappeared from available list
    res_avail = client.get('/api/bicycles/available')
    nums = [b['bicycle_number'] for b in res_avail.get_json()]
    assert 'TEST-101' not in nums

    # 2. Update TEST-101 back to Available
    res_back = client.put('/api/bicycles/1', json={'status': 'Available'}, headers=headers)
    assert res_back.status_code == 200
    assert res_back.get_json()['status'] == 'Available'

    # Verify it reappeared
    res_avail2 = client.get('/api/bicycles/available')
    nums2 = [b['bicycle_number'] for b in res_avail2.get_json()]
    assert 'TEST-101' in nums2

def test_station_availability_update_and_capacity(client, admin_token):
    """Test 10: Station bicycle count updates and capacity limits are enforced."""
    headers = {'Authorization': f'Bearer {admin_token}'}

    # Station 2 has capacity 2, currently 0 available
    station_res = client.get('/api/stations/2')
    assert station_res.status_code == 200
    assert station_res.get_json()['available_bicycles'] == 0
    assert station_res.get_json()['capacity'] == 2

    # Add a bike to Station 2
    res_add1 = client.post('/api/bicycles', json={
        'bicycle_number': 'NEW-201',
        'type': 'City',
        'rental_rate': 6.0,
        'owner_id': 1,
        'station_id': 2,
        'status': 'Available'
    }, headers=headers)
    assert res_add1.status_code == 201

    # Check station count updated to 1
    s_updated = client.get('/api/stations/2').get_json()
    assert s_updated['available_bicycles'] == 1

    # Add second bike to reach capacity 2
    res_add2 = client.post('/api/bicycles', json={
        'bicycle_number': 'NEW-202',
        'type': 'City',
        'rental_rate': 6.0,
        'owner_id': 1,
        'station_id': 2,
        'status': 'Available'
    }, headers=headers)
    assert res_add2.status_code == 201

    s_updated2 = client.get('/api/stations/2').get_json()
    assert s_updated2['available_bicycles'] == 2

    # Attempt to add a 3rd bike to Station 2 (exceeds capacity 2) -> must be rejected
    res_add3 = client.post('/api/bicycles', json={
        'bicycle_number': 'NEW-203',
        'type': 'City',
        'rental_rate': 6.0,
        'owner_id': 1,
        'station_id': 2,
        'status': 'Available'
    }, headers=headers)
    assert res_add3.status_code == 400
    assert 'capacity' in res_add3.get_json()['error'].lower()

