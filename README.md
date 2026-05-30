# ultrifire-images

Aplicación mínima en Flask para Railway que sirve imágenes grandes (`QCOW2`, `ISO`, `OVA`, `VHD`, etc.) desde un volumen persistente montado en `/data`.

## Características

- Python 3.12, Flask y Gunicorn.
- Fija Python 3.12 mediante `.python-version`.
- Preparada para Railway con `Procfile` y `railway.json`.
- No usa base de datos ni autenticación.
- Crea automáticamente `/data/images` al iniciar si no existe.
- Lista archivos disponibles en el volumen persistente.
- Descarga archivos grandes mediante streaming, sin cargar el archivo completo en memoria.
- Envía cabeceras `Content-Length`, `Content-Type` y `Accept-Ranges`.
- Compatible con proxy reverso de Railway mediante `ProxyFix`.
- Logs básicos de estado, listado y descargas.

## Estructura del volumen

Railway debe montar el volumen persistente en:

```text
/data
```

Las imágenes deben copiarse o subirse a:

```text
/data/images
```

Ejemplo:

```text
/data/images/UltriFire-0.1.qcow2
```

## Endpoints

### `GET /`

Respuesta:

```json
{
  "service": "UltriFire Image Server",
  "status": "online"
}
```

### `GET /health`

Respuesta:

```json
{
  "status": "healthy"
}
```

### `GET /images`

Lista todos los archivos presentes en `/data/images`:

```json
{
  "files": [
    {
      "name": "UltriFire-0.1.qcow2",
      "size_bytes": 123456
    }
  ]
}
```

### `GET /images/<filename>`

Descarga directa del archivo por URL pública:

```text
https://ultrifire-images.up.railway.app/images/UltriFire-0.1.qcow2
```

La respuesta incluye:

- `Content-Length`
- `Content-Type`
- `Accept-Ranges: bytes`

## Desarrollo local

Requisitos:

- Python 3.12
- `pip`

Instalación:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear una carpeta local de imágenes para pruebas:

```bash
mkdir -p /tmp/ultrifire-images
cp UltriFire-0.1.qcow2 /tmp/ultrifire-images/
```

Ejecutar con Flask:

```bash
IMAGE_DIR=/tmp/ultrifire-images PORT=8080 python app.py
```

Ejecutar como producción local con Gunicorn:

```bash
IMAGE_DIR=/tmp/ultrifire-images PORT=8080 gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 0 --access-logfile - --error-logfile -
```

Probar endpoints:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/images
curl -I http://localhost:8080/images/UltriFire-0.1.qcow2
```

## Despliegue en Railway

1. Crear un nuevo proyecto en Railway y conectar este repositorio.
2. Agregar un volumen persistente al servicio.
3. Montar el volumen en `/data`.
4. Confirmar que Railway detecte Python/Nixpacks. El proyecto incluye `requirements.txt`, `Procfile` y `railway.json`.
5. Definir la variable `PORT` solo si Railway no la inyecta automáticamente. Railway normalmente la define por el entorno.
6. Desplegar el servicio.
7. Subir las imágenes al volumen en `/data/images`.
8. Verificar el estado:

```bash
curl https://ultrifire-images.up.railway.app/health
```

9. Verificar la descarga:

```bash
curl -I https://ultrifire-images.up.railway.app/images/UltriFire-0.1.qcow2
```

## Configuración

Variables opcionales:

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `IMAGE_DIR` | `/data/images` | Carpeta donde se almacenan las imágenes. Útil para pruebas locales. |
| `LOG_LEVEL` | `INFO` | Nivel de logs de la aplicación. |
| `PORT` | `8080` | Puerto usado al ejecutar `python app.py`. En Railway lo inyecta la plataforma. |

## Notas de producción

- Gunicorn se ejecuta con `--timeout 0` para evitar cortar descargas grandes de larga duración.
- Las descargas usan `send_file(..., conditional=True)`, que entrega el archivo como stream y permite soporte de peticiones condicionales/rango del servidor WSGI.
- No hay autenticación por diseño: cualquier persona con la URL pública puede listar y descargar archivos.
