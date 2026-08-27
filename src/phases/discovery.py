"""
Fase de Descubrimiento (Discovery) para BugBountyTool.
Encargada de encontrar subdominios usando herramientas como subfinder.
"""

import logging
from pathlib import Path
from typing import List, Optional

from core.phase import BasePhase
from utils.helpers import run_command, deduplicate_list, clean_subdomain
from utils.dependencies import resolve_tool_path


class DiscoveryPhase(BasePhase):
    """
    Fase de descubrimiento de subdominios.
    Usa subfinder (o similar) para encontrar subdominios de un dominio objetivo.
    """

    def __init__(
        self,
        output_dir: str | Path,
        domain: str,
        logger: Optional[logging.Logger] = None,
        tool_path: str = "subfinder",
    ):
        """
        Inicializa la fase de descubrimiento.

        Args:
            output_dir: Directorio donde guardar los resultados
            domain: Dominio principal a analizar
            logger: Logger opcional
            tool_path: Ruta al binario de subfinder (por defecto 'subfinder' en PATH)
        """
        super().__init__("Discovery", output_dir, logger)
        self.domain = domain
        self.tool_path = tool_path
        self.output_file = self.output_dir / "discovered_subdomains.txt"

    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """
        Valida que el dominio de entrada tenga sentido.
        """
        if not self.domain or not isinstance(self.domain, str):
            self.logger.error("Dominio no válido proporcionado")
            return False

        # Validación básica de formato de dominio
        if "." not in self.domain:
            self.logger.error("El dominio debe contener al menos un punto")
            return False

        return True

    def execute(self, input_data: List[str] | str | None = None) -> List[str]:
        """
        Ejecuta la fase de descubrimiento usando subfinder.

        Args:
            input_data: No se usa en esta fase, pero mantenido por compatibilidad

        Returns:
            List[str]: Lista de subdominios descubiertos
        """
        self.logger.info(f"Iniciando fase de descubrimiento para: {self.domain}")

        # Validar entrada
        if not self.validate_input(input_data):
            self.logger.error("Validación de entrada fallida")
            return []

        # Comando para subfinder
        # subfinder -d example.com -all -timeout 5 -recursive
        args = [
            "-d", self.domain,
            "-all",
            "-timeout", "5",
            "-recursive"
        ]

        # Resolver binario real (prioriza ~/go/bin/subfinder)
        resolved_path = resolve_tool_path("subfinder")
        if resolved_path:
            self.tool_path = resolved_path
            self.logger.info(f"Binario subfinder resuelto: {self.tool_path}")

        self.logger.info(f"Ejecutando: {self.tool_path} {' '.join(args)}")

        # Ejecutar comando
        success, stdout, stderr = run_command(self.tool_path, args)

        if not success:
            stderr_combined = (stderr or "") + (stdout or "")
            if "Usage:" in stderr_combined or "No such option" in stderr_combined:
                self.logger.error(
                    f"FALLO CRÍTICO DEL BINARIO: se detectó el binario incorrecto de 'subfinder'.\n"
                    f"Comando intentado: '{self.tool_path}'\n"
                    f"Error: {stderr_combined.strip()}\n"
                    f"SOLUCIÓN: Verifica que ~/go/bin/subfinder sea el binario Go de ProjectDiscovery."
                )
            else:
                self.logger.warning(f"subfinder no encontrado o falló: {stderr_combined}")
            self.logger.info("Crea un archivo 'discovered_subdomains.txt' vacío")
            # Crear archivo vacío para no romper el pipeline
            self.save_results([], "discovered_subdomains.txt")
            return []

        # Procesar salida
        raw_subdomains = stdout.strip().split("\n") if stdout.strip() else []

        # Limpiar y deduplicar
        cleaned = [clean_subdomain(sub) for sub in raw_subdomains]
        unique = deduplicate_list(cleaned)

        # Guardar resultados
        self.save_results(unique, "discovered_subdomains.txt")

        self.logger.info(f"Descubiertos {len(unique)} subdominios únicos")
        return unique
