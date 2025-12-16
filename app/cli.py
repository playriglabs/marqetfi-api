"""CLI commands for application management."""

import asyncio

import typer

app = typer.Typer(help="Application CLI commands")


@app.command()
def init_db() -> None:
    """Initialize database tables."""
    from app.core.database import init_db as _init_db

    typer.echo("Initializing database...")
    asyncio.run(_init_db())
    typer.echo("✅ Database initialized successfully!")


@app.command()
def run_migrations() -> None:
    """Run database migrations."""
    import subprocess

    typer.echo("Running database migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)

    if result.returncode == 0:
        typer.echo("✅ Migrations completed successfully!")
    else:
        typer.echo(f"❌ Migration failed: {result.stderr}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create_migration(message: str) -> None:
    """Create a new database migration.

    Args:
        message: Migration description
    """
    import subprocess

    typer.echo(f"Creating migration: {message}")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", message],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        typer.echo("✅ Migration created successfully!")
        typer.echo(result.stdout)
    else:
        typer.echo(f"❌ Failed to create migration: {result.stderr}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create_superuser(
    email: str = typer.Option(..., prompt=True),
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Create a superuser account."""
    from app.core.database import get_session_maker
    from app.core.security import get_password_hash
    from app.models.user import User

    async def _create_superuser() -> None:
        AsyncSessionLocal = get_session_maker()
        async with AsyncSessionLocal() as session:
            # Check if user exists
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                typer.echo(f"❌ User with email {email} already exists!", err=True)
                raise typer.Exit(code=1)

            # Create superuser
            user = User(
                email=email,
                username=username,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
            )
            session.add(user)
            await session.commit()

            typer.echo(f"✅ Superuser {username} created successfully!")

    asyncio.run(_create_superuser())


@app.command()
def run_server(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
) -> None:
    """Run development server."""
    import uvicorn

    typer.echo(f"Starting server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def run_worker(
    concurrency: int = typer.Option(4, help="Number of worker processes"),
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Run Celery worker."""
    import subprocess

    typer.echo(f"Starting Celery worker with {concurrency} processes...")
    result = subprocess.run(
        [
            "celery",
            "-A",
            "app.tasks.celery_app",
            "worker",
            f"--concurrency={concurrency}",
            f"--loglevel={loglevel}",
        ]
    )

    raise typer.Exit(code=result.returncode)


@app.command()
def run_beat() -> None:
    """Run Celery beat scheduler."""
    import subprocess

    typer.echo("Starting Celery beat scheduler...")
    result = subprocess.run(
        [
            "celery",
            "-A",
            "app.tasks.celery_app",
            "beat",
            "--loglevel=info",
        ]
    )

    raise typer.Exit(code=result.returncode)


@app.command()
def test(
    coverage: bool = typer.Option(True, help="Run with coverage"),
    verbose: bool = typer.Option(True, help="Verbose output"),
) -> None:
    """Run tests."""
    import subprocess

    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term", "--cov-report=html"])

    typer.echo("Running tests...")
    result = subprocess.run(cmd)

    raise typer.Exit(code=result.returncode)


@app.command()
def lint() -> None:
    """Run code linters."""
    import subprocess

    typer.echo("Running linters...")

    # Run Ruff
    typer.echo("→ Running Ruff...")
    subprocess.run(["ruff", "check", "app/", "tests/"])

    # Run Black
    typer.echo("→ Running Black...")
    subprocess.run(["black", "--check", "app/", "tests/"])

    # Run isort
    typer.echo("→ Running isort...")
    subprocess.run(["isort", "--check-only", "app/", "tests/"])

    # Run MyPy
    typer.echo("→ Running MyPy...")
    subprocess.run(["mypy", "app/"])

    typer.echo("✅ Linting complete!")


@app.command()
def format_code() -> None:
    """Format code with Black and isort."""
    import subprocess

    typer.echo("Formatting code...")

    subprocess.run(["black", "app/", "tests/"])
    subprocess.run(["isort", "app/", "tests/"])

    typer.echo("✅ Code formatted!")


if __name__ == "__main__":
    app()

