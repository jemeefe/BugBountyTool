"""
Módulo de Reportes para BugBountyTool.
Genera reportes HTML y JSON de los resultados.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class ReportGenerator:
    """
    Generador de reportes para BugBountyTool.
    Genera reportes HTML y JSON con los resultados.
    """

    def __init__(
        self,
        output_dir: str | Path,
        domain: str,
        logger=None
    ):
        """
        Inicializa el generador de reportes.

        Args:
            output_dir: Directorio donde guardar los reportes
            domain: Dominio objetivo
            logger: Logger opcional
        """
        self.output_dir = Path(output_dir)
        self.domain = domain
        self.logger = logger or __import__("logging").getLogger(__name__)

        # Crear directorio de reportes
        self.reports_dir = self.output_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        subdomains: List[str],
        live_hosts: List[str],
        scan_results: List[str],
        vulnerabilities: List[Dict],
        endpoints: List[str],
        parameters: List[Dict],
        report_name: str | None = None
    ) -> str:
        """
        Genera un reporte HTML completo.

        Args:
            subdomains: Lista de subdominios
            live_hosts: Lista de hosts vivos
            scan_results: Resultados del escaneo de puertos
            vulnerabilities: Lista de vulnerabilidades
            endpoints: Lista de endpoints
            parameters: Lista de parámetros
            report_name: Nombre del reporte (opcional)

        Returns:
            str: Ruta al archivo generado
        """
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"report_{self.domain}_{timestamp}.html"

        report_path = self.reports_dir / report_name

        # Contar por severidad
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("info", {}).get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Generar HTML
        html = self._generate_html_content(
            subdomains=subdomains,
            live_hosts=live_hosts,
            scan_results=scan_results,
            vulnerabilities=vulnerabilities,
            endpoints=endpoints,
            parameters=parameters,
            severity_counts=severity_counts
        )

        # Guardar archivo
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.logger.info(f"Reporte HTML generado: {report_path}")
        return str(report_path)

    def _generate_html_content(
        self,
        subdomains: List[str],
        live_hosts: List[str],
        scan_results: List[str],
        vulnerabilities: List[Dict],
        endpoints: List[str],
        parameters: List[Dict],
        severity_counts: Dict[str, int]
    ) -> str:
        """Genera el contenido HTML del reporte."""

        def safe_join(items, max_items=10):
            """Join items with limit."""
            if not items:
                return "None"
            return ", ".join(str(x) for x in list(items)[:max_items]) + (
                f"..." if len(items) > max_items else ""
            )

        def severity_color(severity):
            """Return color for severity."""
            colors = {
                "critical": "#dc3545",
                "high": "#fd7e14",
                "medium": "#ffc107",
                "low": "#28a745",
                "info": "#17a2b8"
            }
            return colors.get(severity.lower(), "#6c757d")

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Bug Bounty - {self.domain}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #444; margin: 30px 0 15px; font-size: 1.3em; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #666; margin-bottom: 15px; font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        .stat {{ display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 5px; color: white; font-weight: bold; }}
        .stat-critical {{ background: #dc3545; }}
        .stat-high {{ background: #fd7e14; }}
        .stat-medium {{ background: #ffc107; color: #333; }}
        .stat-low {{ background: #28a745; }}
        .stat-info {{ background: #17a2b8; }}
        .list-item {{ padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #007bff; }}
        .vuln-item {{ padding: 15px; margin: 8px 0; background: #fff; border-radius: 4px; border-left: 4px solid; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .vuln-critical {{ border-color: #dc3545; }}
        .vuln-high {{ border-color: #fd7e14; }}
        .vuln-medium {{ border-color: #ffc107; }}
        .vuln-low {{ border-color: #28a745; }}
        .vuln-info {{ border-color: #17a2b8; }}
        .vuln-title {{ font-weight: bold; margin-bottom: 5px; }}
        .vuln-severity {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-left: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-top: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte Bug Bounty</h1>
        <p style="color: #666; margin-bottom: 30px;">Target: <strong>{self.domain}</strong> | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <!-- Estadísticas -->
        <div class="card">
            <h3>Estadísticas Generales</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                <div class="stat stat-critical">Critical: {severity_counts['critical']}</div>
                <div class="stat stat-high">High: {severity_counts['high']}</div>
                <div class="stat stat-medium">Medium: {severity_counts['medium']}</div>
                <div class="stat stat-low">Low: {severity_counts['low']}</div>
                <div class="stat stat-info">Info: {severity_counts['info']}</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px;">
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <div style="font-size: 2em; font-weight: bold; color: #007bff;">{len(subdomains)}</div>
                    <div style="color: #666;">Subdominios</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <div style="font-size: 2em; font-weight: bold; color: #28a745;">{len(live_hosts)}</div>
                    <div style="color: #666;">Hosts Vivios</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <div style="font-size: 2em; font-weight: bold; color: #6f42c1;">{len(endpoints)}</div>
                    <div style="color: #666;">Endpoints</div>
                </div>
            </div>
        </div>

        <!-- Subdominios -->
        <div class="card">
            <h3>Subdominios Descubiertos ({len(subdomains)})</h3>
            <div>{safe_join(subdomains, 50)}</div>
        </div>

        <!-- Hosts Vivios -->
        <div class="card">
            <h3>Hosts Vivios ({len(live_hosts)})</h3>
            <div>{safe_join(live_hosts, 50)}</div>
        </div>

        <!-- Vulnerabilidades -->
        <div class="card">
            <h3>Vulnerabilidades Encontradas ({len(vulnerabilities)})</h3>
            {'<div class="vuln-item vuln-critical"><div class="vuln-title">No critical vulnerabilities found</div></div>' if not vulnerabilities else ''}
            {''.join(f"""
            <div class="vuln-item vuln-{v.get('info', {}).get('severity', 'info').lower()}">
                <div class="vuln-title">{v.get('info', {}).get('name', 'Unknown')}</div>
                <div style="color: #666; font-size: 0.9em;">Host: {v.get('host', 'N/A')}</div>
                <div style="color: #666; font-size: 0.9em;">Type: {v.get('type', 'N/A')}</div>
                <div style="margin-top: 8px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    {v.get('description', v.get('raw', ''))[:500]}...
                </div>
            </div>
            """ for v in sorted(vulnerabilities, key=lambda x: x.get('info', {}).get('severity', 'info').lower(), reverse=True)[:20])}
        </div>

        <!-- Endpoints -->
        <div class="card">
            <h3>EndpointsDescubiertos ({len(endpoints)})</h3>
            <div>{safe_join(endpoints, 50)}</div>
        </div>

        <div class="timestamp">Reporte generado por BugBountyTool</div>
    </div>
</body>
</html>
"""
        return html

    def generate_json_report(
        self,
        subdomains: List[str],
        live_hosts: List[str],
        scan_results: List[str],
        vulnerabilities: List[Dict],
        endpoints: List[str],
        parameters: List[Dict],
        report_name: str | None = None
    ) -> str:
        """
        Genera un reporte JSON.

        Args:
            subdomains: Lista de subdominios
            live_hosts: Lista de hosts vivos
            scan_results: Resultados del escaneo
            vulnerabilities: Lista de vulnerabilidades
            endpoints: Lista de endpoints
            parameters: Lista de parámetros
            report_name: Nombre del reporte (opcional)

        Returns:
            str: Ruta al archivo generado
        """
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"report_{self.domain}_{timestamp}.json"

        report_path = self.reports_dir / report_name

        report = {
            "domain": self.domain,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "subdomains_count": len(subdomains),
                "live_hosts_count": len(live_hosts),
                "endpoints_count": len(endpoints),
                "vulnerabilities_count": len(vulnerabilities),
                "parameters_count": len(parameters),
                "severity_breakdown": {}
            },
            "data": {
                "subdomains": subdomains[:1000],  # Limitar
                "live_hosts": live_hosts[:1000],
                "endpoints": endpoints[:1000],
                "vulnerabilities": vulnerabilities,
                "parameters": parameters
            }
        }

        # Severity breakdown
        for vuln in vulnerabilities:
            severity = vuln.get("info", {}).get("severity", "info").lower()
            report["summary"]["severity_breakdown"][severity] = \
                report["summary"]["severity_breakdown"].get(severity, 0) + 1

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Reporte JSON generado: {report_path}")
        return str(report_path)
