"""
Fase de Escaneo (Scanning) para BugBountyTool.
Encargada de escanear puertos y servicios usando nmap.
"""

import logging
from pathlib import Path
from typing import List, Optional

from core.phase import BasePhase
from utils.helpers import run_command, deduplicate_list


class ScanningPhase(BasePhase):
    """
    Fase de escaneo de puertos y servicios.
    Usa nmap (o similar) para detectar puertos abiertos y servicios.
    """

    def __init__(
        self,
        output_dir: str | Path,
        logger: Optional[logging.Logger] = None,
        tool_path: str = "nmap",
    ):
        """
        Inicializa la fase de escaneo.

        Args:
            output_dir: Directorio donde guardar los resultados
            logger: Logger opcional
            tool_path: Ruta al binario de nmap (por defecto 'nmap' en PATH)
        """
        super().__init__("Scanning", output_dir, logger)
        self.tool_path = tool_path
        self.output_file = self.output_dir / "scan_results.txt"

    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """
        Valida que se proporcionen hosts para escanear.
        """
        if not input_data:
            self.logger.error("No se proporcionaron hosts para escanear")
            return False

        if isinstance(input_data, list) and len(input_data) == 0:
            self.logger.warning("Lista de hosts vacía")
            return False

        return True

    def execute(self, input_data: List[str] | str | None = None) -> List[str]:
        """
        Ejecuta la fase de escaneo usando nmap.

        Args:
            input_data: Lista de hosts vivos a escanear

        Returns:
            List[str]: Resultados del escaneo (formato nmap)
        """
        self.logger.info("Iniciando fase de escaneo de puertos y servicios")

        # Cargar y validar entrada
        hosts = self.load_input(input_data)

        if not self.validate_input(hosts):
            self.logger.error("Validación de entrada fallida")
            self.save_results([], "scan_results.txt")
            return []

        if len(hosts) == 0:
            self.logger.warning("No hay hosts para escanear")
            self.save_results([], "scan_results.txt")
            return []

        self.logger.info(f"Escanearé {len(hosts)} hosts...")

        # Guardar hosts en archivo temporal para nmap
        temp_input = self.output_dir / "temp_hosts.txt"
        temp_input.write_text("\n".join(hosts) + "\n")

        # Comando para nmap
        # nmap -sV -sC -T4 -v -iL hosts.txt
        args = [
            "-sV",  # Detección de versiones
            "-sC",  # Scripts por defecto
            "-T4",  # Timing agresivo
            "-v",   # Verboso
            "-iL", str(temp_input)  # Input file con hosts
        ]

        self.logger.info(f"Ejecutando: {self.tool_path} {' '.join(args)}")

        # Ejecutar comando (sin timeout para permitir escaneos completos)
        success, stdout, stderr = run_command(self.tool_path, args, timeout=None)

        # Limpiar archivo temporal
        if temp_input.exists():
            temp_input.unlink()

        if not success:
            self.logger.warning(f"nmap falló: {stderr}")
            self.save_results([], "scan_results.txt")
            return []

        # Guardar resultados completos de nmap
        results = stdout.strip().split("\n") if stdout.strip() else []
        self.save_results(results, "scan_results.txt")

        # Analizar resumen
        hosts_found = len([h for h in results if "Nmap scan report for" in h])
        self.logger.info(f"Escaneo completado. {hosts_found} hosts analizados.")

        return results
