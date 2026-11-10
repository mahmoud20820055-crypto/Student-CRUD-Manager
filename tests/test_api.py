def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "database": "ok"}


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Student CRUD Manager" in res.data


def test_create_and_get(client, student):
    res = client.post("/api/students", json=student)
    assert res.status_code == 201
    created = res.get_json()
    assert created["id"] == 1 and created["email"] == student["email"]

    res = client.get(f"/api/students/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["first_name"] == "Sara"


def test_create_validation_errors(client):
    res = client.post("/api/students", json={"first_name": "", "gpa": 7, "email": "nope"})
    assert res.status_code == 400
    details = res.get_json()["details"]
    assert {"first_name", "gpa", "email", "student_code", "major"} <= details.keys()


def test_duplicate_email_conflict(client, student):
    client.post("/api/students", json=student)
    res = client.post("/api/students", json={**student, "student_code": "S-2"})
    assert res.status_code == 409
    assert res.get_json()["details"] == {"email": "already exists"}


def test_list_and_search(client, student):
    client.post("/api/students", json=student)
    client.post("/api/students", json={**student, "student_code": "S-2", "email": "omar@example.com",
                                       "first_name": "Omar", "major": "Mathematics"})
    assert len(client.get("/api/students").get_json()) == 2
    found = client.get("/api/students?q=math").get_json()
    assert [s["first_name"] for s in found] == ["Omar"]


def test_update_put_and_patch(client, student):
    sid = client.post("/api/students", json=student).get_json()["id"]
    res = client.put(f"/api/students/{sid}", json={**student, "gpa": 3.9})
    assert res.status_code == 200 and res.get_json()["gpa"] == 3.9

    res = client.patch(f"/api/students/{sid}", json={"major": "Data Science"})
    assert res.status_code == 200 and res.get_json()["major"] == "Data Science"

    res = client.put(f"/api/students/{sid}", json={"gpa": 3.0})
    assert res.status_code == 400  # PUT requires the full record


def test_delete(client, student):
    sid = client.post("/api/students", json=student).get_json()["id"]
    assert client.delete(f"/api/students/{sid}").status_code == 204
    assert client.get(f"/api/students/{sid}").status_code == 404
    assert client.delete(f"/api/students/{sid}").status_code == 404


def test_stats(client, student):
    client.post("/api/students", json=student)
    client.post("/api/students", json={**student, "student_code": "S-2", "email": "b@example.com", "gpa": 3.1})
    assert client.get("/api/stats").get_json() == {"total": 2, "average_gpa": 3.4, "majors": 1}
