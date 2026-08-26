"""
Fase de Crawling y Discovery para BugBountyTool.
Encargada de crawlear páginas web y descubrir endpoints.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

from core.phase import BasePhase
from utils.helpers import run_command, deduplicate_list, clean_subdomain


class CrawlingPhase(BasePhase):
    """
    Fase de crawling y discovery de endpoints.
    Usa herramientas como waybackurls, gau y ffuf.
    """

    def __init__(
        self,
        output_dir: str | Path,
        logger: Optional[logging.Logger] = None,
        tools_config: dict | None = None,
    ):
        """
        Inicializa la fase de crawling.

        Args:
            output_dir: Directorio donde guardar los resultados
            logger: Logger opcional
            tools_config: Configuración de herramientas
        """
        super().__init__("Crawling", output_dir, logger)
        self.tools_config = tools_config or {
            "waybackurls": {"enabled": True, "path": "waybackurls"},
            "gau": {"enabled": True, "path": "gau"},
            "ffuf": {"enabled": True, "path": "ffuf"},
            "github": {"enabled": True, "path": "github-endpoints"}
        }

        self.output_file = self.output_dir / "endpoints.txt"
        self.endpoints: List[str] = []

    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """Valida que se proporcionen hosts para crawlear."""
        if not input_data:
            self.logger.error("No se proporcionaron hosts para crawlear")
            return False

        if isinstance(input_data, list) and len(input_data) == 0:
            self.logger.warning("Lista de hosts vacía")
            return False

        return True

    def _run_waybackurls(self, hosts: List[str]) -> List[str]:
        """Ejecuta waybackurls para obtener endpoints históricos."""
        if not self.tools_config.get("waybackurls", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando waybackurls...")

        results = []
        for host in hosts:
            args = [host]
            success, stdout, _ = run_command(
                self.tools_config["waybackurls"]["path"],
                args,
                timeout=120
            )

            if success and stdout.strip():
                lines = stdout.strip().split("\n")
                results.extend([f"{host}{line}" if not line.startswith("http") else line
                               for line in lines])

        return results

    def _run_gau(self, hosts: List[str]) -> List[str]:
        """Ejecuta gau para obtener endpoints."""
        if not self.tools_config.get("gau", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando gau...")

        results = []
        for host in hosts:
            args = [host, "--threads", "10"]
            success, stdout, _ = run_command(
                self.tools_config["gau"]["path"],
                args,
                timeout=120
            )

            if success and stdout.strip():
                lines = stdout.strip().split("\n")
                results.extend([f"{host}{line}" if not line.startswith("http") else line
                               for line in lines])

        return results

    def _run_ffuf(self, hosts: List[str]) -> List[str]:
        """Ejecuta ffuf para fuzzing de directorios."""
        if not self.tools_config.get("ffuf", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando ffuf...")

        # Wordlist común
        wordlist = "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"
        if not Path(wordlist).exists():
            wordlist = "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt"

        results = []
        for host in hosts:
            args = [
                "-u", f"{host.rstrip('/')}/FUZZ",
                "-w", wordlist,
                "-t", "20",
                "-f",
                "-o", "/dev/null"
            ]
            success, stdout, _ = run_command(
                self.tools_config["ffuf"]["path"],
                args,
                timeout=180
            )

            if success and stdout.strip():
                lines = stdout.strip().split("\n")
                results.extend([line for line in lines if "FUZZ" not in line])

        return results

    def execute(self, input_data: List[str] | str | None = None) -> List[str]:
        """
        Ejecuta la fase de crawling.

        Args:
            input_data: Lista de hosts a crawlear

        Returns:
            List[str]: Lista de endpoints descubiertos
        """
        self.logger.info("Iniciando fase de crawling y discovery")

        hosts = self.load_input(input_data)

        if not self.validate_input(hosts):
            self.logger.error("Validación de entrada fallida")
            self._save_endpoints([])
            return []

        if len(hosts) == 0:
            self.logger.warning("No hay hosts para crawlear")
            self._save_endpoints([])
            return []

        self.logger.info(f"Crawlearé {len(hosts)} hosts")

        try:
            # Ejecutar cada herramienta
            all_endpoints = []

            if self.tools_config.get("waybackurls", {}).get("enabled", True):
                wayback = self._run_waybackurls(hosts)
                all_endpoints.extend(wayback)
                self.logger.info(f"waybackurls encontró {len(wayback)} endpoints")

            if self.tools_config.get("gau", {}).get("enabled", True):
                gau = self._run_gau(hosts)
                all_endpoints.extend(gau)
                self.logger.info(f"gau encontró {len(gau)} endpoints")

            if self.tools_config.get("ffuf", {}).get("enabled", True):
                ffuf = self._run_ffuf(hosts)
                all_endpoints.extend(ffuf)
                self.logger.info(f"ffuf encontró {len(ffuf)} endpoints")

            # Procesar resultados
            cleaned = [clean_subdomain(ep) for ep in all_endpoints]
            unique = deduplicate_list([ep for ep in cleaned if ep])

            self.endpoints = unique
            self._save_endpoints(unique)

            self.logger.info(f"Total de endpoints únicos: {len(unique)}")
            return unique

        except Exception as e:
            self.logger.error(f"Error durante el crawling: {e}")
            self._save_endpoints([])
            return []

    def _save_endpoints(self, endpoints: List[str]):
        """Guarda los endpoints en archivo."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(endpoints))
                if endpoints:
                    f.write("\n")
            self.logger.info(f"Endpoints guardados en: {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error guardando endpoints: {e}")

    def get_endpoints_by_pattern(self, pattern: str) -> List[str]:
        """Filtra endpoints por patrón."""
        return [ep for ep in self.endpoints if pattern.lower() in ep.lower()]
