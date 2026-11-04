"""Smoke build check: a PySide6 window that runs statsforecast AutoETS.

Used only to verify that the heavy scientific stack (numba, statsforecast)
and PySide6 can be packaged by PyInstaller. Not part of the product.
"""

import sys
import time

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


def run_forecast() -> str:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS

    rng = np.random.default_rng(0)
    days = pd.date_range("2026-01-01", periods=120, freq="D")
    weekly = 1 + 0.3 * np.sin(2 * np.pi * np.arange(120) / 7)
    df = pd.DataFrame({"unique_id": "demo", "ds": days, "y": rng.poisson(5 * weekly)})
    start = time.perf_counter()
    sf = StatsForecast(models=[AutoETS(season_length=7)], freq="D")
    forecast = sf.forecast(df=df, h=14)
    elapsed = time.perf_counter() - start
    total = float(forecast["AutoETS"].sum())
    return f"Прогноз на 14 дней: {total:.1f} шт. (расчёт {elapsed:.1f} с)"


class Worker(QObject):
    finished = Signal(str)

    def run(self) -> None:
        try:
            self.finished.emit(run_forecast())
        except Exception as exc:  # show any packaging problem in the window
            self.finished.emit(f"Ошибка: {exc!r}")


class Window(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Restock Planner — пробная сборка")
        self.label = QLabel("Нажмите кнопку, чтобы посчитать прогноз")
        self.button = QPushButton("Посчитать прогноз")
        self.button.clicked.connect(self.start)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.resize(420, 120)

    def start(self) -> None:
        self.button.setEnabled(False)
        self.label.setText("Считаю…")
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.done)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def done(self, text: str) -> None:
        self.label.setText(text)
        self.button.setEnabled(True)


def main() -> int:
    if "--headless" in sys.argv:  # automated check without a window
        sys.stdout.reconfigure(encoding="utf-8")
        print(run_forecast())
        return 0
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
