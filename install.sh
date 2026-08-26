#!/bin/bash
# BugBountyTool - Script de instalación robusto para Linux
# Soporta: Debian/Ubuntu/Kali, Arch Linux
# Uso: sudo bash install.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  BugBountyTool - Instalación v2.0"
echo "========================================"

# Verificar si se ejecuta como root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: Este script debe ejecutarse como root${NC}"
   echo "Uso: sudo bash install.sh"
   exit 1
fi

# Obtener el directorio actual (donde está el script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="/opt/bugbountytool"
VENV_DIR="$INSTALL_DIR/venv"

# ============================================
# 1. DETECCIÓN DE DISTRIBUCIÓN
# ============================================
echo ""
echo -e "${BLUE}[1/8] Detectando distribución...${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    echo -e "  ${GREEN}✓${NC} Distribución detectada: $PRETTY_NAME"
else
    echo -e "  ${RED}✗${NC} No se pudo detectar la distribución"
    exit 1
fi

# Determinar el gestor de paquetes
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    PKG_INSTALL="apt-get install -y"
    PKG_UPDATE="apt-get update"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    PKG_INSTALL="pacman -S --noconfirm"
    PKG_UPDATE="pacman -Sy"
else
    echo -e "  ${RED}✗${NC} Gestor de paquetes no soportado"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Gestor de paquetes: $PKG_MANAGER"

# ============================================
# 2. INSTALAR DEPENDENCIAS BASE
# ============================================
echo ""
echo -e "${BLUE}[2/8] Instalando dependencias base...${NC}"

$PKG_UPDATE > /dev/null 2>&1

DEPS_BASE="git nmap"
DEPS_PYTHON=""
DEPS_GO=""

if [ "$PKG_MANAGER" = "apt" ]; then
    DEPS_PYTHON="python3 python3-pip python3-venv"
    DEPS_GO="golang-go"
elif [ "$PKG_MANAGER" = "pacman" ]; then
    DEPS_PYTHON="python python-pip"
    DEPS_GO="go"
fi

echo -e "  Instalando: $DEPS_BASE $DEPS_PYTHON $DEPS_GO"
$PKG_INSTALL $DEPS_BASE $DEPS_PYTHON $DEPS_GO > /dev/null 2>&1

echo -e "  ${GREEN}✓${NC} Dependencias base instaladas"

# ============================================
# 3. VERIFICAR PYTHON
# ============================================
echo ""
echo -e "${BLUE}[3/8] Verificando Python...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "  ${RED}✗${NC} Python3 no está instalado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "  ${RED}✗${NC} Python 3.10+ requerido (encontrado: $PYTHON_VERSION)"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION instalado"

# ============================================
# 4. COPIAR ARCHIVOS
# ============================================
echo ""
echo -e "${BLUE}[4/8] Copiando archivos...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${YELLOW}⚠${NC}  Directorio existente encontrado, respaldando..."
    mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/ 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Archivos copiados a $INSTALL_DIR"

# ============================================
# 5. CREAR VENV E INSTALAR DEPS PYTHON
# ============================================
echo ""
echo -e "${BLUE}[5/8] Creando entorno virtual Python...${NC}"

cd "$INSTALL_DIR"

# Crear venv
python3 -m venv "$VENV_DIR"
echo -e "  ${GREEN}✓${NC} Virtual environment creado en $VENV_DIR"

# Activar venv e instalar dependencias
source "$VENV_DIR/bin/activate"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo -e "  ${GREEN}✓${NC} Dependencias Python instaladas en venv"

# ============================================
# 6. VERIFICAR E INSTALAR GO
# ============================================
echo ""
echo -e "${BLUE}[6/8] Verificando Go...${NC}"

if ! command -v go &> /dev/null; then
    echo -e "  ${RED}✗${NC} Go no está instalado"
    echo -e "  ${YELLOW}Instalando Go...${NC}"
    $PKG_INSTALL $DEPS_GO > /dev/null 2>&1
fi

GO_VERSION=$(go version 2>/dev/null | awk '{print $3}' || echo "unknown")
echo -e "  ${GREEN}✓${NC} Go instalado: $GO_VERSION"

# Configurar GOPATH si no existe
if [ -z "$GOPATH" ]; then
    export GOPATH="$HOME/go"
    export PATH="$PATH:$GOPATH/bin"
fi

# ============================================
# 7. INSTALAR HERRAMIENTAS GO
# ============================================
echo ""
echo -e "${BLUE}[7/8] Instalando herramientas de Bug Bounty (Go)...${NC}"
echo -e "  ${YELLOW}Esto puede tardar varios minutos...${NC}"

# Array de herramientas Go
declare -A GO_TOOLS
GO_TOOLS=(
    ["subfinder"]="github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    ["httpx"]="github.com/projectdiscovery/httpx/cmd/httpx@latest"
    ["nuclei"]="github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
    ["waybackurls"]="github.com/tomnomnom/waybackurls@latest"
    ["gau"]="github.com/lc/gau/v2/cmd/gau@latest"
)

for tool in "${!GO_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $tool ya está instalado"
    else
        echo -e "  ${YELLOW}→${NC} Instalando $tool..."
        go install "${GO_TOOLS[$tool]}" > /dev/null 2>&1 && \
            echo -e "  ${GREEN}✓${NC} $tool instalado" || \
            echo -e "  ${RED}✗${NC} Error instalando $tool"
    fi
done

# Copiar binarios de Go a /usr/local/bin si no están en PATH
if [ -d "$HOME/go/bin" ]; then
    for binary in "$HOME/go/bin"/*; do
        if [ -f "$binary" ]; then
            ln -sf "$binary" "/usr/local/bin/$(basename $binary)" 2>/dev/null || true
        fi
    done
    echo -e "  ${GREEN}✓${NC} Binarios de Go enlazados en /usr/local/bin"
fi

# ============================================
# 8. CREAR WRAPPER SCRIPT
# ============================================
echo ""
echo -e "${BLUE}[8/8] Creando comando 'bugbountytool'...${NC}"

# Crear wrapper que activa el venv automáticamente
cat > /usr/local/bin/bugbountytool << 'EOF'
#!/bin/bash
# BugBountyTool wrapper - activa venv automáticamente

INSTALL_DIR="/opt/bugbountytool"
VENV_DIR="$INSTALL_DIR/venv"

# Activar venv
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

# Ejecutar main.py con todos los argumentos
python3 "$INSTALL_DIR/src/main.py" "$@"
EOF

chmod +x /usr/local/bin/bugbountytool

echo -e "  ${GREEN}✓${NC} Comando 'bugbountytool' creado"

# ============================================
# VERIFICACIÓN FINAL
# ============================================
echo ""
echo "========================================"
echo -e "  ${GREEN}✓ Instalación completada${NC}"
echo "========================================"
echo ""
echo -e "${GREEN}Uso:${NC}"
echo "  bugbountytool example.com"
echo ""
echo -e "${GREEN}Opciones:${NC}"
echo "  -v, --verbose         Modo debug"
echo "  --minimal             Solo fases básicas (1-3)"
echo "  --no-checkpoint       Desactivar checkpoints"
echo "  --skip-deps-check     Omitir verificación de dependencias"
echo ""
echo -e "${GREEN}Configuración:${NC}"
echo "  Editar: $INSTALL_DIR/config/config.yaml"
echo ""
echo -e "${YELLOW}Nota:${NC} Ejecuta 'bugbountytool --help' para ver todas las opciones"
echo -e "${YELLOW}Nota:${NC} La verificación de dependencias se ejecutará al primer uso"
echo ""
