import pytest
import json
from app import app, db_manager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_nl_query_endpoint(client):
    """Test natural language query endpoint"""
    response = client.post('/api/query', 
                         json={'query': 'Show top 3 customers by revenue'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sql_query' in data
    assert 'results' in data

def test_kpis_endpoint(client):
    """Test KPI endpoint"""
    response = client.get('/api/kpis')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_revenue' in data
    assert 'total_orders' in data

def test_chart_endpoint(client):
    """Test chart data endpoint"""
    response = client.get('/api/chart/sales_trend')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)