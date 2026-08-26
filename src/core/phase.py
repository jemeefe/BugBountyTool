"""
Base module for BugBountyTool phases.
Defines the interface that all phases must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
import logging


class BasePhase(ABC):
    """
    Clase base abstracta para las fases del pipeline.
    Todas las fases deben implementar los métodos aquí definidos.
    """

    def __init__(
        self, name: str, output_dir: str | Path, logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa una fase del pipeline.

        Args:
            name: Nombre descriptivo de la fase
            output_dir: Directorio donde guardar los resultados
            logger: Logger opcional (se usará el default si no se proporciona)
        """
        self.name = name
        self.output_dir = Path(output_dir)
        self.logger = logger or logging.getLogger(__name__)
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def execute(self, input_data: List[str] | str | None = None) -> List[str]:
        """
        Ejecuta la fase del pipeline.

        Args:
            input_data: Datos de entrada (puede ser una lista de strings,
                       un único string con ruta a archivo, o None si no se requiere)

        Returns:
            List[str]: Resultados de la fase (subdominios, hosts vivos, etc.)
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """
        Valida los datos de entrada antes de ejecutar la fase.

        Args:
            input_data: Datos a validar

        Returns:
            bool: True si los datos son válidos, False en caso contrario
        """
        pass

    def load_input(self, input_data: List[str] | str | None) -> List[str]:
        """
        Carga y normaliza los datos de entrada.

        Args:
            input_data: Puede ser una lista de strings, un path a archivo, o None

        Returns:
            List[str]: Lista de entradas procesadas
        """
        if input_data is None:
            return []

        if isinstance(input_data, list):
            return input_data

        if isinstance(input_data, str):
            from utils.helpers import read_file_lines

            return read_file_lines(input_data)

        return []

    def save_results(self, results: List[str], filename: str) -> str:
        """
        Guarda los resultados en un archivo dentro del directorio de salida.

        Args:
            results: Lista de resultados a guardar
            filename: Nombre del archivo de salida

        Returns:
            str: Ruta completa al archivo guardado
        """
        from utils.helpers import write_lines_to_file

        output_path = self.output_dir / filename
        success = write_lines_to_file(output_path, results)

        if success:
            self.logger.info(f"Resultados guardados en: {output_path}")
            return str(output_path)

        self.logger.error(f"Error guardando resultados en: {output_path}")
        return ""
