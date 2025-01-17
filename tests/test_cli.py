from unittest.mock import Mock, patch

from click.testing import CliRunner

from lambda_bundler.cli import cli


@patch("lambda_bundler.cli.LambdaPackager")
def test_create_layer_from_requirements(mock_packager, tmp_path):
    # Setup mock
    mock_instance = Mock()
    mock_instance.create_layer_from_requirements.return_value = str(
        tmp_path / "test-layer.zip"
    )
    mock_packager.return_value = mock_instance

    runner = CliRunner()
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text("requests==2.28.1")

    result = runner.invoke(
        cli,
        [
            "create-layer",
            "-r",
            str(requirements_path),
            "-n",
            "test-layer",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Created layer at:" in result.output


@patch("lambda_bundler.cli.LambdaPackager")
def test_create_layer_from_packages(mock_packager, tmp_path):
    # Setup mock
    mock_instance = Mock()
    mock_instance.create_layer_from_packages.return_value = str(
        tmp_path / "test-layer.zip"
    )
    mock_packager.return_value = mock_instance

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "create-layer",
            "-p",
            "requests",
            "-n",
            "test-layer",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Created layer at:" in result.output


@patch("lambda_bundler.cli.DependencyManager")
def test_analyze_requirements(mock_dm, tmp_path):
    # Setup mock
    mock_instance = Mock()
    mock_instance.resolve_dependencies.return_value = {"requests": "2.28.1"}
    mock_dm.return_value = mock_instance

    runner = CliRunner()
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text("requests==2.28.1")

    result = runner.invoke(cli, ["analyze", "-r", str(requirements_path)])

    assert result.exit_code == 0
    assert "Package Dependencies:" in result.output
    assert "requests" in result.output
