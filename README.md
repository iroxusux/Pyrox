# Pyrox

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
![Development Status](https://img.shields.io/badge/status-beta-orange.svg)
![Version](https://img.shields.io/badge/version-1.2.6-blue.svg)

**Pyrox** is a comprehensive Python-based ladder logic editor and industrial automation toolset designed for PLC programming, EPLAN integration, and electrical controls automation. Built with a robust Tkinter-based GUI framework, Pyrox provides professional tools for industrial automation engineers and controls programmers.

## 🚀 Key Features

### 🔧 PLC Integration & Programming

- **Multi-Vendor PLC Support**: Allen-Bradley (Rockwell), Ford, GM, and other industrial controllers
- **Real-time PLC Communication**: Live tag monitoring, reading/writing PLC values
- **L5X File Processing**: Import, export, and manipulate Logix Designer files
- **Ladder Logic Editor**: Visual ladder logic programming with syntax highlighting
- **Controller Validation**: Automated PLC configuration validation and verification

### 📋 EPLAN Integration

- **EPLAN Project Import**: Parse and validate EPLAN electrical schematics
- **Device Mapping**: Automatic mapping between EPLAN devices and PLC I/O
- **Project Validation**: Cross-reference EPLAN designs with PLC configurations
- **PDF Schematic Parsing**: Extract device information from EPLAN-generated PDFs

### 🏗️ Industrial Automation Tools

- **Emulation Generation**: Generate PLC emulation routines for testing
- **Checklist Management**: Create and manage commissioning checklists from markdown templates
- **Tag Management**: Comprehensive PLC tag browsing, editing, and monitoring
- **Watch Tables**: Real-time PLC data monitoring and debugging tools

### 🎨 Professional GUI Framework

- **Modern Tkinter Interface**: Professional-grade user interface with themes
- **Task-Based Architecture**: Modular application structure with extensible tasks
- **Multi-Window Support**: Dockable frames and workspace management
- **Debug Tools**: Integrated debugging and development tools

## 📦 Installation

### Requirements

- **Python 3.13+** (Required)
- Windows (Primary platform - includes `pywin32` support)
- Compatible with Allen-Bradley PLCs and EPLAN software

### Quick Install

```bash
# Clone the repository
git clone https://github.com/iroxusux/Pyrox.git
cd Pyrox

# Install in development mode
pip install -e . --upgrade

# Or install directly from source
pip install . --upgrade
```

### Dependencies

Pyrox automatically installs the following key dependencies:

- **lxml** - XML processing for L5X files
- **pylogix** - Allen-Bradley PLC communication
- **pandas** - Data manipulation and analysis
- **openpyxl** - Excel file processing
- **Pillow** - Image processing
- **PyPDF2, pdfplumber, PyMuPDF** - PDF processing for EPLAN integration
- **platformdirs** - Cross-platform directory management

## 🏁 Quick Start

### Basic Application Setup

```python
from pyrox.applications.app import App
from pyrox.models import ApplicationConfiguration

# Create application configuration
config = ApplicationConfiguration(
    app_name="My PLC Application",
    author_name="Your Name",
    version="1.0.0"
)

# Initialize and run the application
app = App(config)
app.run()
```

### PLC Connection Example

```python
from pyrox.applications.plcio import PlcIoTask
from pyrox.models import ConnectionParameters

# Configure PLC connection
connection_params = ConnectionParameters(
    ip_address="192.168.1.100",
    slot=0
)

# Create PLC I/O task
plc_task = PlcIoTask(app)
plc_task.start()
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure your settings
PYROX_DEBUG=false
PLC_DEFAULT_IP=192.168.1.100
EPLAN_DEFAULT_PROJECT_DIR=./projects
```

## 🏗️ Architecture

### Core Modules

```text
pyrox/
├── applications/          # Application implementations
│   ├── app.py            # Main application framework
│   ├── plcio.py          # PLC I/O and communication
│   ├── ladder.py         # Ladder logic editor
│   ├── ford.py           # Ford-specific PLC support
│   └── indicon.py        # Indicon automation tools
├── models/               # Data models and core objects
│   ├── plc/             # PLC data structures
│   ├── eplan/           # EPLAN integration models
│   ├── gui/             # GUI components and frames
│   └── abc/             # Abstract base classes
├── services/            # Business logic and services
│   ├── eplan.py         # EPLAN processing services
│   ├── env.py           # Environment configuration
│   ├── file.py          # File handling utilities
│   └── checklist.py     # Checklist management
└── tasks/               # Modular application tasks
    ├── ladder.py        # Ladder logic tasks
    └── tools/           # Built-in tools and utilities
```

### Key Design Patterns

- **MVC Architecture**: Clear separation of models, views, and controllers
- **Factory Pattern**: Extensible object creation for different PLC types
- **Task-Based Design**: Modular functionality through application tasks
- **Observer Pattern**: Event-driven updates and notifications

## 🎯 Use Cases

### Industrial Automation Engineers

- Design and validate PLC control systems
- Import EPLAN electrical designs and cross-reference with PLC configurations
- Generate commissioning checklists and documentation

### Controls Programmers

- Develop and debug ladder logic programs
- Monitor PLC tags and variables in real-time
- Validate controller configurations and I/O mappings

### System Integrators

- Integrate multiple automation systems (EPLAN + PLC)
- Generate emulation routines for testing
- Manage project documentation and validation workflows

### Commissioning Engineers

- Use automated checklists for system commissioning
- Verify PLC configurations against design specifications
- Monitor and troubleshoot live PLC systems

## 🔧 Advanced Features

### Custom PLC Support

```python
from pyrox.models.plc import Controller, ControllerMatcher

class CustomController(Controller):
    """Custom PLC controller implementation."""
    
class CustomControllerMatcher(ControllerMatcher):
    """Matcher for custom controllers."""
    
    def is_match(self, controller_data) -> bool:
        return controller_data.get('type') == 'CustomPLC'
```

### EPLAN Integration

```python
from pyrox.services.eplan import import_eplan
from pyrox.models.plc import Controller

# Import EPLAN project and validate against PLC
controller = Controller.from_file("project.L5X")
import_eplan(controller)  # Validates EPLAN design against PLC config
```

### Checklist Automation

```python
from pyrox.services.checklist import compile_checklist_from_md_file

# Generate structured checklist from markdown
checklist = compile_checklist_from_md_file("commissioning_checklist.md")
print(f"Found {len(checklist['sections'])} checklist sections")
```

## 🛠️ Development

### Project Structure

```text
Pyrox/
├── pyrox/                    # Main package
├── docs/                     # Documentation and examples
├── samples/                  # Sample projects and scripts  
├── build/                    # Build outputs
├── logs/                     # Application logs
├── .env.example              # Environment template
├── pyproject.toml           # Project configuration
├── build.sh / build.ps1     # Build scripts
└── deploy.sh / deploy.ps1   # Deployment scripts
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest pyrox/services/test/
pytest pyrox/models/test/

# Run with coverage
pytest --cov=pyrox
```

### Building Distribution

```bash
# Build executable (Windows)
./build.ps1

# Deploy to production
./deploy.ps1
```

## 📚 Documentation

- **[Environment Configuration Guide](ENVIRONMENT.md)** - Complete environment setup
- **[API Documentation](docs/)** - Detailed API reference
- **[Sample Projects](samples/)** - Example implementations
- **[Development Guide](docs/development.md)** - Contributing guidelines

## 🤝 Contributing

Pyrox is developed for industrial automation professionals. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Brian LaFond**  
📧 [Brian.L.LaFond@gmail.com](mailto:Brian.L.LaFond@gmail.com)  
🐙 [GitHub](https://github.com/iroxusux)

## 🙏 Acknowledgments

- Allen-Bradley and Rockwell Automation for PLC standards
- EPLAN Software & Service for electrical design integration
- The Python community for excellent automation libraries
- Industrial automation professionals who inspired this project

---

**Pyrox** - *Professional Python-based ladder logic editor and industrial automation toolset*
