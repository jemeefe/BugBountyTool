"""
Fase de Filtrado (Filtering) para BugBountyTool.
Encargada de verificar qué subdominios están vivos usando httpx.
"""

import logging
from pathlib import Path
from typing import List, Optional

from core.phase import BasePhase
from utils.helpers import run_command, deduplicate_list, clean_subdomain
from utils.dependencies import resolve_tool_path


class FilteringPhase(BasePhase):
    """
    Fase de filtrado de hosts vivos.
    Usa httpx (o similar) para verificar qué subdominios responden.
    """

    def __init__(
        self,
        output_dir: str | Path,
        logger: Optional[logging.Logger] = None,
        tool_path: str = "httpx",
    ):
        """
        Inicializa la fase de filtrado.

        Args:
            output_dir: Directorio donde guardar los resultados
            logger: Logger opcional
            tool_path: Ruta al binario de httpx (por defecto 'httpx' en PATH)
        """
        super().__init__("Filtering", output_dir, logger)
        self.tool_path = tool_path
        self.output_file = self.output_dir / "live_hosts.txt"

    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """
        Valida que se proporcionen subdominios para filtrar.
        """
        if not input_data:
            self.logger.error("No se proporcionaron subdominios para filtrar")
            return False

        if isinstance(input_data, list) and len(input_data) == 0:
            self.logger.warning("Lista de subdominios vacía")
            return False

        return True

    def execute(self, input_data: List[str] | str | None = None) -> List[str]:
        """
        Ejecuta la fase de filtrado usando httpx para verificar hosts vivos.

        Args:
            input_data: Lista de subdominios a verificar

        Returns:
            List[str]: Lista de hosts vivos (con protocolo)
        """
        self.logger.info("Iniciando fase de filtrado para verificar hosts vivos")

        # Cargar y validar entrada
        subdomains = self.load_input(input_data)

        if not self.validate_input(subdomains):
            self.logger.error("Validación de entrada fallida")
            self.save_results([], "live_hosts.txt")
            return []

        if len(subdomains) == 0:
            self.logger.warning("No hay subdominios para filtrar")
            self.save_results([], "live_hosts.txt")
            return []

        self.logger.info(f"Procesando {len(subdomains)} subdominios...")

        # Guardar subdominios en archivo temporal para httpx
        temp_input = self.output_dir / "temp_input.txt"
        temp_input.write_text("\n".join(subdomains) + "\n")

        # Comando para httpx
        # httpx -list subdomains.txt -timeout 10 -retries 2 -threads 100 -silent
        args = [
            "-list", str(temp_input),
            "-timeout", "10",
            "-retries", "2",
            "-threads", "100",
            "-silent"
        ]

        # Resolver binario real (prioriza ~/go/bin/httpx sobre paquetes del sistema)
        resolved_path = resolve_tool_path("httpx")
        if resolved_path:
            self.tool_path = resolved_path
            self.logger.info(f"Binario httpx resuelto: {self.tool_path}")
        else:
            # Fallback al valor recibido (puede ser la ruta del config)
            self.logger.info(f"Usando ruta configurada para httpx: {self.tool_path}")

        self.logger.info(f"Ejecutando: {self.tool_path} {' '.join(args)}")

        # Ejecutar comando
        success, stdout, stderr = run_command(self.tool_path, args)

        # Limpiar archivo temporal
        if temp_input.exists():
            temp_input.unlink()

        # Detectar fallos críticos: binario incorrecto (Usage: ... / No such option)
        stderr_combined = (stderr or "") + (stdout or "")
        if not success:
            if "Usage:" in stderr_combined or "No such option" in stderr_combined or "Invalid usage" in stderr_combined:
                self.logger.error(
                    f"FALLO CRÍTICO DEL BINARIO: se detectó el binario incorrecto de 'httpx'.\n"
                    f"Comando intentado: '{self.tool_path}'\n"
                    f"Error recibido: {stderr_combined.strip()}\n"
                    f"SOLUCIÓN: Asegúrate de que el binario Go de ProjectDiscovery esté disponible.\n"
                    f"  - Si usas 'go install', verifica que ~/go/bin/httpx exista.\n"
                    f"  - Ruta resuelta por el sistema: {self.tool_path}\n"
                    f"  - Si el sistema tiene 'python3-httpx' instalado (p.ej. en Kali),\n"
                    f"    eso sobrescribe el binario Go. Remueve el paquete del sistema\n"
                    f"    o usa la ruta absoluta al binario Go en config/config.yaml."
                )
            else:
                self.logger.warning(f"httpx falló: {stderr_combined}")
            self.save_results([], "live_hosts.txt")
            return []

        # Procesar salida
        raw_hosts = stdout.strip().split("\n") if stdout.strip() else []

        # Limpiar y deduplicar
        cleaned = [clean_subdomain(host) for host in raw_hosts]
        unique = deduplicate_list(cleaned)

        # Guardar resultados (con protocolo si lo tiene httpx)
        self.save_results(unique, "live_hosts.txt")

        self.logger.info(f"Hosts vivos encontrados: {len(unique)}")
        return unique
