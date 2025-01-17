import os
import sys

import click

from .exceptions import (
    DependencyConflictError,
    LayerSizeLimitError,
    PackageNotFoundError,
)
from .logger import setup_logger
from .packager import LambdaPackager


def handle_cli_error(func):
    """Decorator to handle CLI errors gracefully."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            click.echo(f"Error: File not found - {e.filename}", err=True)
            click.echo(
                "Please make sure the file exists and the path is correct.", err=True
            )
            sys.exit(1)
        except PackageNotFoundError as e:
            click.echo(f"Error: {str(e)}", err=True)
            click.echo("Please verify the package name and version.", err=True)
            sys.exit(1)
        except LayerSizeLimitError as e:
            click.echo(f"Error: {str(e)}", err=True)
            click.echo(
                "Try excluding unnecessary packages or increasing the size limit.",
                err=True,
            )
            sys.exit(1)
        except DependencyConflictError as e:
            click.echo(f"Error: {str(e)}", err=True)
            click.echo("Please check for conflicting package versions.", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}", err=True)
            click.echo("If this persists, please report this issue.", err=True)
            sys.exit(1)

    return wrapper


@click.group(help="Lambda Bundler CLI - Create and manage AWS Lambda layers")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """Lambda Bundler CLI entry point."""
    setup_logger(verbose)


@cli.command(name="create-layer")
@click.option("-r", "--requirements", help="Path to requirements.txt")
@click.option("-p", "--packages", help="Comma-separated list of packages")
@click.option("-n", "--name", required=True, help="Layer name")
@click.option("--runtime", default="python3.9", help="Python runtime version")
@click.option("--output-dir", default="./dist", help="Output directory")
@handle_cli_error
def create_layer(requirements, packages, name, runtime, output_dir):
    """Create a Lambda layer from requirements or package list."""
    # Validate input
    if not requirements and not packages:
        click.echo("Error: Must specify either --requirements or --packages", err=True)
        sys.exit(1)

    if requirements and not os.path.exists(requirements):
        raise FileNotFoundError(2, "No such file", requirements)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    packager = LambdaPackager(runtime, output_dir)

    if requirements:
        click.echo(f"Creating layer from requirements file: {requirements}")
        path = packager.create_layer_from_requirements(requirements, name)
        click.echo(f"✓ Created layer at: {path}")
    else:
        package_list = [p.strip() for p in packages.split(",")]
        click.echo(f"Creating layer from packages: {', '.join(package_list)}")
        path = packager.create_layer_from_packages(package_list, name)
        click.echo(f"✓ Created layer at: {path}")


@cli.command(name="analyze")
@click.option("-r", "--requirements", required=True, help="Path to requirements.txt")
@handle_cli_error
def analyze(requirements):
    """Analyze dependencies in requirements.txt file."""
    if not os.path.exists(requirements):
        raise FileNotFoundError(2, "No such file", requirements)

    click.echo(f"Analyzing dependencies in: {requirements}")
    packager = LambdaPackager("python3.9", "./dist")

    try:
        # Read requirements file
        with open(requirements) as f:
            packages = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        deps = packager.dependency_manager.resolve_dependencies(packages)

        # Display results
        click.echo("\nPackage Dependencies:")
        click.echo("=" * 50)

        # Group by top-level and sub-dependencies
        top_level = {
            name: version
            for name, version in deps.items()
            if name.lower()
            in [
                p.split("[")[0].split("==")[0].split(">=")[0].split("<")[0].lower()
                for p in packages
            ]
        }

        # Show top-level dependencies
        click.echo("\nTop-level Packages:")
        click.echo("-" * 20)
        for name, version in sorted(top_level.items()):
            click.echo(f"• {name:<20} {version}")

        # Show all dependencies
        click.echo("\nAll Dependencies:")
        click.echo("-" * 20)
        for name, version in sorted(deps.items()):
            if name not in top_level:
                click.echo(f"• {name:<20} {version}")

        # Get total size (if available)
        click.echo("\nSummary:")
        click.echo("-" * 20)
        click.echo(f"Total packages: {len(deps)}")
        click.echo(f"Top-level packages: {len(top_level)}")
        click.echo(f"Sub-dependencies: {len(deps) - len(top_level)}")

    except Exception as e:
        click.echo(f"Error analyzing dependencies: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
