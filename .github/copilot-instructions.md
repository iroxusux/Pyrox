# Pyrox AI Coding Guidelines

## Architecture Overview

Pyrox is a Python framework providing core services, models, and abstractions for building industrial automation applications. It uses an **interface-driven, mixin-based architecture** with clear separation between interfaces, models, services, and tasks.

### Key Components

- **Interfaces** (`pyrox/interfaces/`): Abstract contracts (IApplication, IApplicationTask, IGuiBackend, IWorkspace) defining system behavior
- **Models** (`pyrox/models/`): Concrete implementations of interfaces with business logic
- **Services** (`pyrox/services/`): Singleton-style utilities (logging, environment, file, GUI management)
- **Tasks** (`pyrox/tasks/`): Modular application extensions implementing IApplicationTask

### Core Patterns

**ServicesRunnableMixin**: The foundation for classes needing service access. Provides:
- `self.env` - Environment variable management
- `self.gui` - GUI backend manager
- `self.logging` - Logging service
- `self.backend` - Active GUI backend instance

**Factory Pattern**: `MetaFactory` enables type registration for extensible object creation:
```python
class MyFactory(MetaFactory):
    _registered_types = {}  # Auto-populated by metaclass
```

**Application Tasks**: Extend `IApplicationTask` for injectable functionality:
```python
class MyTask(IApplicationTask):
    def inject(self): ...  # Add to application context
    def uninject(self): ...  # Remove from application
    def run(self): ...  # Execute task logic
```

## Development Workflows

### Installation & Setup
```bash
# Use install.sh (handles Python 3.13 check, venv, dependencies, git hooks)
./install.sh

# Manual alternative
pip install -e . --upgrade
python utils/setup_hooks.py  # Set up pre-commit hooks
```

### Key Commands
- **Sync README badges**: `python utils/sync_readme.py` (auto-runs via git hooks)
- **Extract TODOs**: `python utils/extract_todos.py` (generates code_todos.md)
- **Run tests**: `pytest pyrox/services/test/` or `pytest pyrox/test/`

### Environment Configuration
Pyrox uses `.env` files loaded via `EnvManager`. Access via:
```python
self.env.get(self.env_keys.core.APP_NAME, 'Default', str)
```

## Critical Code Conventions

### Type Annotations
Always use forward references:
```python
from __future__ import annotations
from typing import Optional, Any
```

### Logging Pattern
Use the singleton log service:
```python
from pyrox.services.logging import log
log(self).debug('Message')  # Automatically uses class name as logger
```

### GUI Backend Abstraction
Never import tkinter directly in application code. Use:
```python
self.backend.create_root_window()  # Framework-agnostic
```

### Abstract Base Classes
Define contracts with ABC:
```python
from abc import abstractmethod
class IMyInterface(ABC):
    @abstractmethod
    def my_method(self) -> None: ...
```

### RuntimeDict Pattern
For auto-saving dictionaries with callbacks:
```python
self.data = RuntimeDict(callback=self.save)
self.data['key'] = 'value'  # Triggers callback automatically
```

## File Organization

```
pyrox/
├── interfaces/        # Abstract interfaces only (no implementations)
├── models/           # Concrete implementations
│   ├── factory.py    # MetaFactory and factory patterns
│   ├── runtime.py    # RuntimeDict and lifecycle management
│   ├── services.py   # ServicesRunnableMixin
│   └── gui/          # GUI models (Tk-specific in gui/tk/)
├── services/         # Singleton-style utilities
│   ├── logging.py    # log() function
│   ├── env.py        # EnvManager
│   └── test/         # Service unit tests
├── tasks/            # Application task implementations
└── utils/            # Build/dev utilities (not runtime code)
```

## Testing

- Tests live in `services/test/`, `models/test/`, or adjacent `test/` dirs
- Use pytest with fixtures from `pyrox/services/test/`
- Log output controlled via pytest.ini_options in pyproject.toml

## Dependencies

**Required**: Python 3.13.9+ (specified in pyproject.toml)
**Key libs**: lxml, pandas, Pillow, pywin32 (Windows), platformdirs, pdfplumber

## Common Gotchas

1. **Menu checkbuttons**: Initial checked state doesn't display on Windows Tkinter (see TODO.md)
2. **Git hooks**: Use `utils/setup_hooks.py` to sync README badges with pyproject.toml version
3. **Virtual environment**: Always activate `.venv` before development
4. **Imports**: Use relative imports within pyrox package, absolute for external
5. **GUI framework**: Tkinter is default but architecture supports other backends via IGuiBackend

## Version Management

Version tracked in `pyproject.toml` and auto-synced to README.md badges via pre-commit hook.

## When Extending Pyrox

1. **New application type**: Subclass `Application` from `pyrox.application`
2. **New task**: Implement `IApplicationTask` interface
3. **New service**: Add to `pyrox/services/` following singleton pattern
4. **New GUI component**: Create in `models/gui/` with framework-agnostic interface
5. **New interface**: Add to `interfaces/` (no implementation code)

## Cross-Project Context

ControlRox builds on Pyrox - changes here affect all downstream applications. Maintain backward compatibility in interfaces.
