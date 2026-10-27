import sys
sys.path.insert(0, ".")
from app.monitor import evaluate_status, health_score

def test_status():
    assert evaluate_status(30, 40, 50) == "HEALTHY"
    assert evaluate_status(81, 40, 50) == "WARNING"
    assert evaluate_status(91, 40, 50) == "CRITICAL"

def test_score():
    assert 0 <= health_score(20,20,20) <= 100
