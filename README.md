# 🚀 AWS S3 File Downloader

Herramienta automatizada para descargar archivos masivamente desde AWS S3 usando Selenium. Diseñada para procesar miles de archivos con control de progreso, capacidad de interrumpir/reanudar y descarga por tandas.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Archivos del Proyecto](#archivos-del-proyecto)
- [Configuración](#configuración)
- [Troubleshooting](#troubleshooting)
- [Contribuir](#contribuir)

## ✨ Características

### 🎯 Funcionalidades Principales
- **Descarga masiva**: Procesa miles de archivos automáticamente
- **Control de progreso**: Guarda estado en `download_progress.json`
- **Interrumpir/Reanudar**: Ctrl+C seguro, continúa donde se quedó
- **Descarga por tandas**: Procesa archivos en grupos configurables
- **Evita duplicados**: No descarga archivos ya existentes
- **Manejo robusto de errores**: Reintentos automáticos y recuperación

### 🛠️ Versiones Disponibles
1. **aws_downloader_test.py**: Versión de prueba (5 archivos)
2. **aws_downloader_batch.py**: Versión por tandas estándar
3. **aws_downloader_fast.py**: Versión optimizada para velocidad
4. **aws_downloader_robust.py**: Versión con manejo robusto de errores
5. **check_status.py**: Verificador de estado y progreso

## 🔧 Requisitos

### Software Necesario
- **Python 3.7+**
- **Google Chrome** (última versión)
- **Cuenta AWS** con acceso a S3

### Dependencias Python
Ver [requirements.txt](requirements.txt) para la lista completa.

Principales:
- `selenium` - Automatización web
- `pandas` - Manipulación de datos CSV
- `webdriver-manager` - Gestión automática de ChromeDriver
- `psutil` - Monitoreo de procesos

## 📦 Instalación

### 1. Clonar/Descargar el Proyecto
```bash
git clone <tu-repositorio>
cd aws-s3-downloader
```

### 2. Crear Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Preparar Datos
Coloca tu archivo CSV con los nombres de archivos en la raíz del proyecto:
- `Informacion archivos cargados Ruta Costera.csv`

## 🚀 Uso

### Paso 1: Prueba Inicial (Recomendado)
```bash
python aws_downloader_test.py
```
- Descarga solo 5 archivos como prueba
- Verifica que todo funcione correctamente

### Paso 2: Descarga Completa
```bash
# Versión estándar por tandas
python aws_downloader_batch.py

# Versión optimizada (más rápida)
python aws_downloader_fast.py

# Versión robusta (más estable)
python aws_downloader_robust.py
```

### Paso 3: Verificar Estado
```bash
python check_status.py
```

## 📂 Estructura del Proyecto

```
RUTA_COSTERA/
├── venv/                                    # Entorno virtual
├── downloads/                               # Archivos descargados (no en git)
├── downloads_test/                          # Descargas de prueba (no en git)
├── aws_downloader_test.py                   # Versión de prueba
├── aws_downloader_batch.py                  # Versión por tandas
├── aws_downloader_fast.py                   # Versión optimizada
├── aws_downloader_robust.py                # Versión robusta
├── check_status.py                          # Verificador de estado
├── download_progress.json                   # Progreso guardado (no en git)
├── Informacion archivos cargados Ruta Costera.csv  # Datos de entrada
├── requirements.txt                         # Dependencias
├── .gitignore                              # Archivos ignorados por git
└── README.md                               # Este archivo
```

## ⚙️ Configuración

### Variables Principales
```python
# En cualquier archivo del downloader
csv_file = "Informacion archivos cargados Ruta Costera.csv"  # Archivo fuente
download_folder = "downloads"                                # Carpeta destino
batch_size = 1500                                           # Archivos por tanda
```

### Formato CSV Requerido
El archivo CSV debe tener una columna llamada `file` con los nombres de archivos:
```csv
id;name;file;created_at;module
270763;SEGURIDAD;NTE2OTIwMjUtMD...pdf;2024-03-21;Empleados
```

## 🔄 Proceso de Descarga

### Flujo Típico
1. **Preparación**: Lee CSV, verifica archivos ya descargados
2. **Navegación Manual**: Abre Chrome, usuario navega a AWS S3
3. **Automatización**: Para cada archivo:
   - Busca en el campo de búsqueda de S3
   - Encuentra y abre el archivo
   - Hace clic en "Descargar"
   - Vuelve atrás para el siguiente
4. **Control**: Guarda progreso cada 5-10 archivos

### Tiempos Estimados
- **Versión estándar**: ~8-12 segundos por archivo
- **Versión optimizada**: ~3-5 segundos por archivo
- **Para 5,000 archivos**: 4-7 horas (dependiendo de la versión)

## 🛡️ Manejo de Errores

### Errores Comunes y Soluciones

#### "Campo búsqueda no encontrado"
- **Causa**: No estás en la página correcta de S3
- **Solución**: Navega a tu bucket → carpeta correcta antes de presionar Enter

#### "Conexión perdida"
- **Causa**: Problemas de red o timeout
- **Solución**: El script reintenta automáticamente, o usa la versión robusta

#### "Proceso no se detiene con Ctrl+C"
- **Causa**: Script atascado en bucle de errores
- **Solución**: Usar `check_status.py` para terminar procesos forzadamente

### Archivos de Log
- El progreso se guarda en `download_progress.json`
- Los logs aparecen en la consola con timestamps
- Use `check_status.py` para verificar estado completo

## 📊 Monitoreo

### Verificar Progreso
```bash
python check_status.py
```

### Información Mostrada
- ✅ Procesos activos/inactivos
- 📊 Progreso total y por tandas
- 📁 Archivos descargados y tamaños
- 🕐 Timestamps de última actividad
- ❌ Lista de archivos fallidos

## 🔧 Troubleshooting

### Problema: Chrome no abre
```bash
# Verificar instalación de Chrome
chrome --version

# Reinstalar webdriver-manager
pip uninstall webdriver-manager
pip install webdriver-manager
```

### Problema: Error de permisos
```bash
# Ejecutar como administrador o verificar permisos de carpeta
# Windows: Clic derecho → "Ejecutar como administrador"
```

### Problema: CSV no se lee
- Verificar encoding del archivo (debe ser UTF-8)
- Verificar separador (coma `,` o punto y coma `;`)
- Verificar que existe la columna `file`

## 🏗️ Bibliotecas Utilizadas

### Core Dependencies
- **selenium**: Automatización de navegador web
- **pandas**: Manipulación y análisis de datos
- **webdriver-manager**: Gestión automática de drivers del navegador

### Support Libraries
- **openpyxl**: Lectura de archivos Excel
- **psutil**: Monitoreo de procesos del sistema
- **pathlib**: Manipulación de rutas de archivos
- **json**: Serialización de datos de progreso
- **logging**: Sistema de logs estructurado

### Built-in Python Modules
- **time**: Control de pausas y timestamps
- **os**: Operaciones del sistema operativo
- **signal**: Manejo de señales del sistema (Ctrl+C)
- **datetime**: Manejo de fechas y horas
- **sys**: Acceso a variables del sistema

## 📈 Optimizaciones

### Versión Fast
- Timeouts reducidos (8s vs 20s)
- Sin carga de imágenes/plugins
- Pausas mínimas entre acciones
- Progreso cada 5 archivos

### Versión Robust
- Manejo mejorado de Ctrl+C
- Reintentos automáticos
- Verificación de conexión
- Mensajes de error detallados

## 🤝 Contribuir

### Para Contribuir
1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estilo de Código
- Seguir PEP 8
- Documentar funciones con docstrings
- Usar logging en lugar de print para debug
- Manejar excepciones apropiadamente

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores

- **maycolroa** - *Desarrollo inicial* - [TuGitHub](https://github.com/maycolroa)

## 🙏 Agradecimientos

- Equipo de Selenium por la excelente librería de automatización
- Comunidad de Python por las herramientas robustas
- AWS por la plataforma S3

---

**⚠️ Nota de Seguridad**: Este proyecto automatiza descargas desde AWS S3. Asegúrate de tener los permisos necesarios y cumplir con las políticas de tu organización antes de usar en entornos de producción.