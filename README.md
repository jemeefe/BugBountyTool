# BugBountyTool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/jemeefe/BugBountyTool)

Framework semi-automatizado para Bug Bounty en Python con pipeline modular, checkpoints y reportes inteligentes.

## Características

- **Pipeline modular** con fases independientes y reutilizables
- **Persistencia inteligente** con checkpoints para reanudar después de fallos
- **Configuración flexible** mediante YAML
- **Rate-limiting configurable** para evitar WAF detection (especialmente con nuclei)
- **Reportes HTML y JSON** con priorización de findings
- **Sin dependencias externas pesadas** - solo Python y herramientas CLI
- **Instalación plug and play** con script automatizado y verificación de dependencias
- **Compatible con pip/pipx** para instalación estándar de Python

## Requisitos

1. **Python 3.10+**
2. **Herramientas requeridas en el PATH**:

| Herramienta | Descripción | Instalación |
|-------------|-------------|-------------|
| subfinder | Descubrimiento de subdominios | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| httpx | Verificación de hosts vivos | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| nmap | Escaneo de puertos y servicios | `apt install nmap` |
| nuclei | Escaneo de vulnerabilidades | `go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest` |
| waybackurls | Extraer URLs del Archivo de la Web | `go install github.com/tomnomnom/waybackurls@latest` |
| gau | Obtener URLs de fuentes públicas | `go install github.com/lc/gau/v2/cmd/gau@latest` |
| ffuf | Fuzzing de directorios y archivos | `go install github.com/ffuf/ffuf@latest` |
| subjs | Extraer JS de subdominios | `go install github.com/subfinder/subjs@latest` |
| dalfox | Testing de XSS | `go install github.com/hahwul/dalfox/v2@latest` |
| qsreplace | Reemplazar parámetros en URLs | `go install github.com/tomnomnom/qsreplace@latest` |

## Instalación

### Opción 1: Script automatizado (Recomendado)

El script `install.sh` detecta automáticamente tu distribución Linux y configura todo:

```bash
# Clonar el repositorio
git clone https://github.com/jemeefe/BugBountyTool.git
cd BugBountyTool

# Ejecutar instalación automatizada
sudo bash install.sh
```

**Qué hace el script:**
- Detecta tu distribución (Debian/Ubuntu/Kali, Arch Linux)
- Instala dependencias base (git, nmap, Python 3.10+, Go)
- Crea un virtual environment en `/opt/bugbountytool/venv`
- Instala herramientas Go (subfinder, httpx, nuclei, waybackurls, gau)
- Crea comando global `bugbountytool` con activación automática del venv
- Verifica la instalación con colores y progreso visual

### Opción 2: Instalación con pip

```bash
# Clonar el repositorio
git clone https://github.com/jemeefe/BugBountyTool.git
cd BugBountyTool

# Instalar como paquete Python
pip install .

# Verificar instalación
bugbountytool --help
```

### Opción 3: Instalación con pipx (Aislado)

```bash
# Clonar el repositorio
git clone https://github.com/jemeefe/BugBountyTool.git
cd BugBountyTool

# Instalar en entorno aislado
pipx install .

# Verificar instalación
bugbountytool --help
```

### Opción 4: Ejecución manual

```bash
# Clonar el repositorio
git clone https://github.com/jemeefe/BugBountyTool.git
cd BugBountyTool

# Instalar dependencias Python
pip install -r requirements.txt

# Ejecutar directamente
python3 src/main.py example.com
```

### Verificación de dependencias

Al ejecutar por primera vez, la herramienta verifica automáticamente las dependencias:

```bash
bugbountytool example.com
```

Verás un output con colores indicando qué herramientas están instaladas:
- ✓ (verde) = Herramienta instalada
- ✗ (rojo) = Herramienta crítica faltante
- ○ (amarillo) = Herramienta opcional faltante

Para omitir esta verificación:
```bash
bugbountytool example.com --skip-deps-check
```

## Uso

### Básico
```bash
bugbountytool example.com
```

### Con opciones
```bash
bugbountytool example.com -d /ruta/proyecto -v
```

### Opciones disponibles

| Opción | Descripción |
|--------|-------------|
| `domain` | Dominio principal a analizar (requerido) |
| `-d, --dir DIR` | Directorio base del proyecto (por defecto: actual) |
| `-c, --config CONFIG` | Ruta al archivo de configuración YAML |
| `-v, --verbose` | Logging en modo DEBUG |
| `--no-checkpoint` | Desactiva el uso de checkpoints |
| `--minimal` | Ejecuta solo las fases básicas (1-3) |
| `--skip-deps-check` | Omite la verificación de dependencias |

### Ejemplos de uso

```bash
# Ejecución básica
bugbountytool example.com

# Modo verbose para debugging
bugbountytool example.com -v

# Solo fases básicas (sin nuclei, crawling, etc.)
bugbountytool example.com --minimal

# Especificar directorio de salida
bugbountytool example.com -d /home/kali/bugbounty/results

# Desactivar checkpoints
bugbountytool example.com --no-checkpoint

# Usar configuración personalizada
bugbountytool example.com -c /path/to/custom-config.yaml

# Omitir verificación de dependencias (más rápido)
bugbountytool example.com --skip-deps-check
```

## Fases del Pipeline

| Fase | Herramienta | Input | Output |
|------|-------------|-------|--------|
| **1. Discovery** | subfinder | Dominio | Lista de subdominios |
| **2. Filtering** | httpx | Subdominios | Hosts vivos |
| **3. Scanning** | nmap | Hosts vivos | Puertos y servicios |
| **4. Vulnerability** | nuclei | Hosts vivos | Findings (JSON) |
| **5. Crawling** | waybackurls, gau, ffuf | Hosts vivos | Endpoints |
| **6. Parameter** | subjs, dalfox | Hosts vivos | Parámetros (JSON) |

## Estructura del Proyecto

```
BugBountyTool/
├── config/
│   └── config.yaml          # Configuración del pipeline
├── outputs/                 # Resultados de cada fase
│   ├── checkpoints/         # Puntos de recuperación
│   └── reports/             # Reportes generados
├── logs/                    # Logs de ejecución
├── temp/                    # Archivos temporales
├── src/
│   ├── __init__.py
│   ├── main.py              # Orquestador principal
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py        # Sistema de logging
│   │   ├── config.py        # Carga de configuración YAML
│   │   ├── dependencies.py  # Verificador de dependencias
│   │   ├── helpers.py       # Utilidades comunes
│   │   └── reporter.py      # Generación de reportes
│   ├── core/
│   │   ├── __init__.py
│   │   └── checkpoint.py    # Sistema de persistencia
│   └── phases/
│       ├── __init__.py
│       ├── phase.py         # Clase base para fases
│       ├── discovery.py     # Fase 1: Descubrimiento
│       ├── filtering.py     # Fase 2: Verificación
│       ├── scanning.py      # Fase 3: Puertos
│       ├── vulnerability.py # Fase 4: Nuclei
│       ├── crawling.py      # Fase 5: Crawling
│       └── parameter.py     # Fase 6: Parameters
├── setup.py                 # Configuración de instalación
├── setup.cfg                # Metadatos del paquete
├── install.sh               # Script de instalación automatizada
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Configuración

El archivo `config/config.yaml` permite personalizar:

- **Tools**: Habilitar/deshabilitar herramientas, path, opciones
- **Rate limiting**: Configurar requests por segundo para nuclei
- **Templates**: Especificar templates de nuclei a usar
- **Pipeline**: Fases a ejecutar y comportamiento

### Ejemplo de rate limiting para nuclei

```yaml
nuclei:
  enabled: true
  rate_limit:
    enabled: true
    requests_per_second: 5
    delay_between_requests: 0.2
  templates:
    - "poc"
    - "cves"
    - "exposed-panels"
```

## Persistencia y Reanudación

El sistema automáticamente crea checkpoints después de cada fase. Si el pipeline se interrumpe, al ejecutar de nuevo se reanudará desde la última fase completada.

Para desactivar esta funcionalidad:
```bash
bugbountytool example.com --no-checkpoint
```

## Reportes

Tras completar el pipeline se generan en `outputs/reports/`:

- **Reporte HTML**: Visualización interactiva en el navegador con tablas y estadísticas
- **Reporte JSON**: Estructura para integración con otras herramientas

## Desinstalación

```bash
# Si instalaste con pip/pipx
pip uninstall bugbountytool
# o
pipx uninstall bugbountytool

# Si instalaste con el script automatizado
sudo rm /usr/local/bin/bugbountytool
sudo rm -rf /opt/bugbountytool
```

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request en el repositorio.

## Issues

Si encuentras un bug o tienes una sugerencia de mejora, por favor abre un issue en [GitHub](https://github.com/jemeefe/BugBountyTool/issues).

## Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## Agradecimientos

- [ProjectDiscovery](https://github.com/projectdiscovery) por sus increíbles herramientas
- Todos los contribuidores y usuarios del proyecto

---

**Repositorio:** [https://github.com/jemeefe/BugBountyTool](https://github.com/jemeefe/BugBountyTool)