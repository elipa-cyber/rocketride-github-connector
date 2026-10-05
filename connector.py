import sqlite3
import requests

DB_PATH = "issues.db"


def create_database():
    connection = sqlite3.connect(DB_PATH)

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


repo = "octocat/Hello-World"
url = f"https://api.github.com/repos/{repo}/issues"

response = requests.get(url, params={"state": "open", "per_page": 10})
response.raise_for_status()

items = response.json()

issues = [
    item for item in items
    if "pull_request" not in item
]
create_database()

connection = sqlite3.connect(DB_PATH)

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

print(f"Saved {len(issues)} issues to {DB_PATH}.")

connection = sqlite3.connect(DB_PATH)

rows = connection.execute("""
    SELECT repository, issue_number, title, url
    FROM issues
    WHERE repository = ?
    ORDER BY issue_number
""", (repo,)).fetchall()

connection.close()

print(f"\nSaved issues for {repo}: {len(rows)}")

for row in rows:
    print(f"#{row[1]}: {row[2]}")
    print(row[3])