import os

import pytest

from layerpack.exceptions import LayerSizeLimitError
from layerpack.layer_builder import LayerBuilder


def test_create_layer_structure(tmp_path):
    builder = LayerBuilder()
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir()

    # Create dummy package
    (packages_dir / "test_package.py").write_text("print('test')")

    layer_dir = builder.create_layer_structure(str(packages_dir))
    assert os.path.exists(layer_dir)
    assert os.path.exists(os.path.join(layer_dir, "python"))


def test_create_zip(tmp_path):
    builder = LayerBuilder(max_size_mb=50)
    layer_dir = tmp_path / "layer"
    layer_dir.mkdir()

    # Create dummy content
    python_dir = layer_dir / "python"
    python_dir.mkdir()
    (python_dir / "test.py").write_text("print('test')")

    zip_path = builder.create_zip(str(layer_dir), str(tmp_path / "test_layer"))
    assert zip_path.endswith(".zip")
    assert os.path.exists(zip_path)


def test_size_limit_exceeded(tmp_path):
    builder = LayerBuilder(max_size_mb=0.0001)  # Very small limit
    layer_dir = tmp_path / "layer"
    layer_dir.mkdir()

    # Create content that will exceed limit
    python_dir = layer_dir / "python"
    python_dir.mkdir()
    (python_dir / "large_file.py").write_text("x" * 1000000)  # 1MB file

    with pytest.raises(LayerSizeLimitError):
        builder.create_zip(str(layer_dir), str(tmp_path / "test_layer"))
