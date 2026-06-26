# Pyrox

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
![Development Status](https://img.shields.io/badge/status-beta-orange.svg)
![Version](https://img.shields.io/badge/version-3.6.11-blue.svg)

**Pyrox** is a Python back-end engine and application framework built on **PyQt6**. It provides a rich set of interfaces, models, services, and abstractions for building industrial automation and desktop applications. Pyrox is designed to be used as a foundation — downstream projects like [ControlRox](https://github.com/iroxusux/ControlRox) build their entire application layer on top of it.

## 🚀 Key Features

### 🏗️ Interface-Driven Architecture

Pyrox enforces a strict separation of concerns through a dedicated interface layer (`pyrox/interfaces/`). Every major abstraction — applications, tasks, scenes, physics bodies, workspaces, services — is defined as a `Protocol` or `ABC` in the interface layer before any concrete implementation exists. This allows downstream consumers to depend on contracts, not implementations.

- **Structural Protocols** (`Protocol` + `@runtime_checkable`): `INameable`, `IDescribable`, `IRunnable`, `IConfigurable`, `IHasId`, `ISpatial2D`, `IKinematic2D`, `IPhysicsBody2D`, and more
- **Application Interfaces**: `IApplication`, `IApplicationTask`, `IWorkspace`, `IViewport`
- **Scene Interfaces**: `IScene`, `ISceneObject`, `ISceneGroup`, `ISceneBridge`, `ISceneBoundLayer`, `ICompositeSceneObject`
- **Physics Interfaces**: `IBasePhysicsBody`, `ICollider2D`, `IRigidBody2D`, `IMaterial`, `IPhysicsEngine`
- **Service Interfaces**: `IEnvironmentManager`, `ILoggingManager`, `ILogger`

### 🎨 PyQt6 GUI Framework

Pyrox is built exclusively on **PyQt6**. All GUI components, the workspace layout, and the application shell are PyQt6-native. There is no tkinter dependency.

- **VSCode-style Workspace**: Vertical icon sidebar (`QTabWidget`), central workspace area for `TaskFrame` panels, an integrated log window, and a status bar — all managed by `Workspace`
- **TaskFrame System**: Custom widgets subclass `TaskFrame`, expose a `.root: QWidget` property, and are registered with the workspace for docking and visibility management
- **CommandBar**: Composable toolbars built with `CommandButton` and `CommandDropdown` widgets
- **AttributeTreeView**: Lazy object introspection tree for exploring any Python object at runtime
- **ObjectExplorer**: Scene object list with add/remove and selection callbacks
- **PropertyPanel**: Auto-generated property editor for objects implementing `IHasProperties`
- **SceneViewer**: Full composited scene viewer including a canvas viewport, object explorer, property panel, scene bridge, and toolbar — all wired together
- **YAML/Text Editors**: `PyroxYamlEditor` and `TextEditorFrame` for in-app editing
- **Dark Theme**: `DefaultTheme` provides consistent color constants across all widgets

### 🧩 Mixin-Based Service Composition

The `ServicesRunnableMixin` composes focused sub-mixins to give any class clean, property-based access to all platform services:

| Property | Service |
|---|---|
| `self.env` / `self.env_keys` | `EnvManager` + `EnvironmentKeys` |
| `self.gui` | `GuiManager` (PyQt6 root, menus, geometry) |
| `self.logging` / `self.log()` | `LoggingManager` |
| `self.directory` | `PlatformDirectoryService` |
| `self.root_window` / `self.file_menu` … | Convenience accessors on `GuiManager` |

Static service classes (`EnvManager`, `GuiManager`, `LoggingManager`, `MenuRegistry`, `GuiStateService`) are never instantiated — they expose only class methods and properties.

### 🏭 Task-Based Application Extension

Applications are extended through `ApplicationTask` subclasses. Each task:

1. Is **auto-registered** with `ApplicationTaskFactory` via the `FactoryTypeABC` metaclass — no manual wiring required
2. Is **instantiated automatically** at application startup via `ApplicationTaskFactory.build_tasks(app)`
3. Injects menu commands into the application's menu bar via `register_menu_command()`
4. Creates and manages its own `TaskFrame` panel via `create_task_frame()` and `create_or_raise_frame()`

```python
from pyrox.models.task import ApplicationTask
from pyrox.models.gui.frame import TaskFrame

class MyTask(ApplicationTask):
    def __init__(self, application):
        super().__init__(application)
        self.register_menu_command(
            menu=self.file_menu,
            registry_id='my_task.open',
            registry_path='File/My Task',
            index=0,
            label='My Task...',
            command=self.create_or_raise_frame,
        )

    def create_task_frame(self) -> TaskFrame:
        return MyTaskFrame(self.application.workspace.workspace_area)
```

### 🎬 Scene & Emulation Environment

Pyrox provides the foundational layer for building 2D scene-based emulation environments:

- **Scene Graph**: `Scene` contains `SceneObject`, `SceneGroup`, and `CompositeSceneObject` instances; all implement interface contracts from `pyrox.interfaces`
- **Physics Engine**: `PhysicsEngineService` drives a 2D physics simulation. Built-in body types include `ConveyorBody`, `CrateBody`, `FloorBody`, `SensorBody`, and `ActorBody`
- **Collision Service**: `CollisionService` with a `SpatialGrid` for broad-phase collision detection
- **Scene Runner**: `SceneRunnerService` and `SceneEventBus` manage scene lifecycle and broadcast scene events
- **Scene Viewer Task**: `SceneviewerApplicationTask` wires together the full interactive scene viewer UI
- **Scene Bridge**: `ISceneBridge` / `ISceneBoundLayer` contracts decouple the rendered canvas layer from the domain scene model

### 📡 Event Bus System

Typed, decoupled communication between components via `EventBus`:

```python
from pyrox.services.bus import EventBus, Event, EventType

class MyEventType(EventType):
    SOMETHING_HAPPENED = 'something_happened'

class MyEvent(Event[MyEventType]):
    data: str

class MyEventBus(EventBus[MyEventType, MyEvent]):
    pass

MyEventBus.subscribe(MyEventType.SOMETHING_HAPPENED, my_callback)
MyEventBus.publish(MyEvent(event_type=MyEventType.SOMETHING_HAPPENED, data='hello'))
```

Each `EventBus` subclass gets its own isolated subscriber registry — no cross-bus leakage.

### 🏗️ Factory Patterns

`MetaFactory` enables extensible type registries. `FactoryTypeABC` auto-registers subclasses with a target factory via `__init_subclass__`:

```python
from pyrox.models.factory import MetaFactory, FactoryTypeABC

class MyFactory(MetaFactory):
    pass  # gets its own _registered_types dict automatically

class MyBase(FactoryTypeABC[MyFactory]):
    pass  # auto-registers with MyFactory

class MyConcrete(MyBase):
    pass  # auto-registered as 'MyConcrete' in MyFactory._registered_types
```

### 🔧 Common Services & Utilities

- **`EnvManager`**: `.env`-based configuration via `python-dotenv`; typed `get()` with defaults
- **`GuiManager`**: Static PyQt6 root window, menu bar, and geometry management; event scheduling
- **`LoggingManager`**: Named loggers, stream capture, and callback routing for log output
- **`PlatformDirectoryService`**: Cross-platform user data, log, and config directories via `platformdirs`
- **`GuiStateService`**: Persists GUI layout preferences (splitter ratios, sidebar widths, etc.) as JSON between sessions
- **`MenuRegistry`**: Centralized registry for all menu items; supports `enable_item()` and `set_command()` from anywhere
- **`SceneRunnerService`** / **`SceneEventBus`**: Scene lifecycle management and event broadcasting
- **`CollisionService`** / **`SpatialGrid`**: 2D spatial indexing and collision detection
- **`PhysicsEngineService`**: 2D physics simulation driver
- **`StatusUpdateEventBus`**: Application-wide status bar messaging

## 📦 Installation

### Requirements

- **Python 3.13.9+** (Required)
- Cross-platform support (Windows, Linux, macOS)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/iroxusux/Pyrox.git
cd Pyrox

# Run the installation script (recommended — handles venv, deps, and git hooks)
./install.sh

# Or install manually:
pip install -e . --upgrade
python utils/setup_hooks.py  # Set up pre-commit hooks
```

### Dependencies

Key runtime dependencies installed automatically:

| Package | Purpose |
|---|---|
| `PyQt6` | GUI framework (required) |
| `python-dotenv` | `.env` configuration loading |
| `platformdirs` | Cross-platform directory resolution |
| `pyyaml` | YAML file support |
| `lxml` | XML processing |
| `pandas` / `openpyxl` | Data and Excel processing |
| `Pillow` | Image processing |
| `pdfplumber` / `PyMuPDF` | PDF processing |
| `pylogix` | Allen-Bradley PLC communication |
| `tomli` | TOML parsing |

## 🏁 Quick Start

### Minimal Application

```python
# myapp/__main__.py
import pyrox
from pyrox.application import Application

app = Application()
app.run()
```

Configuration is read from `.env` at startup:

```bash
# .env
APP_NAME=My Application
APP_DESCRIPTION=Built on Pyrox
APP_AUTHOR=Your Name
```

### Adding a Custom Task

```python
from pyrox.models.task import ApplicationTask
from pyrox.models.gui.frame import TaskFrame
from pyrox.interfaces import IApplication
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

class MyTaskFrame(TaskFrame):
    def __init__(self, parent: QWidget):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Hello from MyTask!"))
        self._root = QWidget(parent)
        self._root.setLayout(layout)

    @property
    def root(self) -> QWidget:
        return self._root


class MyTask(ApplicationTask):
    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self.register_menu_command(
            menu=self.file_menu,
            registry_id='my_task.open',
            registry_path='File/My Task',
            index=0,
            label='My Task...',
            command=self.create_or_raise_frame,
        )

    def create_task_frame(self) -> TaskFrame:
        return MyTaskFrame(self.application.workspace.workspace_area)
```

`MyTask` is automatically discovered and built at startup — no registration call needed.

### Using the Logging Service

```python
from pyrox.services.logging import log

class MyClass:
    def do_work(self):
        log(self).info('Starting work...')
        log(self).debug('Detail message')
```

### Publishing a Status Update

```python
from pyrox.services.status import StatusUpdateEventBus, StatusUpdateEvent, StatusUpdateEventType

StatusUpdateEventBus.publish(
    StatusUpdateEvent(
        event_type=StatusUpdateEventType.UPDATE,
        status_message='Processing complete'
    )
)
```

## 🏗️ Architecture

### Package Layout

```text
pyrox/
├── interfaces/           # Abstract contracts only — no implementations
│   ├── protocols/        # Structural Protocol definitions
│   │   ├── meta.py       # INameable, IRunnable, IConfigurable, IHasId, …
│   │   ├── coord.py      # ICoord2D, IArea2D
│   │   ├── spatial.py    # ISpatial2D, IRotatable, IDirectional2D, IZoomable
│   │   ├── kinematic.py  # IVelocity2D, IKinematic2D
│   │   ├── physics.py    # IPhysicsBody2D, IRigidBody2D, IMaterial, ICollider2D
│   │   ├── property.py   # IHasProperties
│   │   ├── connection.py # IConnectable, Connection
│   │   └── gui.py        # IHasCanvas
│   ├── scene/            # IScene, ISceneObject, ISceneGroup, ISceneBridge, …
│   ├── gui/              # IWorkspace, IViewport
│   ├── physics.py        # IBasePhysicsBody
│   ├── application.py    # IApplication, IApplicationTask
│   ├── services.py       # IEnvironmentManager, ILoggingManager, ILogger
│   └── constants.py      # EnvironmentKeys
│
├── models/               # Concrete implementations
│   ├── factory.py        # MetaFactory, FactoryTypeABC
│   ├── task.py           # ApplicationTask, ApplicationTaskFactory
│   ├── services.py       # ServicesRunnableMixin (Supports* sub-mixins)
│   ├── meta.py           # PyroxObject, SnowFlake, SliceableInt
│   ├── list.py           # HashList, SafeList, TrackedList, Subscribable
│   ├── runtime.py        # RuntimeDict
│   ├── protocols/        # CoreMixin, Nameable, HasId, PhysicsBody2D, …
│   ├── scene/            # Scene, SceneObject, SceneGroup, SceneBridge, …
│   ├── physics/          # BasePhysicsBody, ConveyorBody, CrateBody, FloorBody, …
│   └── gui/              # All PyQt6 widgets
│       ├── frame.py      # TaskFrame base class
│       ├── workspace.py  # Workspace (VSCode-style layout)
│       ├── commandbar.py # CommandBar, CommandButton, CommandDropdown
│       ├── treeview.py   # AttributeTreeView
│       ├── objectexplorer.py   # ObjectExplorer
│       ├── propertypanel.py    # PropertyPanel
│       ├── logframe.py         # LogFrame
│       ├── theme.py            # DefaultTheme
│       ├── yamleditor.py       # PyroxYamlEditor
│       ├── texteditor.py       # TextEditorFrame
│       ├── contextmenu.py      # PyroxContextMenu
│       └── sceneviewer/        # Full scene viewer composite widget
│
├── services/             # Static-class utilities
│   ├── logging.py        # log(), LoggingManager, StreamCapture
│   ├── env.py            # EnvManager
│   ├── gui.py            # GuiManager (PyQt6)
│   ├── gui_state.py      # GuiStateService
│   ├── menu_registry.py  # MenuRegistry, MenuItemDescriptor
│   ├── bus.py            # EventBus, Event, EventType
│   ├── status.py         # StatusUpdateEventBus
│   ├── scene.py          # SceneRunnerService, SceneEventBus, HasSceneMixin
│   ├── file.py           # get_open_file, get_save_file, PlatformDirectoryService
│   ├── theme.py          # ThemeManager
│   ├── collision.py      # CollisionService, SpatialGrid
│   └── physics.py        # PhysicsEngineService
│
├── tasks/                # Built-in ApplicationTask implementations
│   ├── builtin.py        # FileTask, HelpTask, ToolsTask, ViewTask
│   └── sceneviewer.py    # SceneviewerApplicationTask
│
├── application.py        # Application (concrete IApplication entry point)
└── ui/                   # Icons and splash assets
```

### Architectural Layers

```
┌─────────────────────────────────────────────────────┐
│              Downstream Application                 │
│         (e.g. ControlRox, custom apps)              │
├─────────────────────────────────────────────────────┤
│                pyrox/tasks/                         │
│        ApplicationTask subclasses (built-in)        │
├─────────────────────────────────────────────────────┤
│  pyrox/models/     │  pyrox/services/               │
│  Concrete impls    │  Static service classes         │
├─────────────────────────────────────────────────────┤
│                pyrox/interfaces/                    │
│     Protocols, ABCs — no implementation code        │
└─────────────────────────────────────────────────────┘
```

### Core Design Patterns

| Pattern | Where Used |
|---|---|
| **Interface Segregation** | `pyrox/interfaces/` — one interface per concern |
| **Mixin Composition** | `ServicesRunnableMixin` composed of `Supports*` mixins |
| **Factory + Auto-registration** | `MetaFactory` + `FactoryTypeABC.__init_subclass__` |
| **Event Bus** | `EventBus[T, E]` with per-subclass subscriber isolation |
| **RuntimeDict** | Dict with save/change callbacks for persistent state |
| **Menu Registry** | `MenuRegistry` centralises all menu items across tasks |

## 🎯 Use Cases

### Pyrox as a Back-End Engine

Pyrox provides the scaffolding — interface contracts, service infrastructure, GUI shell, scene engine, and physics layer — so that application developers can focus exclusively on domain logic.

- **[ControlRox](https://github.com/iroxusux/ControlRox)**: Industrial automation application built directly on Pyrox; uses `ApplicationTask`, `Scene`, `SceneObject`, and the PyQt6 workspace
- **Custom desktop tools**: Any Python desktop application that needs a structured, extensible PyQt6 shell
- **Emulation environments**: Applications that simulate physical processes using Pyrox's scene graph and physics engine

### Building on Pyrox

1. **New application**: Subclass `Application` from `pyrox.application`
2. **New feature/panel**: Subclass `ApplicationTask`; implement `create_task_frame()` and register menu commands in `__init__`
3. **New GUI widget**: Subclass `TaskFrame`; expose `.root: QWidget` for workspace integration
4. **New service**: Add a static class to `pyrox/services/`; expose via `pyrox/services/__init__.py`
5. **New interface**: Add a `Protocol` or `ABC` to `pyrox/interfaces/` with no implementation
6. **New event**: Subclass `EventType`, `Event`, and `EventBus` — one class per domain
7. **New scene object type**: Subclass `SceneObject` and implement the `ISceneObject` interface
8. **New physics body**: Subclass `BasePhysicsBody` and register with `PhysicsSceneFactory`

## 🛠️ Development

### Setup

```bash
# Install with venv and git hooks (recommended)
./install.sh

# Or manually
pip install -e . --upgrade
python utils/setup_hooks.py
```

### Running Tests

```bash
pytest pyrox/services/test/
pytest pyrox/models/test/
pytest pyrox/tasks/test/
```

### Building Distribution

```bash
./build.sh
```

### Utility Scripts

| Script | Purpose |
|---|---|
| `utils/sync_readme.py` | Sync README version/status badges from `pyproject.toml` |
| `utils/check_version_increment.py` | Verify a version bump exists for code changes |
| `utils/setup_hooks.py` | Install pre-commit hooks |
| `utils/extract_todos.py` | Generate `code_todos.md` from source TODOs |

### Pre-commit Hooks

The pre-commit hook automatically:

1. **Checks for a version bump** when Python source files change
2. **Syncs README badges** from `pyproject.toml` (`version`, `requires-python`, classifiers)

Files that **do not** require a version bump: `README.md`, `.md` files, `docs/`, `.gitignore`, `LICENSE`, `.yml/.yaml`, `utils/`, `hooks/`

Files that **do** require a version bump: `pyrox/**/*.py`, `pyproject.toml`

## 🏭 Related Projects

- **[ControlRox](https://github.com/iroxusux/ControlRox)** — Industrial automation application built on Pyrox

## 🤝 Contributing

Contributions are welcome! Please maintain architectural consistency:

- New interfaces go in `pyrox/interfaces/` with no implementation code
- New concrete implementations go in `pyrox/models/`
- New services go in `pyrox/services/` as static classes
- All code must target **Python 3.13.9+** and use PyQt6 for any GUI work
- Use built-in generic types (`list[str]`, `dict[str, int]`) — never `typing.List`, `typing.Dict`, etc.
- Use `X | Y` unions — never `Optional[X]` or `Union[X, Y]`

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Brian LaFond**  
📧 [Brian.L.LaFond@gmail.com](mailto:Brian.L.LaFond@gmail.com)  
🐙 [GitHub](https://github.com/iroxusux)

---

**Pyrox** — *PyQt6-based back-end engine providing interfaces, models, services, and a scene/emulation environment for building industrial automation and desktop applications*
