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

        # PASO A (Rápido): descubrir puertos abiertos con nmap -sS -p- --min-rate 5000
        # Solo para encontrar qué puertos están abiertos, sin servir versiones
        fast_args = [
            "-sS",          # TCP SYN (rápido, no completa handshake)
            "-p-",          # Todos los puertos (1-65535)
            "--min-rate", "5000",  # Velocidad agresiva
            "-T5",          # Timing máximo
            "--open",       # Solo puertos abiertos
            "-oG", "-",     # Output greppable a stdout
            "-iL", str(temp_input)
        ]
        self.logger.info(f"[PASO A - RÁPIDO] Descubriendo puertos: {self.tool_path} {' '.join(fast_args)}")
        success_fast, stdout_fast, stderr_fast = run_command(self.tool_path, fast_args, timeout=180)

        # Extraer puertos descubiertos
        open_ports = set()
        if success_fast and stdout_fast:
            for line in stdout_fast.strip().split("\n"):
                # Formato greppable: Host: 1.2.3.4 () Ports: 22/open/tcp//ssh/, 80/open/tcp//http/
                if "Ports:" in line:
                    # Extraer puertos de la línea
                    port_part = line.split("Ports:")[1].split(",")
                    for p in port_part:
                        p_clean = p.strip()
                        if "/open" in p_clean:
                            try:
                                port_num = int(p_clean.split("/")[0])
                                open_ports.add(port_num)
                            except ValueError:
                                pass

        if open_ports:
            self.logger.info(f"[PASO A] Puertos abiertos descubiertos: {sorted(open_ports)} ({len(open_ports)} puertos)")
            # PASO B (Quirúrgico): solo escanear los puertos descubiertos con -sV -sC
            port_str = ",".join(str(p) for p in sorted(open_ports))
            # Limitar a los primeros 50 puertos para no saturar
            if len(open_ports) > 50:
                port_str = ",".join(str(p) for p in sorted(open_ports)[:50])
                self.logger.info(f"[PASO B] Limitando a primeros 50 puertos abiertos")

            surgical_args = [
                "-sV", "-sC", "-T4", "-v",
                "-p", port_str,
                "-iL", str(temp_input)
            ]
            self.logger.info(f"[PASO B] Escaneando puertos descubiertos: {self.tool_path} {' '.join(surgical_args)}")
            success, stdout, stderr = run_command(self.tool_path, surgical_args, timeout=None)
        else:
            self.logger.warning("[PASO A] No se descubrieron puertos abiertos; saltando paso B.")
            success, stdout, stderr = False, "", "No open ports found"

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

# OPTIMIZACIÓN RÁPIDA (Paso A): usar naabu para descubrir puertos rápidamente
# Si no hay hosts vivos -> ninguno. Si hay -> Paso B quirúrgico.
