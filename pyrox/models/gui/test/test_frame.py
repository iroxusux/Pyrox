"""Testcase for TaskFrame"""
import unittest
from unittest.mock import Mock, patch
from pyrox.interfaces.gui import ITaskFrame
from pyrox.models.gui.frame import TaskFrame


class TestTaskFrame(unittest.TestCase):
    """Testcase for TaskFrame"""

    def setUp(self) -> None:
        """Set up the test case with PyQt6 widgets mocked."""
        self._patches = [
            patch('pyrox.models.gui.frame.QWidget'),
            patch('pyrox.models.gui.frame.QPushButton'),
            patch('pyrox.models.gui.frame.QLabel'),
            patch('pyrox.models.gui.frame.QHBoxLayout'),
            patch('pyrox.models.gui.frame.QVBoxLayout'),
        ]
        self.MockQWidget = self._patches[0].start()
        self.MockQPushButton = self._patches[1].start()
        self.MockQLabel = self._patches[2].start()
        self.MockQHBoxLayout = self._patches[3].start()
        self.MockQVBoxLayout = self._patches[4].start()
        for p in self._patches:
            self.addCleanup(p.stop)

        self.mock_parent = Mock()
        self.frame = TaskFrame(name="Test Frame", parent=self.mock_parent)

    def test_initialization(self):
        """Test that the frame initializes with the correct name and default values."""
        self.assertEqual(self.frame.name, "Test Frame")
        self.assertFalse(self.frame.get_shown())
        self.assertEqual(self.frame.on_teardown(), [])

    def test_is_itaskframe(self):
        """Test that TaskFrame implements ITaskFrame."""
        self.assertIsInstance(self.frame, ITaskFrame)

    def test_show_hide(self):
        """Test showing and hiding the frame."""
        self.frame.set_shown(True)
        self.assertTrue(self.frame.get_shown())
        self.frame.set_shown(False)
        self.assertFalse(self.frame.get_shown())

    def test_set_shown_updates_root_visibility(self):
        """Test that set_shown calls setVisible on the root widget."""
        self.frame.set_shown(True)
        self.frame._root.setVisible.assert_called_with(True)
        self.frame.set_shown(False)
        self.frame._root.setVisible.assert_called_with(False)

    def test_get_name(self):
        """Test get_name returns the frame name."""
        self.assertEqual(self.frame.get_name(), "Test Frame")

    def test_set_name(self):
        """Test set_name updates the frame name."""
        self.frame.set_name("New Name")
        self.assertEqual(self.frame.name, "New Name")

    def test_default_name_fallback(self):
        """Test that an empty name falls back to 'Task Frame'."""
        frame = TaskFrame(name='', parent=self.mock_parent)
        self.assertEqual(frame.name, 'Task Frame')

    def test_get_root(self):
        """Test that get_root returns the root widget."""
        self.assertIs(self.frame.get_root(), self.frame._root)

    def test_root_property(self):
        """Test that the root property returns the root widget."""
        self.assertIs(self.frame.root, self.frame._root)

    def test_content_frame(self):
        """Test that content_frame returns the content widget."""
        self.assertIs(self.frame.content_frame, self.frame._content_frame)

    def test_build_does_nothing(self):
        """Test that build() executes without error and returns None."""
        result = self.frame.build()
        self.assertIsNone(result)

    def test_destroy_callbacks(self):
        """Test that destroy callbacks are called with the frame as argument."""
        callback = Mock()
        self.frame.on_teardown().append(callback)
        self.frame.teardown()
        callback.assert_called_once_with(self.frame)

    def test_destroy_clears_callbacks(self):
        """Test that destroy clears all registered callbacks after execution."""
        self.frame.on_teardown().append(Mock())
        self.frame.teardown()
        self.assertEqual(self.frame.on_teardown(), [])

    def test_destroy_calls_delete_later(self):
        """Test that destroy calls deleteLater on the root widget."""
        self.frame.teardown()
        self.frame._root.deleteLater.assert_called_once()

    def test_destroy_non_callable_warns(self):
        """Test that a non-callable item in on_destroy generates a warning."""
        self.frame.on_teardown().append('not_a_callable')
        with patch('pyrox.models.gui.frame.log') as mock_log:
            self.frame.teardown()
            mock_log.return_value.warning.assert_called_once()

    def test_close_button_connected_to_destroy(self):
        """Test that the close button clicked signal is connected to destroy."""
        self.MockQPushButton.return_value.clicked.connect.assert_called_once_with(
            self.frame.teardown
        )
