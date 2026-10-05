# Architecture

## Overview

The GitHub Issue Snapshot Connector is a small Python application with three main responsibilities:

1. Fetch one page of open issues from a public GitHub repository.
2. Store issue snapshots persistently in SQLite.
3. Read previously saved issues without making another GitHub API request.

The application separates the reusable connector logic from the command-line interface.

## Components

### `connector.py`

Contains the core application logic and exposes two reusable functions:

- `import_issues(repo, db_path)` — fetches open issues from GitHub and stores them in SQLite.
- `read_issues(repo, db_path)` — retrieves saved issues from SQLite without calling GitHub.

It also contains `create_database(db_path)`, which creates the database table when needed.

### `cli.py`

Provides a small command-line interface around the reusable connector functions.

Supported operations:

```bash
python3 cli.py import owner/repository
python3 cli.py read owner/repository
```

A custom SQLite path can be supplied with `--db`.

### SQLite

SQLite provides persistent local storage without requiring a separate database service.

## Data Flow

### Import

```text
CLI
 |
 v
import_issues()
 |
 v
GitHub Issues API
 |
 v
Filter out pull requests
 |
 v
SQLite UPSERT
 |
 v
JSON-compatible result
```

The connector requests one page of open records from GitHub. Because GitHub's Issues API can also return pull requests, records containing the `pull_request` field are removed before storage.

Each remaining issue is inserted into SQLite. If the repository and issue number already exist, the stored title and URL are updated.

### Read

```text
CLI
 |
 v
read_issues()
 |
 v
SQLite
 |
 v
JSON-compatible result
```

The read path does not call GitHub. This allows previously imported data to remain available across process restarts and when no new API request is made.

## Database Schema

The `issues` table contains:

| Column | Type | Purpose |
| --- | --- | --- |
| `repository` | TEXT | Repository in `owner/name` format |
| `issue_number` | INTEGER | GitHub issue number |
| `title` | TEXT | Issue title |
| `url` | TEXT | GitHub issue URL |

The primary key is:

```text
(repository, issue_number)
```

The composite key is used because issue numbers are unique within a repository but not globally unique across GitHub.

## Duplicate Handling

Imports use SQLite's `ON CONFLICT ... DO UPDATE`.

This means importing the same repository repeatedly does not create duplicate records. If an existing issue has changed, its title and URL can be updated.

## Configuration

The default database path is:

```text
issues.db
```

Both reusable connector functions accept a different `db_path`, and the CLI exposes the same configuration through:

```bash
--db <path>
```

## Error Handling

GitHub HTTP and network failures are caught as `requests.RequestException`.

Instead of allowing the request exception to terminate the application, `import_issues()` returns a JSON-compatible result containing:

- `success: false`
- the requested repository
- an error message

For example, a nonexistent repository produces a GitHub 404 error that is returned to the caller.

## Testing Strategy

Automated tests use pytest and mocked GitHub responses.

The tests cover:

- importing and reading issues
- excluding pull requests
- repeated imports without duplicates
- API failure handling

Temporary SQLite databases are used during tests so the test suite does not modify the normal application database.

A real GitHub API request is used separately when demonstrating the connector.

## Tradeoffs

### SQLite instead of a server database

SQLite keeps the project small and portable while still providing persistent storage and uniqueness constraints.

### One page only

The connector intentionally fetches one API page. Pagination was not implemented because it is outside the challenge scope.

### Public repositories without authentication

The implementation does not require a GitHub token for the requested public-read use case. This keeps setup simple, with the tradeoff that GitHub's unauthenticated API rate limits apply.

### Synchronous requests

The connector uses a normal synchronous HTTP request. For a single-page import this is simpler than introducing asynchronous networking.

### Snapshot retention

The importer inserts new records and updates matching records. It does not delete previously saved records merely because they are absent from a later API response. Deletion/synchronization semantics were not required for this challenge and would require a clearer definition of snapshot behavior.
