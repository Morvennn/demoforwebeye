# Daniel Design
import pytest

from app.github import parse_repo_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/facebook/react", ("facebook", "react")),
        ("https://github.com/facebook/react.git", ("facebook", "react")),
        ("https://github.com/facebook/react/", ("facebook", "react")),
        ("https://github.com/facebook/react/tree/main/packages", ("facebook", "react")),
        ("http://github.com/owner/repo", ("owner", "repo")),
        ("github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/sindresorhus/awesome-nodejs", ("sindresorhus", "awesome-nodejs")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
    ],
)
def test_parse_valid(url, expected):
    assert parse_repo_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://gitlab.com/a/b",
        "https://example.com",
        "https://github.com/onlyone",
        "https://github.com/orgs/python",
        "https://github.com/users/foo",
    ],
)
def test_parse_invalid(url):
    with pytest.raises(ValueError):
        parse_repo_url(url)
