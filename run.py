"""Application entry point."""

import argparse
import signal
import subprocess
import sys
import time
from typing import Any

import uvicorn

from app.config import get_settings

settings = get_settings()

# Global process list for cleanup
processes: list[subprocess.Popen[bytes]] = []
_shutting_down = False


def run_server() -> None:
    """Run FastAPI server."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


def run_celery_worker() -> None:
    """Run Celery worker."""
    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "app.tasks.celery_app",
            "worker",
            "--loglevel=info",
        ],
        check=True,
    )


def run_celery_beat() -> None:
    """Run Celery beat scheduler."""
    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "app.tasks.celery_app",
            "beat",
            "--loglevel=info",
        ],
        check=True,
    )


def signal_handler(sig: int, frame: Any) -> None:
    """Handle shutdown signals."""
    global _shutting_down

    if _shutting_down:
        # Force kill on second interrupt
        print("\n⚠️  Force killing all processes...")
        for process in processes:
            if process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=1)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    pass
        sys.exit(1)

    _shutting_down = True
    print("\n🛑 Shutting down services gracefully...")

    # Terminate all processes
    for process in processes:
        if process.poll() is None:  # Process is still running
            try:
                process.terminate()
            except ProcessLookupError:
                pass

    # Wait for graceful shutdown (max 3 seconds)
    start_time = time.time()
    timeout = 3.0

    while time.time() - start_time < timeout:
        all_done = True
        for process in processes:
            if process.poll() is None:
                all_done = False
                break
        if all_done:
            print("✅ All services stopped gracefully")
            sys.exit(0)
        time.sleep(0.1)

    # Force kill if still running
    print("⚠️  Some processes didn't stop, force killing...")
    for process in processes:
        if process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=1)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                pass

    print("✅ All services stopped")
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run MarqetFi API services")
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Run only the FastAPI server",
    )
    parser.add_argument(
        "--worker-only",
        action="store_true",
        help="Run only the Celery worker",
    )
    parser.add_argument(
        "--beat-only",
        action="store_true",
        help="Run only the Celery beat scheduler",
    )
    parser.add_argument(
        "--no-beat",
        action="store_true",
        help="Run server and worker without beat",
    )

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.server_only:
        run_server()
    elif args.worker_only:
        run_celery_worker()
    elif args.beat_only:
        run_celery_beat()
    else:
        # Run all services
        print("Starting MarqetFi API services...")
        print(f"  - FastAPI server: http://{settings.HOST}:{settings.PORT}")
        print("  - Celery worker: running")
        if not args.no_beat:
            print("  - Celery beat: running")
        print("\nPress Ctrl+C to stop all services\n")

        # Start FastAPI server in subprocess
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                settings.HOST,
                "--port",
                str(settings.PORT),
            ]
            + (["--reload"] if settings.DEBUG else []),
        )
        processes.append(server_process)

        # Start Celery worker in subprocess (use solo pool for better shutdown)
        worker_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "app.tasks.celery_app",
                "worker",
                "--loglevel=info",
                "--pool=solo",  # Better shutdown handling
            ],
        )
        processes.append(worker_process)

        # Start Celery beat (if not disabled)
        if not args.no_beat:
            beat_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "app.tasks.celery_app",
                    "beat",
                    "--loglevel=info",
                ],
            )
            processes.append(beat_process)

        # Wait for all processes
        try:
            while True:
                # Check if any process is still running
                running = [p for p in processes if p.poll() is None]
                if not running:
                    break
                # Wait a bit before checking again
                time.sleep(0.5)
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
