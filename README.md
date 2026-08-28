# Muelltonnen Security

A local, camera-based security system that watches a trash bin ("Muelltonne") using a
YOLO11 object detector. When it detects a person approaching the bin from behind
(lower and to the right of it in frame), it saves a snapshot and a short before/after
video clip, and exposes both plus the application logs through a password-protected,
responsive web UI on the local network.

## How it works

The system is split into a Python backend (camera capture, detection, recording,
API server) and a React frontend (the browser UI). They communicate over HTTP/JSON.

### Backend (`app/`, `main.py`)

- **[main.py](main.py)** — entry point. Parses CLI args (`--config PATH`, `-h`/`--help`),
  opens the webcam, runs the detection loop, and starts the web server in a background
  thread.
- **[app/config.py](app/config.py)** — central configuration (camera settings, timing,
  trigger thresholds, storage paths, web credentials), loaded from a JSON file. See [Configuration](#configuration) below.
- **[app/ring_buffer.py](app/ring_buffer.py)** — a thread-safe fixed-size ring buffer
  that continuously stores raw (unannotated) frames. Its size is
  `fps * (pre_time + post_time)` seconds so it always holds enough history for the
  pre-event portion of a recording.
- **[app/trigger.py](app/trigger.py)** — parses YOLO detection results and decides
  whether a recording should be triggered: a `Person` box counts as a trigger when its
  center is lower and further right than a `German Trashbin` box center, within
  `max(60px, 10% of frame dimension)` per axis.
- **[app/recorder.py](app/recorder.py)** — `EventRecorder` state machine. On trigger it
  creates a timestamp-named directory, immediately saves the annotated frame as
  `trigger.jpeg`, then keeps collecting frames for `post_time` seconds before writing
  the combined pre+post clip as `video.mp4` in that directory.
- **[app/logging_provider.py](app/logging_provider.py)** — configures logging to both
  the console and a rotating logfile at `data/logs/app.log`.
- **[app/live_stream.py](app/live_stream.py)** — `StreamHub`, a thread-safe hand-off
  point for the live view. The capture loop publishes newly annotated frames into it
  only while `has_viewers` is true (i.e. the Live Stream tab is open), so no extra
  annotation work happens otherwise.
- **[app/webapp/server.py](app/webapp/server.py)** — a Flask app that exposes a small
  JSON API (`/api/session`, `/api/login`, `/api/logout`, `/api/captures`, `/api/logs`,
  `/api/captures/<name>` for deletion, `/captures/<name>/<file>` for media,
  `/api/stream`) and serves the built React frontend as static files. Login is
  password-based (`WEBUI_PASSWORD`), backed by a server-side session cookie, with a
  simple brute-force lockout after repeated failed attempts.
  `/api/stream` serves an MJPEG (`multipart/x-mixed-replace`) feed of the annotated
  frames, registering/deregistering a viewer with `StreamHub` for the lifetime of the
  HTTP connection.

### Frontend (`frontend/`)

A Vite + React single-page app that talks to the Flask API above.

- **[frontend/src/App.jsx](frontend/src/App.jsx)** — checks the session on load and
  switches between the login screen and the dashboard.
- **[frontend/src/components/LoginPage.jsx](frontend/src/components/LoginPage.jsx)** —
  password login form.
- **[frontend/src/components/Dashboard.jsx](frontend/src/components/Dashboard.jsx)** —
  tab navigation between "Captures", "Logs" and "Live Stream".
- **[frontend/src/components/CapturesGrid.jsx](frontend/src/components/CapturesGrid.jsx)**
  — polls `/api/captures` and renders timestamped capture cards in a responsive grid.
- **[frontend/src/components/CaptureCard.jsx](frontend/src/components/CaptureCard.jsx)**
  — displays each trigger frame with play and delete actions. Video playback is loaded
  only after Play is pressed.
- **[frontend/src/components/LogViewer.jsx](frontend/src/components/LogViewer.jsx)** —
  polls `/api/logs` and displays the live-tailing logfile content.
- **[frontend/src/components/LiveStreamView.jsx](frontend/src/components/LiveStreamView.jsx)**
  — mounted only while the "Live Stream" tab is active; renders an `<img>` pointed at
  `/api/stream`, showing a "Loading" message until the first frame arrives. Switching
  tabs unmounts it, closing the stream connection so the backend stops annotating
  frames.
- **[frontend/src/api.js](frontend/src/api.js)** — fetch helpers for the JSON API.

The layout is responsive and usable on phones, tablets, and desktops connected to the
same local network as the device running the camera.

### Data layout

```
data/
  captures/
    <date>-<time>/
      trigger.jpeg
      video.mp4
  logs/
    app.log   # rotating logfile, also shown live in the web UI
```

## Configuration

All settings (camera, timing, trigger thresholds, storage, web UI) live in a JSON file.
The repo ships with
[configurations/default_config.json](configurations/default_config.json), grouped by
function and generated by
[configurations/generate_default_config.py](configurations/generate_default_config.py)
from [app/config.py](app/config.py)'s dataclass defaults. Re-run that script (`uv run
python configurations/generate_default_config.py`) any time you want to regenerate it
(e.g. to get a fresh `web_secret_key`).

To customize settings, copy `configurations/default_config.json` to your own file (e.g.
`configurations/my_config.json`), edit the values you need, and pass its path to
`main.py`:

```bash
uv run python main.py --config configurations/my_config.json
# or an absolute path, on Windows or Linux:
uv run python main.py --config /path/to/my_config.json
```

If `--config` is omitted, `configurations/default_config.json` is used. If the given
path doesn't exist or isn't valid JSON, an error is logged and `main.py` exits. Run
`uv run python main.py --help` for the full CLI usage.

`model_path` and `data_dir` may be relative (resolved against the project root) or
absolute paths.

## Development: build and run

### Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js (LTS) and npm, for the frontend
- A connected USB webcam

### Backend setup

```bash
uv sync
```

This installs all Python dependencies (Ultralytics/YOLO, ncnn, Flask, etc.) from
[pyproject.toml](pyproject.toml)/[uv.lock](uv.lock) into a local `.venv`.

### Frontend setup

```bash
cd frontend
npm install
```

### Running for development

You need the Flask backend and the Vite dev server running at the same time; the dev
server proxies API/media calls to Flask (see [frontend/vite.config.js](frontend/vite.config.js)).

1. Start the backend (camera loop + API on port 5000):

   ```bash
   uv run python main.py
   ```

2. In a second terminal, start the frontend dev server with hot reload:

   ```bash
   cd frontend
   npm run dev
   ```

3. Open the URL printed by Vite (typically `http://localhost:5173`) in your browser.
   Log in with the password from `web_password` in your config file (defaults to
   `changeme` — set a real value, see [Configuration](#configuration) above).

## Testing

### Backend tests

```bash
uv run pytest
```

Runs the [pytest](https://docs.pytest.org/) suite in [tests/](tests/), which covers
`app/config.py`, `app/trigger.py`, `app/ring_buffer.py`, `app/recorder.py` (with
`cv2` mocked at the boundary, so no real video codec is needed), `app/live_stream.py`,
`app/logging_provider.py`, the pure helpers in `main.py`, and the Flask API in
`app/webapp/server.py` (auth, session handling, brute-force lockout, path-traversal
guards) via Flask's test client. The camera/model capture loop itself isn't covered
here — it needs real hardware — but the decision logic it delegates to is.

### Frontend tests

```bash
cd frontend
npm test
```

Runs the [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/react)
suite (colocated `*.test.jsx`/`*.test.js` files next to each component and
`api.js`). Use `npm run test:watch` for a watch-mode run while developing.

### Continuous integration

[.github/workflows/test.yml](.github/workflows/test.yml) runs both suites on every
push and pull request.

## Build and deploy

For a real deployment, the frontend is built once into static files and served
directly by Flask — there's no need to run the Vite dev server on the target device.

1. Build the frontend:

   ```bash
   cd frontend
   npm run build
   ```

   This produces `frontend/dist/`, which [app/webapp/server.py](app/webapp/server.py)
   serves automatically (static assets under `/assets/...`, everything else falls back
   to `index.html`). Rebuild and redeploy this step whenever frontend source changes.

2. Install Python dependencies on the target machine:

   ```bash
   uv sync --no-dev
   ```

3. Create a production configuration file and set at least the password:

   ```bash
   cp configurations/default_config.json configurations/production_config.json
   ```

   Edit `configurations/production_config.json` and set `web_password` to a strong
   value under `"web_ui"`. `web_secret_key` (which signs session cookies) is already
   populated with a random value by
   [configurations/generate_default_config.py](configurations/generate_default_config.py);
   keep using the same config file across restarts so sessions aren't invalidated, or
   regenerate it deliberately to force everyone to log in again.

4. Run the application:

   ```bash
   uv run python main.py --config configurations/production_config.json
   ```

   This starts the detection loop and the web server (bound to `0.0.0.0:5000` by
   default) in one process. Anyone on the same local network can then browse to
   `http://<device-ip>:5000` and log in.

5. (Optional) Run it as a persistent service, e.g. with a `systemd` unit that executes
   `uv run python main.py --config configurations/production_config.json` from the
   project directory, so it starts automatically on boot and restarts on failure.

**Note:** the built-in Flask server is fine for a small local-network tool like this,
but is not a hardened production WSGI server. If you expose this beyond a trusted local
network, put it behind a reverse proxy with TLS (e.g. nginx/Caddy) instead of relying on
plain HTTP.
