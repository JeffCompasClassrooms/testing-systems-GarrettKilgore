from squirrel_db import SquirrelDB

import http.client
import json
import os
import pytest
import shutil
import subprocess
import time
import urllib
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "squirrel_db.db")
EMPTY_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "empty_squirrel_db.db")

def describe_squirrel_server():

    @pytest.fixture(autouse=True)
    def reset_database():
        """Reset the squirrel_db.db file before each test case."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        shutil.copyfile(EMPTY_DB_PATH, DB_PATH)
        yield
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    @pytest.fixture(autouse=True, scope="session")
    def start_server():
        server = subprocess.Popen(["python3", "src/squirrel_server.py"])
        time.sleep(1)
        yield
        server.terminate()
        server.wait()

    @pytest.fixture
    def http_client():
        return http.client.HTTPConnection("localhost", 8080)

    @pytest.fixture
    def headers():
        return { "Content-Type": "application/x-www-form-urlencoded" }

    @pytest.fixture
    def squirrel_data():
        return urllib.parse.urlencode({ "name": "Fluffy", "size": "large" })

    def describe_post_squirrels():

        def it_returns_201_and_creates_record(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 201
            http_client.close()

        def it_can_be_retrieved_after_creation(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            http_client.getresponse()
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            body = json.loads(response.read())
            assert body["name"] == "Fluffy"
            assert body["size"] == "large"
            http_client.close()

    def describe_get_squirrels():

        def it_returns_200(http_client):
            http_client.request("GET", "/squirrels")
            assert http_client.getresponse().status == 200

        def it_returns_json_content_type(http_client):
            http_client.request("GET", "/squirrels")
            assert http_client.getresponse().getheader("Content-Type") == "application/json"

        def it_returns_json_array(http_client):
            http_client.request("GET", "/squirrels")
            body = json.loads(http_client.getresponse().read())
            assert isinstance(body, list)

        def it_returns_array_with_created_squirrel(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            http_client.getresponse()
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            body = json.loads(response.read())
            assert any(s["name"] == "Fluffy" and s["size"] == "large" for s in body)
            http_client.close()

    def describe_get_squirrel_by_id():

        def it_returns_200_and_correct_body(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            http_client.getresponse()
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 200
            assert response.getheader("Content-Type") == "application/json"
            body = json.loads(response.read())
            assert body["id"] == 1
            assert body["name"] == "Fluffy"
            assert body["size"] == "large"
            http_client.close()

    def describe_put_squirrels():

        def it_returns_204_and_updates_record(http_client, headers):
            create_data = urllib.parse.urlencode({ "name": "Fluffy", "size": "medium" })
            update_data = urllib.parse.urlencode({ "name": "Fluffier", "size": "giant" })
            http_client.request("POST", "/squirrels", body=create_data, headers=headers)
            http_client.getresponse()
            http_client.request("PUT", "/squirrels/1", body=update_data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 204
            http_client.request("GET", "/squirrels/1")
            updated = json.loads(http_client.getresponse().read())
            assert updated["name"] == "Fluffier"
            assert updated["size"] == "giant"
            http_client.close()

    def describe_delete_squirrels():

        def it_returns_204_and_deletes_record(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            http_client.getresponse()
            http_client.request("DELETE", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 204
            http_client.request("GET", "/squirrels/1")
            not_found = http_client.getresponse()
            assert not_found.status == 404
            http_client.close()

    def describe_404_failures():

        def it_returns_404_for_get_invalid_id(http_client):
            http_client.request("GET", "/squirrels/999")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_put_invalid_id(http_client, headers):
            data = urllib.parse.urlencode({ "name": "Ghost", "size": "tiny" })
            http_client.request("PUT", "/squirrels/999", body=data, headers=headers)
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_delete_invalid_id(http_client):
            http_client.request("DELETE", "/squirrels/999")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_post_with_id(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels/1", body=squirrel_data, headers=headers)
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_put_without_id(http_client, headers, squirrel_data):
            http_client.request("PUT", "/squirrels", body=squirrel_data, headers=headers)
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_delete_without_id(http_client):
            http_client.request("DELETE", "/squirrels")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_unknown_path(http_client):
            http_client.request("GET", "/unknown")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_nested_unknown_path(http_client):
            http_client.request("GET", "/squirrels/1/extra")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_missing_resource(http_client):
            http_client.request("GET", "/")
            assert http_client.getresponse().status == 404
            http_client.close()

        def it_returns_404_for_wrong_method_on_id(http_client):
            http_client.request("POST", "/squirrels/1")
            assert http_client.getresponse().status == 404
            http_client.close()