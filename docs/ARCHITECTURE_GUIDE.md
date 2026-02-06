"""ARCHITECTURE GUIDE: Clean Separation of GUI, Services, and Models

This guide demonstrates the recommended patterns for managing menu items and callbacks
in a layered architecture with proper separation of concerns.

═══════════════════════════════════════════════════════════════════════════════
OVERVIEW OF THE SOLUTION
═══════════════════════════════════════════════════════════════════════════════

The solution uses three key patterns:

1. **MenuRegistry**: Centralized tracking of menu items with unique IDs
2. **SceneEventBus**: Event-driven communication between layers
3. **Ownership Model**: Clear responsibility for menu lifecycle

Layer Responsibilities:
- **Tasks**: Create and register menu items during bootstrap
- **Services**: Publish state change events, no direct GUI access
- **GUI Components**: Subscribe to events, update their own UI

═══════════════════════════════════════════════════════════════════════════════
STEP 1: REFACTOR THE APPLICATION TASK
═══════════════════════════════════════════════════════════════════════════════

BEFORE (Current SceneviewerApplicationTask):
```python
class SceneviewerApplicationTask(ApplicationTask):
    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        
        # Create menu items
        file_menu.add_item(
            index=0,
            label="Save Scene",
            command=SceneRunnerService.save_scene,  # Direct coupling!
            accelerator="Ctrl+S"
        )
        file_menu.disable_item(0)  # Manually tracking indices
        
        # Later: hard to enable/disable from elsewhere
        self._enable_menu_entries(True)  # Called directly from SceneRunnerService!
```

AFTER (Using MenuRegistry):
```python
from pyrox.services import MenuRegistry, SceneEventBus, SceneEventType

class SceneviewerApplicationTask(ApplicationTask):
    OWNER_ID = "SceneviewerApplicationTask"
    
    def __init__(self, application: IApplication) -> None:
        super().__init__(application)
        self._register_menu_items()
        self._subscribe_to_events()
    
    def _register_menu_items(self) -> None:
        '''Register all menu items with the MenuRegistry.'''
        file_menu = self.gui.root_menu().file_menu
        
        # Add "Save Scene" menu item
        file_menu.add_item(
            index=0,
            label="Save Scene",
            command=None,  # Will be set later by GUI component
            accelerator="Ctrl+S",
            underline=0
        )
        
        # Register with MenuRegistry - now trackable by ID!
        MenuRegistry.register_item(
            menu_id="scene.file.save",
            menu_path="File/Save Scene",
            menu_widget=file_menu.menu,
            menu_index=0,
            owner=self.OWNER_ID,
            enabled_by_default=False  # Start disabled
        )
        
        # Add "Load Scene" menu item
        file_menu.add_item(
            index=0,
            label="Load Scene",
            command=None,
            accelerator="Ctrl+O",
            underline=0
        )
        
        MenuRegistry.register_item(
            menu_id="scene.file.load",
            menu_path="File/Load Scene",
            menu_widget=file_menu.menu,
            menu_index=0,
            owner=self.OWNER_ID,
            enabled_by_default=False
        )
        
        # Disable items initially
        MenuRegistry.disable_items_by_owner(self.OWNER_ID)
    
    def _subscribe_to_events(self) -> None:
        '''Subscribe to scene events to enable/disable menu items.'''
        # Enable menu items when scene loads
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._on_scene_loaded
        )
        
        # Disable menu items when scene unloads
        SceneEventBus.subscribe(
            SceneEventType.SCENE_UNLOADED,
            self._on_scene_unloaded
        )
    
    def _on_scene_loaded(self, event: SceneEvent) -> None:
        '''Enable menu items when scene is loaded.'''
        MenuRegistry.enable_items_by_owner(self.OWNER_ID)
    
    def _on_scene_unloaded(self, event: SceneEvent) -> None:
        '''Disable menu items when scene is unloaded.'''
        MenuRegistry.disable_items_by_owner(self.OWNER_ID)
```

Benefits:
✓ No direct coupling to SceneRunnerService
✓ Menu items tracked by meaningful IDs, not fragile indices
✓ Event-driven: Task reacts to events, not called directly
✓ Easy to enable/disable all items at once

═══════════════════════════════════════════════════════════════════════════════
STEP 2: REFACTOR THE SERVICE
═══════════════════════════════════════════════════════════════════════════════

BEFORE (Current SceneRunnerService):
```python
class SceneRunnerService:
    @classmethod
    def set_scene(cls, scene: Optional[IScene]) -> None:
        cls._scene = scene
        if scene:
            cls._enable_menu_entries(True)  # Direct GUI manipulation!
        else:
            cls._enable_menu_entries(False)
        
        for callback in cls.get_on_scene_load_callbacks():  # Multiple callback lists
            callback(scene)
    
    @classmethod
    def _enable_menu_entries(cls, enable: bool) -> None:
        '''Directly imports and calls into Tasks!'''
        from pyrox.tasks.sceneviewer import SceneviewerApplicationTask
        tasks = cls._app.get_tasks()
        for task in tasks:
            if isinstance(task, SceneviewerApplicationTask):
                task.enable_all_sceneviewer_menu_entries()  # Tight coupling!
```

AFTER (Using SceneEventBus):
```python
from pyrox.services import SceneEventBus, SceneEvent, SceneEventType

class SceneRunnerService:
    # Remove _on_scene_load_callbacks - use EventBus instead!
    
    @classmethod
    def set_scene(cls, scene: Optional[IScene]) -> None:
        '''Set the active scene.'''
        cls._scene = scene
        
        if scene:
            cls._register_physics_bodies()
            cls._bind_to_scene_events()
            
            # Publish event instead of calling GUI directly!
            SceneEventBus.publish(SceneEvent(
                event_type=SceneEventType.SCENE_LOADED,
                scene=scene
            ))
        else:
            # Publish unload event
            SceneEventBus.publish(SceneEvent(
                event_type=SceneEventType.SCENE_UNLOADED,
                scene=None
            ))
    
    @classmethod
    def run(cls) -> int:
        '''Start the scene runner.'''
        if cls._running:
            return 1
            
        cls._running = True
        cls._current_time = datetime.now().timestamp()
        
        cls._event_id = GuiManager.unsafe_get_backend().schedule_event(
            cls._update_interval_ms,
            lambda: cls._run_scene()
        )
        
        # Publish started event
        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_STARTED,
            scene=cls._scene
        ))
        
        return 0
    
    @classmethod
    def stop(cls, stop_code: int = 0) -> None:
        '''Stop the scene runner.'''
        cls._running = False
        
        if cls._event_id:
            GuiManager.unsafe_get_backend().cancel_scheduled_event(cls._event_id)
        
        cls._event_id = None
        
        # Publish stopped event
        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_STOPPED,
            scene=cls._scene
        ))
        
        log(cls).info(f"Scene runner stopped with code {stop_code}")
```

Benefits:
✓ No direct GUI manipulation from service layer
✓ No imports of Task classes in service code
✓ Single source of truth for events (EventBus, not callback lists)
✓ Easy to test - just verify events are published

═══════════════════════════════════════════════════════════════════════════════
STEP 3: REFACTOR THE GUI COMPONENT
═══════════════════════════════════════════════════════════════════════════════

BEFORE (GUI calling services directly):
```python
class SceneViewer(GuiWidget):
    def __init__(self):
        # Direct service calls, tight coupling
        self.runner = SceneRunnerService(...)
        self.runner.get_on_scene_load_callbacks().append(self.on_scene_load)
        
    def save_clicked(self):
        # Directly calling service methods
        SceneRunnerService.save_scene()
```

AFTER (GUI as event-driven component):
```python
from pyrox.services import (
    MenuRegistry,
    SceneEventBus,
    SceneEvent,
    SceneEventType,
    SceneRunnerService
)

class SceneViewer(GuiWidget):
    def __init__(self):
        super().__init__()
        self._scene = None
        self._register_menu_callbacks()
        self._subscribe_to_events()
    
    def _register_menu_callbacks(self) -> None:
        '''Register callbacks for menu items created by the Task.'''
        # Set the actual command implementations for menu items
        MenuRegistry.set_command("scene.file.save", self._on_save_clicked)
        MenuRegistry.set_command("scene.file.load", self._on_load_clicked)
        MenuRegistry.set_command("scene.edit.delete", self._on_delete_clicked)
        MenuRegistry.set_command("scene.view.properties", self._on_toggle_properties)
        # etc...
    
    def _subscribe_to_events(self) -> None:
        '''Subscribe to scene state changes.'''
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._on_scene_loaded
        )
        
        SceneEventBus.subscribe(
            SceneEventType.SCENE_STARTED,
            self._on_scene_started
        )
        
        SceneEventBus.subscribe(
            SceneEventType.OBJECT_ADDED,
            self._on_object_added
        )
    
    # Event Handlers
    def _on_scene_loaded(self, event: SceneEvent) -> None:
        '''React to scene being loaded.'''
        self._scene = event.scene
        self.update_display()
    
    def _on_scene_started(self, event: SceneEvent) -> None:
        '''React to scene runner starting.'''
        self.start_animation()
    
    def _on_object_added(self, event: SceneEvent) -> None:
        '''React to object being added to scene.'''
        obj = event.data.get('object')
        self.add_object_to_display(obj)
    
    # Menu Command Implementations
    def _on_save_clicked(self) -> None:
        '''Handle Save Scene menu command.'''
        if self._scene:
            # Call service method - this is fine from GUI!
            SceneRunnerService.save_scene()
    
    def _on_load_clicked(self) -> None:
        '''Handle Load Scene menu command.'''
        SceneRunnerService.load_scene()
        # Scene will be set via SCENE_LOADED event
    
    def _on_delete_clicked(self) -> None:
        '''Handle Delete Selected Objects menu command.'''
        if self._selected_objects:
            for obj in self._selected_objects:
                self._scene.remove_object(obj)
                # This will trigger OBJECT_REMOVED event
    
    def _on_toggle_properties(self) -> None:
        '''Handle Properties Panel menu command.'''
        self.properties_panel.toggle_visibility()
```

Benefits:
✓ GUI component owns its display logic
✓ Reacts to events, not called directly
✓ Can call services (that's fine - it's the GUI layer)
✓ Clean separation: GUI handles display, Service handles business logic

═══════════════════════════════════════════════════════════════════════════════
STEP 4: WHERE SERVICES CAN STILL CALL GUI
═══════════════════════════════════════════════════════════════════════════════

It's OK for services to:
✓ Call GuiManager methods (it's a service)
✓ Call MenuRegistry (it's a service)
✓ Publish events through EventBus

It's NOT OK for services to:
✗ Import and call Task classes directly
✗ Import and call specific GUI widgets
✗ Know about specific menu item labels or indices

═══════════════════════════════════════════════════════════════════════════════
STEP 5: COMPLETE FLOW EXAMPLE
═══════════════════════════════════════════════════════════════════════════════

User clicks "File > Load Scene":

1. Menu item callback → SceneViewer._on_load_clicked()
2. GUI calls → SceneRunnerService.load_scene()
3. Service loads scene and calls → SceneRunnerService.set_scene(scene)
4. Service publishes → SceneEventBus.publish(SCENE_LOADED)
5. Task receives event → SceneviewerApplicationTask._on_scene_loaded()
6. Task enables menus → MenuRegistry.enable_items_by_owner(...)
7. GUI receives event → SceneViewer._on_scene_loaded()
8. GUI updates display → self.update_display()

Clean flow:
- Service doesn't know about GUI
- Task manages its own menu items
- GUI reacts to events and updates display
- MenuRegistry provides central control

═══════════════════════════════════════════════════════════════════════════════
STEP 6: TESTING BENEFITS
═══════════════════════════════════════════════════════════════════════════════

This architecture is much easier to test:

```python
def test_service_publishes_scene_loaded_event():
    '''Test that service publishes correct event when scene is loaded.'''
    # Arrange
    event_received = []
    
    def capture_event(event):
        event_received.append(event)
    
    SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, capture_event)
    
    # Act
    SceneRunnerService.set_scene(mock_scene)
    
    # Assert
    assert len(event_received) == 1
    assert event_received[0].event_type == SceneEventType.SCENE_LOADED
    assert event_received[0].scene == mock_scene


def test_menu_items_enabled_on_scene_load():
    '''Test that menu items are enabled when scene loads.'''
    # Arrange
    MenuRegistry.register_item(
        menu_id="test.item",
        menu_path="Test/Item",
        menu_widget=mock_menu,
        menu_index=0,
        owner="TestOwner"
    )
    MenuRegistry.disable_item("test.item")
    
    # Act
    event = SceneEvent(event_type=SceneEventType.SCENE_LOADED, scene=mock_scene)
    SceneEventBus.publish(event)
    
    # Assert
    descriptor = MenuRegistry.get_item("test.item")
    assert descriptor.enabled == True
```

═══════════════════════════════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════════════════════════════

OLD WAY (Current):
- Services import and call Tasks directly
- Tasks have enable/disable methods called from services
- Callback lists scattered everywhere
- Hard to track what controls what

NEW WAY (Recommended):
- MenuRegistry: Central tracking of all menu items
- SceneEventBus: Event-driven communication
- Tasks: Create and manage their menu items, react to events
- Services: Publish events, no direct GUI access
- GUI: Subscribe to events, implement menu commands

This gives you:
✓ Loose coupling between layers
✓ Easy testing
✓ Clear ownership model
✓ Scalability for adding new features
✓ No circular dependencies
"""
