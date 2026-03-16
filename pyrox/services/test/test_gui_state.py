"""Unit tests for GuiStateService."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from pyrox.services.gui_state import GuiStateService, _DEFAULT_STATE


class TestGuiStateService(unittest.TestCase):
    """Test cases for GuiStateService."""

    def setUp(self):
        """Reset static class state and redirect state file to a temp directory."""
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, 'TestApp_gui_state.json')

        # Reset static class state before every test
        GuiStateService._state = dict(_DEFAULT_STATE)
        GuiStateService._loaded = False

        # Redirect get_state_file_path to our temp file so tests never
        # touch the real user-data directory.
        self._path_patcher = patch.object(
            GuiStateService,
            'get_state_file_path',
            return_value=self.state_file,
        )
        self._path_patcher.start()

    def tearDown(self):
        """Stop patchers and clean up the temp directory."""
        self._path_patcher.stop()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Restore default state so subsequent test classes start clean
        GuiStateService._state = dict(_DEFAULT_STATE)
        GuiStateService._loaded = False

    # ------------------------------------------------------------------
    # Instantiation
    # ------------------------------------------------------------------

    def test_prevent_instantiation(self):
        """GuiStateService must not be directly instantiated."""
        with self.assertRaises(TypeError) as ctx:
            GuiStateService()
        self.assertIn('static class', str(ctx.exception))

    # ------------------------------------------------------------------
    # Default state
    # ------------------------------------------------------------------

    def test_default_size_is_none(self):
        """Before any data is set, get_size() returns (None, None)."""
        self.assertEqual(GuiStateService.get_size(), (None, None))

    def test_default_position_is_none(self):
        """Before any data is set, get_position() returns (None, None)."""
        self.assertEqual(GuiStateService.get_position(), (None, None))

    def test_default_window_state_is_normal(self):
        """Default window state should be 'normal'."""
        self.assertEqual(GuiStateService.get_window_state(), 'normal')

    def test_default_fullscreen_is_false(self):
        """Default fullscreen flag should be False."""
        self.assertFalse(GuiStateService.is_fullscreen())

    # ------------------------------------------------------------------
    # Setters / Getters
    # ------------------------------------------------------------------

    def test_set_and_get_size(self):
        GuiStateService.set_size(1280, 720)
        self.assertEqual(GuiStateService.get_size(), (1280, 720))

    def test_set_and_get_position(self):
        GuiStateService.set_position(100, 200)
        self.assertEqual(GuiStateService.get_position(), (100, 200))

    def test_set_and_get_window_state_normal(self):
        GuiStateService.set_window_state('normal')
        self.assertEqual(GuiStateService.get_window_state(), 'normal')

    def test_set_and_get_window_state_zoomed(self):
        GuiStateService.set_window_state('zoomed')
        self.assertEqual(GuiStateService.get_window_state(), 'zoomed')

    def test_set_and_get_window_state_iconic(self):
        GuiStateService.set_window_state('iconic')
        self.assertEqual(GuiStateService.get_window_state(), 'iconic')

    def test_set_window_state_invalid_raises(self):
        """An invalid window state string should raise ValueError."""
        with self.assertRaises(ValueError):
            GuiStateService.set_window_state('hidden')

    def test_set_and_get_fullscreen_true(self):
        GuiStateService.set_fullscreen(True)
        self.assertTrue(GuiStateService.is_fullscreen())

    def test_set_and_get_fullscreen_false(self):
        GuiStateService.set_fullscreen(False)
        self.assertFalse(GuiStateService.is_fullscreen())

    def test_size_stored_as_int(self):
        """Floats passed to set_size should be coerced to int."""
        GuiStateService.set_size(800.9, 600.1)  # type: ignore[arg-type]
        w, h = GuiStateService.get_size()
        self.assertIsInstance(w, int)
        self.assertIsInstance(h, int)

    def test_position_stored_as_int(self):
        """Floats passed to set_position should be coerced to int."""
        GuiStateService.set_position(50.7, 75.3)  # type: ignore[arg-type]
        x, y = GuiStateService.get_position()
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

    # ------------------------------------------------------------------
    # save() / load()
    # ------------------------------------------------------------------

    def test_save_creates_json_file(self):
        """save() should write a valid JSON file to the state file path."""
        GuiStateService.set_size(800, 600)
        GuiStateService.save()

        self.assertTrue(os.path.isfile(self.state_file))
        with open(self.state_file, encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertEqual(data['width'], 800)
        self.assertEqual(data['height'], 600)

    def test_load_restores_saved_state(self):
        """load() should restore all values that were previously saved."""
        GuiStateService.set_size(1024, 768)
        GuiStateService.set_position(30, 40)
        GuiStateService.set_window_state('zoomed')
        GuiStateService.set_fullscreen(False)
        GuiStateService.save()

        # Reset in-memory state to defaults, then reload from disk
        GuiStateService._state = dict(_DEFAULT_STATE)
        GuiStateService.load()

        self.assertEqual(GuiStateService.get_size(), (1024, 768))
        self.assertEqual(GuiStateService.get_position(), (30, 40))
        self.assertEqual(GuiStateService.get_window_state(), 'zoomed')
        self.assertFalse(GuiStateService.is_fullscreen())

    def test_load_with_no_file_uses_defaults(self):
        """load() with no state file on disk should silently apply defaults."""
        self.assertFalse(os.path.isfile(self.state_file))
        GuiStateService.load()

        self.assertEqual(GuiStateService.get_size(), (None, None))
        self.assertEqual(GuiStateService.get_window_state(), 'normal')
        self.assertFalse(GuiStateService.is_fullscreen())
        self.assertTrue(GuiStateService._loaded)

    def test_load_with_corrupt_file_uses_defaults(self):
        """load() with a corrupt JSON file should silently apply defaults."""
        with open(self.state_file, 'w', encoding='utf-8') as fh:
            fh.write('{ this is not valid json }}}')

        GuiStateService.load()

        self.assertEqual(GuiStateService.get_size(), (None, None))
        self.assertEqual(GuiStateService.get_window_state(), 'normal')

    def test_load_ignores_unknown_keys(self):
        """load() should only accept known keys; foreign keys are dropped."""
        with open(self.state_file, 'w', encoding='utf-8') as fh:
            json.dump({'width': 640, 'height': 480, 'injected_key': 'evil'}, fh)

        GuiStateService.load()

        self.assertEqual(GuiStateService.get_size(), (640, 480))
        self.assertNotIn('injected_key', GuiStateService._state)

    def test_load_marks_loaded_flag(self):
        """load() should set _loaded to True."""
        self.assertFalse(GuiStateService._loaded)
        GuiStateService.load()
        self.assertTrue(GuiStateService._loaded)

    def test_save_with_unwritable_path_does_not_raise(self):
        """save() failures should be silently swallowed, not propagated."""
        with patch('builtins.open', side_effect=OSError('disk full')):
            try:
                GuiStateService.save()
            except OSError:
                self.fail('save() should not propagate OSError')

    # ------------------------------------------------------------------
    # capture_from_window()
    # ------------------------------------------------------------------

    def _make_mock_window(
        self,
        w: int = 800,
        h: int = 600,
        x: int = 10,
        y: int = 20,
        maximized: bool = False,
        minimized: bool = False,
        fullscreen: bool = False,
    ):
        """Return a simple object that mimics the QMainWindow geometry API."""
        class _MockWindow:
            def width(self): return w
            def height(self): return h
            def x(self): return x
            def y(self): return y
            def isMaximized(self): return maximized
            def isMinimized(self): return minimized
            def isFullScreen(self): return fullscreen
            # Methods exercised by apply_to_window
            def resize(self, *a): self._resized = a
            def move(self, *a): self._moved = a
            def showMaximized(self): self._state = 'zoomed'
            def showMinimized(self): self._state = 'iconic'
            def showFullScreen(self): self._state = 'fullscreen'
        return _MockWindow()

    def test_capture_normal_window(self):
        win = self._make_mock_window(800, 600, 10, 20)
        GuiStateService.capture_from_window(win)

        self.assertEqual(GuiStateService.get_size(), (800, 600))
        self.assertEqual(GuiStateService.get_position(), (10, 20))
        self.assertEqual(GuiStateService.get_window_state(), 'normal')
        self.assertFalse(GuiStateService.is_fullscreen())

    def test_capture_maximized_window(self):
        win = self._make_mock_window(maximized=True)
        GuiStateService.capture_from_window(win)
        self.assertEqual(GuiStateService.get_window_state(), 'zoomed')

    def test_capture_minimized_window(self):
        win = self._make_mock_window(minimized=True)
        GuiStateService.capture_from_window(win)
        self.assertEqual(GuiStateService.get_window_state(), 'iconic')

    def test_capture_fullscreen_window(self):
        win = self._make_mock_window(fullscreen=True)
        GuiStateService.capture_from_window(win)
        self.assertTrue(GuiStateService.is_fullscreen())

    # ------------------------------------------------------------------
    # apply_to_window()
    # ------------------------------------------------------------------

    def test_apply_restores_size_and_position(self):
        GuiStateService.set_size(1920, 1080)
        GuiStateService.set_position(50, 60)

        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)

        self.assertEqual(win._resized, (1920, 1080))
        self.assertEqual(win._moved, (50, 60))

    def test_apply_fullscreen_skips_resize(self):
        """When fullscreen is set, apply_to_window should call showFullScreen only."""
        GuiStateService.set_fullscreen(True)
        GuiStateService.set_size(800, 600)

        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)

        self.assertEqual(win._state, 'fullscreen')
        self.assertFalse(hasattr(win, '_resized'))

    def test_apply_maximized_state(self):
        GuiStateService.set_window_state('zoomed')
        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)
        self.assertEqual(win._state, 'zoomed')

    def test_apply_minimized_state(self):
        GuiStateService.set_window_state('iconic')
        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)
        self.assertEqual(win._state, 'iconic')

    def test_apply_no_size_skips_resize(self):
        """With no saved size, apply_to_window should not call resize."""
        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)
        self.assertFalse(hasattr(win, '_resized'))

    def test_apply_no_position_skips_move(self):
        """With no saved position, apply_to_window should not call move."""
        win = self._make_mock_window()
        GuiStateService.apply_to_window(win)
        self.assertFalse(hasattr(win, '_moved'))

    # ------------------------------------------------------------------
    # Round-trip
    # ------------------------------------------------------------------

    def test_round_trip_save_and_load(self):
        """Full round-trip: capture → save → reset → load → apply."""
        win_before = self._make_mock_window(1366, 768, 5, 10)
        GuiStateService.capture_from_window(win_before)
        GuiStateService.save()

        GuiStateService._state = dict(_DEFAULT_STATE)
        GuiStateService.load()

        win_after = self._make_mock_window()
        GuiStateService.apply_to_window(win_after)

        self.assertEqual(win_after._resized, (1366, 768))
        self.assertEqual(win_after._moved, (5, 10))


if __name__ == '__main__':
    unittest.main()
