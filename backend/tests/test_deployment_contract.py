"""Static checks for production deployment invariants."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_production_service_disables_unavailable_code_runner():
    service = (REPOSITORY_ROOT / "deploy" / "hiresense.service").read_text()

    assert "ExecStart=/usr/bin/env CODE_RUNNER_ENABLED=false" in service
    assert "UnsetEnvironment=DATABASE_ADMIN_URL" in service


def test_example_environment_fails_closed_without_code_runner():
    example = (REPOSITORY_ROOT / "backend" / ".env.example").read_text()

    assert "CODE_RUNNER_ENABLED=false" in example
    assert "CODE_RUNNER_URL=\n" in example


def test_deployments_are_not_cancelled_mid_release():
    workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "quality-and-deploy.yml"
    ).read_text()

    assert "cancel-in-progress: false" in workflow


def test_deploy_supports_prepare_before_activation_for_explicit_migrations():
    deploy = (REPOSITORY_ROOT / "deploy" / "deploy-hiresense").read_text()

    preparation = deploy.index('if [[ "$prepare_only" == "1" ]]')
    activation = deploy.index('ln -sfn "$release_dir"')

    assert "--prepare-only" in deploy
    assert preparation < activation
    assert '"${SUDO_USER:-root}" == "hiresense-deploy"' in deploy
    assert '! -user root -o \\( ! -type l -a -perm /022 \\)' in deploy


def test_github_deploy_key_is_restricted_to_a_validated_sha():
    workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "quality-and-deploy.yml"
    ).read_text()
    forced_command = (
        REPOSITORY_ROOT / "deploy" / "hiresense-deploy-ssh"
    ).read_text()

    assert '"deploy $GITHUB_SHA"' in workflow
    assert "SSH_ORIGINAL_COMMAND" in forced_command
    assert "^[0-9a-f]{40}$" in forced_command
    assert 'exec sudo /usr/local/sbin/deploy-hiresense "$release_sha"' in forced_command
