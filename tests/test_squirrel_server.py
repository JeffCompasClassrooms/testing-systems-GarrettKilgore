import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from squirrel_db import SquirrelDB
import http.client
import json
import pytest
import shutil
import subprocess
import time
import urllib
import concurrent.futures
import socket
import psutil

def kill_existing_server(port=8080):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            pid = conn.pid
            if pid:
                p = psutil.Process(pid)
                p.terminate()
                p.wait()


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "squirrel_db.db")
EMPTY_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "empty_squirrel_db.db")

def describe_squirrel_server():

    #@pytest.fixture(autouse=True, scope="session")
    #def start_server():
    #     kill_existing_server(port=8080)
    #     server = subprocess.Popen(["python3", "src/squirrel_server.py"])
    #     time.sleep(1)
    #     yield
    #     server.terminate()
    #     server.wait()

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

        def it_ignores_extra_fields_in_post(http_client, headers):
            data = urllib.parse.urlencode({ "name": "Fluffy", "size": "medium", "color": "gray" })
            http_client.request("POST", "/squirrels", body=data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 201
            http_client.close()

        def it_accepts_very_long_name(http_client, headers):
            long_name = "F" * 500
            data = urllib.parse.urlencode({ "name": long_name, "size": "tiny" })
            http_client.request("POST", "/squirrels", body=data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 201
            http_client.close()

        def it_accepts_unusual_size_label(http_client, headers):
            data = urllib.parse.urlencode({ "name": "Oddball", "size": "colossal" })
            http_client.request("POST", "/squirrels", body=data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 201
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
            http_client.close()

        def it_persists_updated_data(http_client, headers):
            update_data = urllib.parse.urlencode({ "name": "Fluffier", "size": "giant" })
            http_client.request("POST", "/squirrels", body=update_data, headers=headers)
            http_client.getresponse()
            http_client.request("PUT", "/squirrels/1", body=update_data, headers=headers)
            http_client.getresponse()
            http_client.request("GET", "/squirrels/1")
            updated = json.loads(http_client.getresponse().read())
            assert updated["name"] == "Fluffier"
            assert updated["size"] == "giant"
            http_client.close()

        def it_returns_404_when_updating_nonexistent_id(http_client, headers):
            update_data = urllib.parse.urlencode({ "name": "Ghost", "size": "tiny" })
            http_client.request("PUT", "/squirrels/999", body=update_data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 404
        
        def it_fully_replaces_record_when_updating_with_new_data(http_client, headers):
            http_client.request("POST", "/squirrels", body=urllib.parse.urlencode({ "name": "Test2", "size": "Test2Size" }), headers=headers)
            http_client.getresponse()
            update_data = urllib.parse.urlencode({ "name": "NewName", "size": "NewSize" })
            http_client.request("PUT", "/squirrels/1", body=update_data, headers=headers)
            http_client.getresponse()
            http_client.request("GET", "/squirrels/1")
            updated = json.loads(http_client.getresponse().read())
            assert updated["name"] == "NewName"
            assert updated["size"] == "NewSize"
            
        def it_returns_404_when_id_is_not_an_integer(http_client, headers):
            update_data = urllib.parse.urlencode({ "name": "Invalid", "size": "ID" })
            http_client.request("PUT", "/squirrels/abc", body=update_data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 404

        def it_ignores_extra_fields_in_put(http_client, headers):
            create_data = urllib.parse.urlencode({ "name": "Fluffy", "size": "medium" })
            http_client.request("POST", "/squirrels", body=create_data, headers=headers)
            http_client.getresponse()

            update_data = urllib.parse.urlencode({ "name": "Fluffier", "size": "giant", "color": "gray" })
            http_client.request("PUT", "/squirrels/1", body=update_data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 204
            http_client.close()

        def it_allows_update_with_same_data(http_client, headers):
            data = urllib.parse.urlencode({ "name": "Fluffy", "size": "medium" })
            http_client.request("POST", "/squirrels", body=data, headers=headers)
            http_client.getresponse()
            http_client.request("PUT", "/squirrels/1", body=data, headers=headers)
            response = http_client.getresponse()
            assert response.status == 204
            http_client.close()


    def describe_delete_squirrels():

        def it_returns_204_and_deletes_record(http_client, headers, squirrel_data):
            http_client.request("POST", "/squirrels", body=squirrel_data, headers=headers)
            http_client.getresponse()
            http_client.request("DELETE", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 204
            http_client.close()

        def it_removes_record_from_database(http_client):
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 404
            http_client.close()

        def it_returns_404_for_deleting_nonexistent_id(http_client):
            http_client.request("DELETE", "/squirrels/999")
            response = http_client.getresponse()
            assert response.status == 404
            http_client.close()

        def it_returns_404_for_missing_id(http_client):
            http_client.request("DELETE", "/squirrels")
            response = http_client.getresponse()
            assert response.status == 404
            http_client.close()

        def it_allows_immediate_delete_after_create(http_client, headers):
            data = urllib.parse.urlencode({ "name": "Temp", "size": "small" })
            http_client.request("POST", "/squirrels", body=data, headers=headers)
            http_client.getresponse()
            http_client.request("DELETE", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 204
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

    def describe_concurrent_requests():

        def it_handles_multiple_posts_simultaneously(headers):
            def post_squirrel():
                conn = http.client.HTTPConnection("localhost", 8080)
                data = urllib.parse.urlencode({ "name": "Fast", "size": "tiny" })
                conn.request("POST", "/squirrels", body=data, headers=headers)
                return conn.getresponse().status

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(lambda _: post_squirrel(), range(10)))
                assert all(status == 201 for status in results)