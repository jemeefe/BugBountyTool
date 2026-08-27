#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestador principal para BugBountyTool.
Coordina la ejecución de todas las fases del pipeline.

Ejemplo de uso:
    python src/main.py example.com
    bugbountytool example.com

Instalación:
    pip install .
    sudo bash install.sh (para Kali Linux)
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# Determinar si se ejecuta como script instalado o desde el repositorio
if __name__ == "__main__":
    # Si se ejecuta como script directamente (pip install), usar imports absolutos
    try:
        from utils.logger import setup_logger
        from utils.config import load_config, Config
        from utils.dependencies import check_dependencies, check_go_installation
        from core.checkpoint import CheckpointManager, load_checkpoint
        from utils.reporter import ReportGenerator
        from phases.discovery import DiscoveryPhase
        from phases.filtering import FilteringPhase
        from phases.scanning import ScanningPhase
        from phases.vulnerability import VulnerabilityPhase
        from phases.crawling import CrawlingPhase
        from phases.parameter import ParameterPhase
    except ImportError:
        # Si falla, asumir que se ejecuta desde src/ y usar imports relativos
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir.parent))

        from utils.logger import setup_logger
        from utils.config import load_config, Config
        from utils.dependencies import check_dependencies, check_go_installation
        from core.checkpoint import CheckpointManager, load_checkpoint
        from utils.reporter import ReportGenerator
        from phases.discovery import DiscoveryPhase
        from phases.filtering import FilteringPhase
        from phases.scanning import ScanningPhase
        from phases.vulnerability import VulnerabilityPhase
        from phases.crawling import CrawlingPhase
        from phases.parameter import ParameterPhase

from utils.logger import setup_logger
from utils.config import load_config, Config
from core.checkpoint import CheckpointManager, load_checkpoint
from utils.reporter import ReportGenerator

from phases.discovery import DiscoveryPhase
from phases.filtering import FilteringPhase
from phases.scanning import ScanningPhase
from phases.vulnerability import VulnerabilityPhase
from phases.crawling import CrawlingPhase
from phases.parameter import ParameterPhase


class BugBountyPipeline:
    """
    Orquestador principal que coordina las fases del pipeline de bug bounty.
    """

    def __init__(
        self,
        domain: str,
        base_dir: str | Path,
        config: Optional[Config] = None,
        logger: Optional[logging.Logger] = None,
        use_checkpoint: bool = True,
    ):
        """
        Inicializa el pipeline.

        Args:
            domain: Dominio principal a analizar
            base_dir: Directorio base del proyecto
            config: Objeto de configuración opcional
            logger: Logger opcional
            use_checkpoint: Si True, intenta reanudar de checkpoint si existe
        """
        self.domain = domain
        self.base_dir = Path(base_dir)
        self.config = config or load_config(self.base_dir / "config" / "config.yaml")
        self.logger = logger or setup_logger("BugBountyPipeline")
        self.use_checkpoint = use_checkpoint

        # Configurar directorios
        self.outputs_dir = self.base_dir / self.config.output_dir
        self.temp_dir = self.base_dir / "temp"

        # Crear directorios
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar checkpoint
        self.checkpoint: Optional[CheckpointManager] = None
        if self.use_checkpoint:
            self.checkpoint = load_checkpoint(self.outputs_dir, self.domain)
            if self.checkpoint:
                self.logger.info(f"Checkpoint encontrado: {self.checkpoint.checkpoint_id}")

        # Almacenar resultados de cada fase
        self.results: Dict[str, List[Any]] = {}

        # Mantener referencia a las fases ejecutadas
        self.phase_instances: Dict[str, Any] = {}

    def run_phase_discovery(self) -> List[str]:
        """Ejecuta la fase de descubrimiento de subdominios."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 1: DESCUBRIMIENTO DE SUBDOMINIOS")
        self.logger.info("=" * 60)

        # Verificar si ya está completada
        if self.checkpoint and self.checkpoint.is_phase_completed("discovery"):
            self.logger.info("Fase de descubrimiento ya completada. Cargando resultados...")
            subdomains = self.checkpoint.get_results_for_phase("discovery")
            self.results["discovery"] = subdomains
            return subdomains

        phase = DiscoveryPhase(
            output_dir=self.outputs_dir,
            domain=self.domain,
            logger=self.logger,
            tool_path=self.config.get_tool_path("subfinder"),
        )
        self.phase_instances["discovery"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("discovery", "running")

        subdomains = phase.execute()
        self.results["discovery"] = subdomains

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "discovery", "completed",
                len(subdomains),
                phase.output_file
            )

        return subdomains

    def run_phase_filtering(self, input_data: List[str]) -> List[str]:
        """Ejecuta la fase de filtrado para verificar hosts vivos."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 2: FILTRADO - VERIFICACIÓN DE HOSTS VIVOS")
        self.logger.info("=" * 60)

        if self.checkpoint and self.checkpoint.is_phase_completed("filtering"):
            self.logger.info("Fase de filtrado ya completada. Cargando resultados...")
            live_hosts = self.checkpoint.get_results_for_phase("filtering")
            self.results["filtering"] = live_hosts
            return live_hosts

        phase = FilteringPhase(
            output_dir=self.outputs_dir,
            logger=self.logger,
            tool_path=self.config.get_tool_path("httpx"),
        )
        self.phase_instances["filtering"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("filtering", "running")

        live_hosts = phase.execute(input_data)
        self.results["filtering"] = live_hosts

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "filtering", "completed",
                len(live_hosts),
                phase.output_file
            )

        return live_hosts

    def run_phase_scanning(self, input_data: List[str]) -> List[str]:
        """Ejecuta la fase de escaneo de puertos y servicios."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 3: ESCANEO DE PUERTOS Y SERVICIOS")
        self.logger.info("=" * 60)

        if self.checkpoint and self.checkpoint.is_phase_completed("scanning"):
            self.logger.info("Fase de escaneo ya completada. Cargando resultados...")
            scan_results = self.checkpoint.get_results_for_phase("scanning")
            self.results["scanning"] = scan_results
            return scan_results

        phase = ScanningPhase(
            output_dir=self.outputs_dir,
            logger=self.logger,
            tool_path=self.config.get_tool_path("nmap"),
        )
        self.phase_instances["scanning"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("scanning", "running")

        scan_results = phase.execute(input_data)
        self.results["scanning"] = scan_results

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "scanning", "completed",
                len(scan_results),
                phase.output_file
            )

        return scan_results

    def run_phase_vulnerability(self, input_data: List[str]) -> List[dict]:
        """Ejecuta la fase de escaneo de vulnerabilidades con nuclei."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 4: ESCANEO DE VULNERABILIDADES (Nuclei)")
        self.logger.info("=" * 60)

        if self.checkpoint and self.checkpoint.is_phase_completed("vulnerability"):
            self.logger.info("Fase de vulnerabilidad ya completada. Cargando resultados...")
            return self.results.get("vulnerability", [])

        phase = VulnerabilityPhase(
            output_dir=self.outputs_dir,
            logger=self.logger,
            tool_path=self.config.get_tool_path("nuclei"),
            rate_limit_config=self.config.get_rate_limit_config("nuclei"),
            templates=self.config.get_nuclei_templates(),
        )
        self.phase_instances["vulnerability"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("vulnerability", "running")

        findings = phase.execute(input_data)
        self.results["vulnerability"] = findings

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "vulnerability", "completed",
                len(findings),
                phase.output_file
            )

        return findings

    def run_phase_crawling(self, input_data: List[str]) -> List[str]:
        """Ejecuta la fase de crawling y discovery de endpoints."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 5: CRAWLING Y DISCOVERY DE ENDPOINTS")
        self.logger.info("=" * 60)

        if self.checkpoint and self.checkpoint.is_phase_completed("crawling"):
            self.logger.info("Fase de crawling ya completada. Cargando resultados...")
            return self.results.get("endpoints", [])

        phase = CrawlingPhase(
            output_dir=self.outputs_dir,
            logger=self.logger,
            tools_config={
                "waybackurls": {
                    "enabled": self.config.is_tool_enabled("waybackurls"),
                    "path": self.config.get_tool_path("waybackurls")
                },
                "gau": {
                    "enabled": self.config.is_tool_enabled("gau"),
                    "path": self.config.get_tool_path("gau")
                },
                "ffuf": {
                    "enabled": self.config.is_tool_enabled("ffuf"),
                    "path": self.config.get_tool_path("ffuf")
                }
            }
        )
        self.phase_instances["crawling"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("crawling", "running")

        endpoints = phase.execute(input_data)
        self.results["endpoints"] = endpoints

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "crawling", "completed",
                len(endpoints),
                phase.output_file
            )

        return endpoints

    def run_phase_parameter(self, input_data: List[str]) -> List[dict]:
        """Ejecuta la fase de parameter discovery y testing."""
        self.logger.info("=" * 60)
        self.logger.info("FASE 6: PARAMETER DISCOVERY Y TESTING")
        self.logger.info("=" * 60)

        if self.checkpoint and self.checkpoint.is_phase_completed("parameter"):
            self.logger.info("Fase de parameter discovery ya completada.")
            return self.results.get("parameters", [])

        phase = ParameterPhase(
            output_dir=self.outputs_dir,
            logger=self.logger,
            tools_config={
                "subjs": {
                    "enabled": self.config.is_tool_enabled("subjs"),
                    "path": self.config.get_tool_path("subjs")
                },
                "dalfox": {
                    "enabled": self.config.is_tool_enabled("dalfox"),
                    "path": self.config.get_tool_path("dalfox")
                },
                "qsreplace": {
                    "enabled": self.config.is_tool_enabled("qsreplace"),
                    "path": self.config.get_tool_path("qsreplace")
                }
            }
        )
        self.phase_instances["parameter"] = phase

        if self.checkpoint:
            self.checkpoint.update_phase_status("parameter", "running")

        params = phase.execute(input_data)
        self.results["parameters"] = params

        if self.checkpoint:
            self.checkpoint.update_phase_status(
                "parameter", "completed",
                len(params),
                phase.output_file
            )

        return params

    def generate_report(
        self,
        subdomains: List[str],
        live_hosts: List[str],
        scan_results: List[str],
        vulnerabilities: List[dict],
        endpoints: List[str],
        parameters: List[dict]
    ) -> str:
        """Genera el reporte final."""
        self.logger.info("Generando reporte...")

        reporter = ReportGenerator(
            output_dir=self.outputs_dir,
            domain=self.domain,
            logger=self.logger
        )

        report_path = reporter.generate_html_report(
            subdomains=subdomains,
            live_hosts=live_hosts,
            scan_results=scan_results,
            vulnerabilities=vulnerabilities,
            endpoints=endpoints,
            parameters=parameters
        )

        return report_path

    def run(self, full_pipeline: bool = True) -> bool:
        """
        Ejecuta todo el pipeline completo.

        Args:
            full_pipeline: Si True, ejecuta todas las fases hasta la 6

        Returns:
            bool: True si tuvo éxito, False en caso contrario
        """
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"Iniciando BugBountyPipeline para: {self.domain}")
        self.logger.info(f"Directorio base: {self.base_dir}")
        self.logger.info(f"{'=' * 60}\n")

        failed_phases = []

        try:
            # Fase 1: Descubrimiento
            subdomains = self.run_phase_discovery()
            if not subdomains:
                self.logger.warning("No se descubrieron subdominios.")
                failed_phases.append("Discovery")
                subdomains = []

            # Fase 2: Filtrado
            live_hosts = []
            if subdomains:
                live_hosts = self.run_phase_filtering(subdomains)
                if not live_hosts:
                    self.logger.warning("No se encontraron hosts vivos.")
                    failed_phases.append("Filtering")
            else:
                self.logger.warning("Saltando fase de filtrado (sin subdominios).")
                failed_phases.append("Filtering (skipped)")

            # Fase 3: Escaneo
            scan_results = []
            if live_hosts:
                scan_results = self.run_phase_scanning(live_hosts)
                if not scan_results:
                    self.logger.warning("El escaneo no produjo resultados.")
                    failed_phases.append("Scanning")
            else:
                self.logger.warning("Saltando fase de escaneo (sin hosts vivos).")
                failed_phases.append("Scanning (skipped)")

            # Fases adicionales si full_pipeline es True
            vulnerabilities = []
            endpoints = []
            parameters = []

            if full_pipeline and self.config.is_tool_enabled("nuclei"):
                if live_hosts:
                    vulnerabilities = self.run_phase_vulnerability(live_hosts)
                    if not vulnerabilities:
                        failed_phases.append("Vulnerability")
                else:
                    self.logger.warning("Saltando fase de vulnerabilidad (sin hosts vivos).")
                    failed_phases.append("Vulnerability (skipped)")

            if full_pipeline and self.config.is_tool_enabled("waybackurls"):
                if live_hosts:
                    endpoints = self.run_phase_crawling(live_hosts)
                    if not endpoints:
                        failed_phases.append("Crawling")
                else:
                    self.logger.warning("Saltando fase de crawling (sin hosts vivos).")
                    failed_phases.append("Crawling (skipped)")

            if full_pipeline and self.config.is_tool_enabled("subjs"):
                if live_hosts:
                    parameters = self.run_phase_parameter(live_hosts)
                    if not parameters:
                        failed_phases.append("Parameter")
                else:
                    self.logger.warning("Saltando fase de parameter discovery (sin hosts vivos).")
                    failed_phases.append("Parameter (skipped)")

            # Generar reporte
            report_path = self.generate_report(
                subdomains=subdomains,
                live_hosts=live_hosts,
                scan_results=scan_results,
                vulnerabilities=vulnerabilities,
                endpoints=endpoints,
                parameters=parameters
            )

            # Limpiar checkpoint si todo fue exitoso
            if self.checkpoint:
                self.checkpoint.cleanup()

            # Resumen final
            self._print_summary()

            # Mostrar fases fallidas si las hay
            if failed_phases:
                self.logger.warning(f"\n{'=' * 60}")
                self.logger.warning(f"Fases con problemas o sin resultados: {', '.join(failed_phases)}")
                self.logger.warning(f"{'=' * 60}\n")

            self.logger.info(f"\n{'=' * 60}")
            self.logger.info("Pipeline completado")
            self.logger.info(f"{'=' * 60}\n")

            return len(failed_phases) == 0

        except Exception as e:
            self.logger.error(f"Error en el pipeline: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def _print_summary(self):
        """Imprime un resumen de los resultados."""
        self.logger.info("\n" + "-" * 40)
        self.logger.info("RESUMEN DE RESULTADOS")
        self.logger.info("-" * 40)
        self.logger.info(f"Subdominios descubiertos: {len(self.results.get('discovery', []))}")
        self.logger.info(f"Hosts vivos: {len(self.results.get('filtering', []))}")
        self.logger.info(f"Resultados de escaneo: {len(self.results.get('scanning', []))} líneas")

        if self.results.get("vulnerability"):
            vulns = self.results["vulnerability"]
            self.logger.info(f"Vulnerabilidades encontradas: {len(vulns)}")

            severity_counts = {}
            for v in vulns:
                sev = v.get("info", {}).get("severity", "unknown").lower()
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            for sev, count in severity_counts.items():
                self.logger.info(f"  {sev.upper()}: {count}")

        if self.results.get("endpoints"):
            self.logger.info(f"Endpoints descubiertos: {len(self.results['endpoints'])}")

        if self.results.get("parameters"):
            self.logger.info(f"Parámetros encontrados: {len(self.results['parameters'])}")

        self.logger.info("-" * 40)
        self.logger.info(f"Reporte guardado en: {self.base_dir / self.config.output_dir / 'reports'}")


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="BugBountyTool - Pipeline semi-automatizado para Bug Bounty"
    )
    parser.add_argument(
        "domain",
        help="Dominio principal a analizar (ej: example.com)"
    )
    parser.add_argument(
        "-d",
        "--dir",
        default=Path.cwd(),
        help="Directorio base del proyecto (por defecto: directorio actual)"
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Ruta al archivo de configuración YAML"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Habilita logging en modo DEBUG"
    )
    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Desactiva el uso de checkpoints para reanudar"
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Ejecuta solo las fases básicas (1-3)"
    )
    parser.add_argument(
        "--skip-deps-check",
        action="store_true",
        help="Omite la verificación de dependencias"
    )

    args = parser.parse_args()

    # Verificar dependencias antes de comenzar
    if not args.skip_deps_check:
        check_dependencies(strict=False)

    # Cargar configuración
    config_path = Path(args.config) if args.config else Path(args.dir) / "config" / "config.yaml"
    config = load_config(config_path)

    # Configurar logger con nivel adecuado
    log_config = config.logging_config if config else {}
    log_level = "DEBUG" if args.verbose else log_config.get("level", "INFO")

    logger = setup_logger(
        "BugBountyPipeline",
        log_level=log_level,
        log_file=log_config.get("file", "logs/bug_bounty_tool.log"),
        console=log_config.get("console", True)
    )

    # Crear y ejecutar pipeline
    pipeline = BugBountyPipeline(
        domain=args.domain,
        base_dir=args.dir,
        config=config,
        logger=logger,
        use_checkpoint=not args.no_checkpoint
    )

    success = pipeline.run(full_pipeline=not args.minimal)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Añadir el directorio src al path para import relative
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir.parent))

    from utils.logger import setup_logger
    from utils.config import load_config, Config
    from core.checkpoint import CheckpointManager, load_checkpoint
    from utils.reporter import ReportGenerator
    from phases.discovery import DiscoveryPhase
    from phases.filtering import FilteringPhase
    from phases.scanning import ScanningPhase
    from phases.vulnerability import VulnerabilityPhase
    from phases.crawling import CrawlingPhase
    from phases.parameter import ParameterPhase

    main()
