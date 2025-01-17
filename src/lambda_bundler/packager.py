import os
import shutil
from typing import Any, Dict, List, Optional

from .dependency_manager import DependencyManager
from .exceptions import IncompatibleRuntimeError
from .layer_builder import LayerBuilder


class LambdaPackager:
    def __init__(
        self, runtime: str, output_dir: str, config: Optional[Dict[str, Any]] = None
    ):
        self.runtime = runtime
        self.output_dir = output_dir
        self.config = config or {}

        if not runtime.startswith("python3."):
            raise IncompatibleRuntimeError(f"Unsupported runtime: {runtime}")

        self.dependency_manager = DependencyManager()
        self.layer_builder = LayerBuilder(max_size_mb=self.config.get("max_size_mb"))

        os.makedirs(output_dir, exist_ok=True)

    def _parse_requirements(self, requirements_path: str) -> List[str]:
        """Parse requirements file and return list of package specifications."""
        packages = []
        with open(requirements_path) as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Remove inline comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                packages.append(line)
        return packages

    def create_layer_from_requirements(
        self, requirements_path: str, layer_name: str
    ) -> str:
        """Create a Lambda layer from a requirements.txt file."""
        packages = self._parse_requirements(requirements_path)
        return self.create_layer_from_packages(packages, layer_name)

    def create_layer_from_packages(self, packages: List[str], layer_name: str) -> str:
        """Create a Lambda layer from a list of package names."""
        # Filter excluded packages
        excluded = set(self.config.get("exclude_packages", []))
        packages = [p for p in packages if p not in excluded]

        # Resolve and download dependencies
        deps = self.dependency_manager.resolve_dependencies(packages)
        packages_dir = self.dependency_manager.download_packages(deps)

        # Create layer structure
        layer_dir = self.layer_builder.create_layer_structure(packages_dir)

        # Include source files if specified
        for src_dir in self.config.get("include_source", []):
            if os.path.exists(src_dir):
                dst_dir = os.path.join(layer_dir, "python", src_dir)
                os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
                if os.path.isfile(src_dir):
                    shutil.copy2(src_dir, dst_dir)
                else:
                    shutil.copytree(src_dir, dst_dir)

        # Create ZIP file
        output_path = os.path.join(self.output_dir, layer_name)
        return self.layer_builder.create_zip(layer_dir, output_path)
