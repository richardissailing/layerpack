import os
import shutil
import zipfile
from typing import Optional

from .exceptions import LayerSizeLimitError


class LayerBuilder:
    def __init__(self, max_size_mb: Optional[int] = None):
        """Initialize the layer builder.

        Args:
            max_size_mb: Optional maximum size limit for the layer in MB
        """
        self.max_size_mb = max_size_mb

    def create_layer_structure(self, packages_dir: str) -> str:
        """Create the proper directory structure for a Lambda layer.

        Args:
            packages_dir: Directory containing downloaded packages

        Returns:
            Path to the layer directory
        """
        layer_dir = os.path.join(os.path.dirname(packages_dir), "layer")
        python_path = os.path.join(
            layer_dir, "python", "lib", "python3.9", "site-packages"
        )
        os.makedirs(python_path, exist_ok=True)

        # Copy packages to layer structure
        for item in os.listdir(packages_dir):
            src = os.path.join(packages_dir, item)
            dst = os.path.join(python_path, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            else:
                shutil.copytree(src, dst)

        return layer_dir

    def create_zip(self, layer_dir: str, output_path: str) -> str:
        """Create a ZIP file from the layer directory.

        Args:
            layer_dir: Path to the layer directory
            output_path: Desired path for the ZIP file

        Returns:
            Path to the created ZIP file

        Raises:
            LayerSizeLimitError: If layer exceeds size limit
        """
        zip_path = f"{output_path}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(layer_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, layer_dir)
                    zipf.write(file_path, arcname)

        if self.max_size_mb:
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                os.remove(zip_path)
                raise LayerSizeLimitError(size_mb, self.max_size_mb)

        return zip_path
