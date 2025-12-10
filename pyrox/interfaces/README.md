# Comprehensive documentation and examples for the Pyrox interfaces system

This module provides detailed documentation, usage examples, and architectural
guidance for implementing and using the Pyrox interfaces to solve circular
dependencies and create clean, extensible architectures.

## Overview

The Pyrox interfaces system eliminates circular dependencies between services
and models by providing pure abstract interfaces that both can depend on without
creating import cycles. This follows the Dependency Inversion Principle (DIP)
and enables clean, testable, and extensible architectures.

## Key Benefits

1. **Eliminates Circular Dependencies**: Pure interfaces break import cycles
2. **Enables Dependency Injection**: Services can be injected rather than imported
3. **Improves Testability**: Interfaces can be easily mocked for testing
4. **Supports Plugin Architecture**: New implementations can be registered at runtime
5. **Follows SOLID Principles**: Clean separation of concerns and responsibilities

## Architecture Patterns

### 1. Interface Segregation Pattern

Instead of large monolithic interfaces, Pyrox provides focused interfaces:

```python
# Bad: Large monolithic interface
class IEverything(ABC):
    def gui_method(self): pass
    def logging_method(self): pass
    def config_method(self): pass

# Good: Segregated focused interfaces
class IGuiBackend(ABC):
    def create_window(self): pass

class ILogger(ABC):
    def info(self, message): pass

class IConfigurationManager(ABC):
    def get_value(self, key): pass
```

### 2. Dependency Inversion Pattern

High-level modules depend on abstractions, not concretions:

```python
# Bad: Direct dependency on concrete class
from pyrox.services.gui import GuiManager  # Creates circular dependency

class MyModel:
    def __init__(self):
        self.gui = GuiManager  # Direct dependency

# Good: Dependency on interface
from pyrox.interfaces import IGuiBackend

class MyModel:
    def __init__(self, gui_backend: IGuiBackend):
        self.gui = gui_backend  # Injected dependency
```

### 3. Service Registry Pattern

Services are registered and resolved through a central registry:

```python
from pyrox.interfaces import IServiceRegistry, IGuiBackend

# Register services
registry = get_service_registry()
registry.register_service(IGuiBackend, TkinterBackend())

# Resolve services
gui_backend = registry.get_service(IGuiBackend)
```

## Implementation Examples

### Example 1: Fixing GuiManager Circular Dependency

**Before (Circular Dependency):**

```python
# pyrox/services/gui.py
from pyrox.models.gui.backend import TkinterBackend  # Circular import!

class GuiManager:
    def __init__(self):
        self.backend = TkinterBackend()  # Direct dependency
```

**After (Using Interfaces):**

```python
# pyrox/services/gui.py
from pyrox.interfaces import IGuiBackend, IBackendRegistry

class GuiManager:
    def __init__(self, backend_registry: IBackendRegistry):
        self._registry = backend_registry
        self._backend = None
    
    def initialize(self, framework_name: str):
        self._backend = self._registry.create_backend(framework_name)
```

### Example 2: Implementing a Service Registry

```python
from pyrox.interfaces import IServiceRegistry, IGuiBackend
from typing import Type, Dict, Any

class ServiceRegistry(IServiceRegistry):
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, bool] = {}
    
    def register_service(self, service_type: Type[T], implementation: T, singleton: bool = True):
        self._services[service_type] = implementation
        self._singletons[service_type] = singleton
    
    def get_service(self, service_type: Type[T]) -> T:
        if service_type in self._services:
            return self._services[service_type]
        elif service_type in self._factories:
            factory = self._factories[service_type]
            instance = factory()
            if self._singletons.get(service_type, True):
                self._services[service_type] = instance
            return instance
        else:
            raise ServiceNotFoundError(f"Service {service_type} not registered")
```

### Example 3: Backend Registry Implementation

```python
from pyrox.interfaces import IBackendRegistry, IGuiBackend
from typing import Type, Dict, List

class BackendRegistry(IBackendRegistry):
    def __init__(self):
        self._backends: Dict[str, Type[IGuiBackend]] = {}
    
    def register_backend(self, framework_name: str, backend_class: Type[IGuiBackend]):
        self._backends[framework_name] = backend_class
    
    def get_available_frameworks(self) -> List[str]:
        available = []
        for name, backend_class in self._backends.items():
            backend = backend_class()
            if backend.is_available():
                available.append(name)
        return available
    
    def create_backend(self, framework_name: str, **kwargs) -> IGuiBackend:
        if framework_name not in self._backends:
            raise BackendNotFoundError(f"Backend {framework_name} not registered")
        
        backend_class = self._backends[framework_name]
        return backend_class(**kwargs)
```

## Migration Guide

### Step 1: Identify Circular Dependencies

Look for imports between `pyrox.services` and `pyrox.models`:

```bash
# Find circular imports
grep -r "from pyrox.services" pyrox/models/
grep -r "from pyrox.models" pyrox/services/
```

### Step 2: Replace Direct Imports with Interface Dependencies

**Before:**

```python
from pyrox.services.gui import GuiManager

class MyComponent:
    def __init__(self):
        self.gui = GuiManager
```

**After:**

```python
from pyrox.interfaces import IGuiBackend

class MyComponent:
    def __init__(self, gui_backend: IGuiBackend):
        self.gui = gui_backend
```

### Step 3: Implement Service Registration

Create a bootstrap module that registers all services:

```python
# pyrox/bootstrap.py
from pyrox.interfaces import IServiceRegistry, IBackendRegistry
from pyrox.services.registry import ServiceRegistry, BackendRegistry
from pyrox.models.gui.backend import TkinterBackend, ConsoleBackend

def create_service_registry() -> IServiceRegistry:
    registry = ServiceRegistry()
    
    # Register GUI backends
    backend_registry = BackendRegistry()
    backend_registry.register_backend("tkinter", TkinterBackend)
    backend_registry.register_backend("console", ConsoleBackend)
    
    registry.register_service(IBackendRegistry, backend_registry)
    
    return registry
```

### Step 4: Update Application Initialization

Modify your application to use dependency injection:

```python
from pyrox.bootstrap import create_service_registry
from pyrox.interfaces import IBackendRegistry

class Application:
    def __init__(self):
        self.registry = create_service_registry()
        
    def initialize_gui(self, framework: str = "tkinter"):
        backend_registry = self.registry.get_service(IBackendRegistry)
        self.gui_backend = backend_registry.create_backend(framework)
```

## Testing with Interfaces

Interfaces make testing much easier by allowing mock implementations:

```python
from pyrox.interfaces import IGuiBackend
from unittest.mock import Mock

class MockGuiBackend(IGuiBackend):
    def __init__(self):
        self.created_windows = []
    
    def create_window(self, **kwargs):
        window = Mock()
        self.created_windows.append(window)
        return window
    
    def is_available(self):
        return True

# Use in tests
def test_component_creates_window():
    mock_backend = MockGuiBackend()
    component = MyComponent(mock_backend)
    
    component.create_main_window()
    
    assert len(mock_backend.created_windows) == 1
```

## Best Practices

### 1. Keep Interfaces Pure

- No implementation code in interfaces
- No imports from pyrox.services or pyrox.models
- Only import from typing and abc modules

### 2. Use Dependency Injection

- Inject dependencies through constructors
- Avoid global service locators when possible
- Use factories for complex object creation

### 3. Register Services Early

- Register all services during application startup
- Use a bootstrap module for service registration
- Keep registration logic separate from business logic

### 4. Design for Extension

- Use interfaces for all major abstractions
- Support multiple implementations
- Enable runtime registration of new implementations

### 5. Test Interface Contracts

- Test that implementations conform to interfaces
- Use mock implementations for unit testing
- Test integration between components

## Future Extensions

The interface system enables future enhancements:

1. **Plugin System**: Runtime loading of new implementations
2. **Configuration-Driven Services**: Services selected via configuration
3. **Multi-Backend Support**: Multiple GUI backends in one application
4. **Service Composition**: Combining multiple services
5. **Aspect-Oriented Programming**: Cross-cutting concerns via decorators

## Common Patterns

### Singleton Services

```python
registry.register_service(ILogger, LoggingManager(), singleton=True)
```

### Factory Services

```python
registry.register_factory(IGuiWindow, lambda: create_window_for_current_backend())
```

### Lazy Loading

```python
registry.register_factory(IHeavyService, lambda: HeavyService(), singleton=True)
```

### Conditional Registration

```python
if is_gui_available():
    registry.register_service(IGuiBackend, TkinterBackend())
else:
    registry.register_service(IGuiBackend, ConsoleBackend())
```

This interface system provides a solid foundation for clean, extensible,
and testable architecture while eliminating circular dependencies.