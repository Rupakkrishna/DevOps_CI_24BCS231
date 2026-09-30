from datetime import datetime, timedelta
from backend.services.rental_service import calculate_fare

def test_fare_calculation():
    """Test 8: Backend fare calculation (Duration × Hourly Rate)."""
    rate = 10.00  # $10/hour

    # Case 1: Ride under 1 hour (e.g. 30 minutes) -> Minimum 1 hour billed
    start = datetime(2026, 9, 21, 10, 0, 0)
    end_30m = datetime(2026, 9, 21, 10, 30, 0)
    duration, fare = calculate_fare(start, end_30m, rate)
    assert duration == 1.0
    assert fare == 10.00

    # Case 2: Exactly 2 hours
    end_2h = datetime(2026, 9, 21, 12, 0, 0)
    duration2, fare2 = calculate_fare(start, end_2h, rate)
    assert duration2 == 2.0
    assert fare2 == 20.00

    # Case 3: 2 hours and 30 minutes (2.5 hours)
    end_2_5h = datetime(2026, 9, 21, 12, 30, 0)
    duration3, fare3 = calculate_fare(start, end_2_5h, rate)
    assert duration3 == 2.5
    assert fare3 == 25.00

    # Case 4: 1 hour and 15 minutes (1.25 hours) with $7.50 rate
    end_1_25h = datetime(2026, 9, 21, 11, 15, 0)
    duration4, fare4 = calculate_fare(start, end_1_25h, 7.50)
    assert duration4 == 1.25
    assert fare4 == round(1.25 * 7.50, 2)  # 9.38

def test_fare_zero_duration():
    """Test zero-duration fare calculation."""
    start = datetime(2026, 9, 21, 10, 0, 0)
    duration, fare = calculate_fare(start, start, 10.00)

    assert duration == 1.0
    assert fare == 10.00

