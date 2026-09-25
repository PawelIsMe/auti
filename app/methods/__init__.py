import importlib.util
import inspect
from pathlib import Path

from app.logger import logger


def get_all_function_objects_from_directory(dir_path: str) -> list:
    """Ładuje wszystkie pliki .py z podanego katalogu (z wyjątkiem pliku,

    w którym znajduje się ta funkcja) i zwraca zbiorczą listę obiektów/referencji
    do wszystkich zdefiniowanych w nich funkcji.
    """
    directory = Path(dir_path).resolve()
    current_file = Path(__file__).resolve()

    all_functions = []

    # Przeglądamy wszystkie pliki .py w podanym katalogu
    for file_path in directory.glob("*.py"):
        # Ignorujemy plik, w którym zdefiniowana jest ta funkcja
        if file_path.resolve() == current_file:
            continue

        module_name = f"dynamic_mod_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            # Pomijamy pliki, które rzucają wyjątek przy imporcie
            continue

        # Pobieramy same obiekty/referencje funkcji zdefiniowanych bezpośrednio w tym pliku
        functions = [
            obj
            for name, obj in inspect.getmembers(module, inspect.isfunction)
            if obj.__module__ == module.__name__
        ]

        all_functions.extend(functions)
    return all_functions


TOOLS = get_all_function_objects_from_directory("app/methods")