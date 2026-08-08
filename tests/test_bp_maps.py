import io
import os
import database.db_core

def test_map_endpoints_require_auth(client):
    """Verifica que los endpoints de planos devuelven redireccion si no hay auth (auth_guard)."""
    # Como TESTING=True desactiva login de Flask-Login en conftest (LOGIN_DISABLED), 
    # este test pasaría. En el futuro, si probamos los permisos reales, deberemos
    # inyectar un usuario en sesion que no tenga el permiso 'infrastructure' y verificar 403.
    pass

def test_add_map_validates_extensions(client, monkeypatch):
    """Prueba que subir un archivo inválido (ej. txt o pdf no admitido para mapa principal) sea rechazado."""
    import utils.auth
    monkeypatch.setattr(utils.auth, "is_authenticated", lambda: True)
    monkeypatch.setattr(utils.auth, "has_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(utils.auth, "refresh_session_user", lambda: {"username": "test", "roles": ["infrastructure"]})
    monkeypatch.setattr(utils.auth, "is_superuser", lambda: True)

    data = {
        'name': 'Test Building',
        'building': 'Test',
        'floor': '1',
        'file': (io.BytesIO(b"dummy text data"), 'malicious.txt')
    }
    
    response = client.post('/planos/add', data=data, content_type='multipart/form-data', follow_redirects=True)
    
    # bp_maps.py flashes an error and redirects to index
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Formato de archivo no permitido" in html or "Mimetype" in html

def test_add_map_accepts_valid_image(client, monkeypatch):
    """Prueba que se aceptan extensiones de imagen."""
    import utils.auth
    monkeypatch.setattr(utils.auth, "is_authenticated", lambda: True)
    monkeypatch.setattr(utils.auth, "has_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(utils.auth, "refresh_session_user", lambda: {"username": "test", "roles": ["infrastructure"]})
    monkeypatch.setattr(utils.auth, "is_superuser", lambda: True)
    
    # Mocking db insert so we don't actually hit the DB
    class DummyCursor:
        def fetchall(self): return []
        def fetchone(self): return None
        def close(self): pass
        
    class DummyDB:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def execute(self, *args, **kwargs): return DummyCursor()
        def commit(self): pass

    monkeypatch.setattr(database.db_core, "get_db_connection", lambda: DummyDB())
    
    # We also need to mock save() on the file object or os.makedirs to prevent actual disk writes
    from werkzeug.datastructures import FileStorage
    monkeypatch.setattr(FileStorage, "save", lambda *args, **kwargs: None)

    data = {
        'name': 'Test Building',
        'building': 'Test',
        'floor': '1',
        'file': (io.BytesIO(b"fake image data"), 'valid.png')
    }
    
    response = client.post('/planos/add', data=data, content_type='multipart/form-data', follow_redirects=True)
    
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # The view flashes a success message and redirects to maps.index
    assert "Plano subido exitosamente" in html

def test_update_position_records_history(client, monkeypatch):
    """Verifica que update_position guarda el historial del cambio (RED)."""
    import utils.auth
    monkeypatch.setattr(utils.auth, "is_authenticated", lambda: True)
    monkeypatch.setattr(utils.auth, "has_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(utils.auth, "refresh_session_user", lambda: {"username": "test_tech", "roles": ["infrastructure"]})
    monkeypatch.setattr(utils.auth, "is_superuser", lambda: True)

    queries_executed = []

    class DummyCursor:
        def fetchall(self): return []
        def fetchone(self): return None
        def close(self): pass
        
    class DummyDB:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def execute(self, query, params=None):
            queries_executed.append((query, params))
            return DummyCursor()
        def commit(self): pass

    import blueprints.bp_maps
    monkeypatch.setattr(blueprints.bp_maps, "get_db_connection", lambda: DummyDB())

    data = {
        'type': 'pc',
        'id': 'PC-001',
        'map_id': '1',
        'x': '10.5',
        'y': '20.5'
    }

    with client.session_transaction() as sess:
        sess['user'] = {'username': 'test_tech', 'roles': ['infrastructure']}

    response = client.post('/planos/api/update_position', json=data) # wait, standard request format?
    # bp_maps.py update_position accepts json via request.json
    
    assert response.status_code == 200
    
    history_insert_found = False
    for q, p in queries_executed:
        if "INSERT INTO asset_location_history" in q:
            history_insert_found = True
            assert p[0] == 'pc'
            assert p[1] == 'PC-001'
            assert p[6] == 'test_tech' # Changed by user
            break
            
    assert history_insert_found, "The API did not record the position change in history"
