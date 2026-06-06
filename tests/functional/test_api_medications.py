from datetime import datetime, timedelta, timezone


def test_medication_and_schedule_flow(auth_client, seeded):
    medication = auth_client.post(
        "/medications",
        json={"name": "Витамин D", "description": "Утром"},
    )
    assert medication.status_code == 201
    med_id = medication.json()["id"]

    intake_at = datetime.now(timezone.utc) + timedelta(hours=1)
    schedule = auth_client.post(
        f"/medications/{med_id}/schedules",
        json={"intake_at": intake_at.isoformat(), "dose": "1 капсула"},
    )
    assert schedule.status_code == 201
    schedule_id = schedule.json()["id"]

    schedules = auth_client.get(f"/medications/{med_id}/schedules")
    assert schedules.status_code == 200
    assert len(schedules.json()) == 1

    marked = auth_client.post(
        f"/medications/{med_id}/schedules/mark-taken",
        json={"schedule_id": schedule_id},
    )
    assert marked.status_code == 200
    assert marked.json()["taken"] is True

    deleted = auth_client.delete(f"/medications/{med_id}/schedules/{schedule_id}")
    assert deleted.status_code == 204

    schedules_after = auth_client.get(f"/medications/{med_id}/schedules")
    assert schedules_after.status_code == 200
    assert schedules_after.json() == []


def test_list_medications(auth_client, seeded):
    response = auth_client.get("/medications")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_delete_medication(auth_client, seeded):
    created = auth_client.post("/medications", json={"name": "Для удаления"})
    assert created.status_code == 201
    med_id = created.json()["id"]

    deleted = auth_client.delete(f"/medications/{med_id}")
    assert deleted.status_code == 204

    response = auth_client.get(f"/medications/{med_id}")
    assert response.status_code == 404
