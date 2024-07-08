import pytest
import requests_mock
import os

from app import app, save_profile_pic

PICTURES_FOLDER_PATH = "tests/pictures"
PICTURES_FOLDER_NAME = "pictures"
BASE_DIR = "tests"
EXCLUDE_FILES = ["exclude.png"]

# Create a Flask test client
@pytest.fixture(scope='module')
def setup_dirs():
    os.makedirs(PICTURES_FOLDER_PATH, exist_ok=True)
    yield
    for filename in os.listdir(PICTURES_FOLDER_PATH):
        file_path = os.path.join(PICTURES_FOLDER_PATH, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    os.rmdir(PICTURES_FOLDER_PATH)

# Create a Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Mock the urlopen and urlretrieve functions
@pytest.fixture
def mock_requests():
    with requests_mock.Mocker() as m:
        yield m

def test_save_profile_pic_handle_not_found(mock_requests):
    mock_requests.get("https://twitter.com/nonexistent_handle", status_code=404)

    handle = "nonexistent_handle"
    result = save_profile_pic(handle)
    assert result is False

def test_save_profile_pic_no_image(mock_requests):
    mock_requests.get("https://twitter.com/test_handle_no_image", text="""
        <html>
            <body>
                <!-- No image with class ProfileAvatar-image -->
            </body>
        </html>
    """)

    handle = "test_handle_no_image"
    result = save_profile_pic(handle)
    assert result is False

def test_process_handle_no_handle(client):
    response = client.post("/scrape/", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True
    assert "handle" in data

def test_process_handle_not_found(client, mock_requests):
    mock_requests.get("https://twitter.com/nonexistent_handle", status_code=404)

    response = client.post("/scrape/", json={"handle": "nonexistent_handle"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True

def test_get_profile_picture_detail_not_found(client):
    response = client.get("/users/nonexistent_handle/profile_pic/")
    assert response.status_code == 200
    assert b"Profile picture was not found" in response.data
