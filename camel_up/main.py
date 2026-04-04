import os
import sys

# Ensure the project root (camel_up/) is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.run()


if __name__ == '__main__':
    main()