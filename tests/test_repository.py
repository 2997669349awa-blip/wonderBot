import pytest

from astrbot.core.repository import (
    GitHubRepository,
    normalize_repository_url,
    parse_repository_url,
)


def test_github_repository_resolves_branch_with_slashes() -> None:
    repository = GitHubRepository.parse(
        "https://github.com/2997669349awa-blip/wonderBot.git/tree/feature/updater"
    )

    assert repository.owner == "WonderBotDevs"
    assert repository.name == "WonderBot"
    assert repository.branch == "feature/updater"
    assert repository.archive_url == (
        "https://github.com/2997669349awa-blip/wonderBot/archive/refs/heads/feature/updater.zip"
    )
    assert repository.raw_file_url("metadata.yaml") == (
        "https://raw.githubusercontent.com/2997669349awa-blip/wonderBot/"
        "feature/updater/metadata.yaml"
    )


def test_github_repository_uses_head_when_branch_is_unspecified() -> None:
    repository = GitHubRepository.parse("https://github.com/2997669349awa-blip/wonderBot")

    assert repository.branch is None
    assert repository.archive_url == (
        "https://github.com/2997669349awa-blip/wonderBot/archive/HEAD.zip"
    )
    assert repository.raw_file_url("metadata.yaml") == (
        "https://raw.githubusercontent.com/2997669349awa-blip/wonderBot/HEAD/metadata.yaml"
    )


def test_non_github_http_repository_uses_git_transport() -> None:
    repository = parse_repository_url("https://gitee.com/astrbot/demo.git")

    assert repository.provider == "gitee.com"
    assert repository.owner == "astrbot"
    assert repository.name == "demo"
    assert repository.transport == "git"


def test_github_ssh_repository_uses_git_transport() -> None:
    repository = parse_repository_url("git@github.com:2997669349awa-blip/wonderBot.git")

    assert repository.provider == "github.com"
    assert repository.owner == "WonderBotDevs"
    assert repository.name == "WonderBot"
    assert repository.transport == "git"


def test_repository_normalization_accepts_github_shorthand() -> None:
    assert (
        normalize_repository_url("2997669349awa-blip/wonderBot")
        == "https://github.com/2997669349awa-blip/wonderBot"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://gitee.com/astrbot/demo",
        "https://example.com/astrbot/demo",
    ],
)
def test_github_repository_rejects_other_hosts(url: str) -> None:
    with pytest.raises(ValueError, match="Invalid GitHub repository URL"):
        GitHubRepository.parse(url)


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/plugin",
        "ext::sh -c dangerous",
        "https://example.com/plugin.zip",
        "https://user:secret@example.com/owner/plugin.git",
    ],
)
def test_repository_parser_rejects_unsafe_or_non_repository_urls(url: str) -> None:
    with pytest.raises(ValueError):
        parse_repository_url(url)
