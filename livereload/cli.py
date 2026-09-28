import argparse
import logging
import os
from urllib.parse import urlsplit

import tornado.log

from livereload.server import Server, normalize_base_path

logger = logging.getLogger('livereload')


def base_path_from_proxy_uri(uri, port):
    """Get the base path from a code-server style ``VSCODE_PROXY_URI``.

    The URI may be absolute (``https://host/proxy/{{port}}/``), relative
    (``./proxy/{{port}}``, taken as relative to the root) or use a
    subdomain per port (``https://{{port}}.host``, needing no base path).
    """
    path = urlsplit(uri.replace('{{port}}', str(port))).path
    if path.startswith('./'):
        path = path[1:]
    return normalize_base_path(path)


#: Reverse proxy environments ``--proxy`` can detect, in order of preference,
#: as (name, environment variable, parser) tuples.
PROXY_DETECTORS = [
    ('code-server', 'VSCODE_PROXY_URI', base_path_from_proxy_uri),
]


def detect_base_path(port, environ=os.environ):
    """Return ``(name, base_path)`` for the first proxy environment found,
    or ``None`` if there is none.
    """
    for name, var, parse in PROXY_DETECTORS:
        value = environ.get(var)
        if not value:
            continue
        try:
            return name, parse(value, port)
        except ValueError:
            logger.warning('Ignoring %s=%r: not a usable base path', var, value)
    return None


def resolve_base_path(args, environ=os.environ):
    """Work out the base path from ``--base-path`` and ``--proxy``."""
    if not args.proxy:
        return args.base_path
    if args.base_path is not None:
        logger.warning('Both --base-path and --proxy given, using --base-path')
        return args.base_path
    detected = detect_base_path(args.port, environ)
    if detected is None:
        logger.warning('--proxy: no reverse proxy environment detected, '
                       'serving at the root')
        return None
    name, path = detected
    logger.info('--proxy: detected %s, using base path %s', name, path or '/')
    return path


def base_path(value):
    try:
        return normalize_base_path(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


parser = argparse.ArgumentParser(description='Start a `livereload` server')
parser.add_argument(
    '--host',
    help='Hostname to run `livereload` server on',
    type=str,
    default='127.0.0.1'
)
parser.add_argument(
    '-p', '--port',
    help='Port to run `livereload` server on',
    type=int,
    default=35729
)
parser.add_argument(
    'directory',
    help='Directory to serve files from',
    type=str,
    default='.',
    nargs='?'
)
parser.add_argument(
    '-t', '--target',
    help='File or directory to watch for changes',
    type=str,
)
parser.add_argument(
    '-w', '--wait',
    help='Time delay in seconds before reloading',
    type=float,
    default=0.0
)
parser.add_argument(
    '-o', '--open-url-delay',
    help='If set, triggers browser opening <D> seconds after starting',
    type=float
)
parser.add_argument(
    '-d', '--debug',
    help='Enable Tornado pretty logging',
    action='store_true'
)
parser.add_argument(
    '--base-path',
    help='URL path prefix when served behind a reverse proxy that strips '
         'it, e.g. /proxy/5500',
    type=base_path,
)
parser.add_argument(
    '--proxy',
    help="Detect the base path from the reverse proxy environment "
         "(currently code-server's VSCODE_PROXY_URI)",
    action='store_true'
)


def main(argv=None):
    args = parser.parse_args()

    if args.debug:
        tornado.log.enable_pretty_logging()

    # Create a new application
    server = Server()
    server.watcher.watch(args.target or args.directory, delay=args.wait)
    server.serve(host=args.host, port=args.port, root=args.directory,
                 open_url_delay=args.open_url_delay,
                 base_path=resolve_base_path(args))
