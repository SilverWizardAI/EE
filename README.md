# 🏛️ Silver Wizard Software - Enterprise Edition (EE)

**Enterprise Architecture & Infrastructure Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Built with UV](https://img.shields.io/badge/built%20with-UV-blueviolet)](https://github.com/astral-sh/uv)

---

## 🎯 Overview

**EE (Enterprise Edition)** is the foundational infrastructure and tooling platform for the entire **Silver Wizard Software** ecosystem. It provides:

- **Shared Infrastructure Components** - Reusable libraries and frameworks
- **Development Tools** - CLI tools, build systems, and automation
- **Cross-Project Standards** - Coding standards, patterns, and best practices
- **Integration Framework** - APIs and protocols for inter-project communication
- **Enterprise Architecture** - Documentation, ADRs, and system design

---

## 🏗️ Architecture

### Silver Wizard Software Ecosystem

EE is the infrastructure backbone for these Silver Wizard products:

| Project | Description | Status |
|---------|-------------|--------|
| **MacR** | Mac Retriever - Email & photo management | Active |
| **MacR-PyQt** | PyQt version of Mac Retriever | Active |
| **C3** | Campaign Command & Control - Orchestration | Active |
| **CMC** | Content Management & Control | Active |
| **Brand_Manager** | Brand & marketing asset management | Active |
| **FS** | File System utilities | Active |
| **MM** | Media Manager | Active |
| **NG** | Next Generation tools | Development |
| **PIW** | Python Install Wizard | Active |
| **PQTI** | PyQt Tools & Infrastructure | Active |

### Core Principles

1. **DRY (Don't Repeat Yourself)** - Shared code lives here
2. **Separation of Concerns** - Clear architectural boundaries
3. **Security by Default** - Secure configurations out of the box
4. **Performance First** - Optimized, benchmarked infrastructure
5. **Developer Experience** - Easy to use, well-documented tools

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- UV package manager (recommended)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/SilverWizardAI/EE.git
cd EE

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up development environment
uv sync

# Run tests
uv run pytest
```

---

## 📂 Project Structure

```
EE/
├── .claude/                 # Claude AI configuration
├── infrastructure/          # Core infrastructure components
│   ├── common/             # Shared utilities
│   ├── security/           # Security frameworks
│   └── monitoring/         # Observability tools
├── tools/                  # Development tools
│   ├── cli/               # Command-line tools
│   ├── build/             # Build systems
│   └── testing/           # Testing frameworks
├── shared/                 # Shared libraries
│   ├── models/            # Data models
│   ├── protocols/         # Communication protocols
│   └── interfaces/        # API interfaces
├── templates/              # Project templates
├── docs/                   # Architecture documentation
│   ├── adr/               # Architecture Decision Records
│   ├── api/               # API documentation
│   └── guides/            # Development guides
├── tests/                  # Infrastructure tests
├── .gitignore
├── README.md              # This file
└── pyproject.toml         # Project configuration
```

---

## 🔧 Core Components

### Infrastructure

- **Common Utilities** - Logging, configuration, error handling
- **Security Framework** - Authentication, authorization, encryption
- **Monitoring & Observability** - Metrics, logging, tracing
- **Data Access Layer** - Database abstractions and ORM utilities

### Development Tools

- **Build System** - Unified build and packaging tools
- **CLI Framework** - Command-line interface foundation
- **Testing Tools** - Test fixtures, mocks, and utilities
- **Code Quality** - Linters, formatters, and quality gates

### Shared Libraries

- **Data Models** - Common data structures and schemas
- **Communication Protocols** - Inter-service communication
- **API Interfaces** - Standardized API contracts
- **UI Components** - Reusable UI widgets and themes

---

## 📚 Documentation

- **[Architecture Overview](docs/architecture/overview.md)** - System architecture
- **[API Documentation](docs/api/)** - API reference
- **[Development Guides](docs/guides/)** - How-to guides
- **[ADRs](docs/adr/)** - Architecture decisions
- **[Contributing](docs/CONTRIBUTING.md)** - Contribution guidelines

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=infrastructure --cov=tools --cov=shared

# Run specific test suite
uv run pytest tests/infrastructure/

# Run with verbose output
uv run pytest -v
```

---

## 🤝 Contributing

EE is the foundation for all Silver Wizard Software projects. Contributions should:

1. **Maintain High Quality** - Comprehensive tests and documentation
2. **Follow Standards** - Adhere to coding standards and patterns
3. **Think Cross-Project** - Consider impact on all sister projects
4. **Document Decisions** - Create ADRs for architectural changes

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🔗 Links

- **GitHub Organization:** [SilverWizardAI](https://github.com/SilverWizardAI)
- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/SilverWizardAI/EE/issues)
- **Discussions:** [GitHub Discussions](https://github.com/SilverWizardAI/EE/discussions)

---

## 📊 Status

**Current Version:** 0.1.0 (Initial Development)
**Status:** 🚧 Active Development
**Last Updated:** 2026-02-05

---

**Built with ❤️ by Silver Wizard Software**
