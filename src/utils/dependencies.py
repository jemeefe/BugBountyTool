"""
Dependency checker para BugBountyTool.
Verifica que las herramientas CLI requeridas estén instaladas.
"""

import os
import shutil
import sys
from typing import Dict, List, Tuple


# Colores ANSI para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def check_command(command: str) -> bool:
    """
    Verifica si un comando está disponible en el PATH.

    Args:
        command: Nombre del comando a verificar

    Returns:
        bool: True si el comando existe, False si no
    """
    # Asegurar que ~/go/bin esté en el PATH (prioridad alta: projectdiscovery tools)
    go_bin = os.path.expanduser("~/go/bin")
    if go_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{go_bin}:{os.environ.get('PATH', '')}"

    return shutil.which(command) is not None


# Rutas conocidas de binarios Go (projectdiscovery, lc, tomnomnom) que pueden
# colisionar con paquetes del sistema (p.ej. httpx de Python en Kali).
_GO_TOOL_DIRS = [
    os.path.expanduser("~/go/bin"),
    "/usr/local/go/bin",
    "/opt/go/bin",
]


def resolve_tool_path(tool: str) -> str | None:
    """
    Resuelve la ruta absoluta correcta de un binario, priorizando la versión Go
    (ProjectDiscovery, lc, tomnomnom) sobre cualquier binario del mismo nombre en
    el PATH del sistema (p.ej. el paquete python3-httpx de Kali).

    Args:
        tool: Nombre del binario (p.ej. "httpx", "subfinder", "nuclei").

    Returns:
        str | None: Ruta absoluta si se encuentra, None en caso contrario.
    """
    # 1) Buscar primero en directorios Go conocidos (orden estable)
    for d in _GO_TOOL_DIRS:
        candidate = os.path.join(d, tool)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    # 2) Fallback al PATH (asegurarse de que ~/go/bin está delante)
    go_bin = os.path.expanduser("~/go/bin")
    current = os.environ.get("PATH", "")
    if go_bin and go_bin not in current.split(os.pathsep):
        os.environ["PATH"] = f"{go_bin}{os.pathsep}{current}"

    found = shutil.which(tool)
    return found


def get_install_command(tool: str) -> str:
    """
    Devuelve el comando de instalación para una herramienta.

    Args:
        tool: Nombre de la herramienta

    Returns:
        str: Comando de instalación
    """
    install_commands = {
        "subfinder": "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "httpx": "go install github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "nmap": "sudo apt install nmap  # o: sudo pacman -S nmap",
        "nuclei": "go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
        "waybackurls": "go install github.com/tomnomnom/waybackurls@latest",
        "gau": "go install github.com/lc/gau/v2/cmd/gau@latest",
        "ffuf": "go install github.com/ffuf/ffuf@latest",
        "subjs": "go install github.com/lc/subjs@latest",
        "dalfox": "go install github.com/hahwul/dalfox/v2@latest",
        "qsreplace": "go install github.com/tomnomnom/qsreplace@latest",
    }
    return install_commands.get(tool, "Instalación manual requerida")


def install_tool(tool: str) -> bool:
    """
    Instala una herramienta usando el comando apropiado.

    Args:
        tool: Nombre de la herramienta a instalar

    Returns:
        bool: True si la instalación fue exitosa
    """
    import subprocess

    install_commands = {
        "subfinder": ["go", "install", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"],
        "httpx": ["go", "install", "github.com/projectdiscovery/httpx/cmd/httpx@latest"],
        "nmap": ["sudo", "apt", "install", "-y", "nmap"],
        "nuclei": ["go", "install", "github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"],
        "waybackurls": ["go", "install", "github.com/tomnomnom/waybackurls@latest"],
        "gau": ["go", "install", "github.com/lc/gau/v2/cmd/gau@latest"],
        "ffuf": ["go", "install", "github.com/ffuf/ffuf@latest"],
        "subjs": ["go", "install", "github.com/lc/subjs@latest"],
        "dalfox": ["go", "install", "github.com/hahwul/dalfox/v2@latest"],
        "qsreplace": ["go", "install", "github.com/tomnomnom/qsreplace@latest"],
    }

    if tool not in install_commands:
        return False

    try:
        print(f"  {Colors.BLUE}→{Colors.END} Instalando {tool}...")

        # Asegurar que GOPATH esté configurado
        go_path = os.path.expanduser("~/go")
        env = os.environ.copy()
        env["GOPATH"] = go_path
        env["PATH"] = f"{go_path}/bin:{env.get('PATH', '')}"

        result = subprocess.run(
            install_commands[tool],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,  # 5 minutos timeout
            env=env
        )

        if result.returncode == 0:
            # Actualizar PATH globalmente después de instalar
            go_bin = os.path.expanduser("~/go/bin")
            if go_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{go_bin}:{os.environ.get('PATH', '')}"

            print(f"  {Colors.GREEN}✓{Colors.END} {tool} instalado correctamente")
            return True
        else:
            print(f"  {Colors.RED}✗{Colors.END} Error instalando {tool}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  {Colors.RED}✗{Colors.END} Timeout instalando {tool}")
        return False
    except Exception as e:
        print(f"  {Colors.RED}✗{Colors.END} Error: {str(e)}")
        return False


def check_dependencies(strict: bool = False, auto_install: bool = True) -> Tuple[bool, List[str]]:
    """
    Verifica todas las dependencias del pipeline.

    Args:
        strict: Si True, sale del programa si falta una herramienta crítica
        auto_install: Si True, ofrece instalación automática interactiva

    Returns:
        Tuple[bool, List[str]]: (all_ok, missing_tools)
    """
    # Usa resolve_tool_path para evitar colisiones con paquetes del sistema
    critical_tools = {
        "subfinder": "Fase 1: Descubrimiento de subdominios",
        "httpx": "Fase 2: Verificación de hosts vivos",
        "nmap": "Fase 3: Escaneo de puertos",
    }

    # Herramientas opcionales (fases avanzadas 4-6)
    optional_tools = {
        "nuclei": "Fase 4: Escaneo de vulnerabilidades",
        "waybackurls": "Fase 5: Crawling de endpoints",
        "gau": "Fase 5: Obtención de URLs",
        "ffuf": "Fase 5: Fuzzing de directorios",
        "subjs": "Fase 6: Extracción de JavaScript",
        "dalfox": "Fase 6: Testing de XSS",
        "qsreplace": "Fase 6: Manipulación de parámetros",
    }

    print(f"\n{Colors.BOLD}Verificando dependencias...{Colors.END}", flush=True)

    missing_critical = []
    missing_optional = []
    all_ok = True

    # Verificar herramientas críticas (silencioso si todo OK)
    critical_status = []
    for tool, description in critical_tools.items():
        path = resolve_tool_path(tool)
        if path:
            critical_status.append((tool, True))
        else:
            critical_status.append((tool, False))
            missing_critical.append(tool)
            all_ok = False

    # Verificar herramientas opcionales (silencioso si todo OK)
    optional_status = []
    for tool, description in optional_tools.items():
        path = resolve_tool_path(tool)
        if path:
            optional_status.append((tool, True))
        else:
            optional_status.append((tool, False))
            missing_optional.append(tool)

    # Mostrar comandos de instalación si faltan herramientas
    missing_tools = missing_critical + missing_optional

    if missing_tools and auto_install:
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}Herramientas faltantes detectadas:{Colors.END}")

        if missing_critical:
            print(f"\n{Colors.RED}Críticas:{Colors.END}")
            for tool in missing_critical:
                print(f"  - {tool}")

        if missing_optional:
            print(f"\n{Colors.YELLOW}Opcionales:{Colors.END}")
            for tool in missing_optional:
                print(f"  - {tool}")

        print("\n" + "=" * 60)

        # Preguntar si desea instalar
        try:
            response = input(f"\n{Colors.BOLD}¿Deseas instalar las herramientas faltantes automáticamente? (Y/N): {Colors.END}").strip().upper()

            if response == 'Y':
                print(f"\n{Colors.BOLD}Iniciando instalación automática...{Colors.END}\n")

                # Verificar Go primero si hay herramientas Go
                go_tools = [t for t in missing_tools if t != "nmap"]
                if go_tools and not check_command("go"):
                    print(f"{Colors.RED}ERROR: Go no está instalado.{Colors.END}")
                    print("Instala Go primero:")
                    print(f"  {Colors.BLUE}sudo apt install golang-go{Colors.END}")
                    print(f"  {Colors.BLUE}# o: sudo pacman -S go{Colors.END}")
                    if strict:
                        sys.exit(1)
                    return all_ok, missing_tools

                # Instalar herramientas
                installed = []
                failed = []

                for tool in missing_tools:
                    if install_tool(tool):
                        installed.append(tool)
                    else:
                        failed.append(tool)

                # Verificar nuevamente las herramientas instaladas
                print(f"\n{Colors.BOLD}Verificando instalaciones...{Colors.END}")
                actually_installed = []
                still_missing = []

                for tool in installed:
                    if check_command(tool):
                        actually_installed.append(tool)
                    else:
                        still_missing.append(tool)
                        failed.append(tool)

                # Resumen
                print(f"\n{Colors.BOLD}Resumen de instalación:{Colors.END}")
                if actually_installed:
                    print(f"{Colors.GREEN}✓ Instaladas y verificadas ({len(actually_installed)}):{Colors.END}")
                    for tool in actually_installed:
                        print(f"  - {tool}")

                if still_missing:
                    print(f"\n{Colors.YELLOW}⚠ Instaladas pero no detectadas en PATH ({len(still_missing)}):{Colors.END}")
                    for tool in still_missing:
                        print(f"  - {tool}")
                    print(f"\n{Colors.YELLOW}Solución: Cierra y vuelve a abrir tu terminal, o ejecuta:{Colors.END}")
                    print(f"  {Colors.BLUE}export PATH=\"$HOME/go/bin:$PATH\"{Colors.END}")

                if failed:
                    print(f"\n{Colors.RED}✗ Falló la instalación ({len([x for x in failed if x not in still_missing])}):{Colors.END}")
                    for tool in failed:
                        if tool not in still_missing:
                            print(f"  - {tool}")
                            print(f"    Comando manual: {Colors.BLUE}{get_install_command(tool)}{Colors.END}")

                # Actualizar estado
                if not failed or all(t in still_missing for t in failed):
                    all_ok = True
                    missing_tools = []
                    if still_missing:
                        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Todas las herramientas instaladas{Colors.END}")
                        print(f"{Colors.YELLOW}Nota: Reinicia tu terminal para usar las herramientas recién instaladas.{Colors.END}")
                    else:
                        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Todas las herramientas instaladas correctamente{Colors.END}")
                else:
                    all_ok = False
                    missing_tools = failed
            else:
                print(f"\n{Colors.YELLOW}Instalación manual requerida.{Colors.END}")
                print("\nPara instalar manualmente, ejecuta:")
                for tool in missing_tools:
                    print(f"  {Colors.BLUE}{get_install_command(tool)}{Colors.END}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Instalación cancelada por el usuario.{Colors.END}")
            if strict:
                sys.exit(1)

    elif missing_critical:
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Faltan herramientas críticas{Colors.END}")
        print("\nPara instalarlas, ejecuta:")
        for tool in missing_critical:
            print(f"  {Colors.BLUE}{get_install_command(tool)}{Colors.END}")

        if strict:
            print(f"\n{Colors.RED}Saliendo... Instala las herramientas críticas primero.{Colors.END}")
            sys.exit(1)
    elif missing_optional:
        print(f"\n{Colors.YELLOW}AVISO: Algunas herramientas opcionales no están instaladas{Colors.END}")
        print("Las fases avanzadas (4-6) pueden fallar sin ellas.")
        print("\nPara instalarlas, ejecuta:")
        for tool in missing_optional:
            print(f"  {Colors.BLUE}{get_install_command(tool)}{Colors.END}")
        print(f"\n{Colors.GREEN}Puedes continuar con el escaneo básico (fases 1-3).{Colors.END}")
    else:
        # Todo OK: completamente silencioso (sin ruido)
        pass

    return all_ok, missing_tools


def check_go_installation() -> bool:
    """
    Verifica si Go está instalado y configurado correctamente.

    Returns:
        bool: True si Go está instalado
    """
    if not check_command("go"):
        print(f"{Colors.YELLOW}AVISO: Go no está instalado.{Colors.END}")
        print("Necesitas Go para instalar herramientas de bug bounty.")
        print("\nPara instalar Go:")
        print(f"  {Colors.BLUE}Ubuntu/Debian: sudo apt install golang{Colors.END}")
        print(f"  {Colors.BLUE}Arch: sudo pacman -S go{Colors.END}")
        print(f"  {Colors.BLUE}O desde: https://go.dev/dl/{Colors.END}")
        return False
    return True


if __name__ == "__main__":
    # Test del módulo
    check_go_installation()
    check_dependencies(strict=False)
