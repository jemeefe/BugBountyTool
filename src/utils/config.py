"""
Módulo de configuración para BugBountyTool.
Carga y valida la configuración desde config.yaml.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class Config:
    """
    Clase para manejar la configuración de BugBountyTool.
    Carga la configuración desde un archivo YAML y provee acceso estructurado.
    """

    def __init__(self, config_path: str | Path = "config/config.yaml"):
        """
        Inicializa la configuración cargando desde el archivo YAML.

        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Carga y parsea el archivo de configuración YAML."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                # Configuración por defecto si no existe el archivo
                self.config = {
                    "target": {"domain": "", "output_dir": "outputs"},
                    "tools": {
                        "subfinder": {
                            "enabled": True,
                            "path": "subfinder",
                            "options": ["-all", "-timeout", "5", "-recursive"]
                        },
                        "httpx": {
                            "enabled": True,
                            "path": "httpx",
                            "options": ["-timeout", "10", "-retries", "2", "-t", "100", "-silent"]
                        },
                        "nmap": {
                            "enabled": True,
                            "path": "nmap",
                            "options": ["-sV", "-sC", "-T4", "-v"]
                        },
                        "nuclei": {
                            "enabled": False,
                            "path": "nuclei",
                            "options": ["-silent", "-json"],
                            "rate_limit": {
                                "enabled": True,
                                "requests_per_second": 5,
                                "delay_between_requests": 0.2
                            },
                            "templates": ["poc", "cves", "exposed-panels"]
                        }
                    },
                    "pipeline": {
                        "phases": ["discovery", "filtering", "scanning"],
                        "keep_intermediates": True
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                        "file": "logs/bug_bounty_tool.log",
                        "console": True
                    }
                }
        except yaml.YAMLError as e:
            print(f"Error cargando configuración YAML: {e}")
            # Fallback a configuración por defecto
            self.config = {}

    @property
    def target_domain(self) -> str:
        """Dominio objetivo."""
        return self.config.get("target", {}).get("domain", "")

    @property
    def output_dir(self) -> str:
        """Directorio de salida."""
        return self.config.get("target", {}).get("output_dir", "outputs")

    @property
    def logging_config(self) -> Dict[str, Any]:
        """Configuración de logging."""
        return self.config.get("logging", {})

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de una herramienta específica.

        Args:
            tool_name: Nombre de la herramienta (ej: 'subfinder', 'httpx')

        Returns:
            Dict con la configuración de la herramienta
        """
        return self.config.get("tools", {}).get(tool_name, {})

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Verifica si una herramienta está habilitada.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            True si está habilitada
        """
        return self.get_tool_config(tool_name).get("enabled", False)

    def get_tool_path(self, tool_name: str) -> str:
        """
        Obtiene la ruta al binario de una herramienta.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Ruta al binario
        """
        return self.get_tool_config(tool_name).get("path", tool_name)

    def get_tool_options(self, tool_name: str) -> List[str]:
        """
        Obtiene las opciones por defecto de una herramienta.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Lista de opciones
        """
        return self.get_tool_config(tool_name).get("options", [])

    def get_rate_limit_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de rate-limiting para una herramienta.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Dict con configuración de rate-limiting
        """
        tool_config = self.get_tool_config(tool_name)
        return tool_config.get("rate_limit", {
            "enabled": False,
            "requests_per_second": 10,
            "delay_between_requests": 0.1
        })

    def get_phases(self) -> List[str]:
        """
        Obtiene la lista de fases del pipeline.

        Returns:
            Lista de nombres de fases
        """
        return self.config.get("pipeline", {}).get("phases", [])

    def should_keep_intermediates(self) -> bool:
        """
        Verifica si se deben mantener archivos intermedios.

        Returns:
            True si se deben mantener
        """
        return self.config.get("pipeline", {}).get("keep_intermediates", True)

    def get_nuclei_templates(self) -> List[str]:
        """
        Obtiene la lista de templates de nuclei a usar.

        Returns:
            Lista de nombres de templates
        """
        return self.get_tool_config("nuclei").get("templates", [])


def load_config(config_path: str | Path = "config/config.yaml") -> Config:
    """
    Función fábrica para cargar la configuración.

    Args:
        config_path: Ruta al archivo de configuración

    Returns:
        Config: Objeto de configuración
    """
    return Config(config_path)
