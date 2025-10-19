import os
import shutil
import subprocess
import time
import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"
DB_PATH = os.path.join(os.path.dirname(__file__), "squirrel_db.db")
TEMPLATE_DB = os.path.join(os.path.dirname(__file__), "template_squirrel_db.db")
SERVER_PATH = os.path.join(os.path.dirname(__file__), "squirrel_server.py")

@pytest.fixture(autouse=True)
def reset_db_and_server():
    # Reset DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.copyfile(TEMPLATE_DB, DB_PATH)

    # Start server
    server = subprocess.Popen(["python3", SERVER_PATH])
    time.sleep(0.5)  # Give server time to start

    yield

    # Teardown
    server.terminate()
    server.wait()

def describe_squirrel_server_api():

    def describe_create_endpoint():
        def it_creates_a_new_squirrel():
            data = {"name": "Fluffy", "size": "large"}
            response = requests.post(f"{BASE_URL}/squirrels", data=data)
            assert response.status_code == 201

    def describe_list_endpoint():
        def it_returns_all_squirrels():
            requests.post(f"{BASE_URL}/squirrels", data={"name": "Chip", "size": "small"})
            response = requests.get(f"{BASE_URL}/squirrels")
            squirrels = response.json()
            assert response.status_code == 200
            assert isinstance(squirrels, list)
            assert any(s["name"] == "Chip" and s["size"] == "small" for s in squirrels)

    def describe_retrieve_endpoint():
        def it_returns_specific_squirrel():
            requests.post(f"{BASE_URL}/squirrels", data={"name": "Nutty", "size": "medium"})
            squirrels = requests.get(f"{BASE_URL}/squirrels").json()
            squirrel_id = squirrels[-1]["id"]
            response = requests.get(f"{BASE_URL}/squirrels/{squirrel_id}")
            assert response.status_code == 200
            assert response.json()["name"] == "Nutty"

    def describe_update_endpoint():
        def it_updates_existing_squirrel():
            requests.post(f"{BASE_URL}/squirrels", data={"name": "Shadow", "size": "tiny"})
            squirrel_id = requests.get(f"{BASE_URL}/squirrels").json()[0]["id"]
            response = requests.put(f"{BASE_URL}/squirrels/{squirrel_id}", data={"name": "Shadow", "size": "large"})
            assert response.status_code == 204
            updated = requests.get(f"{BASE_URL}/squirrels/{squirrel_id}").json()
            assert updated["size"] == "large"

    def describe_delete_endpoint():
        def it_deletes_a_squirrel():
            requests.post(f"{BASE_URL}/squirrels", data={"name": "Bolt", "size": "fast"})
            squirrel_id = requests.get(f"{BASE_URL}/squirrels").json()[0]["id"]
            response = requests.delete(f"{BASE_URL}/squirrels/{squirrel_id}")
            assert response.status_code == 204
            response = requests.get(f"{BASE_URL}/squirrels/{squirrel_id}")
            assert response.status_code == 404

    def describe_failure_conditions():
        def it_returns_404_for_unknown_path():
            response = requests.get(f"{BASE_URL}/unknown")
            assert response.status_code == 404

        def it_returns_404_for_missing_id_on_get():
            response = requests.get(f"{BASE_URL}/squirrels/999")
            assert response.status_code == 404

        def it_returns_404_for_missing_id_on_put():
            response = requests.put(f"{BASE_URL}/squirrels/999", data={"name": "Ghost", "size": "none"})
            assert response.status_code == 404

        def it_returns_404_for_missing_id_on_delete():
            response = requests.delete(f"{BASE_URL}/squirrels/999")
            assert response.status_code == 404

        def it_returns_404_for_post_with_id():
            response = requests.post(f"{BASE_URL}/squirrels/1", data={"name": "Invalid", "size": "tiny"})
            assert response.status_code == 404

        def it_returns_404_for_put_without_id():
            response = requests.put(f"{BASE_URL}/squirrels", data={"name": "NoID", "size": "tiny"})
            assert response.status_code == 404

        def it_returns_404_for_delete_without_id():
            response = requests.delete(f"{BASE_URL}/squirrels")
            assert response.status_code == 404

        def it_returns_404_for_get_with_non_numeric_id():
            response = requests.get(f"{BASE_URL}/squirrels/abc")
            assert response.status_code == 404

        def it_returns_404_for_put_with_non_numeric_id():
            response = requests.put(f"{BASE_URL}/squirrels/abc", data={"name": "Weird", "size": "odd"})
            assert response.status_code == 404

        def it_returns_404_for_delete_with_non_numeric_id():
            response = requests.delete(f"{BASE_URL}/squirrels/abc")
            assert response.status_code == 404
