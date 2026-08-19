# Contributing to Autonomous Jules

Thank you for your interest in contributing to **Autonomous Jules**! We welcome open-source contributions from developers, researchers, and automation engineers.

## Getting Started

### Prerequisites
- Python 3.10+
- `git`
- `pip`

### Setting Up Local Environment
1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/autonomous-jules.git
   cd autonomous-jules
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the package in editable mode along with testing dependencies:
   ```bash
   pip install -e .
   pip install pytest
   ```

4. Run the test suite:
   ```bash
   python3 -m pytest
   ```

## Workflow & Code Standards
- **Coding Style**: Follow standard PEP 8 conventions.
- **Type Annotations**: Use Python type hints (`typing.Dict`, `typing.Optional`, `typing.List`, etc.) for all public functions and classes.
- **Testing**: Ensure all new features or bug fixes include corresponding unit or integration tests under `tests/`.
- **Documentation**: Update relevant markdown files under `docs/` or `README.md` when introducing new features, CLI commands, or API methods.

## Submitting Pull Requests
1. Create a descriptive branch for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Commit your changes with clear, standard commit messages:
   ```bash
   git commit -m "feat: add support for task polling status in JulesClient"
   ```
3. Push to your fork and submit a Pull Request against the `main` branch.
