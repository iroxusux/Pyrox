"""Quick Reference: Common Patterns for GUI-Service Integration

This file provides quick copy-paste examples for common patterns.
"""

# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 1: Registering a Menu Item from a Task
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import MenuRegistry

# In your ApplicationTask.__init__():
file_menu = self.gui.root_menu().file_menu

# Add the menu item
file_menu.add_item(
    index=0,
    label="My Action",
    command=None,  # Will be set by GUI component
    accelerator="Ctrl+M",
    underline=0
)

# Register it with MenuRegistry
MenuRegistry.register_item(
    menu_id="my_feature.file.action",  # Unique ID, use namespace
    menu_path="File/My Action",  # Human-readable path
    menu_widget=file_menu.menu,  # The tkinter Menu widget
    menu_index=0,  # Index where we added it
    owner="MyFeatureTask",  # Your task class name
    category="myfeature"  # Optional: for bulk operations
)


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 2: Setting Menu Item Callbacks from GUI Component
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import MenuRegistry

class MyGuiComponent:
    def __init__(self):
        self._register_menu_callbacks()
    
    def _register_menu_callbacks(self):
        # Link menu items to your implementation
        MenuRegistry.set_command("my_feature.file.action", self._on_action)
        MenuRegistry.set_command("my_feature.edit.undo", self._on_undo)
    
    def _on_action(self):
        # Your implementation
        print("Action triggered from menu!")


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 3: Enabling/Disabling Menu Items Based on State
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import MenuRegistry

# Enable/disable single item by ID
MenuRegistry.enable_item("my_feature.file.action")
MenuRegistry.disable_item("my_feature.file.action")

# Enable/disable all items owned by a task
MenuRegistry.enable_items_by_owner("MyFeatureTask")
MenuRegistry.disable_items_by_owner("MyFeatureTask")

# Query state
descriptor = MenuRegistry.get_item("my_feature.file.action")
if descriptor and descriptor.enabled:
    print("Menu item is enabled")


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 4: Publishing Events from Services
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import SceneEventBus, SceneEvent, SceneEventType

# In your service method:
def load_data(self, data):
    # ... do work ...
    
    # Publish event when done
    SceneEventBus.publish(SceneEvent(
        event_type=SceneEventType.SCENE_LOADED,
        scene=data,
        data={"source": "file", "filename": "scene.json"}
    ))


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 5: Subscribing to Events in Tasks
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import SceneEventBus, SceneEvent, SceneEventType, MenuRegistry

class MyTask(ApplicationTask):
    def __init__(self, application):
        super().__init__(application)
        self._register_menu_items()
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        # React to scene events
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._on_scene_loaded
        )
        
        SceneEventBus.subscribe(
            SceneEventType.SCENE_UNLOADED,
            self._on_scene_unloaded
        )
    
    def _on_scene_loaded(self, event: SceneEvent):
        # Enable my menu items
        MenuRegistry.enable_items_by_owner("MyTask")
    
    def _on_scene_unloaded(self, event: SceneEvent):
        # Disable my menu items
        MenuRegistry.disable_items_by_owner("MyTask")


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 6: Subscribing to Events in GUI Components
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import SceneEventBus, SceneEvent, SceneEventType

class MyGuiWidget:
    def __init__(self):
        self._scene = None
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        # Subscribe to relevant events
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._on_scene_loaded
        )
        
        SceneEventBus.subscribe(
            SceneEventType.OBJECT_ADDED,
            self._on_object_added
        )
    
    def _on_scene_loaded(self, event: SceneEvent):
        # Update display with new scene
        self._scene = event.scene
        self.refresh_display()
    
    def _on_object_added(self, event: SceneEvent):
        # Add object to display
        obj = event.data.get('object')
        self.add_to_display(obj)


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 7: Creating Custom Event Types (Advanced)
# ═══════════════════════════════════════════════════════════════════════════

from enum import Enum, auto
from pyrox.services import SceneEventBus, SceneEvent

# Extend SceneEventType with custom events
class MyCustomEventType(Enum):
    DATA_IMPORTED = auto()
    VALIDATION_FAILED = auto()
    EXPORT_COMPLETE = auto()

# Publish custom event (reuse SceneEvent structure)
SceneEventBus.publish(SceneEvent(
    event_type=MyCustomEventType.DATA_IMPORTED,
    scene=None,
    data={"record_count": 100, "source": "api"}
))

# Subscribe to custom event
def on_import(event):
    record_count = event.data.get('record_count', 0)
    print(f"Imported {record_count} records")

SceneEventBus.subscribe(MyCustomEventType.DATA_IMPORTED, on_import)


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 8: Bulk Menu Operations
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import MenuRegistry

# Get all menu items for a specific owner
items = MenuRegistry.get_items_by_owner("MyTask")
for item in items:
    print(f"{item.menu_id}: {item.menu_path} (enabled: {item.enabled})")

# Check if a menu item exists before using it
if MenuRegistry.get_item("my_feature.file.action"):
    MenuRegistry.enable_item("my_feature.file.action")


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 9: Cleanup and Unsubscribing
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import SceneEventBus, MenuRegistry

class MyComponent:
    def __init__(self):
        self._event_callback = self._on_scene_loaded
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, self._event_callback)
    
    def destroy(self):
        # Clean up subscriptions
        SceneEventBus.unsubscribe(SceneEventType.SCENE_LOADED, self._event_callback)
        
        # Unregister menu items if this component owns them
        # (Usually not needed - tasks own menu items)
        # MenuRegistry.unregister_item("my_component.action")


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 10: State Query Examples
# ═══════════════════════════════════════════════════════════════════════════

from pyrox.services import MenuRegistry, SceneEventBus, SceneEventType

# Check how many items are registered for a task
items = MenuRegistry.get_items_by_owner("SceneviewerApplicationTask")
print(f"SceneViewer has {len(items)} menu items")

# Check how many subscribers for an event
count = SceneEventBus.get_subscriber_count(SceneEventType.SCENE_LOADED)
print(f"{count} components are listening for SCENE_LOADED")

# Get all registered menu items
all_items = MenuRegistry.get_all_items()
for menu_id, descriptor in all_items.items():
    print(f"{menu_id}: {descriptor.menu_path}")
"""
