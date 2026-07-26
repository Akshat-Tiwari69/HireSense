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
