import sys


REG_BUFFER_CMD = '\x1b[?1049l'
ALT_BUFFER_CMD = '\x1b[?1049h'


def enter_alternate_mode():
    sys.stdout.write(ALT_BUFFER_CMD)
    sys.stdout.flush()


def exit_alternate_mode():
    sys.stdout.write(REG_BUFFER_CMD)


if __name__ == '__main__':
    try:
        enter_alternate_mode()
        while True:
            word = input('Enter something, idiot')
            print(word)
    finally:
        exit_alternate_mode()
