"""
Módulo de logging para BugBountyTool.
Proporciona configuración centralizada para logs en consola y archivo.
"""

import logging
import os
from pathlib import Path


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: str | None = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configura y devuelve un logger con las especificaciones dadas.

    Args:
        name: Nombre del logger (normalmente __name__ del módulo)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta al archivo de log (opcional)
        console: Si True, también muestra logs en consola

    Returns:
        logging.Logger: Configurado según los parámetros
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Evitar duplicación de handlers
    if logger.handlers:
        return logger

    # Formato de logs con colores para consola
    class ColorFormatter(logging.Formatter):
        RED = '\033[91m'
        YELLOW = '\033[93m'
        RESET = '\033[0m'

        def format(self, record):
            msg = super().format(record)
            if record.levelno == logging.WARNING:
                msg = f"{self.YELLOW}{msg}{self.RESET}"
            elif record.levelno >= logging.ERROR:
                msg = f"{self.RED}{msg}{self.RESET}"
            return msg

    formatter = ColorFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Handler de consola
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Handler de archivo
    if log_file:
        log_path = Path(log_file)
        # Crear directorio si no existe
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Logger por defecto para el framework
default_logger = setup_logger("BugBountyTool")
