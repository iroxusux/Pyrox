"""Unit tests for task.py module."""
import pytest
from PyQt6.QtWidgets import QMenu
from unittest.mock import MagicMock, patch

from pyrox.models.task import ApplicationTask, ApplicationTaskFactory


class ConcreteApplicationTask(ApplicationTask):
    def create_task_frame(self):
        mock_frame = MagicMock()
        mock_frame.root.isVisible.return_value = True
        return mock_frame


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.name = 'TestApp'
    return app


class TestApplicationTaskFactory:
    @pytest.fixture(autouse=True)
    def _reset_factory(self):
        ApplicationTaskFactory._registered_types = {}
        ApplicationTaskFactory._tasks = {}
        yield
        ApplicationTaskFactory._registered_types = {}
        ApplicationTaskFactory._tasks = {}

    def test_build_tasks_calls_each_task_with_application(self):
        mock_application = MagicMock()
        mock_task_cls_a = MagicMock()
        mock_task_cls_a.__name__ = 'TaskA'
        mock_task_cls_b = MagicMock()
        mock_task_cls_b.__name__ = 'TaskB'
        ApplicationTaskFactory._registered_types = {
            'TaskA': mock_task_cls_a,
            'TaskB': mock_task_cls_b,
        }

        ApplicationTaskFactory.build_tasks(mock_application)

        mock_task_cls_a.assert_called_once_with(application=mock_application)
        mock_task_cls_b.assert_called_once_with(application=mock_application)
        assert 'TaskA' in ApplicationTaskFactory._tasks
        assert 'TaskB' in ApplicationTaskFactory._tasks
        assert ApplicationTaskFactory._tasks['TaskA'] is mock_task_cls_a.return_value
        assert ApplicationTaskFactory._tasks['TaskB'] is mock_task_cls_b.return_value

    def test_build_tasks_empty_registry(self):
        mock_application = MagicMock()
        ApplicationTaskFactory._registered_types = {}
        ApplicationTaskFactory.build_tasks(mock_application)  # should not raise

    def test_build_tasks_logs_count(self):
        mock_application = MagicMock()
        mock_task_cls = MagicMock()
        mock_task_cls.__name__ = 'Task'
        ApplicationTaskFactory._registered_types = {'Task': mock_task_cls}

        with patch('pyrox.models.task.log') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger
            ApplicationTaskFactory.build_tasks(mock_application)

        mock_log.assert_called_once_with(ApplicationTaskFactory)
        mock_logger.debug.assert_called_once()


class TestApplicationTask:
    def test_init_registers_task_with_application(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_app.register_task.assert_called_once_with(task)

    def test_get_application_returns_application(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        assert task.get_application() is mock_app

    def test_set_application_updates_application(self, mock_app):
        mock_app_b = MagicMock()
        mock_app_b.name = 'TestApp2'
        task = ConcreteApplicationTask(application=mock_app)
        task.set_application(mock_app_b)
        assert task.get_application() is mock_app_b

    def test_application_property_getter(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        assert task.application is mock_app

    def test_application_property_setter(self, mock_app):
        mock_app_b = MagicMock()
        task = ConcreteApplicationTask(application=mock_app)
        task.application = mock_app_b
        assert task.get_application() is mock_app_b

    def test_register_menu_command_delegates_to_gui_manager(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        dummy_command = MagicMock()

        with patch('pyrox.models.task.GuiManager.insert_menu_command_with_accelerator') as mock_insert, \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.open',
                registry_path='File/Open',
                index=0,
                label='Open',
                command=dummy_command,
                accelerator='Ctrl+O',
                underline=0,
            )

        mock_insert.assert_called_once_with(
            menu=mock_menu,
            index=0,
            label='Open',
            command=dummy_command,
            accelerator='Ctrl+O',
            underline=0,
        )

    def test_register_menu_command_noop_when_no_command(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)

        with patch('pyrox.models.task.GuiManager.insert_menu_command_with_accelerator') as mock_insert, \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.save',
                registry_path='File/Save',
                index=1,
                label='Save',
                command=None,
                accelerator='Ctrl+S',
                underline=0,
            )

        mock_insert.assert_called_once()
        assert mock_insert.call_args.kwargs['command'] is None

    def test_register_menu_command_disables_when_not_enabled(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        mock_action = MagicMock()

        with patch('pyrox.models.task.GuiManager.insert_menu_command_with_accelerator',
                   return_value=mock_action), \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='edit.undo',
                registry_path='Edit/Undo',
                index=0,
                label='Undo',
                command=MagicMock(),
                accelerator='Ctrl+Z',
                underline=0,
                enabled=False,
            )

        mock_action.setEnabled.assert_called_once_with(False)

    def test_register_menu_command_enabled_does_not_disable(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        mock_action = MagicMock()

        with patch('pyrox.models.task.GuiManager.insert_menu_command_with_accelerator',
                   return_value=mock_action), \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='edit.redo',
                registry_path='Edit/Redo',
                index=0,
                label='Redo',
                command=MagicMock(),
                accelerator='Ctrl+Y',
                underline=0,
                enabled=True,
            )

        mock_action.setEnabled.assert_not_called()

    def test_register_menu_command_registers_with_registry(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        dummy_command = MagicMock()
        mock_action = MagicMock()

        with patch('pyrox.models.task.GuiManager.insert_menu_command_with_accelerator',
                   return_value=mock_action), \
                patch('pyrox.models.task.MenuRegistry') as mock_registry:
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.exit',
                registry_path='File/Exit',
                index=2,
                label='Exit',
                command=dummy_command,
                accelerator='Alt+F4',
                underline=1,
                category='file',
                subcategory='actions',
            )

        mock_registry.register_item.assert_called_once_with(
            menu_id='file.exit',
            menu_path='File/Exit',
            menu_widget=mock_menu,
            menu_index=2,
            owner='ConcreteApplicationTask',
            action=mock_action,
            command=dummy_command,
            category='file',
            subcategory='actions',
        )

    def test_register_submenu_inserts_cascade(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        mock_submenu = MagicMock(spec=QMenu)
        existing_action = MagicMock()
        mock_menu.actions.return_value = [MagicMock(), existing_action]

        with patch('pyrox.models.task.MenuRegistry'):
            task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='view.panels',
                registry_path='View/Panels',
                index=1,
                label='Panels',
                underline=0,
            )

        mock_menu.insertMenu.assert_called_once_with(existing_action, mock_submenu)
        mock_submenu.setTitle.assert_called_once_with('Panels')

    def test_register_submenu_returns_submenu(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        mock_submenu = MagicMock(spec=QMenu)

        with patch('pyrox.models.task.MenuRegistry'):
            result = task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='view.tools',
                registry_path='View/Tools',
                index=0,
                label='Tools',
                underline=0,
            )

        assert result is mock_submenu

    def test_register_submenu_registers_with_registry(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=QMenu)
        mock_submenu = MagicMock(spec=QMenu)

        with patch('pyrox.models.task.MenuRegistry') as mock_registry:
            task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='help.about',
                registry_path='Help/About',
                index=0,
                label='About',
                underline=0,
                category='help',
            )

        mock_registry.register_item.assert_called_once_with(
            menu_id='help.about',
            menu_path='Help/About',
            menu_widget=mock_submenu,
            menu_index=0,
            owner='ConcreteApplicationTask',
            category='help',
        )

    def test_task_frame_initially_none(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        assert task._task_frame is None

    def test_frame_destroy_callback_is_set(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        assert callable(task._frame_destroy_callback)

    def test_create_or_raise_frame_creates_when_none(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_frame = MagicMock()
        mock_frame.root.isVisible.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        assert task._task_frame is mock_frame

    def test_create_or_raise_frame_registers_with_workspace(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_frame = MagicMock()
        mock_frame.root.isVisible.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        mock_app.workspace.register_frame.assert_called_once_with(mock_frame)

    def test_create_or_raise_frame_attaches_destroy_callback(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        mock_frame = MagicMock()
        mock_frame.root.isVisible.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        mock_frame.on_teardown.return_value.append.assert_called_once_with(task._frame_destroy_callback)

    def test_create_or_raise_frame_raises_alive_frame(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        alive_frame = MagicMock()
        alive_frame.root.isVisible.return_value = True
        task._task_frame = alive_frame

        with patch.object(task, 'create_task_frame') as mock_create:
            task.create_or_raise_frame()
            mock_create.assert_not_called()

        mock_app.workspace.raise_frame.assert_called_once_with(alive_frame)

    def test_create_or_raise_frame_recreates_destroyed_frame(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        dead_frame = MagicMock()
        dead_frame.root.isVisible.return_value = False
        task._task_frame = dead_frame

        new_frame = MagicMock()
        new_frame.root.isVisible.return_value = True

        with patch.object(task, 'create_task_frame', return_value=new_frame):
            task.create_or_raise_frame()

        assert task._task_frame is new_frame

    def test_on_frame_destroyed_clears_task_frame(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        task._task_frame = MagicMock()
        task._on_frame_destroyed()
        assert task._task_frame is None

    def test_frame_destroy_callback_triggers_on_frame_destroyed(self, mock_app):
        task = ConcreteApplicationTask(application=mock_app)
        with patch.object(task, '_on_frame_destroyed') as mock_handler:
            task._frame_destroy_callback()
            mock_handler.assert_called_once()
