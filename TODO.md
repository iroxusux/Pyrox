# TODO List

This file tracks outstanding tasks, bugs, and feature requests for the Pyrox project.

## Legend

- 🔴 **Critical** - Blocking issue or severe bug
- 🟡 **High** - Important feature or significant bug
- 🟢 **Medium** - Nice to have or minor bug
- ⚪ **Low** - Future consideration or polish

## Active Issues

### 🔴 Critical

None currently.

### 🟡 High

#### Menu Checkbutton Initial State Issue
**File:** `pyrox/models/gui/tk/menu.py`  
**Line:** ~54 (add_checkbutton method)  
**Status:** In Progress  
**Description:** Tkinter menu checkbuttons do not show checked state on initialization when variable is True. The checkmark only appears after first user click.  
**Attempted Solutions:**
- Setting BooleanVar after creation ❌
- Using invoke() method ❌
- Setting master parameter on BooleanVar ❌
- Explicit onvalue/offvalue parameters ❌
- Using entryconfig to reapply variable ❌

**Next Steps:**
- Research tkinter menu widget limitations
- Consider alternative UI approach (toolbar buttons instead of menu checkbuttons)
- Check if this is a platform-specific issue (Windows)

---

### 🟢 Medium

#### Add Scrollbars for Large Scenes
**File:** `pyrox/models/gui/sceneviewer.py:373`  
**Status:** Not Started  
**Description:** Scene viewer needs scrollbars when content exceeds visible area.

#### Add Ruler/Coordinate Display
**File:** `pyrox/models/gui/sceneviewer.py:374`  
**Status:** Not Started  
**Description:** Add visual rulers and coordinate display to scene viewer.

#### Add Keyboard Shortcuts
**File:** `pyrox/models/gui/sceneviewer.py:403`  
**Status:** Not Started  
**Description:** Implement common keyboard shortcuts (Ctrl+Z undo, Ctrl+D duplicate, etc.).

#### Implement Viewport Culling
**File:** `pyrox/models/gui/sceneviewer.py:802`  
**Status:** Not Started  
**Description:** Add viewport culling optimization for rendering large scenes.

#### Add Rendering Order/Layering Support
**File:** `pyrox/models/gui/sceneviewer.py:841`  
**Status:** Not Started  
**Description:** Implement z-order/layering system for scene objects.

#### Add Scene Background Rendering
**File:** `pyrox/models/gui/sceneviewer.py:842`  
**Status:** Not Started  
**Description:** Support for custom scene backgrounds.

#### Add More Shape Support
**File:** `pyrox/models/gui/sceneviewer.py:916`  
**Status:** Not Started  
**Description:** Add support for polygon, text, image/sprite rendering.

#### Add Scrollbar to Property Panel
**File:** `pyrox/models/gui/tk/propertypanel.py:100`  
**Status:** Not Started  
**Description:** Property panel needs scrollbars for many properties.

#### Add Color Picker Button
**File:** `pyrox/models/gui/tk/propertypanel.py:356`  
**Status:** Not Started  
**Description:** Add color picker widget for color properties.

---

### ⚪ Low

#### Integrate Frame with GuiManager
**File:** `pyrox/models/gui/tk/frame.py:92`  
**Status:** Not Started  
**Description:** Properly integrate Frame initialization with GuiManager.

#### Implement Default Keybindings
**File:** `pyrox/models/gui/tk/backend.py:351`  
**Status:** Not Started  
**Description:** Add default keybinding setup if needed.

---

## Completed

<!-- Move completed items here with completion date -->

---

## How to Use This File

1. **Adding New Tasks:** Add items under the appropriate priority section with relevant details
2. **Updating Status:** Change status as work progresses (Not Started → In Progress → Completed)
3. **Completing Tasks:** Move completed items to the "Completed" section with date
4. **Priority Changes:** Move tasks between priority sections as needed

## Related Files

- `TODO.md` - This file (high-level task tracking)
- `CHANGELOG.md` - Historical record of changes
- Inline `# TODO:` comments - Implementation-level notes in code
