from src.db import get_pending_notifications


def test_pending_notifications_uses_patient_chat_when_no_guardian(monkeypatch):
    captured_sql = []

    class FakeCursor:
        def execute(self, query, params=None):
            captured_sql.append(query)

        def fetchall(self):
            return []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeConn:
        def cursor(self, row_factory=None):
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("src.db.get_conn", lambda: FakeConn())
    monkeypatch.setattr("src.db.ensure_schedule_notification_schema", lambda: None)

    get_pending_notifications()

    assert captured_sql
    query = captured_sql[0]
    assert "n.telegram_sent_at IS NULL" in query
    assert "n.guardian_id IS NULL AND p.telegram_chat_id IS NOT NULL" in query
    assert "n.guardian_id IS NOT NULL AND g.telegram_chat_id IS NOT NULL" in query
