def test_app_starts(client):
    """
    Verifica que la aplicación puede iniciar y la página principal
    responde con un estado HTTP exitoso, o al menos redirige a login.
    """
    response = client.get('/')
    # Esperamos un 200 OK o un 302 a la pantalla de login.
    assert response.status_code in [200, 302]
