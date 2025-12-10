# Pyrox

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
![Development Status](https://img.shields.io/badge/status-beta-orange.svg)
![Version](https://img.shields.io/badge/version-2.0.52-blue.svg)

**Pyrox** is a Python-based engine that provides common services, models, and abstractions for building different types of applications. Originally part of a comprehensive industrial automation suite, Pyrox has been refactored into a focused core library that serves as the foundation for specialized applications like [ControlRox](https://github.com/iroxusux/ControlRox).

## 🚀 Key Features

### 🏗️ Core Application Framework

- **Task-Based Architecture**: Modular application structure with extensible tasks and services
- **Abstract Base Classes**: Well-defined interfaces for consistent application development
- **Factory Pattern Implementation**: Extensible object creation patterns for different application types
- **Model-View-Controller Support**: Clean separation of concerns for maintainable applications

### 🎨 GUI Framework & Components

- **Modern Tkinter Interface**: Professional-grade user interface components and themes
- **Reusable GUI Models**: Common GUI patterns like frames, notebooks, menus, and dialogs
- **Workspace Management**: Multi-window support with dockable frames and layout management
- **Legacy Support**: Backwards compatibility with existing GUI implementations

### 🔧 Common Services & Utilities

- **File & Stream Processing**: Robust file handling, archiving, and data streaming utilities
- **Environment Management**: Cross-platform configuration and environment variable handling
- **Logging & Debugging**: Comprehensive logging framework with debug tools
- **Data Manipulation**: XML processing, dictionary utilities, and object manipulation
- **Timer & Notification Services**: Event scheduling and notification systems

### 🧩 Extensible Models

- **Application Models**: Base classes for building different types of applications
- **GUI Component Models**: Reusable interface components for consistent user experiences
- **Abstract Interfaces**: Well-defined contracts for extending functionality
- **Configuration Management**: Flexible configuration handling for various application needs

## 📦 Installation

### Requirements

- **Python 3.13+** (Required)
- Cross-platform support (Windows, Linux, macOS)
- Compatible with applications built on the Pyrox framework

### Quick Install

```bash
# Clone the repository
git clone https://github.com/iroxusux/Pyrox.git
cd Pyrox

# Run the installation script (recommended)
./install.sh

# Or install manually:
pip install -e . --upgrade

# Set up Git hooks (for README badge sync)
python utils/setup_hooks.py

# Manually sync README badges from pyproject.toml
python utils/sync_readme.py
```

### Dependencies

Pyrox automatically installs the following key dependencies:

- **lxml** - XML processing capabilities
- **pandas** - Data manipulation and analysis
- **openpyxl** - Excel file processing
- **Pillow** - Image processing support
- **PyPDF2, pdfplumber, PyMuPDF** - PDF processing utilities
- **platformdirs** - Cross-platform directory management
- **pywin32** - Windows integration (Windows only)

## 🏁 Quick Start

### Basic Application Setup

```python
from pyrox.models.application import Application
from pyrox.models.menu import Menu

# Create a basic application
class MyApp(Application):
    def __init__(self):
        super().__init__(
            app_name="My Application",
            author_name="Your Name",
            version="1.0.0"
        )
    
    def initialize(self):
        # Set up your application-specific logic
        self.setup_gui()
        self.load_tasks()

# Initialize and run the application
app = MyApp()
app.run()
```

### Using Core Services

```python
from pyrox.services.file import FileService
from pyrox.services.logging import get_logger
from pyrox.services.env import EnvironmentService

# File operations
file_service = FileService()
data = file_service.read_json("config.json")

# Logging
logger = get_logger(__name__)
logger.info("Application started")

# Environment management
env_service = EnvironmentService()
debug_mode = env_service.get_bool("DEBUG", default=False)
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure your settings
PYROX_DEBUG=false
PYROX_LOG_LEVEL=INFO
PYROX_CONFIG_DIR=./config
```

## 🏗️ Architecture

### Core Modules

```text
pyrox/
├── models/                  # Core data models and abstractions
│   ├── application.py       # Base application framework
│   ├── menu.py             # Menu system models
│   ├── model.py            # Base model classes
│   ├── task.py             # Task framework
│   ├── abc/                # Abstract base classes
│   │   ├── factory.py      # Factory pattern implementations
│   │   ├── list.py         # List abstractions
│   │   ├── meta.py         # Metaclass utilities
│   │   ├── network.py      # Network abstractions
│   │   ├── runtime.py      # Runtime abstractions
│   │   ├── save.py         # Save/load abstractions
│   │   └── stream.py       # Stream processing abstractions
│   ├── gui/                # GUI component models
│   │   ├── backend.py      # GUI backend abstractions
│   │   ├── commandbar.py   # Command bar components
│   │   ├── contextmenu.py  # Context menu models
│   │   ├── frame.py        # Frame abstractions
│   │   ├── listbox.py      # Listbox components
│   │   ├── menu.py         # Menu components
│   │   ├── notebook.py     # Notebook/tab components
│   │   ├── treeview.py     # Tree view components
│   │   └── workspace.py    # Workspace management
│   └── test/               # Model unit tests
├── services/               # Business logic and utilities
│   ├── archive.py          # Archive and compression services
│   ├── bit.py              # Bit manipulation utilities
│   ├── byte.py             # Byte processing services
│   ├── decorate.py         # Decorator utilities
│   ├── dict.py             # Dictionary manipulation
│   ├── env.py              # Environment management
│   ├── factory.py          # Factory service implementations
│   ├── file.py             # File handling utilities
│   ├── gui.py              # GUI utility services
│   ├── logging.py          # Logging framework
│   ├── logic.py            # Common logic utilities
│   ├── notify_services.py  # Notification services
│   ├── object.py           # Object manipulation utilities
│   ├── search.py           # Search and filtering services
│   ├── stream.py           # Stream processing services
│   ├── timer.py            # Timer and scheduling services
│   ├── xml.py              # XML processing utilities
│   └── test/               # Service unit tests
├── tasks/                  # Task framework and built-in tasks
│   ├── builtin/            # Built-in task implementations
│   └── test/               # Task unit tests
└── ui/                     # User interface assets
    ├── icons/              # Application icons
    └── splash/             # Splash screen assets
```

### Key Design Patterns

- **Abstract Base Classes**: Consistent interfaces across all components
- **Factory Pattern**: Flexible object creation for different application types  
- **Task-Based Design**: Modular functionality through application tasks
- **Observer Pattern**: Event-driven updates and notifications
- **Model-View-Controller**: Clear separation of concerns for maintainable code

## 🎯 Use Cases

### Application Developers

- Build applications with consistent architecture and patterns
- Leverage proven GUI components and frameworks
- Utilize common services for file handling, logging, and configuration
- Extend functionality through the task-based system

### System Integrators

- Create specialized applications using Pyrox as a foundation
- Implement domain-specific functionality on top of core services
- Maintain consistency across multiple related applications
- Benefit from shared models and abstractions

### Framework Users

- Industrial automation applications (like [ControlRox](https://github.com/iroxusux/ControlRox))
- Desktop applications requiring robust GUI frameworks
- Applications needing task-based architecture
- Projects requiring consistent logging, configuration, and file handling

### Library Developers

- Extend Pyrox with domain-specific modules
- Implement new task types and services
- Create specialized GUI components
- Build on proven architectural patterns

## 🤖 Automated Badge Synchronization

Pyrox automatically keeps README badges in sync with your `pyproject.toml` metadata:

### What Gets Synced

- **Python Version**: From `requires-python` field
- **License**: Extracted from `classifiers`
- **Development Status**: From development status classifiers
- **Project Version**: From `version` field

### How It Works

- **Pre-commit Automation**: Handles both version checking and badge syncing before each commit
  - Version Increment Check: Ensures version is bumped for code changes
  - Badge Synchronization: Automatically syncs badges from `pyproject.toml`
- **Manual Tools**:
  - `python utils/sync_readme.py` - Sync badges anytime
  - `python utils/check_version_increment.py` - Check version increment requirement

### Supported Classifiers

```toml
[project]
version = "1.5.0"
requires-python = ">=3.13"
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 3.13",
]
```

This ensures your README always reflects your actual project configuration!

### Version Increment Enforcement

The pre-commit hook automatically checks if code changes require a version bump:

- **Smart Detection**: Distinguishes between code changes and documentation updates
- **Flexible Rules**: Only enforces version increments for actual code changes
- **Clear Guidance**: Provides helpful suggestions for version increments
- **Bypass for Docs**: Allows commits that only change documentation/config files

**Files that DON'T require version bumps:**

- `README.md` and other `.md` files
- Documentation in `docs/` directory  
- `.gitignore`, `LICENSE`, `.yml/.yaml` files
- Git hooks and utility scripts (`utils/sync_*.py`, `hooks/`)

**Files that DO require version bumps:**

- Python source code in `pyrox/`
- `pyproject.toml` dependencies or configuration
- Any other source code files

## 🔧 Advanced Features

### Custom Application Development

```python
from pyrox.models.application import Application
from pyrox.models.task import Task

class CustomTask(Task):
    """Custom task implementation."""
    
    def execute(self):
        # Implement your task logic
        self.logger.info("Executing custom task")
        return True

class CustomApplication(Application):
    """Custom application built on Pyrox."""
    
    def load_tasks(self):
        # Register your custom tasks
        self.register_task("custom", CustomTask)
```

### GUI Component Extension

```python
from pyrox.models.gui.frame import Frame
from pyrox.services.gui import GuiService

class CustomFrame(Frame):
    """Custom GUI frame."""
    
    def setup_widgets(self):
        # Implement your GUI layout
        self.gui_service.create_button(
            parent=self,
            text="Custom Action",
            command=self.handle_action
        )
```

### Service Extension

```python
from pyrox.services.object import ObjectService
from pyrox.services.logging import get_logger

class CustomService(ObjectService):
    """Custom service implementation."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process_data(self, data):
        # Implement your service logic
        return self.transform(data)
```

## 🛠️ Development

### Project Structure

```text
Pyrox/
├── pyrox/                    # Main package
│   ├── models/              # Core models and abstractions
│   ├── services/            # Business logic and utilities
│   ├── tasks/               # Task framework
│   └── ui/                  # User interface assets
├── docs/                     # Documentation and examples
├── build/                    # Build outputs
├── logs/                     # Application logs
├── .env.example              # Environment template
├── pyproject.toml           # Project configuration
├── build.sh                 # Build script
└── install.sh               # Installation script
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest pyrox/models/test/
pytest pyrox/services/test/

# Run with coverage
pytest --cov=pyrox
```

### Building Distribution

```bash
# Build package
./build.sh

# Install locally for development
pip install -e . --upgrade
```

## 📚 Documentation

- **[API Documentation](docs/)** - Detailed API reference for all modules
- **[Architecture Guide](docs/architecture.md)** - Deep dive into Pyrox architecture
- **[Development Guide](docs/development.md)** - Contributing and extension guidelines
- **[Environment Configuration](docs/environment.md)** - Complete environment setup guide

## 🏭 Related Projects

- **[ControlRox](https://github.com/iroxusux/ControlRox)** - Industrial automation application built on Pyrox
- Applications using Pyrox as their foundation benefit from shared models and services

## 🤝 Contributing

Pyrox is a foundational library for Python applications. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your contributions maintain the architectural consistency and include appropriate tests.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Brian LaFond**  
📧 [Brian.L.LaFond@gmail.com](mailto:Brian.L.LaFond@gmail.com)  
🐙 [GitHub](https://github.com/iroxusux)

## 🙏 Acknowledgments

- The Python community for excellent libraries and frameworks
- Contributors who have helped shape the architecture and design
- Applications built on Pyrox that have driven feature development
- The open-source community for inspiration and best practices

---

**Pyrox** - *Python-based engine for services and common models across different types of applications*
