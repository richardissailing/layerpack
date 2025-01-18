# layerpack

[![CI](https://github.com/yourusername/layerpack/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/layerpack/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/layerpack.svg)](https://badge.fury.io/py/layerpack)
[![Python Version](https://img.shields.io/pypi/pyversions/layerpack.svg)](https://pypi.org/project/layerpack/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for simplifying AWS Lambda deployment by automatically managing dependencies and creating deployment packages. Uses UV for reliable dependency resolution.

## Features

- Automatically detects and downloads required Python packages
- Creates Lambda-compatible ZIP files with all dependencies
- Supports custom package versions and requirements.txt
- Handles platform-specific dependencies for AWS Lambda
- Optimizes package size through selective inclusion
- Supports layer creation with multiple runtimes
- Uses UV for reliable dependency resolution

## Installation

You can install layerpack using pip:

```bash
pip install layerpack
```

Or using Poetry:

```bash
poetry add layerpack
```

## Usage

### Basic Usage

```python
from layerpack import LambdaPackager

# Initialize packager
packager = LambdaPackager(
    runtime="python3.9",
    output_dir="./dist"
)

# Create a layer from requirements.txt
packager.create_layer_from_requirements("requirements.txt", "my-layer")

# Or specify packages directly
packager.create_layer_from_packages(
    packages=["pandas", "numpy"],
    layer_name="data-science-layer"
)
```

### Command Line Interface

The library provides a convenient CLI with verbose logging support:

```bash
# Analyze dependencies in requirements.txt
lambda-bundler -v analyze -r requirements.txt

# Create layer from requirements.txt
lambda-bundler create-layer -r requirements.txt -n my-layer

# Create layer from package list
lambda-bundler create-layer -p pandas,numpy -n data-science-layer
```

### Example requirements.txt

```txt
# Core dependencies
requests>=2.31.0
urllib3<2.0.0  # Compatible with requests

# Data processing
pandas==2.2.0
numpy==1.26.4

# AWS 
boto3==1.34.34
botocore==1.34.34

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.1
```

### Advanced Configuration

```python
packager = LambdaPackager(
    runtime="python3.9",
    output_dir="./dist",
    config={
        "exclude_packages": ["pytest", "mock"],
        "include_source": ["custom_module/"],
        "optimization_level": 2,
        "max_size_mb": 250,
        "compatible_runtimes": ["python3.8", "python3.9"]
    }
)
```

## Configuration Options

- `exclude_packages`: List of packages to exclude from the layer
- `include_source`: List of local source directories to include
- `optimization_level`: Python optimization level (0-2)
- `max_size_mb`: Maximum size limit for the layer
- `compatible_runtimes`: List of compatible Python runtimes
- `strip_test_files`: Remove test files to reduce size
- `include_dependencies`: Include transitive dependencies

## Error Handling

The library provides specific exceptions for different error cases:

- `PackageNotFoundError`: Package not found in PyPI
- `IncompatibleRuntimeError`: Package incompatible with Lambda runtime
- `LayerSizeLimitError`: Layer exceeds size limit
- `DependencyConflictError`: Conflicting package dependencies

## Development

### Prerequisites

- Python 3.9 or higher
- UV for dependency management

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/richardissailing/layerpack.git
cd layerpack
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

4. Run linting:
```bash
poetry run ruff check .
poetry run ruff format .
```

### Building and Publishing

1. Build the package:
```bash
poetry build
```

2. Publish to PyPI:
```bash
poetry publish
```

## Best Practices

1. Always specify exact package versions in requirements.txt
2. Use the `exclude_packages` option to remove unnecessary dependencies
3. Set appropriate `compatible_runtimes` for cross-runtime compatibility
4. Enable `strip_test_files` to reduce layer size
5. Use `optimization_level=2` for production deployments
6. Use the verbose flag (-v) when troubleshooting dependency resolution

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Write your changes
4. Run the tests (`poetry run pytest`)
5. Run the linter (`poetry run ruff check .`)
6. Submit a Pull Request

Please make sure your PR includes:
- A clear description of the changes
- Updates to documentation if needed
- Additional tests for new features
- All tests passing and code linted

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.