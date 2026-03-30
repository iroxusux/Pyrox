# Pyrox AI Coding Guidelines

## Architecture Overview

Pyrox is a Python framework providing core services, models, and abstractions for building industrial automation applications. It uses an **interface-driven, mixin-based architecture** with clear separation between interfaces, models, services, and tasks.

### Key Components

- **Interfaces** (`pyrox/interfaces/`): Abstract contracts (`IApplication`, `IApplicationTask`, `IWorkspace`, `IScene`, `ISceneObject`, etc.) using `Protocol` and `ABCMeta`. No implementation code belongs here.
- **Models** (`pyrox/models/`): Concrete implementations of interfaces. Protocol implementations live in `models/protocols/`. GUI widgets in `models/gui/`. Physics bodies in `models/physics/`. Scene graph in `models/scene/`.
- **Services** (`pyrox/services/`): Static-class utilities (`EnvManager`, `GuiManager`, `LoggingManager`, `SceneRunnerService`, event buses, etc.). Consumed via `ServicesRunnableMixin` properties.
- **Tasks** (`pyrox/tasks/`): Modular application extensions (`ApplicationTask` subclasses) that inject menus and frames into a running application.

### Core Patterns

**ServicesRunnableMixin**: The foundation for classes needing service access. Composed of focused sub-mixins:
- `self.env` / `self.env_keys` — `EnvManager` + `EnvironmentKeys`
- `self.gui` — `GuiManager` (PyQt6-based)
- `self.logging` / `self.log()` — `LoggingManager`
- `self.directory` — `PlatformDirectoryService`
- `self.root_window` / `self.root_menu` / `self.file_menu` etc. — convenience accessors on `GuiManager`

**Factory Pattern**: `MetaFactory` enables type registration for extensible object creation. Subclasses auto-initialize their own `_registered_types` dict via `__init_subclass__`:
```python
class MyFactory(MetaFactory):
    pass  # _registered_types auto-created by MetaFactory.__init_subclass__
```

**`FactoryTypeMeta`**: Metaclass used on `ApplicationTask` to auto-register subclasses with `ApplicationTaskFactory`. Tasks are built automatically at app startup.

**Application Tasks**: Subclass `ApplicationTask` (not the interface directly). Override `create_task_frame()` and call `create_or_raise_frame()` to show/raise windows:
```python
class MyTask(ApplicationTask):
    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self.register_menu_command(menu=self.file_menu, ...)

    def create_task_frame(self) -> TaskFrame:
        return MyTaskFrame(self.application.workspace.workspace_area)
```

**Event Bus**: Decouple components via typed event buses:
```python
class MyEventBus(EventBus[MyEventType, MyEvent]):
    pass

MyEventBus.subscribe(MyEventType.SOMETHING, callback)
MyEventBus.publish(MyEvent(event_type=MyEventType.SOMETHING, ...))
```

**`MenuRegistry`**: Centralized registry for all menu items. Use `register_menu_command()` from `ApplicationTask` which auto-registers. Enables `MenuRegistry.enable_item("id")` / `set_command("id", fn)` from anywhere.

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
Pyrox uses `.env` files loaded via `EnvManager`:
```python
self.env.get(self.env_keys.core.APP_NAME, 'Default', str)
```

## Critical Code Conventions

### Typing
- Use **built-in generic types** — `list[str]`, `dict[str, int]`, `tuple[int, ...]` — never `List`, `Dict`, `Tuple` from `typing`.
- Use `X | Y` union syntax instead of `Optional[X]` or `Union[X, Y]`.
- **No forward references** (string literals like `'MyClass'`). Restructure imports or use `TYPE_CHECKING` guards if needed.
- `from __future__ import annotations` is present in some legacy files but should not be added to new files.

### Logging
Use the `log` helper imported from `pyrox.services.logging`:
```python
from pyrox.services.logging import log
log(self).debug('Message')   # uses class name as logger name
log(MyClass).warning('...')  # pass class when outside instance context
```

### GUI — PyQt6
The GUI layer is **PyQt6**. Never import `tkinter` in new or modified code.
- Root window and menus are managed by the static `GuiManager`.
- Access via `ServicesRunnableMixin` properties: `self.root_window`, `self.file_menu`, etc.
- All custom widgets subclass `TaskFrame` (from `pyrox.models.gui.frame`) and expose a `.root: QWidget` property for placement in splitters/workspaces.
- The `Workspace` widget provides a VSCode-style layout: vertical icon sidebar (`QTabWidget`), central workspace area for `TaskFrame` panels, a log window, and a status bar.

### Abstract Base Classes / Protocols
Interfaces use `Protocol` with `@runtime_checkable` for structural contracts, and `ABCMeta`/`ABC` for explicit abstract hierarchies:
```python
from typing import Protocol, runtime_checkable
@runtime_checkable
class IMyProtocol(Protocol):
    def my_method(self) -> None: ...
```

### RuntimeDict Pattern
For dictionaries with automatic save callbacks:
```python
self.data = RuntimeDict(callback=self.save)
self.data['key'] = 'value'  # triggers callback automatically
```

### GUI State vs .env
Use `GuiStateService` (not `EnvManager`/`EnvironmentKeys`) to persist any GUI layout preferences between sessions — splitter positions, sidebar width, log window height, etc. State is stored as JSON in the platform user-data directory.

```python
# Read layout state (always merge before writing back)
width = float(GuiStateService.get_geometry_state().get('sidebar_width', 0.33))

# Write layout state (get-merge-capture-save pattern)
state = GuiStateService.get_geometry_state()
state['sidebar_width'] = new_width
GuiStateService.capture_geometry_state(state)
GuiStateService.save()
```

`GuiStateService` is loaded at startup via `GuiStateService.load()` and saved explicitly after state changes. Use `PlatformDirectoryService` for resolving user data, log, and config directories — never hardcode paths or rely on `.env` for per-installation directory discovery.

## File Organization

```
pyrox/
├── interfaces/           # Abstract interfaces only — no implementations
│   ├── protocols/        # Structural Protocol definitions (INameable, IRunnable, etc.)
│   ├── scene/            # Scene/object/bridge interface contracts
│   ├── gui/              # IWorkspace, IViewport
│   ├── application.py    # IApplication, IApplicationTask
│   ├── constants.py      # EnvironmentKeys
│   └── services.py       # IEnvironmentManager, ILogger, etc.
├── models/               # Concrete implementations
│   ├── protocols/        # Implementations of interface protocols (CoreMixin, Nameable, etc.)
│   ├── factory.py        # MetaFactory, FactoryTypeMeta
│   ├── runtime.py        # RuntimeDict
│   ├── meta.py           # PyroxObject, SnowFlake, SliceableInt
│   ├── list.py           # HashList, SafeList, TrackedList, Subscribable
│   ├── services.py       # ServicesRunnableMixin (composed of Supports* mixins)
│   ├── task.py           # ApplicationTask, ApplicationTaskFactory
│   ├── scene/            # Scene, SceneObject, SceneGroup, etc.
│   ├── physics/          # BasePhysicsBody, ConveyorBody, CrateBody, etc.
│   └── gui/              # All PyQt6 widgets
│       ├── frame.py      # TaskFrame base class
│       ├── workspace.py  # Workspace (VSCode-style layout)
│       ├── commandbar.py # CommandBar, CommandButton, CommandDropdown
│       ├── treeview.py   # AttributeTreeView (lazy object introspection)
│       ├── objectexplorer.py  # ObjectExplorer (scene object list)
│       ├── propertypanel.py   # PropertyPanel (IHasProperties display/edit)
│       ├── logframe.py        # LogFrame
│       ├── theme.py           # DefaultTheme (dark theme constants)
│       ├── yamleditor.py      # PyroxYamlEditor
│       ├── texteditor.py      # TextEditorFrame
│       ├── contextmenu.py     # PyroxContextMenu
│       └── sceneviewer/       # Full scene viewer (viewer, explorer, properties, bridge, toolbar)
├── services/             # Static-class utilities
│   ├── logging.py        # log(), LoggingManager, StreamCapture
│   ├── env.py            # EnvManager
│   ├── gui.py            # GuiManager (PyQt6)
│   ├── gui_state.py      # GuiStateService
│   ├── menu_registry.py  # MenuRegistry, MenuItemDescriptor
│   ├── bus.py            # EventBus, Event, EventType base classes
│   ├── status.py         # StatusUpdateEventBus
│   ├── scene.py          # SceneRunnerService, SceneEventBus, HasSceneMixin
│   ├── file.py           # get_open_file, get_save_file, PlatformDirectoryService
│   ├── theme.py          # ThemeManager
│   ├── collision.py      # CollisionService, SpatialGrid
│   ├── physics.py        # PhysicsEngineService
│   └── environment.py    # EnvironmentService
├── tasks/                # Built-in ApplicationTask implementations
│   ├── builtin.py        # FileTask, HelpTask, ToolsTask, ViewTask
│   └── sceneviewer.py    # SceneviewerApplicationTask
└── utils/                # Build/dev utilities (not runtime code)
```

## Testing

- Tests live in `services/test/`, `models/test/`, or adjacent `test/` dirs
- Use pytest; log output controlled via `pytest.ini_options` in `pyproject.toml`

## Dependencies

**Required**: Python 3.13.9+ (specified in `pyproject.toml`)
**Key libs**: `PyQt6`, `lxml`, `pandas`, `Pillow`, `platformdirs`, `pdfplumber`, `python-dotenv`, `pyyaml`, `pylogix`, `PyMuPDF`, `tomli`

## Common Gotchas

1. **No `tkinter`**: The GUI backend is PyQt6. `notebook.py` is legacy and should not be used in new code.
2. **Static services**: `GuiManager`, `EnvManager`, `LoggingManager`, `MenuRegistry` etc. are static classes — never instantiate them.
3. **Task auto-registration**: Any `ApplicationTask` subclass is auto-registered via `FactoryTypeMeta` and built at startup. Don't manually add tasks to the factory.
4. **`TaskFrame.root`**: Always add `task_frame.root` to a Qt layout/splitter — not the `TaskFrame` object itself.
5. **Git hooks**: Use `utils/setup_hooks.py` to sync README badges with `pyproject.toml` version.
6. **Virtual environment**: Always activate `.venv` before development.
7. **Relative imports**: Use relative imports within the `pyrox` package; absolute for external dependencies.

## Version Management

Version tracked in `pyproject.toml` and auto-synced to `README.md` badges via pre-commit hook.

## When Extending Pyrox

1. **New application type**: Subclass `Application` from `pyrox.application`
2. **New task**: Subclass `ApplicationTask`; implement `create_task_frame()` and register menu commands in `__init__`
3. **New service**: Add a static class to `pyrox/services/`; expose via `pyrox/services/__init__.py`
4. **New GUI widget**: Subclass `TaskFrame` in `models/gui/`; expose `.root: QWidget` for layout integration
5. **New interface**: Add a `Protocol` or `ABC` to `interfaces/` with no implementation code
6. **New event**: Subclass `EventType` (enum) and `Event` (dataclass), then `EventBus` — one class per domain

## Cross-Project Context

ControlRox builds on Pyrox — changes to interfaces or `ServicesRunnableMixin` affect all downstream applications. Maintain backward compatibility in interfaces.
