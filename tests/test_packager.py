import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from layerpack.exceptions import IncompatibleRuntimeError
from layerpack.packager import LambdaPackager


def test_init_invalid_runtime():
    with pytest.raises(IncompatibleRuntimeError):
        LambdaPackager("python2.7", "./dist")


@patch("layerpack.packager.DependencyManager")
@patch("layerpack.packager.LayerBuilder")
def test_create_layer_from_packages(mock_builder, mock_dm, tmp_path):
    # Create necessary directories
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # Setup mocks
    mock_dm_instance = Mock()
    mock_dm_instance.resolve_dependencies.return_value = {"requests": "2.28.1"}
    mock_dm_instance.download_packages.return_value = str(packages_dir)
    mock_dm.return_value = mock_dm_instance

    mock_builder_instance = Mock()
    mock_builder_instance.create_layer_structure.return_value = str(tmp_path / "layer")
    mock_builder_instance.create_zip.return_value = str(tmp_path / "test-layer.zip")
    mock_builder.return_value = mock_builder_instance

    # Create dummy package file
    (packages_dir / "requests").mkdir(parents=True, exist_ok=True)
    (packages_dir / "requests" / "__init__.py").touch()

    # Create test zip file
    (tmp_path / "test-layer.zip").touch()

    packager = LambdaPackager("python3.9", str(tmp_path))
    path = packager.create_layer_from_packages(["requests"], "test-layer")

    assert str(path).endswith(".zip")
    assert path.exists()


@patch("layerpack.packager.DependencyManager")
@patch("layerpack.packager.LayerBuilder")
def test_create_layer_from_requirements(mock_builder, mock_dm, tmp_path):
    # Create necessary directories
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # Setup mocks
    mock_dm_instance = Mock()
    mock_dm_instance.resolve_dependencies.return_value = {
        "requests": "2.28.1",
        "urllib3": "1.26.8",
    }
    mock_dm_instance.download_packages.return_value = str(packages_dir)
    mock_dm.return_value = mock_dm_instance

    mock_builder_instance = Mock()
    mock_builder_instance.create_layer_structure.return_value = str(tmp_path / "layer")
    mock_builder_instance.create_zip.return_value = str(tmp_path / "test-layer.zip")
    mock_builder.return_value = mock_builder_instance

    # Create test requirements file
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text("requests==2.28.1\nurllib3==1.26.8")

    # Create dummy package files
    for pkg in ["requests", "urllib3"]:
        pkg_dir = packages_dir / pkg
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").touch()

    # Create test zip file
    (tmp_path / "test-layer.zip").touch()

    packager = LambdaPackager("python3.9", str(tmp_path))
    path = packager.create_layer_from_requirements(str(requirements_path), "test-layer")

    assert str(path).endswith(".zip")
    assert path.exists()


@patch("layerpack.packager.DependencyManager")
@patch("layerpack.packager.LayerBuilder")
def test_config_exclude_packages(mock_builder, mock_dm, tmp_path):
    # Create necessary directories
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # Setup mocks
    mock_dm_instance = Mock()
    mock_dm_instance.resolve_dependencies.return_value = {"requests": "2.28.1"}
    mock_dm_instance.download_packages.return_value = str(packages_dir)
    mock_dm.return_value = mock_dm_instance

    mock_builder_instance = Mock()
    mock_builder_instance.create_layer_structure.return_value = str(tmp_path / "layer")
    mock_builder_instance.create_zip.return_value = str(tmp_path / "test-layer.zip")
    mock_builder.return_value = mock_builder_instance

    # Create dummy package file
    (packages_dir / "requests").mkdir(parents=True, exist_ok=True)
    (packages_dir / "requests" / "__init__.py").touch()

    # Create test zip file
    (tmp_path / "test-layer.zip").touch()

    config = {"exclude_packages": ["urllib3"]}
    packager = LambdaPackager("python3.9", str(tmp_path), config)
    path = packager.create_layer_from_packages(["requests", "urllib3"], "test-layer")

    assert str(path).endswith(".zip")
    assert path.exists()


@patch("layerpack.packager.DependencyManager")
@patch("layerpack.packager.LayerBuilder")
@patch("layerpack.packager.shutil.copytree")
def test_config_include_source(mock_copytree, mock_builder, mock_dm, tmp_path):
    # Create necessary directories
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # Setup mocks
    mock_dm_instance = Mock()
    mock_dm_instance.resolve_dependencies.return_value = {"requests": "2.28.1"}
    mock_dm_instance.download_packages.return_value = str(packages_dir)
    mock_dm.return_value = mock_dm_instance

    mock_builder_instance = Mock()
    mock_builder_instance.create_layer_structure.return_value = str(tmp_path / "layer")
    mock_builder_instance.create_zip.return_value = str(tmp_path / "test-layer.zip")
    mock_builder.return_value = mock_builder_instance

    # Create test source directory with content
    source_dir = tmp_path / "custom_module"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "test.py").write_text("print('test')")

    # Create dummy package file
    (packages_dir / "requests").mkdir(parents=True, exist_ok=True)
    (packages_dir / "requests" / "__init__.py").touch()

    # Create test zip file
    (tmp_path / "test-layer.zip").touch()

    # Mock copytree to prevent actual file operations
    mock_copytree.return_value = None

    config = {"include_source": [str(source_dir)]}
    packager = LambdaPackager("python3.9", str(tmp_path), config)
    path = packager.create_layer_from_packages(["requests"], "test-layer")

    assert str(path).endswith(".zip")
    assert path.exists()

    # Verify source directory was included
    mock_copytree.assert_called_with(
        str(source_dir),
        str(
            Path(mock_builder_instance.create_layer_structure.return_value)
            / source_dir.name
        ),
        dirs_exist_ok=True,
    )
