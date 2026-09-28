import unittest

from livereload.cli import (
    base_path_from_proxy_uri,
    detect_base_path,
    parser,
    resolve_base_path,
)


class TestBasePathFromProxyUri(unittest.TestCase):
    def test_absolute_uri(self):
        uri = 'https://example.com/proxy/{{port}}/'
        assert base_path_from_proxy_uri(uri, 5500) == '/proxy/5500'

    def test_relative_uri(self):
        assert base_path_from_proxy_uri('./proxy/{{port}}', 5500) == '/proxy/5500'

    def test_root_relative_uri(self):
        assert base_path_from_proxy_uri('/proxy/{{port}}', 5500) == '/proxy/5500'

    def test_subdomain_uri_needs_no_base_path(self):
        assert base_path_from_proxy_uri('https://{{port}}.example.com', 5500) == ''

    def test_uri_without_port_placeholder(self):
        uri = 'https://example.com/fixed/path'
        assert base_path_from_proxy_uri(uri, 5500) == '/fixed/path'

    def test_rejects_unsafe_path(self):
        with self.assertRaises(ValueError):
            base_path_from_proxy_uri('https://example.com/a"b/{{port}}', 5500)

    def test_rejects_parent_relative_uri(self):
        # Relative to what isn't known, so it can't be resolved safely
        with self.assertRaises(ValueError):
            base_path_from_proxy_uri('../proxy/{{port}}', 5500)


class TestDetectBasePath(unittest.TestCase):
    def test_detects_code_server(self):
        environ = {'VSCODE_PROXY_URI': 'https://example.com/proxy/{{port}}/'}
        assert detect_base_path(5500, environ) == ('code-server', '/proxy/5500')

    def test_nothing_detected(self):
        assert detect_base_path(5500, {}) is None
        assert detect_base_path(5500, {'VSCODE_PROXY_URI': ''}) is None

    def test_ignores_unusable_value(self):
        for uri in ('https://example.com/a b/', '../proxy/{{port}}'):
            environ = {'VSCODE_PROXY_URI': uri}
            with self.assertLogs('livereload', 'WARNING'):
                assert detect_base_path(5500, environ) is None


class TestResolveBasePath(unittest.TestCase):
    environ = {'VSCODE_PROXY_URI': 'https://example.com/proxy/{{port}}/'}

    def resolve(self, *argv, environ=None):
        args = parser.parse_args(list(argv))
        return resolve_base_path(args, self.environ if environ is None else environ)

    def test_environment_ignored_without_proxy_flag(self):
        assert self.resolve() is None
        assert self.resolve('--base-path', '/x') == '/x'

    def test_proxy_flag_uses_serve_port(self):
        assert self.resolve('--proxy', '-p', '8000') == '/proxy/8000'

    def test_explicit_base_path_wins(self):
        with self.assertLogs('livereload', 'WARNING'):
            assert self.resolve('--proxy', '--base-path', '/x') == '/x'

    def test_proxy_flag_with_nothing_detected(self):
        with self.assertLogs('livereload', 'WARNING'):
            assert self.resolve('--proxy', environ={}) is None
