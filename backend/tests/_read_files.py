"""Temporary helper to dump file contents."""
def test_dump():
    with open("backend/app/visualization/heatmap.py") as f:
        print("=== HEATMAP.PY ===")
        print(f.read())
    with open("backend/app/models/schemas.py") as f:
        print("=== SCHEMAS.PY ===")
        print(f.read())
    with open("backend/app/services/demand_service.py") as f:
        print("=== DEMAND_SERVICE.PY ===")
        print(f.read())
    assert True
