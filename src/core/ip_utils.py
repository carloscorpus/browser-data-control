import requests

def get_public_ip():
    """Obtiene la IP pública del equipo usando un servicio externo."""
    try:
        response = requests.get('https://api.ipify.org?format=text', timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception:
        return None
