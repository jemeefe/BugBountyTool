#!/bin/bash
# BugBountyTool - Script de instalación para Kali Linux
# Uso: sudo bash install.sh

set -e

echo "========================================"
echo "BugBountyTool - Instalación"
echo "========================================"

# Verificar si se ejecuta como root
if [[ $EUID -ne 0 ]]; then
   echo "Error: Este script debe ejecutarse como root"
   echo "Uso: sudo bash install.sh"
   exit 1
fi

# Directorio donde se instalará
INSTALL_DIR="/opt/bugbountytool"

echo ""
echo "[1/5] Clonando el repositorio..."

# Obtener el directorio actual (donde está el script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copiar archivos al directorio de instalación
if [ -d "$INSTALL_DIR" ]; then
    echo "  Directorio existente encontrado, actualizando..."
else
    echo "  Creando directorio: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Copiar archivos
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/ 2>/dev/null || true

echo "  [OK] Archivos copiados"

echo ""
echo "[2/5] Verificando dependencias de Python..."

# Verificar Python3
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: Python3 no está instalado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc) -ne 1 ]]; then
    echo "  ERROR: Python 3.10+ requerido (encontrado: $PYTHON_VERSION)"
    exit 1
fi

echo "  [OK] Python3 $PYTHON_VERSION instalado"

echo ""
echo "[3/5] Instalando dependencias Python..."

cd "$INSTALL_DIR"
pip3 install --upgrade pip > /dev/null 2>&1
pip3 install -r requirements.txt > /dev/null 2>&1

echo "  [OK] Dependencias instaladas"

echo ""
echo "[4/5] Creando enlace simbólico..."

# Crear enlace simbólico en /usr/local/bin
if [ -L "/usr/local/bin/bugbountytool" ]; then
    rm "/usr/local/bin/bugbountytool"
    echo "  Enlace existente eliminado"
fi

ln -s "$INSTALL_DIR/src/main.py" "/usr/local/bin/bugbountytool"
chmod +x "/usr/local/bin/bugbountytool"

echo "  [OK] Enlace creado en /usr/local/bin/bugbountytool"

echo ""
echo "[5/5] Verificando instalación..."

# Verificar
if command -v bugbountytool &> /dev/null; then
    echo "  [OK] bugbountytool está disponible en el PATH"
else
    echo "  [ERROR] No se pudo añadir al PATH"
    echo "  Añade manualmente: export PATH=\$PATH:/usr/local/bin"
fi

echo ""
echo "========================================"
echo "Instalación completada!"
echo "========================================"
echo ""
echo "Uso:"
echo "  bugbountytool example.com"
echo ""
echo "Opciones:"
echo "  -v, --verbose     Modo debug"
echo "  --minimal         Solo fases básicas (1-3)"
echo "  --no-checkpoint   Desactivar checkpoints"
echo "  -d, --dir         Directorio de salida"
echo ""
echo "Configuración:"
echo "  Editar: $INSTALL_DIR/config/config.yaml"
echo ""
echo "Requiere herramientas CLI:"
echo "  subfinder, httpx, nmap, nuclei, waybackurls"
echo "  gau, ffuf, subjs, dalfox, qsreplace"
echo ""
