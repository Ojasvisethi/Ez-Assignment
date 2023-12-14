import io
from fastapi.testclient import TestClient


from main import app

client = TestClient(app)

def test_upload_file_invalid_file_type():
    data = {
        "username": "test",
        "password": "123456",
    }

    response_token = client.post("/token", data=data)
    access_token = response_token.json()["access_token"]
    assert access_token
    headers = {"Authorization": f"Bearer {access_token}"}

    # # Prepare a file with an invalid type (txt file)
        # Use a file stored in the 'uploads' folder
    file_path = "test.txt"
    file_path2 = "Gsoc.xlsx"

    # Read the file content
    with open(file_path, "rb") as file:
        file_content = file.read()
    with open(file_path2, "rb") as file:
        file_content2 = file.read()

    # Prepare files dictionary for file upload
    files = {"file": (file_path, file_content)}
    files2 = {"file": (file_path2, file_content2)}

    # Make the request to the /files/ endpoint
    response_upload = client.post("/files/", headers=headers, files=files)
    response_upload2 = client.post("/files/", headers=headers, files=files2)

    # Assert the response status code
    assert response_upload.status_code == 404
    assert response_upload2.status_code == 200
    # Assert the response content for invalid file type
    # assert response_upload.json()["detail"] == "Invalid`` file type. Only pptx, docx, and xlsx are allowed."


def test_list_all_uploaded_files():
    response = client.get("/clientuser/uploadedFiles")
    assert response

def test_client_user_login():
    data2 = {
        "username": "test",
        "password": "123456",
    }
    response2 = client.post('/clientuser/login' , data=data2 )
    assert response2.status_code == 422
    assert "detail" in response2.json()