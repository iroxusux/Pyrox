"""Unit tests for TkGuiManager in pyrox/services/gui.py."""

from __future__ import annotations

import tkinter as tk
import unittest
from unittest.mock import MagicMock, Mock, patch

from pyrox.interfaces.constants import EnvironmentKeys
from pyrox.services.gui import TkGuiManager, _accelerator_to_tk_binding
from pyrox.services.menu_registry import MenuRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_manager() -> None:
    """Reset all TkGuiManager class-level state between tests."""
    TkGuiManager._initialized = False
    TkGuiManager._root_window = None
    TkGuiManager._root_menu = None
    TkGuiManager._file_menu = None
    TkGuiManager._edit_menu = None
    TkGuiManager._view_menu = None
    TkGuiManager._tools_menu = None
    TkGuiManager._help_menu = None
    TkGuiManager._after_id = None


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

class TestTkGuiManagerInstantiation(unittest.TestCase):
    """TkGuiManager is a static class — instantiation must be prevented."""

    def test_cannot_be_instantiated(self):
        """Calling TkGuiManager() raises TypeError."""
        with self.assertRaises(TypeError):
            TkGuiManager()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Root Window Management
# ---------------------------------------------------------------------------

class TestTkGuiManagerRootWindow(unittest.TestCase):
    """Tests for root window creation and retrieval."""

    def setUp(self):
        _reset_manager()
        MenuRegistry.clear()

    def tearDown(self):
        _reset_manager()
        MenuRegistry.clear()

    # ---- get_root ----

    def test_get_root_raises_before_initialization(self):
        """get_root() raises RuntimeError when no window exists yet."""
        with self.assertRaises(RuntimeError, msg="Root window not initialized"):
            TkGuiManager.get_root()

    # ---- create_root_window ----

    @patch('pyrox.services.gui.ThemeManager')
    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui.tk.Tk')
    def test_create_root_window_returns_tk_instance(
        self, mock_tk_class, mock_env, mock_theme
    ):
        """create_root_window() constructs and returns a tk.Tk instance."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_env.get.return_value = '800x600'

        result = TkGuiManager.create_root()

        mock_tk_class.assert_called_once()
        self.assertIs(result, mock_root)

    @patch('pyrox.services.gui.ThemeManager')
    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui.tk.Tk')
    def test_create_root_window_calls_theme_setup(
        self, mock_tk_class, mock_env, mock_theme
    ):
        """create_root_window() ensures the theme is applied."""
        mock_tk_class.return_value = MagicMock()
        mock_env.get.return_value = '800x600'

        TkGuiManager.create_root()

        mock_theme.ensure_theme_created.assert_called_once()

    @patch('pyrox.services.gui.ThemeManager')
    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui.tk.Tk')
    def test_create_root_window_is_idempotent(
        self, mock_tk_class, mock_env, mock_theme
    ):
        """create_root_window() returns the existing window on subsequent calls."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_env.get.return_value = '800x600'

        first = TkGuiManager.create_root()
        second = TkGuiManager.create_root()

        mock_tk_class.assert_called_once()
        self.assertIs(first, second)

    @patch('pyrox.services.gui.ThemeManager')
    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui.tk.Tk')
    def test_get_root_returns_created_window(
        self, mock_tk_class, mock_env, mock_theme
    ):
        """get_root() returns the window after create_root_window()."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_env.get.return_value = '800x600'

        TkGuiManager.create_root()
        result = TkGuiManager.get_root()

        self.assertIs(result, mock_root)

    # ---- focus / quit / run loop ----

    def _with_mock_root(self):
        """Inject a mock root directly (no Tk()). Returns the mock."""
        mock_root = MagicMock()
        TkGuiManager._root_window = mock_root
        return mock_root

    def test_focus_root_window_calls_focus(self):
        """focus_root_window() delegates to window.focus()."""
        mock_root = self._with_mock_root()
        TkGuiManager.focus_root()
        mock_root.focus.assert_called_once()

    def test_quit_application_calls_quit(self):
        """quit_application() delegates to window.quit()."""
        mock_root = self._with_mock_root()
        TkGuiManager.quit_application()
        mock_root.quit.assert_called_once()

    def test_run_main_loop_calls_mainloop(self):
        """run_main_loop() delegates to window.mainloop()."""
        mock_root = self._with_mock_root()
        TkGuiManager.run_main_loop()
        mock_root.mainloop.assert_called_once()


# ---------------------------------------------------------------------------
# Window Title
# ---------------------------------------------------------------------------

class TestTkGuiManagerTitle(unittest.TestCase):
    """Tests for get_title() and set_title()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    def test_set_title_updates_window(self):
        """set_title() calls title() on the root window."""
        TkGuiManager.set_title("My Application")
        self.mock_root.title.assert_called_with("My Application")

    def test_set_title_raises_type_error_for_non_string(self):
        """set_title() raises TypeError when title is not a string."""
        for bad in (42, None, ['title'], object()):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    TkGuiManager.set_title(bad)  # type: ignore[arg-type]

    def test_get_title_returns_window_title(self):
        """get_title() returns the value reported by the window."""
        self.mock_root.title.return_value = "App Title"
        result = TkGuiManager.get_title(None)
        self.assertEqual(result, "App Title")

    def test_set_title_with_explicit_window(self):
        """set_title() uses the supplied window instead of root."""
        custom = MagicMock()
        TkGuiManager.set_title("Custom", window=custom)
        custom.title.assert_called_with("Custom")
        self.mock_root.title.assert_not_called()

    def test_get_title_with_explicit_window(self):
        """get_title() uses the supplied window instead of root."""
        custom = MagicMock()
        custom.title.return_value = "Custom Title"
        result = TkGuiManager.get_title(custom)
        self.assertEqual(result, "Custom Title")
        self.mock_root.title.assert_not_called()


# ---------------------------------------------------------------------------
# Window Icon
# ---------------------------------------------------------------------------

class TestTkGuiManagerIcon(unittest.TestCase):
    """Tests for set_icon()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    def test_set_icon_raises_type_error_for_non_string(self):
        """set_icon() raises TypeError when path is not a string."""
        for bad in (123, None, ['icon.ico']):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    TkGuiManager.set_icon(bad)  # type: ignore[arg-type]

    def test_set_icon_on_root_window(self):
        """set_icon() calls iconbitmap on the root window by default."""
        TkGuiManager.set_icon("resources/icon.ico")
        self.mock_root.iconbitmap.assert_called_with("resources/icon.ico")

    def test_set_icon_on_custom_window(self):
        """set_icon() calls iconbitmap on a supplied window."""
        custom = MagicMock()
        TkGuiManager.set_icon("resources/icon.ico", window=custom)
        custom.iconbitmap.assert_called_with("resources/icon.ico")
        self.mock_root.iconbitmap.assert_not_called()


# ---------------------------------------------------------------------------
# Event Handling
# ---------------------------------------------------------------------------

class TestTkGuiManagerEvents(unittest.TestCase):
    """Tests for hotkey binding, event scheduling, and protocol hooks."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    # ---- bind_hotkey ----

    def test_bind_hotkey_registers_with_root(self):
        """bind_hotkey() calls bind() on the root window."""
        callback = Mock()
        TkGuiManager.bind_hotkey('<Control-s>', callback)
        self.mock_root.bind.assert_called_once()
        bound_hotkey = self.mock_root.bind.call_args[0][0]
        self.assertEqual(bound_hotkey, '<Control-s>')

    def test_bind_hotkey_wrapper_invokes_callback(self):
        """The wrapper passed to bind() calls the original callback on key event."""
        callback = Mock()
        TkGuiManager.bind_hotkey('<Control-s>', callback)
        wrapper = self.mock_root.bind.call_args[0][1]
        wrapper(Mock())  # simulate Tkinter key event
        callback.assert_called_once()

    # ---- schedule / cancel ----

    def test_schedule_event_calls_after(self):
        """schedule_event() delegates to root.after()."""
        callback = Mock()
        self.mock_root.after.return_value = 42

        result = TkGuiManager.schedule_event(500, callback)

        self.mock_root.after.assert_called_with(500, callback)
        self.assertEqual(result, 42)

    def test_cancel_scheduled_event_calls_after_cancel(self):
        """cancel_scheduled_event() delegates to root.after_cancel() with the given id."""
        TkGuiManager.cancel_scheduled_event('42')
        self.mock_root.after_cancel.assert_called_with('42')

    # ---- window event subscriptions ----

    def test_subscribe_to_window_change_event_binds_configure(self):
        """subscribe_to_window_change_event() binds the <Configure> event with add='+'."""
        callback = Mock()
        TkGuiManager.subscribe_to_window_change_event(callback)
        self.mock_root.bind.assert_called_once()
        self.assertEqual(self.mock_root.bind.call_args[0][0], '<Configure>')
        self.assertEqual(self.mock_root.bind.call_args.kwargs.get('add'), '+')

    def test_subscribe_to_window_change_event_does_not_replace_existing_binding(self):
        """Multiple subscribers are stacked via add='+' rather than replacing each other."""
        cb1, cb2 = Mock(), Mock()
        TkGuiManager.subscribe_to_window_change_event(cb1)
        TkGuiManager.subscribe_to_window_change_event(cb2)
        # Both calls must use add='+'
        for c in self.mock_root.bind.call_args_list:
            self.assertEqual(c.kwargs.get('add'), '+')

    def test_subscribe_to_window_close_event_sets_protocol(self):
        """subscribe_to_window_close_event() sets WM_DELETE_WINDOW protocol."""
        callback = Mock()
        TkGuiManager.subscribe_to_window_close_event(callback)
        self.mock_root.protocol.assert_called_once_with("WM_DELETE_WINDOW", callback)

    # ---- reroute_excepthook ----

    def test_reroute_excepthook_sets_report_callback_exception(self):
        """reroute_excepthook() assigns the callback to tk.report_callback_exception."""
        original = getattr(tk, 'report_callback_exception', None)
        callback = Mock()
        try:
            TkGuiManager.reroute_excepthook(callback)
            self.assertIs(tk.report_callback_exception, callback)  # type: ignore[attr-defined]
        finally:
            if original is not None:
                tk.report_callback_exception = original  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Root Menu Management
# ---------------------------------------------------------------------------

class TestTkGuiManagerRootMenu(unittest.TestCase):
    """Tests for root menu creation and sub-menu accessors."""

    def setUp(self):
        _reset_manager()
        MenuRegistry.clear()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()
        MenuRegistry.clear()

    @patch('pyrox.services.gui.tk.Menu')
    def test_create_root_menu_returns_menu(self, mock_menu_class):
        """create_root_menu() creates a tk.Menu and attaches it to root."""
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu

        result = TkGuiManager.create_root_menu()

        self.assertIsNotNone(result)

    @patch('pyrox.services.gui.tk.Menu')
    def test_create_root_menu_configures_root(self, mock_menu_class):
        """create_root_menu() calls root.config(menu=...) to attach the menu."""
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu

        TkGuiManager.create_root_menu()

        self.mock_root.config.assert_called_with(menu=mock_menu)

    @patch('pyrox.services.gui.tk.Menu')
    def test_create_root_menu_is_idempotent(self, mock_menu_class):
        """create_root_menu() returns the same menu object on repeated calls."""
        mock_menu_class.return_value = MagicMock()

        first = TkGuiManager.create_root_menu()
        second = TkGuiManager.create_root_menu()

        self.assertIs(first, second)

    @patch('pyrox.services.gui.tk.Menu')
    def test_create_root_menu_registers_five_submenus(self, mock_menu_class):
        """create_root_menu() registers all five standard menus in MenuRegistry."""
        mock_menu_class.return_value = MagicMock()

        TkGuiManager.create_root_menu()

        for menu_id in ('file_menu', 'edit_menu', 'view_menu', 'tools_menu', 'help_menu'):
            with self.subTest(menu_id=menu_id):
                self.assertIsNotNone(MenuRegistry.get_item(menu_id))

    @patch('pyrox.services.gui.tk.Menu')
    def test_create_root_menu_adds_cascades(self, mock_menu_class):
        """create_root_menu() adds five cascades to the root menu."""
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu

        TkGuiManager.create_root_menu()

        self.assertEqual(mock_menu.add_cascade.call_count, 5)

    def test_get_root_menu_raises_before_initialization(self):
        """get_root_menu() raises RuntimeError if menu has not been created."""
        with self.assertRaises(RuntimeError):
            TkGuiManager.get_root_menu()

    @patch('pyrox.services.gui.tk.Menu')
    def test_get_root_menu_after_creation(self, mock_menu_class):
        """get_root_menu() returns the menu after create_root_menu()."""
        mock_menu_class.return_value = MagicMock()
        created = TkGuiManager.create_root_menu()
        self.assertIs(TkGuiManager.get_root_menu(), created)

    def test_submenu_accessors_raise_before_creation(self):
        """All sub-menu getters raise RuntimeError before create_root_menu()."""
        accessors = [
            TkGuiManager.get_file_menu,
            TkGuiManager.get_edit_menu,
            TkGuiManager.get_view_menu,
            TkGuiManager.get_tools_menu,
            TkGuiManager.get_help_menu,
        ]
        for accessor in accessors:
            with self.subTest(accessor=accessor.__name__):
                with self.assertRaises(RuntimeError):
                    accessor()

    @patch('pyrox.services.gui.tk.Menu')
    def test_submenu_accessors_after_creation(self, mock_menu_class):
        """All sub-menu getters return valid widgets after create_root_menu()."""
        mock_menu_class.return_value = MagicMock()
        TkGuiManager.create_root_menu()

        for accessor in (
            TkGuiManager.get_file_menu,
            TkGuiManager.get_edit_menu,
            TkGuiManager.get_view_menu,
            TkGuiManager.get_tools_menu,
            TkGuiManager.get_help_menu,
        ):
            with self.subTest(accessor=accessor.__name__):
                self.assertIsNotNone(accessor())

    @patch('pyrox.services.gui.tk.Menu')
    def test_submenus_owned_by_tk_gui_manager(self, mock_menu_class):
        """All registered sub-menus are owned by 'TkGuiManager'."""
        mock_menu_class.return_value = MagicMock()
        TkGuiManager.create_root_menu()

        items = MenuRegistry.get_items_by_owner('TkGuiManager')
        self.assertEqual(len(items), 5)
        for item in items:
            with self.subTest(menu_id=item.menu_id):
                self.assertEqual(item.owner, 'TkGuiManager')


# ---------------------------------------------------------------------------
# Window Geometry Save / Restore
# ---------------------------------------------------------------------------

class TestTkGuiManagerWindowGeometry(unittest.TestCase):
    """Tests for save_window_geometry() and restore_window_geometry()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root
        TkGuiManager._after_id = None

    def tearDown(self):
        _reset_manager()

    # ---- save_window_geometry ----

    @patch('pyrox.services.gui.EnvManager')
    def test_save_window_geometry_schedules_delayed_event(self, _mock_env):
        """save_window_geometry() calls after() exactly once."""
        self.mock_root.after.return_value = 'after#1'

        TkGuiManager.save_root_geometry()

        self.mock_root.after.assert_called_once()
        self.assertEqual(TkGuiManager._after_id, 'after#1')

    @patch('pyrox.services.gui.EnvManager')
    def test_save_window_geometry_cancels_pending_event(self, _mock_env):
        """save_window_geometry() cancels the previous pending event."""
        TkGuiManager._after_id = 'after#old'
        self.mock_root.after.return_value = 'after#new'

        TkGuiManager.save_root_geometry()

        self.mock_root.after_cancel.assert_called_with('after#old')

    @patch('pyrox.services.gui.EnvManager')
    def test_save_window_geometry_no_cancel_when_no_pending(self, _mock_env):
        """save_window_geometry() does not cancel anything when no event is pending."""
        TkGuiManager._after_id = None
        self.mock_root.after.return_value = 1

        TkGuiManager.save_root_geometry()

        self.mock_root.after_cancel.assert_not_called()

    # ---- restore_window_geometry ----

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_window_geometry_enables_fullscreen(self, mock_env):
        """restore_window_geometry() sets fullscreen when env flag is True."""
        def _get(key, default=None, cast_type=None):
            if key == EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN:
                return True
            return default

        mock_env.get.side_effect = _get

        TkGuiManager.restore_root_geometry()

        self.mock_root.attributes.assert_any_call('-fullscreen', True)

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_window_geometry_applies_size_and_position(self, mock_env):
        """restore_window_geometry() builds and applies a full geometry string."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: (100, 200),
                EnvironmentKeys.ui.UI_WINDOW_SIZE: '1024x768',
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'normal',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        TkGuiManager.restore_root_geometry()

        self.mock_root.geometry.assert_called_with('1024x768+100+200')

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_window_geometry_applies_window_state(self, mock_env):
        """restore_window_geometry() restores the saved window state."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: None,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: None,
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'zoomed',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        TkGuiManager.restore_root_geometry()

        self.mock_root.state.assert_called_with('zoomed')

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_window_geometry_size_only(self, mock_env):
        """restore_window_geometry() handles size without position gracefully."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: None,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: '800x600',
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'normal',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        TkGuiManager.restore_root_geometry()

        self.mock_root.geometry.assert_called_with('800x600')


# ---------------------------------------------------------------------------
# Accelerator → Tkinter binding conversion
# ---------------------------------------------------------------------------

class TestAcceleratorToTkBinding(unittest.TestCase):
    """Tests for the module-level _accelerator_to_tk_binding() helper."""

    def test_ctrl_alpha_lowercases_key(self):
        """Ctrl+Q becomes <Control-q>."""
        self.assertEqual(_accelerator_to_tk_binding('Ctrl+Q'), '<Control-q>')

    def test_ctrl_shift_alpha_preserves_case(self):
        """Ctrl+Shift+S becomes <Control-Shift-S> (case preserved under Shift)."""
        self.assertEqual(_accelerator_to_tk_binding('Ctrl+Shift+S'), '<Control-Shift-S>')

    def test_function_key_only(self):
        """F1 becomes <F1>."""
        self.assertEqual(_accelerator_to_tk_binding('F1'), '<F1>')

    def test_alt_function_key(self):
        """Alt+F4 becomes <Alt-F4>."""
        self.assertEqual(_accelerator_to_tk_binding('Alt+F4'), '<Alt-F4>')

    def test_control_spelled_out(self):
        """'Control+S' (spelled-out modifier) is accepted."""
        self.assertEqual(_accelerator_to_tk_binding('Control+S'), '<Control-s>')

    def test_empty_string_returns_none(self):
        """Empty accelerator string returns None."""
        self.assertIsNone(_accelerator_to_tk_binding(''))

    def test_none_like_empty_returns_none(self):
        """Accelerator with no key token returns None."""
        self.assertIsNone(_accelerator_to_tk_binding('Ctrl+Shift+'))

    def test_multiple_modifiers(self):
        """Ctrl+Alt+Del becomes <Control-Alt-Delete>."""
        self.assertEqual(_accelerator_to_tk_binding('Ctrl+Alt+Delete'), '<Control-Alt-Delete>')


# ---------------------------------------------------------------------------
# TkGuiManager.insert_menu_command_with_accelerator
# ---------------------------------------------------------------------------

class TestInsertMenuCommandWithAccelerator(unittest.TestCase):
    """Tests for TkGuiManager.insert_menu_command_with_accelerator()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        TkGuiManager._root_window = self.mock_root
        self.mock_menu = MagicMock()

    def tearDown(self):
        _reset_manager()

    def test_inserts_command_into_menu(self):
        """The method calls insert_command on the provided menu widget."""
        cmd = Mock()
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=cmd,
            accelerator='Ctrl+Q',
            underline=0,
        )
        self.mock_menu.insert_command.assert_called_once_with(
            index=0,
            label='Exit',
            command=cmd,
            accelerator='Ctrl+Q',
            underline=0,
        )

    def test_binds_hotkey_on_root(self):
        """The method also binds the accelerator key on the root window."""
        cmd = Mock()
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=cmd,
            accelerator='Ctrl+Q',
            underline=0,
        )
        bound_keys = [c[0][0] for c in self.mock_root.bind.call_args_list]
        self.assertIn('<Control-q>', bound_keys)

    def test_no_binding_for_empty_accelerator(self):
        """No hotkey binding occurs when accelerator is an empty string."""
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=Mock(),
            accelerator='',
            underline=0,
        )
        self.mock_root.bind.assert_not_called()

    def test_no_op_command_used_when_command_is_none(self):
        """A None command is replaced with a no-op rather than raising."""
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=None,
            accelerator='Ctrl+Q',
            underline=0,
        )
        # insert_command must still be called
        self.mock_menu.insert_command.assert_called_once()
        # and since command is None → no-op, no binding expected
        self.mock_root.bind.assert_not_called()

    def test_hotkey_wrapper_calls_command(self):
        """The hotkey wrapper bound to the root actually invokes the command."""
        cmd = Mock()
        TkGuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Test',
            command=cmd,
            accelerator='F1',
            underline=0,
        )
        # Retrieve the wrapper that was bound
        wrapper = self.mock_root.bind.call_args[0][1]
        wrapper(Mock())  # simulate Tkinter key event
        cmd.assert_called_once()


if __name__ == '__main__':
    unittest.main()
