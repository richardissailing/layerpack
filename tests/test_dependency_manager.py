import os
import subprocess
from unittest.mock import Mock, patch

import pytest

from lambda_bundler.dependency_manager import DependencyManager
from lambda_bundler.exceptions import (
    DependencyConflictError,
    PackageNotFoundError,
)


def test_check_uv_available():
    """Test the _check_uv_available method."""
    # Mock which and version checks
    with patch("subprocess.run") as mock_run:
        # First call for 'which uv'
        mock_run.side_effect = [
            Mock(stdout="/usr/local/bin/uv\n"),  # which uv result
            Mock(),  # uv --version result
        ]

        dm = DependencyManager()
        assert dm.use_uv is True
        assert dm.uv_path == "/usr/local/bin/uv"

    # Test when uv is not available
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "uv")):
        dm = DependencyManager()
        assert dm.use_uv is False
        assert dm.uv_path is None


@patch("subprocess.run")
def test_resolve_dependencies_uv_success(mock_run):
    """Test successful dependency resolution using uv."""
    # Mock subprocess run to return a successful result with package versions
    mock_result = Mock()
    mock_result.stdout = "requests==2.28.1\nchardet==3.0.4"
    mock_run.return_value = mock_result

    # Create DependencyManager with a mock uv path
    dm = DependencyManager(uv_path="/mock/uv")

    # Test resolving multiple packages
    packages = ["requests", "chardet"]
    deps = dm.resolve_dependencies(packages)

    # Assertions
    assert isinstance(deps, dict)
    assert "requests" in deps
    assert "chardet" in deps
    assert deps["requests"] == "2.28.1"
    assert deps["chardet"] == "3.0.4"

    # Verify subprocess was called once
    assert mock_run.call_count == 1
    args, kwargs = mock_run.call_args
    assert "/mock/uv" in args[0]
    assert "pip" in args[0]
    assert "compile" in args[0]


def test_resolve_dependencies_with_comments():
    """Test resolving dependencies with comments and empty lines."""
    # Create DependencyManager with a mock uv path
    dm = DependencyManager(uv_path="/mock/uv")

    # Mock subprocess run
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.stdout = "requests==2.28.1\n# This is a comment\nchardet==3.0.4"
        mock_run.return_value = mock_result

        packages = ["requests", "# This is a comment", "", "chardet"]
        deps = dm.resolve_dependencies(packages)

        assert "requests" in deps
        assert "chardet" in deps


def test_resolve_dependencies_no_packages():
    """Test resolving with no valid packages."""
    dm = DependencyManager()

    with pytest.raises(DependencyConflictError, match="No dependencies to resolve"):
        dm.resolve_dependencies([])


def test_resolve_dependencies_package_not_found():
    """Test handling of package not found scenario."""
    dm = DependencyManager(uv_path="/mock/uv")

    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(
            returncode=1,
            cmd="/mock/uv pip compile",
            stderr=(
                "ERROR: Could not find a version that satisfies the "
                "requirement nonexistent-package"
            ),
        ),
    ):
        with pytest.raises(PackageNotFoundError, match="Package not found:"):
            dm.resolve_dependencies(["nonexistent-package"])


@patch("subprocess.run")
def test_download_packages(mock_run, tmp_path):
    """Test downloading packages."""
    dm = DependencyManager(uv_path="/mock/uv")
    dm.temp_dir = str(tmp_path)  # Override temp dir for testing

    # Mock successful package download
    mock_run.return_value = Mock(returncode=0, stderr="")

    packages = {"requests": "2.28.1"}
    download_path = dm.download_packages(packages)

    # Verify download path
    assert os.path.basename(download_path) == "packages"
    assert os.path.exists(download_path)

    # Verify subprocess call
    assert mock_run.call_count == 1
    args, kwargs = mock_run.call_args
    assert "/mock/uv" in args[0]
    assert "pip" in args[0]
    assert "install" in args[0]
    assert "requests==2.28.1" in args[0]


def test_download_packages_failure():
    """Test handling of package download failure."""
    dm = DependencyManager(uv_path="/mock/uv")

    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(
            returncode=1,
            cmd="/mock/uv pip install",
            stderr="Failed to download package",
        ),
    ):
        with pytest.raises(
            DependencyConflictError, match="Failed to download packages"
        ):
            dm.download_packages({"requests": "2.28.1"})


def test_cleanup(tmp_path):
    """Test cleanup method."""
    dm = DependencyManager()
    dm.temp_dir = str(tmp_path)

    # Create some files/directories to verify cleanup
    os.makedirs(os.path.join(dm.temp_dir, "test_dir"))
    with open(os.path.join(dm.temp_dir, "test_file.txt"), "w") as f:
        f.write("test")

    dm.cleanup()

    # Verify temp directory is removed
    assert not os.path.exists(dm.temp_dir)
