import pytest
from fastapi.testclient import TestClient

def test_simple_component_creation(auth_headers, client, db_session):
    """Minimal test using conftest fixtures"""
    # Create category
    cat_response = client.post(
        "/api/v1/categories",
        json={"name": "Test Cat", "description": "Test"},
        headers=auth_headers
    )
    print(f"\nCategory creation: {cat_response.status_code}")
    
    # Create storage
    storage_response = client.post(
        "/api/v1/storage-locations",
        json={"name": "Test Storage", "type": "drawer"},
        headers=auth_headers
    )
    print(f"Storage creation: {storage_response.status_code}")
    
    assert cat_response.status_code == 201
    assert storage_response.status_code == 201
    
    # Create component
    comp_response = client.post(
        "/api/v1/components",
        json={
            "name": "Test Component",
            "part_number": "TEST123",
            "category_id": cat_response.json()["id"],
            "storage_location_id": storage_response.json()["id"],
            "quantity_on_hand": 10
        },
        headers=auth_headers
    )
    print(f"Component creation: {comp_response.status_code}")
    if comp_response.status_code != 201:
        print(f"Component response: {comp_response.text}")
    assert comp_response.status_code == 201
    
    # Search for component
    search_response = client.get("/api/v1/components?search=TEST123")
    print(f"Search status: {search_response.status_code}")
    search_data = search_response.json()
    print(f"Search results: found {search_data['total']} components")
    
    # Manually rebuild FTS
    from backend.src.database.search import get_component_search_service
    search_service = get_component_search_service()
    count = search_service.rebuild_fts_index(db_session)
    print(f"FTS rebuild: indexed {count} components")
    
    # Search again
    search_response2 = client.get("/api/v1/components?search=TEST123")
    search_data2 = search_response2.json()
    print(f"Search after rebuild: found {search_data2['total']} components")
