import os
import platform
from abc import ABC, abstractmethod
import tempfile
from typing import Optional

class PrintManager(ABC):
    @abstractmethod
    def print_file(self, filepath: str) -> None:
        pass

    @staticmethod
    def get_instance() -> 'PrintManager':
        system = platform.system().lower()
        if system == 'windows':
            return WindowsPrintManager()
        else:
            return UnixPrintManager()

class WindowsPrintManager(PrintManager):
    def print_file(self, filepath: str) -> None:
        try:
            import win32print
            import win32api
            win32api.ShellExecute(
                0,
                "print",
                filepath,
                None,
                ".",
                0
            )
        except ImportError:
            print(f"Arquivo gerado em: {filepath}")
            print("Impressão não disponível no Windows sem win32print")

class UnixPrintManager(PrintManager):
    def print_file(self, filepath: str) -> None:
        try:
            os.system(f"lpr {filepath}")
        except:
            print(f"Arquivo gerado em: {filepath}")
            print("Impressão não disponível neste sistema")
