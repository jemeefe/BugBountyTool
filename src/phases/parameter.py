"""
Fase de Parameter Discovery para BugBountyTool.
Encargada de descubrir y testear parámetros con dalfox.
"""

import logging
import time
import json
from pathlib import Path
from typing import List, Optional, Dict

from core.phase import BasePhase
from utils.helpers import run_command, deduplicate_list


class ParameterPhase(BasePhase):
    """
    Fase de discovery y testing de parámetros.
    Usa dalfox para discovery y testing de XSS/SSRF.
    """

    def __init__(
        self,
        output_dir: str | Path,
        logger: Optional[logging.Logger] = None,
        tools_config: dict | None = None,
    ):
        """
        Inicializa la fase de parameter discovery.

        Args:
            output_dir: Directorio donde guardar los resultados
            logger: Logger opcional
            tools_config: Configuración de herramientas
        """
        super().__init__("Parameter", output_dir, logger)
        self.tools_config = tools_config or {
            "subjs": {"enabled": True, "path": "subjs"},
            "dalfox": {"enabled": True, "path": "dalfox"},
            "qsreplace": {"enabled": True, "path": "qsreplace"}
        }

        self.output_file = self.output_dir / "parameters.json"
        self.parameters: List[Dict] = []

    def validate_input(self, input_data: List[str] | str | None) -> bool:
        """Valida que se proporcionen URLs para analizar."""
        if not input_data:
            self.logger.error("No se proporcionaron URLs para analizar")
            return False

        if isinstance(input_data, list) and len(input_data) == 0:
            self.logger.warning("Lista de URLs vacía")
            return False

        return True

    def _run_subjs(self, urls: List[str]) -> List[str]:
        """Ejecuta subjs para extraer parámetros de JavaScript."""
        if not self.tools_config.get("subjs", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando subjs...")

        results = []
        temp_file = self.output_dir / "temp_urls_subjs.txt"
        temp_file.write_text("\n".join(urls) + "\n")

        args = ["-l", str(temp_file)]
        success, stdout, _ = run_command(
            self.tools_config["subjs"]["path"],
            args,
            timeout=120
        )

        if success and stdout.strip():
            results = stdout.strip().split("\n")

        if temp_file.exists():
            temp_file.unlink()

        return results

    def _run_qsreplace(self, urls: List[str]) -> List[Dict]:
        """Ejecuta qsreplace para extraer parámetros de URLs."""
        if not self.tools_config.get("qsreplace", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando qsreplace...")

        results = []
        temp_file = self.output_dir / "temp_urls_qs.txt"
        temp_file.write_text("\n".join(urls) + "\n")

        args = ["-l", str(temp_file)]
        success, stdout, _ = run_command(
            self.tools_config["qsreplace"]["path"],
            args,
            timeout=120
        )

        if success and stdout.strip():
            lines = stdout.strip().split("\n")
            for line in lines:
                if "=" in line:
                    param = line.split("=")[0].split("?")[-1].split("&")[-1]
                    results.append({
                        "url": line,
                        "parameter": param,
                        "source": "qsreplace"
                    })

        if temp_file.exists():
            temp_file.unlink()

        return results

    def _run_dalfox(self, urls: List[str]) -> List[Dict]:
        """Ejecuta dalfox para testing de XSS."""
        if not self.tools_config.get("dalfox", {}).get("enabled", True):
            return []

        self.logger.info("Ejecutando dalfox (XSS scanning)...")

        results = []
        for url in urls[:20]:  # Limitar a 20 URLs por ejecución
            args = ["scan", "url", url, "--min-time", "30"]
            success, stdout, _ = run_command(
                self.tools_config["dalfox"]["path"],
                args,
                timeout=180
            )

            if success and stdout.strip():
                results.append({
                    "url": url,
                    "scan_results": stdout.strip(),
                    "source": "dalfox"
                })

        return results

    def execute(self, input_data: List[str] | str | None = None) -> List[Dict]:
        """
        Ejecuta la fase de parameter discovery.

        Args:
            input_data: Lista de URLs a analizar

        Returns:
            List[Dict]: Lista de parámetros y findings
        """
        self.logger.info("Iniciando fase de parameter discovery")

        urls = self.load_input(input_data)

        if not self.validate_input(urls):
            self.logger.error("Validación de entrada fallida")
            self._save_parameters([])
            return []

        if len(urls) == 0:
            self.logger.warning("No hay URLs para analizar")
            self._save_parameters([])
            return []

        self.logger.info(f"Analizaré {len(urls)} URLs")

        try:
            all_params = []

            # SubJS para parámetros de JS
            subjs_params = self._run_subjs(urls)
            for param in subjs_params:
                all_params.append({
                    "parameter": param,
                    "source": "subjs",
                    "type": "javascript"
                })
            self.logger.info(f"subjs encontró {len(subjs_params)} parámetros")

            # QSReplace para parámetros de URL
            qs_params = self._run_qsreplace(urls)
            all_params.extend(qs_params)
            self.logger.info(f"qsreplace encontró {len(qs_params)} parámetros")

            # Dalfox para XSS testing
            dalfox_results = self._run_dalfox(urls)
            all_params.extend(dalfox_results)

            # Guardar resultados únicos
            unique_params = self._deduplicate_parameters(all_params)
            self.parameters = unique_params
            self._save_parameters(unique_params)

            self.logger.info(f"Total de parámetros únicos: {len(unique_params)}")
            return unique_params

        except Exception as e:
            self.logger.error(f"Error durante el parameter discovery: {e}")
            self._save_parameters([])
            return []

    def _deduplicate_parameters(self, params: List[Dict]) -> List[Dict]:
        """Elimina parámetros duplicados."""
        seen = set()
        unique = []

        for param in params:
            if "parameter" in param:
                key = (param.get("parameter"), param.get("source"))
                if key not in seen:
                    seen.add(key)
                    unique.append(param)
            else:
                unique.append(param)

        return unique

    def _save_parameters(self, parameters: List[Dict]):
        """Guarda los parámetros en JSON."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(parameters, f, indent=2)
            self.logger.info(f"Parámetros guardados en: {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error guardando parámetros: {e}")

    def get_xss_vulnerabilities(self) -> List[Dict]:
        """Obtiene solo los findings de XSS."""
        return [
            p for p in self.parameters
            if p.get("source") == "dalfox"
        ]
