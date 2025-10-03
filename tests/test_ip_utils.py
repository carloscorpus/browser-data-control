import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import patch, Mock
from core.ip_utils import get_public_ip

def test_get_public_ip_success():
    """Test que get_public_ip retorna la IP correctamente cuando la respuesta es exitosa."""
    with patch('core.ip_utils.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "192.168.1.100"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        ip = get_public_ip()
        assert ip == "192.168.1.100"
        mock_get.assert_called_once_with('https://api.ipify.org?format=text', timeout=5)

def test_get_public_ip_with_whitespace():
    """Test que get_public_ip elimina espacios en blanco de la respuesta."""
    with patch('core.ip_utils.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "  192.168.1.100  \n"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        ip = get_public_ip()
        assert ip == "192.168.1.100"

def test_get_public_ip_request_exception():
    """Test que get_public_ip retorna None cuando hay una excepción de requests."""
    with patch('core.ip_utils.requests.get', side_effect=Exception('Network error')):
        ip = get_public_ip()
        assert ip is None

def test_get_public_ip_http_error():
    """Test que get_public_ip retorna None cuando hay un error HTTP."""
    with patch('core.ip_utils.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception('HTTP Error')
        mock_get.return_value = mock_response
        
        ip = get_public_ip()
        assert ip is None

def test_get_public_ip_timeout():
    """Test que get_public_ip usa el timeout correcto."""
    with patch('core.ip_utils.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "192.168.1.100"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        get_public_ip()
        mock_get.assert_called_once_with('https://api.ipify.org?format=text', timeout=5)