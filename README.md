# GitHub Issue Snapshot Connector

A small Python command-line application that imports one page of open issues from a public GitHub repository, stores them in SQLite, and reads the saved issues without making another GitHub API request.

## Features

- Accepts a GitHub repository in `owner/name` format
- Fetches one page of open issues from the GitHub API
- Excludes pull requests returned by GitHub's Issues API
- Stores repository, issue number, title, and URL in SQLite
- Updates existing records instead of creating duplicates
- Reads saved issues from SQLite without calling GitHub
- Supports a configurable database path
- Returns JSON-compatible results
- Handles GitHub API failures with a useful error result
- Includes automated tests using mocked API responses

## Prerequisites

- Python 3.9 or newer
- pip
- Internet access for real GitHub imports

A GitHub token is not required for public repository reads.

## Setup

Clone the repository and move into the project directory:

```bash
git clone <repository-url>
cd rocketride-github-connector
```

Optional but recommended: create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

### Import issues from GitHub

```bash
python3 cli.py import octocat/Hello-World
```

Example result:

```json
{
  "success": true,
  "repository": "octocat/Hello-World",
  "imported_count": 23
}
```

The exact count can change because the repository's open issues change over time.

### Read saved issues

```bash
python3 cli.py read octocat/Hello-World
```

The read operation uses the local SQLite database and does not call GitHub.

Example:

```json
{
  "success": true,
  "repository": "octocat/Hello-World",
  "issues": [
    {
      "number": 123,
      "title": "Example issue",
      "url": "https://github.com/octocat/Hello-World/issues/123"
    }
  ]
}
```

### Use a different database path

```bash
python3 cli.py import octocat/Hello-World --db custom.db
python3 cli.py read octocat/Hello-World --db custom.db
```

## Tests

Run the automated test suite with:

```bash
python3 -m pytest -v
```

The tests verify:

- importing and reading saved issues
- filtering pull requests from the Issues API response
- repeated imports do not create duplicate records
- GitHub API failures return an error result

The API is mocked in the automated tests so the test suite does not depend on a live GitHub request.

## Design Notes

The connector uses two reusable functions:

- `import_issues(repo, db_path)` fetches and stores open issues
- `read_issues(repo, db_path)` reads previously stored issues locally

SQLite was chosen because it provides persistent storage with no separate database server or setup. A composite primary key of repository and issue number uniquely identifies an issue. SQLite's `ON CONFLICT ... DO UPDATE` behavior allows repeated imports to update existing issues instead of creating duplicates.

The project intentionally handles only one API page because pagination is outside the requested scope.

## AI and Other Tools Used

### ChatGPT

I used ChatGPT as a development assistant while building the project. It helped me:

- break the challenge into smaller implementation steps
- understand how to call the GitHub Issues API with Python `requests`
- understand SQLite table creation and parameterized queries
- implement the SQLite upsert used to prevent duplicate records
- structure reusable import and read functions
- create pytest tests with mocked GitHub responses
- troubleshoot the local Python dependency warning caused by urllib3 v2 and LibreSSL
- review the CLI and documentation

I did not treat AI output as automatically correct. I ran the program against the real GitHub API, inspected the returned data, reran imports, read the SQLite data back, deliberately tested an invalid repository, and ran the automated test suite.

### Other tools

- **GitHub REST API** — source of live public issue data
- **Python** — application language
- **requests** — HTTP requests to GitHub
- **SQLite** — persistent local issue storage
- **pytest** — automated testing
- **Git** — version control
- **Terminal** — running and verifying the application

## An Unfamiliar Problem I Solved With AI

One behavior I did not initially expect was that GitHub's Issues API also returns pull requests. During a real API test, the response contained records with a `pull_request` field and pull-request URLs.

With AI assistance, I learned that the response should be filtered by checking for that field:

```python
issues = [
    item for item in items
    if "pull_request" not in item
]
```

I verified the solution in two ways. First, I reran the connector against the real GitHub repository and confirmed that the saved results contained issue URLs rather than pull-request URLs. Second, the automated test data includes a fake pull request alongside two issues and verifies that only the two issues are stored.

This was useful because I did not just copy a suggested fix; I checked the actual API behavior and added a regression test for it.

## Error Handling

If GitHub returns an error or the HTTP request fails, the import operation returns a JSON-compatible error result instead of terminating with an unhandled request exception.

For example, a nonexistent repository produces a result similar to:

```json
{
  "success": false,
  "repository": "this-owner-does-not-exist/this-repo-does-not-exist",
  "error": "404 Client Error: Not Found ..."
}
```

## Project Files

- `connector.py` — GitHub import, SQLite storage, and local read logic
- `cli.py` — command-line interface
- `test_connector.py` — automated tests
- `requirements.txt` — Python dependencies
- `Architecture.md` — architecture and implementation decisions