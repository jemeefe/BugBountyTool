"""
Módulo de utilidades para BugBountyTool.
Contiene funciones comunes utilizadas en todo el framework.
"""

import os
import subprocess
import shlex
from pathlib import Path
from typing import List, Tuple, Optional


def run_command(
    command: str,
    args: List[str],
    cwd: str | Path | None = None,
    timeout: int | None = None,
) -> Tuple[bool, str, str]:
    """
    Ejecuta un comando del sistema de forma segura usando subprocess.

    Args:
        command: Comando a ejecutar (ej: 'subfinder', 'httpx')
        args: Lista de argumentos para el comando
        cwd: Working directory donde ejecutar el comando (opcional)
        timeout: Tiempo máximo de ejecución en segundos (opcional)

    Returns:
        Tuple[bool, str, str]: (success, stdout, stderr)
    """
    try:
        full_command = [command] + args
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Comando ejecutado por más tiempo que el timeout permitido"
    except FileNotFoundError:
        return False, "", f"Comando '{command}' no encontrado. Asegúrate de que esté en el PATH"
    except Exception as e:
        return False, "", f"Error ejecutando el comando: {str(e)}"


def read_file_lines(file_path: str | Path) -> List[str]:
    """
    Lee un archivo y devuelve una lista de líneas sin saltos de línea.

    Args:
        file_path: Ruta al archivo

    Returns:
        List[str]: Líneas del archivo
    """
    path = Path(file_path)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def write_lines_to_file(file_path: str | Path, lines: List[str]) -> bool:
    """
    Escribe una lista de líneas en un archivo.

    Args:
        file_path: Ruta al archivo de salida
        lines: Lista de líneas a escribir

    Returns:
        bool: True si tuvo éxito, False en caso contrario
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            if lines:
                f.write("\n")
        return True
    except Exception:
        return False


def clean_subdomain(subdomain: str) -> str:
    """
    Limpia un subdominio eliminando protocolos y rutas.

    Args:
        subdomain: Subdominio a limpiar

    Returns:
        str: Subdominio limpio
    """
    # Eliminar protocolos
    subdomain = subdomain.replace("http://", "").replace("https://", "")
    # Eliminar rutas
    subdomain = subdomain.split("/")[0]
    # Eliminar puertos
    subdomain = subdomain.split(":")[0]
    return subdomain.strip()


def deduplicate_list(items: List[str]) -> List[str]:
    """
    Elimina elementos duplicados de una lista manteniendo el orden.

    Args:
        items: Lista de elementos

    Returns:
        List[str]: Lista sin duplicados
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
