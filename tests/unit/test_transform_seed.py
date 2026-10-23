from aap_migration.cli.commands.transform import (
    credential_types_support_managed_filter,
    is_builtin_credential_type,
)
from aap_migration.migration.transformer import ProjectTransformer


def test_credential_types_support_managed_filter() -> None:
    assert credential_types_support_managed_filter("2.3") is True
    assert credential_types_support_managed_filter("2.6") is True
    assert credential_types_support_managed_filter("1.0") is False
    assert credential_types_support_managed_filter("2.2") is False


def test_is_builtin_credential_type() -> None:
    assert is_builtin_credential_type({"managed": True, "name": "Machine"}) is True
    assert is_builtin_credential_type({"namespace": "tower", "name": "Ansible Tower"}) is True
    assert is_builtin_credential_type({"name": "Custom"}) is False


def test_project_transformer_defers_git_refspec() -> None:
    transformer = ProjectTransformer()

    transformed = transformer.transform_resource(
        "projects",
        {
            "id": 1,
            "name": "pull-request-project",
            "organization": 2,
            "scm_type": "git",
            "scm_url": "https://example.com/repo.git",
            "scm_refspec": "+refs/pull/*:refs/remotes/origin/pr/*",
        },
    )

    assert transformed["_deferred_scm_details"]["scm_refspec"] == (
        "+refs/pull/*:refs/remotes/origin/pr/*"
    )
    assert "scm_refspec" not in transformed
