import os
import shutil
import subprocess
import tempfile

from .exceptions import DependencyConflictError, PackageNotFoundError
from .logger import logger


class DependencyManager:
    def __init__(self, uv_path=None):
        """Initialize temporary directory for package management.

        Args:
            uv_path: Optional path to uv executable.
            If not provided, will attempt to find it.
        """
        self.temp_dir = tempfile.mkdtemp()
        logger.debug(f"Initialized temporary directory at {self.temp_dir}")
        self.uv_path = uv_path
        self.use_uv = self._check_uv_available()

    def _check_uv_available(self) -> bool:
        """Check if uv is available in the environment."""
        try:
            # If uv_path is provided, use that directly
            if self.uv_path:
                subprocess.run(
                    [self.uv_path, "--version"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return True

            # Otherwise try to find uv in PATH
            result = subprocess.run(
                ["which", "uv"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.uv_path = result.stdout.strip()

            # Verify the found uv works
            subprocess.run(
                [self.uv_path, "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("uv not available, falling back to pip")
            self.uv_path = None
            return False

    def resolve_dependencies(self, packages: list[str]) -> dict[str, str]:
        """
        Resolve dependencies using uv if available, otherwise use pip.

        Args:
            packages: List of package names/specs

        Returns:
            Dict mapping package names to versions
        """
        logger.info(f"Resolving dependencies for {len(packages)} packages")
        logger.debug(f"Packages: {packages}")

        try:
            # Filter out comments and empty lines
            package_specs = [
                p.strip()
                for p in packages
                if p.strip() and not p.strip().startswith("#")
            ]

            if not package_specs:
                raise DependencyConflictError("No dependencies to resolve")

            logger.debug(f"Adding dependencies: {package_specs}")

            # Create requirements.txt
            req_file = os.path.join(self.temp_dir, "requirements.txt")
            with open(req_file, "w") as f:
                for package in package_specs:
                    f.write(f"{package}\n")

            if self.use_uv:
                cmd = [self.uv_path, "pip", "compile", req_file]
            else:
                # Fallback to pip
                cmd = ["pip", "freeze"]

            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as original_err:
                # Check for specific package not found scenarios
                if (
                    "not found" in original_err.stderr.lower()
                    or "could not find a version" in original_err.stderr.lower()
                ):
                    raise PackageNotFoundError(
                        f"Package not found: {original_err.stderr}"
                    ) from original_err
                raise DependencyConflictError(
                    f"Dependency resolution failed: {original_err.stderr}"
                ) from original_err

            # Parse the resolved dependencies
            dependencies = {}
            for line in result.stdout.splitlines():
                if line and not line.startswith("#"):
                    try:
                        name, version = line.split("==")
                        dependencies[name.strip()] = version.strip()
                    except ValueError:
                        continue

            logger.info(f"Successfully resolved {len(dependencies)} dependencies")
            for name, version in dependencies.items():
                logger.debug(f"Resolved: {name}=={version}")
            return dependencies

        except Exception as e:
            logger.error(f"Dependency resolution failed: {str(e)}")
            raise

    def download_packages(self, package_specs: dict[str, str]) -> str:
        """
        Download packages to a local directory.

        Args:
            package_specs: Dictionary of package names and versions

        Returns:
            Path to the directory containing downloaded packages
        """
        logger.info(f"Downloading {len(package_specs)} packages...")
        logger.debug(f"Package specs: {package_specs}")

        download_dir = os.path.join(self.temp_dir, "packages")
        os.makedirs(download_dir, exist_ok=True)

        try:
            # Download each package individually to track progress
            for name, version in package_specs.items():
                logger.info(f"Installing {name}=={version}")

                install_cmd = [
                    self.uv_path if self.use_uv else "pip",
                    "pip" if self.use_uv else "",
                    "install",
                    f"{name}=={version}",
                    "--target",
                    download_dir,
                ]
                # Remove empty strings from the command
                install_cmd = [cmd for cmd in install_cmd if cmd]

                subprocess.run(
                    install_cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            logger.info(f"Successfully downloaded packages to {download_dir}")
            return download_dir

        except subprocess.CalledProcessError as original_err:
            logger.error(f"Package download failed: {original_err.stderr}")
            raise DependencyConflictError(
                f"Failed to download packages: {original_err.stderr}"
            ) from original_err

    def cleanup(self):
        """Cleanup temporary directory."""
        try:
            shutil.rmtree(self.temp_dir)
            logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary directory: {e}")

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup()
