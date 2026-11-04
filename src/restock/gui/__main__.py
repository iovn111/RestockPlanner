"""Entry point of the desktop application. Implemented in Stage 6."""

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication, QLabel

    app = QApplication(sys.argv)
    label = QLabel("Restock Planner — интерфейс появится на Этапе 6.")
    label.setWindowTitle("Restock Planner")
    label.resize(420, 120)
    label.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
