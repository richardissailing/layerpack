import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from .dependency_manager import DependencyManager
from .exceptions import (
    ConfigurationError,
    IncompatibleRuntimeError,
    LayerSizeLimitError,
)
from .layer_builder import LayerBuilder
from .logger import logger


@dataclass
class LambdaPackagerConfig:
    """Configuration class for Lambda Packager."""

    exclude_packages: list[str] = field(default_factory=list)
    include_source: list[Union[str, Path]] = field(default_factory=list)
    optimization_level: int = 1
    max_size_mb: int = 250
    compatible_runtimes: list[str] = field(default_factory=lambda: ["python3.9"])
    strip_test_files: bool = True
    include_dependencies: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        # Convert string paths to Path objects
        self.include_source = [
            Path(p) if isinstance(p, str) else p for p in self.include_source
        ]

    def _validate_config(self):
        """Validate configuration values."""
        if not 0 <= self.optimization_level <= 2:
            raise ConfigurationError(
                "Invalid optimization level. Must be 0, 1, or 2", "optimization_level"
            )

        if self.max_size_mb <= 0:
            raise ConfigurationError("Maximum size must be positive", "max_size_mb")

        valid_runtimes = {
            "python3.7",
            "python3.8",
            "python3.9",
            "python3.10",
            "python3.11",
        }
        invalid_runtimes = set(self.compatible_runtimes) - valid_runtimes
        if invalid_runtimes:
            raise ConfigurationError(
                f"Invalid runtimes: {invalid_runtimes}", "compatible_runtimes"
            )


class LambdaPackager:
    """Enhanced Lambda Packager with configuration support."""

    def __init__(self, runtime: str, output_dir: str, config: Optional[dict] = None):
        """Initialize the Lambda packager.

        Args:
            runtime: Python runtime version (e.g., "python3.9")
            output_dir: Directory for output files
            config: Optional configuration dictionary
        """
        self.runtime = runtime
        self.output_dir = Path(output_dir)
        self.config = (
            LambdaPackagerConfig(**config) if config else LambdaPackagerConfig()
        )

        # Initialize managers
        self.dependency_manager = DependencyManager()
        self.layer_builder = LayerBuilder(max_size_mb=self.config.max_size_mb)

        # Validate runtime compatibility
        if self.runtime not in self.config.compatible_runtimes:
            raise IncompatibleRuntimeError(
                "current_package",
                f"Runtime {runtime} not in compatible runtimes:",
                f" {self.config.compatible_runtimes}",
            )

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _should_include_package(self, package_name: str) -> bool:
        """Check if a package should be included in the layer."""
        return package_name not in self.config.exclude_packages and (
            self.config.include_dependencies
            or package_name in self._get_direct_dependencies()
        )

    def _get_direct_dependencies(self) -> list[str]:
        """Get list of direct dependencies (non-transitive)."""
        # Implementation depends on how requirements are stored
        return []

    def _copy_source_files(self, layer_dir: Path):
        """Copy source files to the layer directory.

        Args:
            layer_dir: Path to the layer directory
        """
        for source_path in self.config.include_source:
            if not source_path.exists():
                logger.warning(f"Source path does not exist: {source_path}")
                continue

            dest_path = layer_dir / source_path.name
            if source_path.is_dir():
                if dest_path.exists():
                    shutil.rmtree(str(dest_path))
                shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=True)
            else:
                shutil.copy2(str(source_path), str(dest_path))

    def _remove_test_files(self, layer_dir: Path):
        """Remove test files if strip_test_files is enabled."""
        if not self.config.strip_test_files:
            return

        patterns = ["test_*.py", "*_test.py", "tests/", "testing/"]
        for pattern in patterns:
            for path in layer_dir.rglob(pattern):
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

    def _check_layer_size(self, layer_dir: Path):
        """Check if layer size is within limits."""
        total_size = sum(f.stat().st_size for f in layer_dir.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)

        if size_mb > self.config.max_size_mb:
            raise LayerSizeLimitError(size_mb, self.config.max_size_mb)

    def create_layer_from_requirements(
        self, requirements_path: Union[str, Path], layer_name: str
    ) -> Path:
        """Create a Lambda layer from a requirements.txt file."""
        requirements_path = Path(requirements_path)
        if not requirements_path.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

        with open(requirements_path) as f:
            packages = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        return self.create_layer_from_packages(packages, layer_name)

    def create_layer_from_packages(self, packages: list[str], layer_name: str) -> Path:
        """Create a Lambda layer from a list of packages."""
        logger.info(f"Creating layer '{layer_name}' from {len(packages)} packages")

        try:
            # Create necessary directories
            packages_dir = self.output_dir / "packages"
            packages_dir.mkdir(parents=True, exist_ok=True)

            # Resolve and filter dependencies
            deps = self.dependency_manager.resolve_dependencies(packages)
            included_deps = {
                name: version
                for name, version in deps.items()
                if self._should_include_package(name)
            }

            # Download packages
            downloaded_dir = Path(
                self.dependency_manager.download_packages(included_deps)
            )
            if not downloaded_dir.exists():
                raise FileNotFoundError(
                    f"Package download directory not found: {downloaded_dir}"
                )

            # Create layer directory structure
            layer_dir = Path(
                self.layer_builder.create_layer_structure(str(packages_dir))
            )

            # Copy packages to layer
            for item in os.listdir(downloaded_dir):
                src = downloaded_dir / item
                dst = layer_dir / item
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            # Copy source files and apply configurations
            self._copy_source_files(layer_dir)
            if self.config.strip_test_files:
                self._remove_test_files(layer_dir)
            self._check_layer_size(layer_dir)

            # Create final ZIP file
            zip_path = str(self.output_dir / f"{layer_name}.zip")
            self.layer_builder.create_zip(str(layer_dir), zip_path)

            logger.info(f"Created layer at {zip_path}")
            return Path(zip_path)

        except Exception as e:
            logger.error(f"Failed to create layer: {str(e)}")
            raise
