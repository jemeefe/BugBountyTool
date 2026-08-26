# 🛡️ BugBountyTool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/yourusername/bugbountytool)

Framework semi-automatizado para Bug Bounty en Python con pipeline modular, checkpoints y reportes inteligentes.

![BugBountyTool](https://img.shields.io/github/stars/yourusername/bugbountytool?style=social)

## ✨ Características

- 🚀 **Pipeline modular** con fases independientes y reutilizables
- 🔄 **Persistencia inteligente** con checkpoints para reanudar después de fallos
- ⚙️ **Configuración flexible** mediante YAML
- ⚡ **Rate-limiting configurabile** para evitar WAF detection (especialmente con nuclei)
- 📊 **Reportes HTML y JSON** con priorización de findings
- 🐍 **Sin dependencias externas pesadas** - solo Python y herramientas CLI
- 🛠️ **Fácil instalación** como cualquier herramienta CLI (nmap, httpx, etc.)

## 📋 Requisitos

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

## 🚀 Instalación en Kali Linux

### Opción 1: Instalación pip (recomendada)

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/bugbountytool.git
cd bugbountytool

# Instalar como paquete Python
sudo pip3 install .

# Verificar instalación
bugbountytool --help
```

### Opción 2: Script de instalación automatizada

```bash
# Clonar y ejecutar script
git clone https://github.com/yourusername/bugbountytool.git
cd bugbountytool
sudo bash install.sh
```

Este script:
- Copia los archivos a `/opt/bugbountytool`
- Instala dependencias Python
- Crea un enlace simbólico en `/usr/local/bin/bugbountytool`

### Opción 3: Añadir al PATH manualmente

Añade este alias a tu `~/.bashrc` o `~/.zshrc`:

```bash
alias bugbountytool='python3 /ruta/a/bugbountytool/src/main.py'
```

Luego recarga tu shell:
```bash
source ~/.bashrc  # o ~/.zshrc
```

### Opción 4: Instalación manual con pip

```bash
# Clonar y entrar en el directorio
git clone https://github.com/yourusername/bugbountytool.git
cd bugbountytool

# Instalar dependencias
pip3 install -r requirements.txt

# Ejecutar con Python
python3 src/main.py example.com
```

## 📖 Uso

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
```

## 🎯 Fases del Pipeline

| Fase | Herramienta | Input | Output |
|------|-------------|-------|--------|
| **1. Discovery** | subfinder | Dominio | Lista de subdominios |
| **2. Filtering** | httpx | Subdominios | Hosts vivos |
| **3. Scanning** | nmap | Hosts vivos | Puertos y servicios |
| **4. Vulnerability** | nuclei | Hosts vivos | Findings (JSON) |
| **5. Crawling** | waybackurls, gau, ffuf | Hosts vivos | Endpoints |
| **6. Parameter** | subjs, dalfox | Hosts vivos | Parámetros (JSON) |

## 🏗️ Estructura del Proyecto

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
│   │   ├── helpers.py       # Utilidades comunes
│   │   └── reporter.py      # Generación de reportes
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
├── install.sh               # Script de instalación para Kali
├── requirements.txt
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

## ⚙️ Configuración

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

## 🔄 Persistencia y Reanudación

El sistema automáticamente crea checkpoints después de cada fase. Si el pipeline se interrumpe, al ejecutar de nuevo se reanudará desde la última fase completada.

Para desactivar esta funcionalidad:
```bash
bugbountytool example.com --no-checkpoint
```

## 📊 Reportes

Tras completar el pipeline se generan en `outputs/reports/`:

- **Reporte HTML**: Visualización interactiva en el navegador con tablas y estadísticas
- **Reporte JSON**: Estructura para integración con otras herramientas

### Ejemplo de reporte HTML generado

![Reporte HTML](https://img.shields.io/badge/report-HTML-green) (ver archivo en `outputs/reports/`)

## 🗑️ Desinstalación

```bash
# Si instalaste con pip
pip3 uninstall bugbountytool

# Si instalaste con el script
sudo rm /usr/local/bin/bugbountytool
sudo rm -rf /opt/bugbountytool
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee [CONTRIBUTING.md](CONTRIBUTING.md) para obtener detalles sobre nuestro código de conducta y el proceso para enviar pull requests.

## 🐛 Issues

Si encuentras un bug o tienes una sugerencia de mejora, por favor abre un issue en GitHub.

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [ProjectDiscovery](https://github.com/projectdiscovery) por sus increíbles herramientas
- Todos los contribuidores y usuarios del proyecto

## 📞 Contacto

- GitHub: [@yourusername](https://github.com/yourusername)
- Twitter: [@yourtwitter](https://twitter.com/yourtwitter)

---

⭐️ Si te gusta el proyecto, no olvides darle una estrella!