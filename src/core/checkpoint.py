"""
Sistema de persistencia (Checkpoint) para BugBountyTool.
Permite reanudar el pipeline después de fallos o interrupciones.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging


class CheckpointManager:
    """
    Gestor de checkpoints para persistencia del pipeline.
    Permite guardar el estado de cada fase y reanudar después.
    """

    def __init__(
        self,
        output_dir: str | Path,
        domain: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el gestor de checkpoints.

        Args:
            output_dir: Directorio donde guardar los checkpoints
            domain: Dominio objetivo (usado para nombres únicos)
            logger: Logger opcional
        """
        self.output_dir = Path(output_dir)
        self.domain = domain
        self.logger = logger or logging.getLogger(__name__)

        # Directorio para checkpoints
        self.checkpoint_dir = self.output_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Nombre único basado en dominio y timestamp
        self.checkpoint_id = self._generate_checkpoint_id()
        self.checkpoint_file = self.checkpoint_dir / f"{self.checkpoint_id}.json"

        # Estado del checkpoint
        self.state: Dict[str, Any] = {
            "checkpoint_id": self.checkpoint_id,
            "domain": self.domain,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": None,
            "phases": {},
            "status": "created"
        }

    def _generate_checkpoint_id(self) -> str:
        """Genera un ID único para el checkpoint."""
        timestamp = str(time.time())
        domain_hash = hashlib.md5(self.domain.encode()).hexdigest()[:8]
        return f"checkpoint_{domain_hash}_{timestamp[:10]}"

    def save_checkpoint(self) -> bool:
        """
        Guarda el estado actual en el archivo de checkpoint.

        Returns:
            bool: True si tuvo éxito
        """
        try:
            self.state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.state["status"] = "in_progress"

            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)

            self.logger.info(f"Checkpoint guardado en: {self.checkpoint_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando checkpoint: {e}")
            return False

    def update_phase_status(
        self,
        phase_name: str,
        status: str,
        result_count: int = 0,
        output_file: str | Path | None = None
    ):
        """
        Actualiza el estado de una fase en el checkpoint.

        Args:
            phase_name: Nombre de la fase
            status: Estado (pending, running, completed, failed)
            result_count: Cantidad de resultados
            output_file: Ruta al archivo de salida (opcional)
        """
        if phase_name not in self.state["phases"]:
            self.state["phases"][phase_name] = {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "result_count": 0,
                "output_file": None
            }

        phase_state = self.state["phases"][phase_name]
        phase_state["status"] = status
        phase_state["result_count"] = result_count

        if status == "running":
            phase_state["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        elif status in ["completed", "failed"]:
            phase_state["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        if output_file:
            phase_state["output_file"] = str(output_file)

        self.save_checkpoint()

    def get_phase_status(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de una fase.

        Args:
            phase_name: Nombre de la fase

        Returns:
            Dict con el estado de la fase o None si no existe
        """
        return self.state["phases"].get(phase_name)

    def is_phase_completed(self, phase_name: str) -> bool:
        """
        Verifica si una fase ya fue completada.

        Args:
            phase_name: Nombre de la fase

        Returns:
            True si la fase está completada
        """
        phase_state = self.get_phase_status(phase_name)
        return phase_state and phase_state.get("status") == "completed"

    def get_completed_phases(self) -> List[str]:
        """
        Obtiene la lista de fases completadas.

        Returns:
            Lista de nombres de fases completadas
        """
        return [
            name for name, state in self.state["phases"].items()
            if state.get("status") == "completed"
        ]

    def get_results_for_phase(self, phase_name: str) -> List[str]:
        """
        Obtiene los resultados de una fase completada.

        Args:
            phase_name: Nombre de la fase

        Returns:
            Lista de resultados
        """
        phase_state = self.get_phase_status(phase_name)
        if not phase_state or phase_state.get("status") != "completed":
            return []

        output_file = phase_state.get("output_file")
        if not output_file or not Path(output_file).exists():
            return []

        with open(output_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def is_resumable(self) -> bool:
        """
        Verifica si el checkpoint permite reanudar.

        Returns:
            True si hay fases completadas
        """
        return len(self.get_completed_phases()) > 0

    def cleanup(self):
        """Elimina el archivo de checkpoint (usado al completar todo)."""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                self.logger.info("Checkpoint limpiado")
            except Exception as e:
                self.logger.warning(f"Error limpiando checkpoint: {e}")


def load_checkpoint(
    output_dir: str | Path,
    domain: str
) -> Optional[CheckpointManager]:
    """
    Carga un checkpoint existente si existe.

    Args:
        output_dir: Directorio de salida
        domain: Dominio objetivo

    Returns:
        CheckpointManager si existe, None si no
    """
    output_path = Path(output_dir)
    checkpoint_dir = output_path / "checkpoints"

    if not checkpoint_dir.exists():
        return None

    # Buscar el checkpoint más reciente para este dominio
    domain_hash = hashlib.md5(domain.encode()).hexdigest()[:8]
    matching_files = [
        f for f in checkpoint_dir.glob("*.json")
        if domain_hash in f.name
    ]

    if not matching_files:
        return None

    # Cargar el más reciente
    latest = max(matching_files, key=lambda x: x.stat().st_mtime)

    checkpoint = CheckpointManager(output_dir, domain)
    try:
        with open(latest, "r", encoding="utf-8") as f:
            checkpoint.state = json.load(f)
        checkpoint.checkpoint_file = latest
        return checkpoint
    except Exception as e:
        return None
