
# Backend Project Documentation

This backend project is built using **FastAPI** and **Poetry** for dependency management. It includes API endpoints for user management, team operations, and monitoring, with robust configurations for running in different environments.

## Table of Contents
1. [Installation and Running](#installation-and-running)
   - [Poetry](#poetry)
   - [Docker](#docker)
2. [Project Structure](#project-structure)
3. [Configuration](#configuration)
4. [API Endpoints](#api-endpoints)
5. [Migrations](#migrations)
6. [Testing](#testing)

## Installation and Running

### Poetry

This project uses **Poetry** for dependency management.

To set up and run the project locally, use the following commands:

```bash
poetry install
poetry run python -m backend
```

This will start the server on the configured host.

- Swagger documentation can be accessed at: `/api/docs`.
- Read more about **Poetry** here: [Poetry Documentation](https://python-poetry.org/).

### Docker

You can start the project using **Docker** with this command:

```bash
docker compose up --build
```

For development with autoreload and exposed ports, add `-f deploy/docker-compose.dev.yml`:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.dev.yml --project-directory . up --build
```

- This command exposes the web application on port 8000, mounts the current directory, and enables autoreload.
- You must rebuild the image every time you modify `poetry.lock` or `pyproject.toml` with the command:
  
```bash
docker compose build
```

## Project Structure

The project structure is organized as follows:

```bash
backend/
├── conftest.py        # Fixtures for all tests.
├── db                 # Database configurations and models
│   ├── dao            # Data Access Objects (interact with the database).
│   └── models         # ORM models.
├── __main__.py        # Startup script (starts uvicorn).
├── services           # External services like RabbitMQ or Redis.
├── settings.py        # Main project settings.
├── static             # Static content.
├── tests              # Tests for the project.
└── web                # Web server configuration and API handlers.
    ├── api # API routes and handlers.
    │   │
    │   v1 # Api version      
    │   └── router.py  # Main API router.
    ├── application.py # FastAPI application configuration.
    └── lifespan.py    # Startup and shutdown lifecycle events.
```

## Configuration

This application can be configured using environment variables.

1. Create a `.env` file in the root directory.
2. Environment variables should start with the `BACKEND_` prefix.

For example, if you have a variable `random_parameter` in `backend/settings.py`, you would configure it in `.env` as:

```bash
BACKEND_RANDOM_PARAMETER="your_value"
```

Example `.env` file:

```bash
# GLobal configuration
BACKEND_RELOAD="True"
BACKEND_PORT="8000"
BACKEND_ENVIRONMENT="dev"

# Database configuration
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=5432
BACKEND_DB_USER=backend
BACKEND_DB_PASS=backend
BACKEND_DB_BASE=backend
BACKEND_DB_ECHO=False

# Mail configuration
BACKEND_MAIL_SERVER=
BACKEND_MAIL_PORT=
BACKEND_MAIL_USERNAME=
BACKEND_MAIL_PASSWORD=
BACKEND_EMAIL_FROM=

# JWT configuration
BACKEND_SECRET_KEY=
```

Read more about Pydantic's **BaseSettings** class [here](https://pydantic-docs.helpmanual.io/usage/settings/).

## API Endpoints

The following API endpoints are available in the project:

### User Endpoints

- **POST** `/api/v1/user/auth`: Authenticate a user.
- **GET** `/api/v1/user/me`: Get current user info.
- **GET** `/api/v1/user/{id}`: Get user details by user ID.
- **PATCH** `/api/v1/user/settings`: Update user settings.
- **POST** `/api/v1/user/settings/email/confirm`: Confirm user's email address.
- **POST** `/api/v1/user`: Create a new user.
- **POST** `/api/v1/user/verify/send`: Send verification email.
- **POST** `/api/v1/user/verify`: Verify user.
- **POST** `/api/v1/user/password/reset/send`: Send password reset email.
- **POST** `/api/v1/user/password/reset`: Reset user password.

### Team Endpoints

- **POST** `/api/v1/team`: Create a new team.
- **PUT** `/api/v1/team`: Update an existing team.
- **GET** `/api/v1/team/{team_id}`: Get details of a team by team ID.
- **DELETE** `/api/v1/team/{team_id}`: Delete a team by team ID.
- **GET** `/api/v1/teams`: Get list of all teams for the user.
- **POST** `/api/v1/team/invitation`: Send an invitation to a new member.
- **GET** `/api/v1/team/invitation/{invitation_id}`: Get details of an invitation.
- **GET** `/api/v1/team/{team_id}/invitations`: Get list of all invitations for a team.
- **PUT** `/api/v1/team/invitation/{invitation_id}/toggle`: Toggle the status of an invitation.
- **DELETE** `/api/v1/team/invitation/{invitation_id}/delete`: Delete an invitation.


### Monitoring and Metrics

- **GET** `/api/v1/monitoring/health`: Health check for the service.
- **GET** `/metrics`: Expose service metrics.

## Migrations

For database migrations, use Alembic.

### Applying Migrations

To run all migrations or until a specific revision ID:

```bash
alembic upgrade "<revision_id>"
```

To apply all pending migrations:

```bash
alembic upgrade head
```

### Reverting Migrations

To revert to a specific migration:

```bash
alembic downgrade "<revision_id>"
```

To revert all migrations:

```bash
alembic downgrade base
```

### Generating Migrations

- For automatic change detection:

```bash
alembic revision --autogenerate
```

- For generating an empty migration file:

```bash
alembic revision
```

## Running Tests

You can run the tests either locally or in Docker.

### Running Tests Locally

1. Start a PostgreSQL database, for example using Docker:

```bash
docker run -p "5432:5432" -e "POSTGRES_PASSWORD=backend" -e "POSTGRES_USER=backend" -e "POSTGRES_DB=backend" postgres:16.3-bullseye
```

2. Run the tests using pytest:

```bash
pytest -vv .
```

### Running Tests in Docker

To run tests inside a Docker container:

```bash
docker compose run --build --rm api pytest -vv .
docker compose down
```


