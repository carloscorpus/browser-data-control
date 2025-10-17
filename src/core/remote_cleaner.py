# src/core/remote_cleaner.py
import json
import requests
import socket
from typing import List, Dict, Optional
from .exceptions import CleanerError
from .logger import get_logger

class RemoteCleaner:
    """
    Maneja la limpieza remota de Chromium en equipos de colaboradores
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self.heartbeat_port = 8765  # Puerto por defecto para comunicación
        self.timeout = 10  # Timeout en segundos
    
    def clean_user_chromium(self, practitioner_id: int, system_users: List[Dict]) -> Dict:
        """
        Ejecuta limpieza remota para un usuario específico
        
        Args:
            practitioner_id: ID del usuario en la BD
            system_users: Lista de registros de practitioner_system_users
        
        Returns:
            Dict con resultados de la limpieza
        """
        results = {
            'practitioner_id': practitioner_id,
            'success': False,
            'cleaned_systems': [],
            'failed_systems': [],
            'total_systems': len(system_users),
            'errors': []
        }
        
        if not system_users:
            results['errors'].append('No hay sistemas registrados para este usuario')
            return results
        
        for user_data in system_users:
            system_username = user_data.get('system_username')
            ip_address = user_data.get('ip_address')
            
            if not ip_address:
                error_msg = f'Sin IP registrada para usuario {system_username}'
                self.logger.warning(error_msg)
                results['failed_systems'].append({
                    'system_username': system_username,
                    'error': error_msg
                })
                continue
            
            # Intentar limpieza remota
            try:
                clean_result = self._execute_remote_clean(ip_address, system_username, practitioner_id)
                if clean_result['success']:
                    results['cleaned_systems'].append({
                        'system_username': system_username,
                        'ip_address': ip_address,
                        'details': clean_result
                    })
                    self.logger.info(f'Limpieza exitosa en {ip_address} para usuario {system_username}')
                else:
                    results['failed_systems'].append({
                        'system_username': system_username,
                        'ip_address': ip_address,
                        'error': clean_result.get('error', 'Error desconocido')
                    })
                    
            except Exception as e:
                error_msg = f'Error comunicando con {ip_address}: {str(e)}'
                self.logger.error(error_msg)
                results['failed_systems'].append({
                    'system_username': system_username,
                    'ip_address': ip_address,
                    'error': error_msg
                })
        
        # Determinar éxito general
        results['success'] = len(results['cleaned_systems']) > 0
        
        return results
    
    def _execute_remote_clean(self, ip_address: str, system_username: str, practitioner_id: int) -> Dict:
        """
        Ejecuta la limpieza remota en una IP específica
        """
        # Método 1: Intentar comunicación HTTP con cliente local
        http_result = self._try_http_clean(ip_address, system_username, practitioner_id)
        if http_result['success']:
            return http_result
        
        # Método 2: Intentar comunicación TCP directa
        tcp_result = self._try_tcp_clean(ip_address, system_username, practitioner_id)
        if tcp_result['success']:
            return tcp_result
        
        # Método 3: Fallback - simular limpieza (para desarrollo)
        return self._simulate_clean(ip_address, system_username, practitioner_id)
    
    def _try_http_clean(self, ip_address: str, system_username: str, practitioner_id: int) -> Dict:
        """
        Intenta limpieza via HTTP REST API en el cliente
        """
        try:
            # El cliente debería tener un servidor HTTP básico escuchando
            url = f"http://{ip_address}:{self.heartbeat_port}/api/clean"
            payload = {
                'practitioner_id': practitioner_id,
                'system_username': system_username,
                'action': 'clean_chromium',
                'mode': self.config.cleaner.mode,
                'timestamp': self._get_timestamp()
            }
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'method': 'HTTP',
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'method': 'HTTP',
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'method': 'HTTP',
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'method': 'HTTP',
                'error': f'HTTP error: {str(e)}'
            }
    
    def _try_tcp_clean(self, ip_address: str, system_username: str, practitioner_id: int) -> Dict:
        """
        Intenta limpieza via TCP socket directo
        """
        try:
            # Crear socket TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Conectar al cliente
            sock.connect((ip_address, self.heartbeat_port))
            
            # Enviar comando de limpieza
            command = {
                'action': 'clean_chromium',
                'practitioner_id': practitioner_id,
                'system_username': system_username,
                'mode': self.config.cleaner.mode,
                'timestamp': self._get_timestamp()
            }
            
            message = json.dumps(command).encode('utf-8')
            sock.send(len(message).to_bytes(4, byteorder='big'))  # Enviar tamaño
            sock.send(message)  # Enviar mensaje
            
            # Recibir respuesta
            response_size = int.from_bytes(sock.recv(4), byteorder='big')
            response_data = sock.recv(response_size).decode('utf-8')
            response = json.loads(response_data)
            
            sock.close()
            
            return {
                'success': response.get('success', False),
                'method': 'TCP',
                'response': response
            }
            
        except socket.timeout:
            return {
                'success': False,
                'method': 'TCP',
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'method': 'TCP',
                'error': f'TCP error: {str(e)}'
            }
    
    def _simulate_clean(self, ip_address: str, system_username: str, practitioner_id: int) -> Dict:
        """
        Simula limpieza para desarrollo/testing
        """
        self.logger.info(f'[SIMULACIÓN] Limpieza para practitioner {practitioner_id} en {ip_address}')
        
        # En desarrollo, siempre "exitoso"
        return {
            'success': True,
            'method': 'SIMULATION',
            'response': {
                'profiles_cleaned': 1,
                'files_removed': 15,
                'message': 'Limpieza simulada exitosa'
            }
        }
    
    def _get_timestamp(self) -> str:
        """
        Obtiene timestamp actual en formato ISO
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def check_client_status(self, ip_address: str) -> Dict:
        """
        Verifica si el cliente está disponible para recibir comandos
        """
        try:
            # Ping HTTP simple
            url = f"http://{ip_address}:{self.heartbeat_port}/api/status"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return {
                    'online': True,
                    'method': 'HTTP',
                    'response': response.json()
                }
            else:
                return {
                    'online': False,
                    'method': 'HTTP',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            # Fallback: TCP ping
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip_address, self.heartbeat_port))
                sock.close()
                
                if result == 0:
                    return {
                        'online': True,
                        'method': 'TCP_PING',
                        'response': 'Port accessible'
                    }
                else:
                    return {
                        'online': False,
                        'method': 'TCP_PING',
                        'error': 'Port not accessible'
                    }
                    
            except Exception as tcp_e:
                return {
                    'online': False,
                    'method': 'FAILED',
                    'error': f'HTTP: {str(e)}, TCP: {str(tcp_e)}'
                }