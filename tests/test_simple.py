from flask import url_for


def test_can_use_client(client):
    assert client.get(url_for('login')).status_code == 200
