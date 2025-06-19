"""run this engine locally (for debugging or demonstration purposes)
    """
from __future__ import annotations

import datetime
from pyrox.models.plc import Controller


def main():
    """test this engine environment with a default application
    """
    start_time = datetime.datetime.now()
    _ = Controller.from_file(r"C:\Users\MH8243\EQUANS\Indicon LLC - Software & Emulation - Documents\Pyrox\docs\controls\_test_gm.L5X")  # Root file
    end_time = datetime.datetime.now()
    print(f"Controller loaded in {end_time - start_time} seconds")


if __name__ == '__main__':
    main()
