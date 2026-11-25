# Network_Programming_Coursework

[![CI](https://github.com/bury7/Network_Programming_Coursework/actions/workflows/sample-ci.yml/badge.svg)](https://github.com/bury7/Network_Programming_Coursework/actions/workflows/sample-ci.yml)
[![Docker Hub](https://img.shields.io/docker/image-size/bury7/network-programming-coursework/latest?label=docker%20hub)](https://hub.docker.com/r/bury7/network-programming-coursework)

This is a repository with the coursework I did as part of a network programming course at the university.

The image is published on Docker Hub: [bury7/network-programming-coursework](https://hub.docker.com/r/bury7/network-programming-coursework).

## Task

1. Create a separate repository for the project code.
2. Develop an integrated Python project that meets the following requirements:
   - develop a web server with one of the frameworks, following the tasks of Lab 2. The web server must:
     - handle at least one path;
     - authenticate requests with Basic Auth;
   - integrate the REST API from Lab 3 into the project;
   - cover one of the functions with unit tests written with `pytest`;
   - write CI with GitHub Actions that builds the web project into a container and publishes it on Docker Hub, following the example https://github.com/dandrushko/python-lab.
3. Optional: check that the web application starts from the published container.

## Solution

A Flask web server where every request needs HTTP Basic authentication. Users and the product catalog are stored in SQLite; passwords are stored as hashes.

| Path                  | Methods                        | From  | What it does                                   |
|-----------------------|--------------------------------|-------|------------------------------------------------|
| `/`                   | `GET`                          | Lab 2 | Returns "Hello World!"                         |
| `/currency?today`     | `GET`                          | Lab 2 | USD rate for today from the NBU API            |
| `/currency?yesterday` | `GET`                          | Lab 2 | USD rate for the previous day from the NBU API |
| `/items`              | `GET`, `POST`, `PUT`, `DELETE` | Lab 3 | List, create, replace or delete all products   |
| `/items/<id>`         | `GET`, `PUT`, `DELETE`         | Lab 3 | Read, update or delete one product             |

`/currency` answers in JSON or XML when the request has `Content-Type: application/json` or `application/xml`, and in plain text (`USD - 45,3541`) otherwise. Products are JSON objects with `name`, `price` and `color`, for example `{"name": "T-shirt", "price": 499.99, "color": "black"}`. Errors come back as JSON, for example `{"error": "Item 42 not found"}`.

| Path                                                               | What it is                                                     |
|--------------------------------------------------------------------|----------------------------------------------------------------|
| [src/coursework/](src/coursework)                                  | Flask app: Basic Auth, database, currency and items endpoints  |
| [tests/](tests)                                                    | `pytest` tests, including unit tests for `parse_item`          |
| [Dockerfile](Dockerfile)                                           | Image built with uv from `uv.lock`, runs gunicorn on port 5000 |
| [.github/workflows/sample-ci.yml](.github/workflows/sample-ci.yml) | CI: checks and tests, then build and push to Docker Hub        |

## How to run

### Locally
Install [uv](https://docs.astral.sh/uv/), then from the repository root:

```bash
uv sync
uv run flask --app coursework add-user admin
uv run flask --app coursework run
```

The server listens on http://127.0.0.1:5000. `add-user` asks for a password; run it again to change the password.

```bash
curl -u admin:password http://127.0.0.1:5000/
curl -u admin:password "http://127.0.0.1:5000/currency?today"
curl -u admin:password -H "Content-Type: application/json" "http://127.0.0.1:5000/currency?yesterday"
curl -u admin:password -H "Content-Type: application/json" \
     --data '{"name": "T-shirt", "price": 499.99, "color": "black"}' http://127.0.0.1:5000/items
curl -u admin:password http://127.0.0.1:5000/items
```

### Tests
```bash
uv run pytest
```

### Docker
`ADMIN_USERNAME` and `ADMIN_PASSWORD` create (or update) a user when the app starts. Without them the server still starts, but no user exists, so every request gets `401 Unauthorized`.

```bash
docker build -t coursework .
docker run -p 5000:5000 -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=password coursework
```

Data lives in `/app/instance` inside the container and is lost when the container is removed. Add `-v coursework-data:/app/instance` to keep it.

### CI and Docker Hub
The workflow runs on every pull request and every push to `main`. It checks formatting, lint and types, and runs the tests. On a push to `main` it then builds the image and pushes it to Docker Hub as [`bury7/network-programming-coursework`](https://hub.docker.com/r/bury7/network-programming-coursework) with the `latest` tag and the commit SHA as tags.

One-time setup:

1. On Docker Hub open **Account settings** → **Personal access tokens** → **Generate new token** with **Read & Write** access.
2. In this GitHub repository open **Settings** → **Secrets and variables** → **Actions** and add two repository secrets:
   - `DOCKERHUB_USERNAME` — your Docker Hub username;
   - `DOCKERHUB_TOKEN` — the token from step 1.
3. Push to `main` and watch the run in the **Actions** tab.

### Run the published image
```bash
docker run -p 5000:5000 -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=password bury7/network-programming-coursework
curl -u admin:password http://127.0.0.1:5000/
```
