"""
Smoke test: confirms the application actually starts and is reachable
over a real network call -- not simulated via TestClient. Run this
BEFORE the functional test suite (tests/test_*_generated.py), as a
separate "is the app alive" gate.

Usage:
    python tests/smoke_test_health.py
"""
import subprocess
import sys
import time
import requests

HOST = "127.0.0.1"
PORT = 8001  # different port from manual dev runs, avoids collisions
HEALTH_URL = f"http://{HOST}:{PORT}/health"
STARTUP_TIMEOUT_SECONDS = 10


def main():
    print(f"Starting the application as a real subprocess on port {PORT}...")
    server_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", HOST,
            "--port", str(PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        deadline = time.time() + STARTUP_TIMEOUT_SECONDS
        last_error = None
        while time.time() < deadline:
            try:
                response = requests.get(HEALTH_URL, timeout=1)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    print(f"PASS: application is running and reachable at {HEALTH_URL}")
                    print(f"Response: {response.status_code} {response.json()}")
                    return 0
                else:
                    last_error = f"Unexpected response: {response.status_code} {response.text}"
            except requests.exceptions.ConnectionError as exc:
                last_error = f"Not reachable yet: {exc}"
            time.sleep(0.5)

        print(f"FAIL: application did not become healthy within {STARTUP_TIMEOUT_SECONDS}s.")
        print(f"Last error: {last_error}")
        stdout, stderr = server_process.communicate(timeout=2)
        print("---- server stdout ----")
        print(stdout.decode(errors="replace"))
        print("---- server stderr ----")
        print(stderr.decode(errors="replace"))
        return 1

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    sys.exit(main())
