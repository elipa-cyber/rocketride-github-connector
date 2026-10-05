import argparse
import json

from connector import import_issues, read_issues


def main():
    parser = argparse.ArgumentParser(
        description="Import and read GitHub issue snapshots."
    )

    parser.add_argument(
        "action",
        choices=["import", "read"],
        help="Import issues from GitHub or read saved issues."
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in owner/name format."
    )

    parser.add_argument(
        "--db",
        default="issues.db",
        help="Path to the SQLite database."
    )

    args = parser.parse_args()

    if args.action == "import":
        result = import_issues(args.repository, args.db)
    else:
        result = read_issues(args.repository, args.db)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()