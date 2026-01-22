# ⚙️ PipeFlow Pro

**Motor de cálculo hidráulico industrial** para simulación de pérdidas de presión en sistemas de tuberías.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Descripción

PipeFlow Pro es una aplicación web que calcula la caída de presión en sistemas de tuberías utilizando:

- **CoolProp**: Propiedades termofísicas reales de fluidos
- **Fluids**: Cálculos de mecánica de fluidos (Reynolds, fricción)
- **Darcy-Weisbach**: Ecuación extendida para pérdidas
- **Visualización SVG**: Diagrama interactivo del sistema de tuberías

### Fórmulas Utilizadas

**Número de Reynolds:**
```
Re = (ρ × v × D) / μ
```

**Caída de Presión (Darcy-Weisbach Extendida):**
```
ΔP = [f × (L/D) + ΣK] × (ρ × v²/2)
```

Donde:
- `f` = Factor de fricción (Colebrook-White)
- `L` = Longitud de tubería (100m por defecto)
- `D` = Diámetro interno
- `ΣK` = Suma de coeficientes de accesorios
- `ρ` = Densidad del fluido
- `v` = Velocidad de flujo

## ✨ Características

- **Cálculo en tiempo real** con propiedades termofísicas precisas
- **Gestión de Accesorios** mediante lista detallada
- **Validación de rangos físicos** (presión, temperatura, velocidad)
- **Alertas de diseño** para condiciones críticas
- **Interfaz moderna** con tema oscuro profesional
- **API REST** con documentación Swagger/OpenAPI

## 🚀 Instalación

### Requisitos
- Python 3.9 o superior
- pip (gestor de paquetes)

### Pasos

1. **Clonar o descargar el proyecto**

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate  # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno** (opcional)
   ```bash
   cp .env.example .env
   # Editar .env según necesidades
   ```

## 🖥️ Uso

### Iniciar el servidor backend
```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://127.0.0.1:8000`

### Iniciar servidor frontend (recomendado)
```bash
python -m http.server 3000
```

Luego abrir `http://localhost:3000/index.html` en el navegador.

### Verificar estado del servidor
```bash
curl http://127.0.0.1:8000/health
```

## 📡 API Reference

### POST `/calcular`

Ejecuta la simulación hidráulica.

**Request Body:**
```json
{
  "fluido": "Methane",
  "presion": 7000000,
  "temperatura": 298.15,
  "diametro": 0.12,
  "velocidad": 2.0,
  "k_accesorios": 1.5
}
```

**Response:**
```json
{
  "delta_p": 12345.67,
  "reynolds": 150000,
  "factor_f": 0.0234,
  "densidad": 48.52,
  "viscosidad": 0.000012,
  "diametro_interno": 0.11,
  "regimen": "Turbulento",
  "advertencias": []
}
```

### GET `/health`

Endpoint de health check para monitoreo.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "fluidos_disponibles": ["Methane", "Water", "Ethane", "Hydrogen", "Nitrogen", "CarbonDioxide", "Propane"]
}
```

### GET `/docs`

Documentación interactiva Swagger UI.

### GET `/redoc`

Documentación alternativa ReDoc.

## 🔧 Fluidos Soportados

| Fluido | Código CoolProp | Aplicación Típica |
|--------|-----------------|-------------------|
| Gas Natural | `Methane` | Gasoductos |
| Agua | `Water` | Inyección, servicios |
| Etano | `Ethane` | Procesamiento gas |
| Hidrógeno | `Hydrogen` | Energía limpia |
| Nitrógeno | `Nitrogen` | Inertización |
| CO₂ | `CarbonDioxide` | Captura de carbono |
| Propano | `Propane` | GLP |

## 📊 Accesorios (K-Factors)

Basados en Crane TP-410:

| Accesorio | K |
|-----------|---|
| Codo 90° Estándar | 0.9 |
| Codo 45° Estándar | 0.4 |
| Codo 90° Radio Largo | 0.6 |
| Tee (Flujo Directo) | 0.3 |
| Tee (Flujo por Rama) | 1.5 |
| Válvula Globo | 10.0 |
| Válvula Compuerta | 0.17 |
| Válvula Retención | 2.5 |
| Válvula Bola | 0.05 |
| Válvula Mariposa | 0.35 |
| Entrada de Tanque | 0.5 |
| Salida de Tanque | 1.0 |
| Reducción Gradual | 0.15 |
| Expansión Gradual | 0.30 |

## ⚠️ Consideraciones de Diseño

- **Velocidad > 25 m/s**: Riesgo de erosión y ruido (alerta crítica)
- **Velocidad > 15 m/s**: Considerar diseño antierosión (advertencia)
- **Reynolds 2300-4000**: Zona de transición (resultados inestables)
- **Rugosidad**: 4.5×10⁻⁵ m (acero comercial por defecto)
- **Espesor de pared**: 5mm por defecto

## 🗂️ Estructura del Proyecto

```
medidor de presion/
├── index.html        # Frontend - Interfaz de usuario
├── script.js         # Lógica del frontend
├── style.css         # Estilos con sistema de diseño
├── main.py           # Backend FastAPI
├── requirements.txt  # Dependencias Python
├── .env.example      # Template de configuración
├── README.md         # Esta documentación
└── venv/             # Entorno virtual (generado)
```

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 👤 Autor

**Antony Picon**

## 👥 Contribuir

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcion`)
3. Commit cambios (`git commit -am 'Agregar nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Crear Pull Request

## 🛣️ Roadmap

- [ ] Re-implementación de visualización (Diagrama/Editor)
- [ ] Exportar informes PDF
- [ ] Guardar/cargar configuraciones
- [ ] Soporte para sistemas en paralelo
