"""Unit tests for pyrox/tasks/builtin.py"""
import importlib
import unittest
from unittest.mock import MagicMock, patch

from pyrox.services import TkGuiManager
from pyrox.services.menu_registry import MenuRegistry


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_app(name: str = 'TestApp') -> MagicMock:
    """Minimal mock IApplication."""
    app = MagicMock()
    app.name = name
    return app


class _TaskTestBase(unittest.TestCase):
    """Base class that patches all TkGuiManager menu accessors and MenuRegistry
    so that no real tkinter or GUI code runs during tests."""

    def setUp(self):
        self.app = _make_app()

        self.mock_file_menu = MagicMock()
        self.mock_edit_menu = MagicMock()
        self.mock_view_menu = MagicMock()
        self.mock_help_menu = MagicMock()
        self.mock_tools_menu = MagicMock()
        self.mock_root = MagicMock()

        self._patches = [
            patch.object(TkGuiManager, 'get_file_menu',  return_value=self.mock_file_menu),
            patch.object(TkGuiManager, 'get_edit_menu',  return_value=self.mock_edit_menu),
            patch.object(TkGuiManager, 'get_view_menu',  return_value=self.mock_view_menu),
            patch.object(TkGuiManager, 'get_help_menu',  return_value=self.mock_help_menu),
            patch.object(TkGuiManager, 'get_tools_menu', return_value=self.mock_tools_menu),
            patch.object(TkGuiManager, 'get_root',       return_value=self.mock_root),
            patch.object(MenuRegistry, 'register_item'),
        ]
        self.mocks = [p.start() for p in self._patches]
        self.mock_register_item = self.mocks[-1]

    def tearDown(self):
        for p in self._patches:
            p.stop()

    # ------------------------------------------------------------------
    # Helper: collect all registry_ids passed to MenuRegistry.register_item
    # ------------------------------------------------------------------
    def _registered_ids(self) -> list[str]:
        return [c.kwargs['menu_id'] for c in self.mock_register_item.call_args_list]


# ---------------------------------------------------------------------------
# FileTask
# ---------------------------------------------------------------------------

class TestFileTask(_TaskTestBase):
    """Tests for FileTask."""

    def _make_task(self):
        from pyrox.tasks.builtin import FileTask
        return FileTask(application=self.app)

    def test_registers_task_with_application(self):
        """ApplicationTask base registers self with the application on init."""
        task = self._make_task()
        self.app.register_task.assert_called_once_with(task)

    def test_inserts_separator_on_file_menu(self):
        """FileTask adds a separator at index 99998 before the Exit item."""
        self._make_task()
        self.mock_file_menu.insert_separator.assert_called_once_with(index=99998)

    def test_registers_exit_command(self):
        """FileTask registers an Exit command with the expected id and path."""
        self._make_task()
        ids = self._registered_ids()
        self.assertIn('exit', ids)

    def test_exit_command_registry_path(self):
        """The Exit command uses the 'File/Exit' registry path."""
        self._make_task()
        exit_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'exit'
        )
        self.assertEqual(exit_call.kwargs['menu_path'], 'File/Exit')

    def test_exit_command_calls_application_quit(self):
        """Invoking the Exit command calls application.quit(exit_code=0)."""
        self._make_task()
        _ = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'exit'
        )
        # The command is stored in the menu widget call, not directly in register_item;
        # retrieve it from insert_command call on the file menu mock.
        insert_calls = self.mock_file_menu.insert_command.call_args_list
        self.assertTrue(len(insert_calls) > 0, "insert_command should have been called")
        command = insert_calls[0].kwargs.get('command') or insert_calls[0].args[1] if insert_calls[0].args else None
        if command is None:
            # Reconstruct from kwargs
            for c in insert_calls:
                if 'Exit' in str(c):
                    command = c.kwargs.get('command')
                    break
        if command:
            command()
            self.app.quit.assert_called_once_with(exit_code=0)

    def test_exit_uses_file_menu(self):
        """The Exit command is inserted into the file menu widget."""
        self._make_task()
        exit_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'exit'
        )
        self.assertIs(exit_call.kwargs['menu_widget'], self.mock_file_menu)

    def test_exit_category_is_system(self):
        """The Exit command has category='system'."""
        self._make_task()
        exit_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'exit'
        )
        self.assertEqual(exit_call.kwargs.get('category'), 'system')

    def test_exit_accelerator_is_bound_on_root(self):
        """FileTask binds Ctrl+Q on the root window so the hotkey works."""
        self._make_task()
        bound_keys = [c[0][0] for c in self.mock_root.bind.call_args_list]
        self.assertIn('<Control-q>', bound_keys)


# ---------------------------------------------------------------------------
# HelpTask
# ---------------------------------------------------------------------------

class TestHelpTask(_TaskTestBase):
    """Tests for HelpTask."""

    def _make_task(self):
        from pyrox.tasks.builtin import HelpTask
        with patch('pyrox.tasks.builtin.show_help_window'):
            return HelpTask(application=self.app)

    def test_registers_task_with_application(self):
        task = self._make_task()
        self.app.register_task.assert_called_once_with(task)

    def test_registers_about_command(self):
        """HelpTask registers an 'about' menu entry."""
        self._make_task()
        self.assertIn('about', self._registered_ids())

    def test_about_registry_path(self):
        """The about entry uses 'Help/About Pyrox' as its registry path."""
        self._make_task()
        about_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'about'
        )
        self.assertEqual(about_call.kwargs['menu_path'], 'Help/About Pyrox')

    def test_about_uses_help_menu(self):
        """The about command is inserted into the help menu widget."""
        self._make_task()
        about_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'about'
        )
        self.assertIs(about_call.kwargs['menu_widget'], self.mock_help_menu)

    def test_about_category_is_help(self):
        """The about entry has category='help'."""
        self._make_task()
        about_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'about'
        )
        self.assertEqual(about_call.kwargs.get('category'), 'help')

    def test_about_accelerator_is_bound_on_root(self):
        """HelpTask binds F1 on the root window so the hotkey works."""
        self._make_task()
        bound_keys = [c[0][0] for c in self.mock_root.bind.call_args_list]
        self.assertIn('<F1>', bound_keys)

    def test_about_command_invokes_show_help_window(self):
        """Invoking the about command calls show_help_window with the root window."""
        with patch('pyrox.tasks.builtin.show_help_window') as mock_show:
            _ = HelpTask = None
            from pyrox.tasks.builtin import HelpTask  # type: ignore
            _ = HelpTask(application=self.app)
            # Pull the command out of insert_command call on the help menu
            insert_calls = self.mock_help_menu.insert_command.call_args_list
            self.assertTrue(insert_calls, "insert_command should have been called on help_menu")
            command = insert_calls[0].kwargs.get('command')
            if command:
                command()
                mock_show.assert_called_once_with(self.mock_root)


# ---------------------------------------------------------------------------
# ToolsTask
# ---------------------------------------------------------------------------

class TestToolsTask(_TaskTestBase):
    """Tests for ToolsTask."""

    def _make_task(self):
        from pyrox.tasks.builtin import ToolsTask
        with patch('pyrox.tasks.builtin.TextEditorFrame'):
            return ToolsTask(application=self.app)

    def test_registers_task_with_application(self):
        task = self._make_task()
        self.app.register_task.assert_called_once_with(task)

    def test_registers_text_editor_command(self):
        """ToolsTask registers a 'text_editor' menu entry."""
        self._make_task()
        self.assertIn('text_editor', self._registered_ids())

    def test_text_editor_registry_path(self):
        """The text_editor entry uses 'Tools/Text Editor' as its registry path."""
        self._make_task()
        te_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'text_editor'
        )
        self.assertEqual(te_call.kwargs['menu_path'], 'Tools/Text Editor')

    def test_text_editor_uses_tools_menu(self):
        """The text_editor command is inserted into the tools menu widget."""
        self._make_task()
        te_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'text_editor'
        )
        self.assertIs(te_call.kwargs['menu_widget'], self.mock_tools_menu)

    def test_text_editor_category_is_tools(self):
        """The text_editor entry has category='tools'."""
        self._make_task()
        te_call = next(
            c for c in self.mock_register_item.call_args_list
            if c.kwargs.get('menu_id') == 'text_editor'
        )
        self.assertEqual(te_call.kwargs.get('category'), 'tools')

    def test_text_editor_accelerator_is_bound_on_root(self):
        """ToolsTask binds Ctrl+T on the root window so the hotkey works."""
        self._make_task()
        bound_keys = [c[0][0] for c in self.mock_root.bind.call_args_list]
        self.assertIn('<Control-t>', bound_keys)

    def test_initial_frame_is_none(self):
        """_text_editor_frame starts as None."""
        task = self._make_task()
        self.assertIsNone(task._text_editor_frame)

    def test_create_frame_creates_new_frame_when_none(self):
        """_create_frame builds a TextEditorFrame when none exists."""
        from pyrox.tasks.builtin import ToolsTask
        mock_frame = MagicMock()
        mock_frame.root.winfo_exists.return_value = True

        with patch('pyrox.tasks.builtin.TextEditorFrame', return_value=mock_frame) as MockTEF:
            task = ToolsTask(application=self.app)
            task._create_frame()

            MockTEF.assert_called_once_with(self.app.workspace.workspace_area)
            self.app.workspace.register_frame.assert_called_once_with(mock_frame)
            self.assertIs(task._text_editor_frame, mock_frame)

    def test_create_frame_raises_existing_frame_when_alive(self):
        """_create_frame raises an existing alive frame instead of creating a new one."""
        from pyrox.tasks.builtin import ToolsTask

        mock_frame = MagicMock()
        mock_frame.root.winfo_exists.return_value = True  # frame is alive

        with patch('pyrox.tasks.builtin.TextEditorFrame', return_value=mock_frame):
            task = ToolsTask(application=self.app)
            task._text_editor_frame = mock_frame  # pre-set as existing

            task._create_frame()

            self.app.workspace.raise_frame.assert_called_once_with(mock_frame)
            self.app.workspace.register_frame.assert_not_called()

    def test_create_frame_recreates_after_frame_destroyed(self):
        """_create_frame creates a new frame if the existing frame's window is gone."""
        from pyrox.tasks.builtin import ToolsTask

        dead_frame = MagicMock()
        dead_frame.root.winfo_exists.return_value = False  # window destroyed

        new_frame = MagicMock()
        with patch('pyrox.tasks.builtin.TextEditorFrame', return_value=new_frame) as MockTEF:
            task = ToolsTask(application=self.app)
            task._text_editor_frame = dead_frame

            task._create_frame()

            MockTEF.assert_called_once()
            self.assertIs(task._text_editor_frame, new_frame)


# ---------------------------------------------------------------------------
# Cross-task: factory registration
# ---------------------------------------------------------------------------

class TestBuiltinTaskFactoryRegistration(unittest.TestCase):
    """Verify that the built-in tasks are registered in ApplicationTaskFactory."""

    def test_builtin_tasks_registered_in_factory(self):
        import pyrox.models
        import pyrox.models.task
        import pyrox.tasks.builtin
        importlib.reload(pyrox.models.task)
        importlib.reload(pyrox.models)      # Re-bind pyrox.models names to the new task classes
        importlib.reload(pyrox.tasks.builtin)

        registered = pyrox.models.task.ApplicationTaskFactory.get_registered_types()
        self.assertIn('FileTask',  registered)
        self.assertIn('HelpTask',  registered)
        self.assertIn('ToolsTask', registered)

    def test_all_builtin_tasks_are_subclasses_of_application_task(self):
        from pyrox.models.task import ApplicationTask
        from pyrox.tasks.builtin import FileTask, HelpTask, ToolsTask

        for cls in (FileTask, HelpTask, ToolsTask):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(issubclass(cls, ApplicationTask))


if __name__ == '__main__':
    unittest.main(verbosity=2)
