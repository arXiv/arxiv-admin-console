import pytest
from fastapi.testclient import TestClient


class TestCountries:
    def test_get_all_countries_iso2(self, admin_api_db_only_client: TestClient):
        response = admin_api_db_only_client.get("/v1/countries/iso2")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 200  # There are many countries in the list
        assert response.headers['X-Total-Count'] == str(len(response.json()))

    def test_get_country_by_iso2(self, admin_api_db_only_client: TestClient):
        response = admin_api_db_only_client.get("/v1/countries/iso2/US")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "US"
        assert data["country_name"] == "United States"

    def test_get_country_not_found(self, admin_api_db_only_client: TestClient):
        response = admin_api_db_only_client.get("/v1/countries/iso2/XX")
        assert response.status_code == 404

    def test_get_all_countries_iso2_sorted(self, admin_api_db_only_client: TestClient):
        response = admin_api_db_only_client.get("/v1/countries/iso2?_sort=country_name&_order=ASC")
        assert response.status_code == 200
        data = response.json()
        assert data[0]['country_name'] == 'Afghanistan'

    def test_get_all_countries_iso2_paginated(self, admin_api_db_only_client: TestClient):
        response = admin_api_db_only_client.get("/v1/countries/iso2?_start=0&_end=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
