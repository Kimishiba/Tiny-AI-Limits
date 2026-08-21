# Vendored assets

## `improv-wifi-serial-launch-button.bundle.js`

Self-bundled copy of the [`improv-wifi-serial-sdk`](https://github.com/improv-wifi/sdk-serial-js)
browser widget, used by `emulator/setup.html` for WiFi provisioning over USB.

**Why self-bundled instead of loaded from a CDN at runtime:** the package's
published `dist/serial-launch-button.js` dynamically imports a chunk
(`serial-provision-dialog.js`) containing a bare `import ... from "tslib"`
specifier, which only resolves inside a bundler -- loading it directly via
`<script type="module" src="https://unpkg.com/...">` fails with
`TypeError: Failed to resolve module specifier "tslib"`. Auto-resolving CDNs
like `esm.sh` fix that, but introduced a different bug: this package's
`@material/web` dependency (used for the provisioning dialog's UI) has
several internal cross-entry-point shared modules (e.g. `md-focus-ring`)
that esm.sh's per-package CDN resolution doesn't always dedupe, causing
`Failed to execute 'define' on 'CustomElementRegistry': the name
"md-focus-ring" has already been used`. A real bundler resolves the whole
dependency graph as one program and dedupes by construction, sidestepping
both issues -- and removes the runtime dependency on any third-party CDN
being up at all for a first-run onboarding flow.

To rebuild after bumping the version:

```bash
mkdir /tmp/improv-bundle && cd /tmp/improv-bundle
npm init -y
npm install improv-wifi-serial-sdk@<version>
npx esbuild node_modules/improv-wifi-serial-sdk/dist/serial-launch-button.js \
  --bundle --format=esm --minify \
  --outfile=improv-wifi-serial-launch-button.bundle.js
cp improv-wifi-serial-launch-button.bundle.js /path/to/repo/emulator/vendor/
```
