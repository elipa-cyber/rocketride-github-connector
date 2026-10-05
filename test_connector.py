from unittest.mock import patch, Mock

from connector import import_issues, read_issues


FAKE_GITHUB_RESPONSE = [
    {
        "number": 101,
        "title": "First test issue",
        "html_url": "https://github.com/test/repo/issues/101"
    },
    {
        "number": 102,
        "title": "Second test issue",
        "html_url": "https://github.com/test/repo/issues/102"
    },
    {
        "number": 103,
        "title": "This is actually a pull request",
        "html_url": "https://github.com/test/repo/pull/103",
        "pull_request": {}
    }
]


def make_mock_response():
    response = Mock()
    response.json.return_value = FAKE_GITHUB_RESPONSE
    response.raise_for_status.return_value = None
    return response


@patch("connector.requests.get")
def test_import_and_read(mock_get, tmp_path):
    mock_get.return_value = make_mock_response()
    db_path = str(tmp_path / "test.db")

    result = import_issues("test/repo", db_path)
    saved = read_issues("test/repo", db_path)

    assert result["success"] is True
    assert result["imported_count"] == 2
    assert len(saved["issues"]) == 2
    assert saved["issues"][0]["number"] == 101


@patch("connector.requests.get")
def test_repeated_import_does_not_duplicate(mock_get, tmp_path):
    mock_get.return_value = make_mock_response()
    db_path = str(tmp_path / "test.db")

    import_issues("test/repo", db_path)
    import_issues("test/repo", db_path)

    saved = read_issues("test/repo", db_path)

    assert len(saved["issues"]) == 2


@patch("connector.requests.get")
def test_api_failure(mock_get, tmp_path):
    import requests

    mock_get.side_effect = requests.RequestException("GitHub unavailable")
    db_path = str(tmp_path / "test.db")

    result = import_issues("test/repo", db_path)

    assert result["success"] is False
    assert "GitHub unavailable" in result["error"]

def test_read_does_not_call_github(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("connector.requests.get") as mock_get:
        saved = read_issues("test/repo", db_path)

    mock_get.assert_not_called()
    assert saved["success"] is True
    assert saved["repository"] == "test/repo"
    assert saved["issues"] == []

@patch("connector.requests.get")
def test_invalid_repository_format(mock_get, tmp_path):
    db_path = str(tmp_path / "test.db")

    result = import_issues("banana", db_path)

    assert result["success"] is False
    assert result["error"] == "Repository must be in owner/name format."
    mock_get.assert_not_called()