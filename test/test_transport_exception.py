import unittest
from unittest.mock import patch

import urllib3

from mux_python import ApiClient, AssetsApi
from mux_python.exceptions import ApiException, UnauthorizedException


class TransportExceptionTest(unittest.TestCase):
    def test_tls_failure_preserves_sdk_exception(self):
        with ApiClient() as client:
            with patch.object(client.rest_client.pool_manager, 'request',
                              side_effect=urllib3.exceptions.SSLError('certificate failed')):
                with self.assertRaises(ApiException) as caught:
                    AssetsApi(client).list_assets()
            self.assertEqual(caught.exception.status, 0)
            self.assertIn('certificate failed', caught.exception.reason)
            self.assertIsNone(caught.exception.body)

    def assert_exception_body_preserved(self, body):
        error = UnauthorizedException(status=401, reason='Unauthorized')
        error.body = body
        with ApiClient() as client:
            with patch.object(client, 'request', side_effect=error):
                with self.assertRaises(UnauthorizedException) as caught:
                    AssetsApi(client).list_assets()
        self.assertIs(caught.exception, error)
        self.assertEqual(caught.exception.status, 401)
        expected = body.decode('utf-8') if isinstance(body, bytes) else body
        self.assertEqual(caught.exception.body, expected)

    def test_missing_error_body(self):
        self.assert_exception_body_preserved(None)

    def test_already_decoded_error_body(self):
        self.assert_exception_body_preserved('Unauthorized')

    def test_utf8_error_body_still_decoded(self):
        self.assert_exception_body_preserved(b'Unauthorized')

    def test_empty_byte_body_still_decoded(self):
        self.assert_exception_body_preserved(b'')
