# Contribuir a BugBountyTool

Gracias por tu interés en contribuir a BugBountyTool. Este documento te guiará a través del proceso.

## Code of Conduct

Por favor, mantén un ambiente respetuoso y profesional en todas tus interacciones.

## Cómo contribuir

### 1. Fork del repositorio

```bash
# Haz fork del repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/tu-usuario/bugbountytool.git
cd bugbountytool
```

### 2. Crea una rama para tu feature

```bash
git checkout -b feature/nueva-funcionalidad
# o
git checkout -b fix/bug-correccion
```

### 3. Realiza tus cambios

- Sigue el estilo del código existente
- Agrega comentarios donde sea necesario
- Mantén los cambios enfocados en una sola funcionalidad o corrección

### 4. Ejecuta pruebas

```bash
# Verifica que el script funcione
python3 src/main.py --help

# Ejecuta con un dominio de prueba (cambia example.com por tu dominio)
python3 src/main.py example.com --minimal
```

### 5. Haz commit de tus cambios

```bash
git add .
git commit -m "Descripción clara de tus cambios"
```

### 6. Push a tu fork

```bash
git push origin feature/nueva-funcionalidad
```

### 7. Abre un Pull Request

Ve a GitHub y abre un Pull Request desde tu rama hacia la rama `main` del repositorio original.

## Estilo del Código

- Usa Python 3.10+ features (type hints, f-strings)
- Sigue PEP 8 para nomenclatura
- Comenta código complejo
- Documenta nuevas funciones

## Estructura del Proyecto

```
src/
├── main.py              # Entry point principal
├── utils/               # Utilidades generales
│   ├── logger.py        # Logging
│   ├── config.py        # Configuración YAML
│   ├── helpers.py       # Funciones auxiliares
│   └── reporter.py      # Generación de reportes
└── phases/              # Fases del pipeline
    ├── phase.py         # Clase base
    ├── discovery.py     # Discovery
    ├── filtering.py     # Filtering
    ├── scanning.py      # Scanning
    ├── vulnerability.py # Nuclei
    ├── crawling.py      # Crawling
    └── parameter.py     # Parameter discovery
```

## Preguntas?

Abre un issue para cualquier pregunta o discusión.
