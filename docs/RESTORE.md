# Restauración Completa En Mac Nuevo

Guía para recuperar Sistema Pericial tras pérdida, cambio de equipo o reinstalación. Asume que el código está en GitHub y que los datos se conservan en backups ZIP guardados en iCloud mediante `BACKUPS_DIR`.

## 1. Requisitos Previos

- macOS.
- Python 3.12 recomendado.
- Acceso al repositorio GitHub.
- Acceso a iCloud Drive donde están los backups.
- Terminal.

## 2. Clonar El Repositorio

```bash
git clone https://github.com/Gspott/sistema_pericial.git
cd sistema_pericial
```

## 3. Crear Entorno Virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Crear `.env`

Copia el ejemplo y revisa rutas y secretos:

```bash
cp .env.example .env
```

Revisar como mínimo:

- `SESSION_SECRET_KEY`: definir una clave propia y guardarla en lugar seguro.
- `DB_PATH`: normalmente `data/pericial.db`.
- `UPLOAD_DIR`, `INFORMES_DIR`, `FOTOS_DIR`, `LOGS_DIR`, `EXPORTS_DIR`.
- `BACKUPS_DIR`: definirlo si se quiere seguir usando iCloud.

Ejemplo de `BACKUPS_DIR` con ruta de iCloud y espacios:

```bash
BACKUPS_DIR="/Users/carlosblanco/Library/Mobile Documents/com~apple~CloudDocs/Casa/Trabajo Arquitecto Técnico/Sistema Pericial/Backup"
```

## 5. Restaurar Backup

Localiza el último ZIP en iCloud. Ejemplo:

```bash
ICLOUD_BACKUPS="/Users/carlosblanco/Library/Mobile Documents/com~apple~CloudDocs/Casa/Trabajo Arquitecto Técnico/Sistema Pericial/Backup"
ls -lh "$ICLOUD_BACKUPS"
```

Descomprime el ZIP en una carpeta temporal:

```bash
mkdir -p /tmp/sistema_pericial_restore
unzip "$ICLOUD_BACKUPS/backup_sistema_pericial_YYYYMMDD_HHMMSS.zip" -d /tmp/sistema_pericial_restore
```

Copia los datos restaurados al proyecto:

```bash
mkdir -p data uploads informes fotos logs

cp "/tmp/sistema_pericial_restore/data/pericial.db" "data/pericial.db"
rsync -a "/tmp/sistema_pericial_restore/uploads/" "uploads/"
rsync -a "/tmp/sistema_pericial_restore/informes/" "informes/"
rsync -a "/tmp/sistema_pericial_restore/fotos/" "fotos/"
```

Si el backup contiene `logs/` y quieres conservarlos:

```bash
rsync -a "/tmp/sistema_pericial_restore/logs/" "logs/"
```

Usa siempre comillas en rutas de iCloud porque contienen espacios.

## 6. Arrancar La App

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## 7. Verificaciones Tras Restaurar

- Abrir login/app.
- Revisar expedientes.
- Revisar facturas.
- Revisar adjuntos y fotos.
- Crear backup manual:

```bash
./backup_now.sh
```

- Confirmar que aparece un ZIP nuevo en iCloud:

```bash
ls -lh "$ICLOUD_BACKUPS"
```

## 8. Problemas Frecuentes

### Falta FastAPI

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### No Aparece La Base De Datos

Revisar que existe:

```bash
ls -lh data/pericial.db
```

También revisar `DB_PATH` en `.env`.

### No Aparecen Imágenes O Adjuntos

Revisar:

```bash
ls -lh uploads
ls -lh fotos
```

Restaurar de nuevo esas carpetas desde el ZIP si están vacías.

### Ruta iCloud Con Espacios

Usar siempre comillas:

```bash
ls -lh "/Users/carlosblanco/Library/Mobile Documents/com~apple~CloudDocs/Casa/Trabajo Arquitecto Técnico/Sistema Pericial/Backup"
```

### Permisos De Scripts

```bash
chmod +x backup_now.sh
chmod +x backup.sh
```

## 9. Nota De Seguridad

- No subir `.env`.
- No subir backups.
- No subir `data/pericial.db`.
- No subir `uploads/`, `informes/`, `fotos/`, `logs/` ni `exports/`.
- Guardar secretos, tokens y `SESSION_SECRET_KEY` en un lugar seguro.
- Verificar que `.gitignore` sigue cubriendo datos y archivos generados.
