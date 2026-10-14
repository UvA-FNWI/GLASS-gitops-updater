from unittest.mock import MagicMock, patch

from gitops_updater.providers.gitlab import GitLabProvider


def test_gitlab_provider_loads_token_via_get_secret():
    with (
        patch(
            "gitops_updater.providers.gitlab.get_secret",
            return_value="gitlab-pat",
        ) as get_secret,
        patch("gitops_updater.providers.gitlab.Gitlab") as gitlab_cls,
    ):
        project = MagicMock()
        client = MagicMock()
        client.projects.get.return_value = project
        gitlab_cls.return_value = client

        provider = GitLabProvider(
            "https://gitlab.example",
            "GITLAB_TOKEN_PATH",
            "main",
            "group/project",
        )

    get_secret.assert_called_once_with("GITLAB_TOKEN_PATH")
    gitlab_cls.assert_called_once_with(
        "https://gitlab.example", private_token="gitlab-pat"
    )
    client.projects.get.assert_called_once_with("group/project")
    assert provider.branch == "main"
    assert provider.project is project
