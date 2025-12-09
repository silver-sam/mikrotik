import unittest
import os
from unittest.mock import patch, MagicMock
from io import StringIO
import devices  # Assumes devices.py is in PYTHONPATH or same directory

class TestDevices(unittest.TestCase):

    def setUp(self):
        # Reset environment variables before each test
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('devices.logger')
    def test_missing_env_vars(self, mock_logger):
        # Ensure all required env vars are missing
        with patch.dict(os.environ, {}, clear=True):
            # We need to reload the module or re-import the vars? 
            # Actually devices.py reads env vars at module level for defaults, 
            # but main logic checks them in get_active_devices_rest logic (re-reading global constants?)
            # Wait, the constants in devices.py (ROUTER_IP etc) are loaded at import time.
            # To test this properly without reloading module, we might need to mock the *constants* 
            # in the devices module OR refactor devices.py to read env vars inside the function 
            # or allow passing them as args. 
            
            # Use patching of the module-level constants for this test since we can't easily re-import
            with patch('devices.ROUTER_IP', None), \
                 patch('devices.ROUTER_USER', None), \
                 patch('devices.ROUTER_PASSWORD', None), \
                 patch('devices.ROUTER_CERT_PATH', None):
                
                result = devices.get_active_devices_rest()
                self.assertEqual(result, [])
                # Verify error logs
                self.assertTrue(mock_logger.error.called)

    @patch('devices.requests.get')
    def test_get_active_devices_success(self, mock_get):
        # Mock configuration
        with patch('devices.ROUTER_IP', '1.2.3.4'), \
             patch('devices.ROUTER_USER', 'user'), \
             patch('devices.ROUTER_PASSWORD', 'pass'), \
             patch('devices.ROUTER_CERT_PATH', '/tmp/cert'):

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                if 'arp' in url:
                    mock_resp.json.return_value = [
                        {'address': '192.168.1.10', 'mac-address': 'AA:BB:CC:DD:EE:FF', 'interface': 'ether1', 'dynamic': 'true', 'disabled': 'false'},
                        {'address': '192.168.1.11', 'mac-address': 'AA:BB:CC:DD:EE:00', 'interface': 'ether1', 'dynamic': 'false', 'disabled': 'false', 'comment': 'StaticDevice'},
                    ]
                elif 'lease' in url:
                    mock_resp.json.return_value = [
                        {'mac-address': 'AA:BB:CC:DD:EE:FF', 'host-name': 'DynamicHost'},
                    ]
                return mock_resp
            
            mock_get.side_effect = side_effect

            devices_list = devices.get_active_devices_rest()
            
            # Should contain both entries
            self.assertEqual(len(devices_list), 2)
            
            # Check for enriched names
            # Dynamic device: gets name from DHCP
            self.assertEqual(devices_list[0]['address'], '192.168.1.10')
            self.assertEqual(devices_list[0]['name'], 'DynamicHost')
            
            # Static device: gets name from ARP comment
            self.assertEqual(devices_list[1]['address'], '192.168.1.11')
            self.assertEqual(devices_list[1]['name'], 'StaticDevice')

    @patch('devices.requests.get')
    def test_api_boolean_handling(self, mock_get):
        # Test handling of boolean vs string types for dynamic/disabled
        with patch('devices.ROUTER_IP', '1.2.3.4'), \
             patch('devices.ROUTER_USER', 'user'), \
             patch('devices.ROUTER_PASSWORD', 'pass'), \
             patch('devices.ROUTER_CERT_PATH', '/tmp/cert'):

            # Simpler mock for this test: just return empty leases so we don't crash
            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                if 'arp' in url:
                     mock_resp.json.return_value = [
                        {'address': '10.0.0.1', 'dynamic': True, 'disabled': False}, 
                        {'address': '10.0.0.2', 'dynamic': 'true', 'disabled': 'false'},
                        {'address': '10.0.0.3', 'dynamic': 'false', 'disabled': False},
                    ]
                else:
                    mock_resp.json.return_value = []
                return mock_resp
            
            mock_get.side_effect = side_effect

            results = devices.get_active_devices_rest()
            
            # All 3 should be included
            self.assertEqual(len(results), 3)

    @patch('devices.requests.get')
    @patch('devices.logger')
    def test_request_exception(self, mock_logger, mock_get):
        with patch('devices.ROUTER_IP', '1.2.3.4'), \
             patch('devices.ROUTER_USER', 'user'), \
             patch('devices.ROUTER_PASSWORD', 'pass'), \
             patch('devices.ROUTER_CERT_PATH', '/tmp/cert'):

            # Fail immediately on first call (ARP)
            mock_get.side_effect = devices.requests.exceptions.RequestException("Connection error")
            
            result = devices.get_active_devices_rest()
            self.assertEqual(result, [])
            self.assertTrue(mock_logger.error.called)

if __name__ == '__main__':
    unittest.main()
