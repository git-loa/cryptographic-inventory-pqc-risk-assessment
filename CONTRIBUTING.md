# Contributing Guidelines

Thank you for your interest in contributing to the TLS Inventory Scanner & PQC
Risk Assessment project. This project is designed for learning, experimentation,
and practical exploration of TLS cryptography and early post‑quantum security.

Contributions are welcome as long as they align with the project's goals of
clarity, correctness, and educational value.

---

## How to Contribute

### 1. Fork the repository
Create your own fork and work from a feature branch.

### 2. Keep changes small and focused
Each pull request should address a single issue, feature, or improvement.

### 3. Follow the code style
This project uses:
- `black` for formatting
- `flake8` for linting
- `mypy` for type checking
- `pre-commit` for consistency

Install hooks with:

pre-commit install

Code

### 4. Add tests when appropriate
Unit tests live in `tests/`, and fuzz tests use Hypothesis.

### 5. Document new functionality
If you add or modify pipeline stages, update:
- relevant docstrings
- the README
- any templates or configuration files affected

### 6. Submit a pull request
Include a short description of the change and why it improves the project.

---

## Contribution Scope

This project is not intended to be a production‑grade scanner. Contributions
should focus on:

- improving clarity and readability
- adding small, testable components
- enhancing TLS/PQC analysis logic
- expanding reporting capabilities
- improving developer experience

Large architectural changes or production‑level features may not be accepted.

---

## Code of Conduct

Be respectful, constructive, and collaborative.
This project is for learning and exploration — keep discussions positive and helpful.
