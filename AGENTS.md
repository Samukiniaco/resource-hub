# AGENTS.md

## Role

You are a coding agent working on this repository.

Read this file before modifying the project.

Follow the existing architecture and conventions. Do not introduce unrequested features or replace established technologies without a clear reason.

---

## Project Overview

This is a Windows desktop utility designed for distributing and organizing resources used alongside an external Minecraft launcher.

The application operates completely independently from the launcher itself.

> **CRITICAL RULE:** The external launcher must **NOT** be modified, forked, embedded, or treated as part of this project under any circumstances.

### Features & Responsibilities
- Provide links for Minecraft versions, shared libraries, Java packages, and launcher-related external resources.
- Display patches, miscellaneous files, descriptions, optional banners, and update notices.
- Handle remote catalog updates with robust offline/caching mechanisms.
- Provide a dedicated `JavaPath` helper for `vortex_launcher.conf`.
- **Scope Limit:** The application does **not** download or execute any linked resources. It only displays information and manages/copies URLs.

---

## Technical Stack

- **Target Platform:** Windows
- **Language:** Python
- **GUI Framework:** Tkinter
- **Image Processing:** Pillow (PIL)
- **Standard Library First:** Rely on Python's standard library whenever possible. Avoid adding external dependencies unless thoroughly justified.

---

## Repository Structure

Keep UI, data handling, and application logic cleanly separated.

```text
app/
├── main.py
├── ui/
├── services/
├── models/
└── utils/

tools/
data/
assets/
tests/
```

---

## Remote Catalog Architecture

The remote catalog is the single source of truth for all remotely configurable resources. The application must **never** hard-code resource data inside Python scripts.

The catalog URL must be configurable.

### JSON Schema Architecture

```json
{
  "schema_version": 1,
  "app": {
    "catalog_version": "1.0.0",
    "changelog": ""
  },
  "minecraft": {
    "versions": []
  },
  "libraries": {},
  "java": [],
  "launcher": {},
  "other": []
}
```

#### Object Schemas

* **Minecraft Version Object:**
```json
{
  "id": "1.8.9",
  "name": "Minecraft 1.8.9",
  "description": "",
  "banner": "",
  "link": "",
  "warning": ""
}
```


* **Java Object:**
```json
{
  "version": "21",
  "name": "Java 21",
  "description": "",
  "link": ""
}
```


* **Other Resource / Patch Object:**
```json
{
  "name": "Example Patch",
  "description": "",
  "category": "patch",
  "link": "",
  "banner": "",
  "warning": ""
}
```



### Catalog Handling Rules

* Do **not** assume a fixed number of versions or resources.
* The UI must generate resource entries dynamically from the parsed catalog.
* Empty optional fields must be handled gracefully without visual glitches or crashes.

---

## Link Management Rules

1. **No WebViews:** External links must never be opened inside an embedded WebView.
2. **Opening Links:** Always use `webbrowser.open(url)` to launch the user's default system browser.
3. **Copying Links:** Copy the exact URL directly to the system clipboard upon user request.
4. **No Direct Execution:** The application must never automatically download, install, or execute files referenced by links.

---

## Catalog Updates & Caching Mechanics

The application must maintain a local copy of the last known valid catalog file.

### Update Workflow

1. Request the remote catalog asynchronously.
2. Save the incoming payload to a temporary file.
3. Parse and validate the schema strictly.
4. **Successful Validation:** Replace the local cached catalog file with the new file.
5. **Validation / Network Failure:** Discard the temporary file and retain the current valid local catalog.

> **CRITICAL RULE:** Never destroy or invalidate a working local catalog due to network timeouts, malformed JSON, incomplete HTTP responses, or connection dropouts.

### Failure Handling

* If the remote catalog cannot be retrieved, fallback silently to the local cached catalog.
* Display a non-intrusive UI indicator informing the user that the catalog could not be updated.
* Provide a button or option to open the direct catalog URL in the default browser for manual inspection/download.

### Update Notifications

* Compare the local catalog version string against the newly fetched remote version.
* When a newer version is detected:
* Display an update notice.
* Present the changelog to the user.
* Allow the user to dismiss/continue using the application freely.


* If the catalog includes warnings (e.g., reinstallation of libraries required), display the exact warning text provided by the catalog. Do not invent custom warning messages.

---

## Shared Libraries Handling

* Libraries represent a global, shared resource.
* **Do NOT** duplicate library URLs across individual Minecraft version entries.
* The catalog provides a global library package definition.
* If the catalog indicates that the shared library package has changed, present a clear notice advising the user to reinstall or update their library package.

---

## Java Path Helper Specification

The application provides a specialized utility tool to update the Java executable path used by the external launcher configuration.

### Processing Logic

1. Prompt the user to select a Java installation directory.
2. Recursively search the selected directory for `java.exe` (accepting arbitrary directory names and structures).
3. **Single Result:** Select the discovered `java.exe`.
4. **Multiple Results:** Prompt the user with a selection dialog to choose the desired `java.exe`.
5. Locate `vortex_launcher.conf` relative to the tool/application execution root.
6. Target and update **only** the `JavaPath = ...` configuration entry.
7. **Preserve** all other lines, comments, and values inside `vortex_launcher.conf` intact.

*Example target line:*

```ini
JavaPath = C:\Program Files\Java\jdk-21\bin\java.exe
```

> **Safety Rule:** If no `java.exe` is discovered, or if `vortex_launcher.conf` is missing, abort the operation immediately and display a clear error message. Do not modify or write files on failure.

---

## UI & Visual Design Requirements

* The interface must feel like a modern, clean, lightweight utility rather than a raw JSON/config editor.
* Use a tabbed or multi-section layout containing:
1. **Minecraft**
2. **Libraries**
3. **Java**
4. **Other Files & Patches**
5. **Updates / About**


* Render resource entries using reusable UI components/cards.

### Card Component Architecture

A standard resource card should dynamically display:

* Resource Name
* Description
* Optional Banner Image
* Warning Notice (if present)
* **Open** Button
* **Copy Link** Button

> **Code Organization:** Do not duplicate or hard-code UI blocks for specific resources. Everything must be generated dynamically from catalog data.

---

## Image Handling Guidelines

* Banners are strictly optional.
* Fetch remote images asynchronously to prevent freezing or blocking the Tkinter main UI thread.
* If an image fails to load or is unreachable:
* Do not throw an exception or crash.
* Render a local fallback placeholder image.
* Keep the rest of the resource card functional.


* Implement a local caching mechanism for remote banner images.

---

## Error Handling & Logging

* **User Communication:** All user-facing error messages must be clear, simple, and actionable.
* **No Tracebacks in UI:** Never expose raw Python tracebacks or stack traces directly to end users in popups or dialogs.
* **Logging:** Log diagnostic details internally during development/debugging.
* Must gracefully handle at least:
* Lack of internet connectivity / offline state
* Network timeouts
* Malformed or invalid JSON payloads
* Missing catalog fields or schema mismatches
* Invalid or malformed URLs
* Missing local catalog cache
* Missing `vortex_launcher.conf`
* Missing or multiple `java.exe` instances



---

## Security Guidelines

* **Untrusted Input:** Treat all incoming remote catalog data as untrusted input. Sanitize and validate before processing.
* **Execution Prevention:** The application must **never** execute local or remote files referenced in the catalog.
* **Zero Secrets:** Never commit passwords, API keys, access tokens, credentials, or private authenticated URLs into source code or public repositories.

---

## Development Guidelines

Before writing or modifying code:

1. Inspect the existing codebase and understand the architectural patterns.
2. Reuse existing utility functions and UI components whenever possible.
3. Apply the smallest reasonable change required to solve the task.
4. Test the affected functionality thoroughly before committing.
5. Avoid unnecessary rewrites of working modules.
6. Avoid speculative abstractions or premature generalizations.
7. Do not introduce external dependencies for tasks natively supported by the Python Standard Library.

---

## Git Conventions

Keep commits focused, small, and logical.

### Commit Prefixes

* `feat:` New feature implementation
* `fix:` Bug fix
* `ui:` User interface adjustments or layout changes
* `refactor:` Code reorganization without functional changes
* `test:` Adding or updating tests
* `docs:` Documentation updates
* `chore:` Maintenance, build setup, or dependency updates

### Ignore & Never Commit

* Virtual environments (`.venv/`, `env/`)
* Cache directories (`__pycache__/`, `.pytest_cache/`)
* Compiled binaries or temporary files (`.pyc`, `.exe`, `.tmp`)
* Environment variables, secrets, or local catalogs with sensitive data

---

## Definition of Done (DoD)

A task or feature is considered complete **only** when:

* It strictly adheres to all specifications in this document.
* It does not break existing application features.
* All edge cases and errors are handled gracefully.
* The UI remains intuitive, responsive, and functional.
* No unneeded external dependencies have been introduced.
* Relevant unit or integration tests are added or updated.