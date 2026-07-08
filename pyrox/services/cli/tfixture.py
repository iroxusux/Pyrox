"""Test fixture file so i dont have to keep changing envs while developing this in my core.
"""
from pyrox.services.cli.app import TerminalApplication
from pyrox.services.cli.menu import MenuItem
from pyrox.services.cli.state import InteractiveMenuState


if __name__ == '__main__':
    sub_state = InteractiveMenuState(
        None,
        'Sub Menu',
        [
            MenuItem('Child item 1', lambda: 'child item 1 selected'),
            MenuItem('Child item 2', lambda: 'child item 2 selected'),
            MenuItem('Child item 3', lambda: 'child item 3 selected'),
        ]
    )
    main_state = InteractiveMenuState(
        None,
        'Interactive Menu Demo',
        [
            MenuItem('Go to sub-menu', lambda: app.change_state(sub_state)),
            MenuItem('Item 2', lambda: 'item 2 selected'),
            MenuItem('Item 3', lambda: 'item 3 selected'),
            MenuItem('Exit', lambda: exit(0))
        ]
    )
    with TerminalApplication(initial_state=main_state) as app:
        app.run()
