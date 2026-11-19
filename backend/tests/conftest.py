"""Keep legacy business tests focused on their original API contracts."""
import pytest
import database
from main import app
from services.auth import require_family
from repositories.knowledge import initialize


@pytest.fixture(autouse=True)
def legacy_business_access(request, tmp_path, monkeypatch):
    monkeypatch.setattr(database,'DATA_DIR',tmp_path)
    monkeypatch.setattr(database,'DATABASE_PATH',tmp_path/'business.db')
    database.init_db()
    initialize()
    if request.node.name.startswith('test_access_'):
        yield
        return
    app.dependency_overrides[require_family]=lambda: None
    yield
    app.dependency_overrides.pop(require_family,None)
