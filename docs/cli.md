# Command Line Interface

The `livereload` command can be used for starting a live-reloading server, that
serves a directory.

```{command-output} livereload --help

```

It will listen to port 35729 by default, since that's the usual port for
[LiveReload browser extensions].

[livereload browser extensions]: https://livereload.com/extensions/

## Running behind a reverse proxy

The injected script works out the host, port and scheme from the page's URL,
so a reverse proxy in front of the server generally just works. If the proxy
serves it under a path prefix, pass that prefix with `--base-path`, so the
browser loads `livereload.js` and opens its websocket under it too. For
example, with [code-server]'s `/proxy/<port>/` URLs:

```
$ livereload --port 5500 --base-path /proxy/5500
```

The proxy must strip the prefix before forwarding requests (code-server's
`/proxy/` does, `/absproxy/` does not), and must forward websockets.

Alternatively, pass `--proxy` to detect the base path from the environment.
Currently this reads code-server's `VSCODE_PROXY_URI`, replacing `{{port}}`
with the port being served:

| `VSCODE_PROXY_URI`              | Base path     |
| ------------------------------- | ------------- |
| `https://host/proxy/{{port}}/`  | `/proxy/5500` |
| `./proxy/{{port}}`              | `/proxy/5500` |
| `https://{{port}}.host`         | none          |

A relative value is taken as relative to the root, so this won't work if
code-server itself is served under a prefix; use `--base-path` for that.
If `--base-path` is also given, it takes precedence.

[code-server]: https://coder.com/docs/code-server/guide#accessing-web-services

```{versionchanged} 2.0.0
`Guardfile` is no longer supported. Write a Python script using the API instead.
```
