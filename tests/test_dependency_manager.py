import os
from unittest.mock import Mock, patch

from layerpack.dependency_manager import DependencyManager


@patch("subprocess.run")
def test_resolve_dependencies_uv_success(mock_run):
    """Test successful dependency resolution using uv."""
    # Mock subprocess run to return a successful result with package versions
    mock_version_check = Mock()
    mock_version_check.stdout = ""

    mock_compile = Mock()
    mock_compile.stdout = "requests==2.28.1\nchardet==3.0.4"

    # Set up mock to return different values for different calls
    mock_run.side_effect = [mock_version_check, mock_compile]

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

    # Verify both calls were made with correct arguments
    assert mock_run.call_count == 2
    calls = mock_run.call_args_list

    # First call should be version check
    assert calls[0][0][0] == ["/mock/uv", "--version"]

    # Second call should be dependency resolution
    assert "/mock/uv" in calls[1][0][0]
    assert "pip" in calls[1][0][0]
    assert "compile" in calls[1][0][0]


@patch("subprocess.run")
def test_download_packages(mock_run, tmp_path):
    """Test downloading packages."""
    # Mock version check and package download responses
    mock_version_check = Mock()
    mock_version_check.stdout = ""

    mock_install = Mock()
    mock_install.returncode = 0
    mock_install.stderr = ""

    mock_run.side_effect = [mock_version_check, mock_install]

    dm = DependencyManager(uv_path="/mock/uv")
    dm.temp_dir = str(tmp_path)  # Override temp dir for testing

    packages = {"requests": "2.28.1"}
    download_path = dm.download_packages(packages)

    # Verify download path
    assert os.path.basename(download_path) == "packages"
    assert os.path.exists(download_path)

    # Verify both calls were made with correct arguments
    assert mock_run.call_count == 2
    calls = mock_run.call_args_list

    # First call should be version check
    assert calls[0][0][0] == ["/mock/uv", "--version"]

    # Second call should be package installation
    assert "/mock/uv" in calls[1][0][0]
    assert "pip" in calls[1][0][0]
    assert "install" in calls[1][0][0]
    assert "requests==2.28.1" in calls[1][0][0]
