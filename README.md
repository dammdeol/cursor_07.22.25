# Catálogo de Productos Ralph Wilson

Una aplicación web que permite scraping y navegación de productos desde ralphwilson.com.mx.

## Características

- **Web Scraping**: Extrae automáticamente productos desde ralphwilson.com.mx
- **Base de Datos**: Almacena productos en SQLite con modelos estructurados
- **Interfaz Web**: Navegación intuitiva con filtros avanzados
- **Búsqueda**: Sistema de búsqueda con sugerencias en tiempo real
- **Administración**: Panel de control para gestionar el scraping
- **Responsive**: Diseño adaptable para móviles y desktop

## Tecnologías

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Scraping**: Selenium, BeautifulSoup4, Requests
- **Base de Datos**: SQLite (configurable para PostgreSQL/MySQL)

## Instalación

1. **Clonar/Descargar el proyecto**
```bash
cd /path/to/project
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno (opcional)**
```bash
export SECRET_KEY="tu-clave-secreta"
export DATABASE_URL="sqlite:///products.db"
```

4. **Ejecutar la aplicación**
```bash
python app.py
```

5. **Acceder a la aplicación**
- Aplicación principal: http://localhost:5000
- Panel de administración: http://localhost:5000/admin

## Uso

### 1. Iniciar Scraping
1. Ve al panel de administración: `/admin`
2. Haz clic en "Iniciar Scraping"
3. Espera a que el proceso complete

### 2. Navegación
- **Inicio**: Vista general con estadísticas y productos recientes
- **Productos**: Lista completa con filtros avanzados
- **Categorías**: Navegación por categorías de productos
- **Detalle**: Información completa de cada producto

### 3. Búsqueda
- Usa la barra de búsqueda en el header
- Obtén sugerencias en tiempo real
- Filtra por categoría, tipo de superficie, etc.

## Estructura del Proyecto

```
.
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── scraper.py             # Lógica de web scraping
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── products.html
│   ├── product_detail.html
│   ├── categories.html
│   ├── admin.html
│   ├── 404.html
│   └── 500.html
└── static/              # Archivos estáticos
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── images/
        └── products/    # Imágenes descargadas
```

## API Endpoints

- `GET /` - Página principal
- `GET /products` - Lista de productos con filtros
- `GET /product/<id>` - Detalle de producto
- `GET /categories` - Categorías disponibles
- `GET /admin` - Panel de administración
- `POST /admin/scrape` - Iniciar scraping
- `POST /admin/clear-data` - Limpiar datos
- `GET /api/products` - API JSON de productos
- `GET /api/search` - API de búsqueda

## Configuración

### Base de Datos
Por defecto usa SQLite. Para usar PostgreSQL o MySQL:

```python
# PostgreSQL
DATABASE_URL = "postgresql://user:password@localhost/dbname"

# MySQL
DATABASE_URL = "mysql://user:password@localhost/dbname"
```

### Variables de Entorno
- `SECRET_KEY`: Clave secreta para Flask
- `DATABASE_URL`: URL de conexión a la base de datos

## Desarrollo

### Agregar nuevas categorías
Edita el array `category_keywords` en `scraper.py`:

```python
category_keywords = [
    'laminados', 'cuarzo', 'superficie-solida', 
    'nueva-categoria'  # Agregar aquí
]
```

### Personalizar scraping
Modifica los selectores en `scraper.py` según los cambios del sitio web.

## Troubleshooting

### Error de ChromeDriver
```bash
# El scraper instala automáticamente ChromeDriver
# Si hay problemas, instala manualmente:
pip install webdriver-manager
```

### Error de permisos
```bash
chmod +x app.py
```

### Error de dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## Licencia

Este proyecto es para fines educativos y de demostración.

## Contacto

Para preguntas o soporte, por favor abre un issue en el repositorio.
