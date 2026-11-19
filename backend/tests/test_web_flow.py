"""Isolated smoke test across controller, service and repository boundaries."""
import database
from fastapi.testclient import TestClient
from main import app


def test_web_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(database, 'DATABASE_PATH', tmp_path / 'flow.db')
    with TestClient(app) as client:
        member = client.post('/api/members', json={'name': '网页联调成员'})
        assert member.status_code == 201
        medicine = client.post('/api/medicines', json={
            'name': '联调药品', 'owner': '网页联调成员',
            'dose': '测试剂量', 'frequency': '测试频次',
        })
        assert medicine.status_code == 201
        medicines = client.get('/api/medicines', params={'owner': '网页联调成员'})
        assert medicines.json()[0]['id'] == medicine.json()['id']
        reminder = client.post('/api/reminders', json={
            'medicine_id': medicine.json()['id'], 'medicine_name': '联调药品',
            'member_name': '网页联调成员', 'time': '08:00', 'dose': '测试剂量',
        })
        assert reminder.status_code == 201
        payload = {'reminder_id': reminder.json()['id'],
                   'medicine_name': '联调药品', 'member_name': '网页联调成员',
                   'dose': '测试剂量'}
        record = client.post('/api/records', json=payload)
        assert record.status_code == 201
        assert client.post('/api/records', json=payload).status_code == 409
        assert client.delete(f"/api/records/{record.json()['id']}").status_code == 204
        # Data persists across a fresh database connection.
        with database.get_connection() as connection:
            assert connection.execute('SELECT COUNT(*) FROM medicines').fetchone()[0] == 1
            assert connection.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 0
