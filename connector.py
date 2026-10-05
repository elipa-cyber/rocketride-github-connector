import sqlite3
import requests

DEFAULT_DB_PATH = "issues.db"


def create_database(db_path=DEFAULT_DB_PATH):
    """Create the issues table if it does not already exist."""
    connection = sqlite3.connect(db_path)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            repository TEXT NOT NULL,
            issue_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            PRIMARY KEY (repository, issue_number)
        )
    """)

    connection.commit()
    connection.close()


def import_issues(repo, db_path=DEFAULT_DB_PATH):
    """Fetch open GitHub issues and save them to SQLite."""
    url = f"https://api.github.com/repos/{repo}/issues"

    try:
        response = requests.get(
            url,
            params={"state": "open", "per_page": 30},
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return {
            "success": False,
            "repository": repo,
            "error": str(error)
        }

    items = response.json()

    # GitHub's Issues API also returns pull requests.
    # Keep only actual issues.
    issues = [
        item for item in items
        if "pull_request" not in item
    ]

    create_database(db_path)
    connection = sqlite3.connect(db_path)

    for issue in issues:
        connection.execute("""
            INSERT INTO issues (repository, issue_number, title, url)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(repository, issue_number)
            DO UPDATE SET
                title = excluded.title,
                url = excluded.url
        """, (
            repo,
            issue["number"],
            issue["title"],
            issue["html_url"]
        ))

    connection.commit()
    connection.close()

    return {
        "success": True,
        "repository": repo,
        "imported_count": len(issues)
    }


def read_issues(repo, db_path=DEFAULT_DB_PATH):
    """Return saved issues from SQLite without calling GitHub."""
    create_database(db_path)
    connection = sqlite3.connect(db_path)

    rows = connection.execute("""
        SELECT issue_number, title, url
        FROM issues
        WHERE repository = ?
        ORDER BY issue_number
    """, (repo,)).fetchall()

    connection.close()

    issues = [
        {
            "number": row[0],
            "title": row[1],
            "url": row[2]
        }
        for row in rows
    ]

    return {
        "success": True,
        "repository": repo,
        "issues": issues
    }


if __name__ == "__main__":
    repository = "octocat/Hello-World"

    print(import_issues(repository))
    print(read_issues(repository))