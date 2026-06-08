# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (handles Python 3.13 check, venv, dependencies, git hooks)
./install.sh

# Manual install
pip install -e . --upgrade && python utils/setup_hooks.py

# Run all tests
pytest

# Run tests for a specific module
pytest pyrox/models/test/
pytest pyrox/services/test/

# Run a single test file or test
pytest pyrox/models/test/test_factory.py
pytest pyrox/models/test/test_factory.py::TestMetaFactory::test_init_subclass_initializes_registered_types

# Headless (CI) — required when PyQt6 widgets are involved
QT_QPA_PLATFORM=offscreen pytest

# Build distributable
./build.sh

# Extract TODOs to code_todos.md
python utils/extract_todos.py
```

Version is tracked in `pyproject.toml` and auto-synced to `README.md` badges via a pre-commit hook installed by `setup_hooks.py`.

## Architecture

Pyrox is a PyQt6-based application framework for industrial automation tooling. It follows a strict **interface → model → service → task** layering:

```
pyrox/interfaces/    # Protocols and ABCs only — zero implementation code
pyrox/models/        # Concrete implementations of interfaces
pyrox/services/      # Static utility classes (never instantiated)
pyrox/tasks/         # ApplicationTask subclasses (built-in features)
```

**Downstream applications** (e.g. ControlRox) depend on all four layers. Changes to `interfaces/` or `ServicesRunnableMixin` are breaking changes downstream.

### ServicesRunnableMixin

The base mixin for any class that needs framework services. Composed of focused sub-mixins that expose static service classes as properties:

| Property | Provides |
|---|---|
| `self.env` / `self.env_keys` | `EnvManager` + `EnvironmentKeys` |
| `self.logging` / `self.log()` | `LoggingManager` |
| `self.gui` | `GuiManager` (PyQt6) |
| `self.root_window`, `self.file_menu`, etc. | Convenience accessors on `GuiManager` |
| `self.directory` | `PlatformDirectoryService` |

`GuiManager`, `EnvManager`, `LoggingManager`, and `MenuRegistry` are static classes — never instantiate them.

### ApplicationTask (plugin system)

Subclass `ApplicationTask` to add a new panel/feature. `FactoryTypeMeta` auto-registers every subclass at class-definition time; they are built automatically at app startup — no manual factory registration needed.

```python
class MyTask(ApplicationTask):
    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self.register_menu_command(menu=self.file_menu, ...)

    def create_task_frame(self) -> TaskFrame:
        return MyTaskFrame(self.application.workspace.workspace_area)
```

Call `create_or_raise_frame()` (not `create_task_frame()` directly) to show/raise the window.

### TaskFrame (GUI widgets)

All custom widgets subclass `TaskFrame` (`pyrox.models.gui.frame`). Always add `task_frame.root` (the inner `QWidget`) to Qt layouts and splitters — not the `TaskFrame` object itself.

`Workspace` (`pyrox.models.gui.workspace`) provides a VSCode-style layout: vertical icon sidebar, central area for `TaskFrame` panels, log window, and status bar.

### Event Bus

Decouple components with typed, domain-scoped buses:

```python
class MyEventBus(EventBus[MyEventType, MyEvent]):
    pass

MyEventBus.subscribe(MyEventType.SOMETHING, callback)
MyEventBus.publish(MyEvent(event_type=MyEventType.SOMETHING, ...))
```

Each `EventBus` subclass owns its own `_subscribers` dict.

### GUI state persistence

Use `GuiStateService` (not `.env`) to persist layout preferences (splitter ratios, sidebar widths, etc.) between sessions. State is stored as JSON via `PlatformDirectoryService` — never hardcode paths.

```python
# Get-merge-capture-save pattern
state = GuiStateService.get_geometry_state()
state['sidebar_width'] = new_width
GuiStateService.capture_geometry_state(state)
GuiStateService.save()
```

### RuntimeDict

A `dict` subclass that fires a callback on every write — use it for data that must auto-save:

```python
self.data = RuntimeDict(callback=self.save)
self.data['key'] = 'value'  # triggers self.save() automatically
```

## Code Conventions

**Typing** — built-in generics only:
- `list[str]`, `dict[str, int]`, `X | Y` — never `List`, `Dict`, `Optional`, `Union`
- No forward-reference strings. Use `TYPE_CHECKING` guards instead.
- Do **not** add `from __future__ import annotations` to new files (some legacy files have it).

**Logging**:
```python
from pyrox.services.logging import log
log(self).info('message')       # inside instance methods
log(MyClass).warning('...')     # outside instance context
```

**Interfaces** — use `Protocol` with `@runtime_checkable` for structural contracts; `ABC`/`ABCMeta` for explicit hierarchies. No implementation code in `interfaces/`.

**GUI** — PyQt6 only. `notebook.py` in `models/gui/` is legacy tkinter; do not use it in new code.

**Imports** — use relative imports within the `pyrox` package; absolute imports for external dependencies.

## Testing Conventions

- Plain pytest functions or classes — **never** `unittest.TestCase`
- `@pytest.fixture` with appropriate `scope` for shared setup
- `monkeypatch` for simple attribute/env overrides; `unittest.mock.patch` for complex mocks
- Plain `assert` statements and `pytest.raises` — no `self.assert*`
- Test files live adjacent to their module in a `test/` subdirectory

## Extending Pyrox

| Goal | Approach |
|---|---|
| New application entry point | Subclass `Application` from `pyrox.application` |
| New feature panel | Subclass `ApplicationTask`; implement `create_task_frame()` |
| New service | Static class in `pyrox/services/`; export from `pyrox/services/__init__.py` |
| New GUI widget | Subclass `TaskFrame` in `models/gui/`; expose `.root: QWidget` |
| New interface | `Protocol` or `ABC` in `interfaces/` with no implementation |
| New event domain | Subclass `EventType`, `Event`, and `EventBus` — one set per domain |