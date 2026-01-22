"""
PipeFlow Pro API - Motor de Cálculo Hidráulico Industrial
Version: 2.0.0
Author: Antony Picon

Endpoints:
    POST /calcular - Ejecutar simulación hidráulica
    GET /health - Health check para monitoreo
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

import CoolProp.CoolProp as CP
import fluids

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pipeflow")

# Constantes de validación física
LIMITS = {
    "presion": {"min": 1e3, "max": 1e9, "unit": "Pa"},           # 0.01 bar - 10,000 bar
    "temperatura": {"min": 100, "max": 1000, "unit": "K"},        # -173°C - 727°C
    "diametro": {"min": 0.001, "max": 10, "unit": "m"},           # 1mm - 10m
    "velocidad": {"min": 0, "max": 100, "unit": "m/s"},           # 0 - 100 m/s
    "longitud": {"min": 0.1, "max": 100000, "unit": "m"},         # 10cm - 100km
    "k_accesorios": {"min": 0, "max": 1000, "unit": "-"}          # Sin límite práctico
}

FLUIDOS_SOPORTADOS = ["Methane", "Water", "Ethane", "Hydrogen", "Nitrogen", "CarbonDioxide", "Propane"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para startup y shutdown."""
    logger.info("🚀 PipeFlow Pro API iniciando...")
    logger.info(f"   Fluidos soportados: {', '.join(FLUIDOS_SOPORTADOS)}")
    yield
    logger.info("👋 PipeFlow Pro API cerrando...")


# Configuración de la aplicación
app = FastAPI(
    title="PipeFlow Pro API",
    description="""
## Motor de Cálculo Hidráulico Industrial

Calcula pérdidas de presión en sistemas de tuberías utilizando:
- **CoolProp**: Propiedades termofísicas reales
- **Fluids**: Cálculos de mecánica de fluidos
- **Darcy-Weisbach**: Ecuación extendida

### Fórmulas

**Número de Reynolds:**
```
Re = (ρ × v × D) / μ
```

**Caída de Presión:**
```
ΔP = [f × (L/D) + ΣK] × (ρ × v²/2)
```
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)

logger.info(f"   CORS configurado para: {allowed_origins}")


# ============================================================================
# ESQUEMAS DE VALIDACIÓN
# ============================================================================

class DatosEntrada(BaseModel):
    """Datos de entrada para la simulación hidráulica."""
    
    fluido: str = Field(
        ...,
        description="Nombre del fluido (código CoolProp)",
        json_schema_extra={"example": "Methane"}
    )
    presion: float = Field(
        ...,
        gt=0,
        description="Presión absoluta en Pascales",
        json_schema_extra={"example": 7000000}
    )
    temperatura: float = Field(
        ...,
        gt=0,
        description="Temperatura absoluta en Kelvin",
        json_schema_extra={"example": 298.15}
    )
    diametro: float = Field(
        ...,
        gt=0,
        description="Diámetro exterior de tubería en metros",
        json_schema_extra={"example": 0.12}
    )
    velocidad: float = Field(
        ...,
        ge=0,
        description="Velocidad de flujo en m/s",
        json_schema_extra={"example": 2.0}
    )
    longitud: float = Field(
        default=100.0,
        gt=0,
        description="Longitud de la tubería en metros",
        json_schema_extra={"example": 100.0}
    )
    k_accesorios: float = Field(
        default=0.0,
        ge=0,
        description="Suma de coeficientes K de accesorios",
        json_schema_extra={"example": 1.5}
    )

    @field_validator("fluido")
    @classmethod
    def validar_fluido(cls, v: str) -> str:
        if v not in FLUIDOS_SOPORTADOS:
            raise ValueError(
                f"Fluido '{v}' no soportado. Opciones: {', '.join(FLUIDOS_SOPORTADOS)}"
            )
        return v

    @field_validator("presion")
    @classmethod
    def validar_presion(cls, v: float) -> float:
        lim = LIMITS["presion"]
        if not lim["min"] <= v <= lim["max"]:
            raise ValueError(
                f"Presión fuera de rango válido ({lim['min']:.0e} - {lim['max']:.0e} {lim['unit']})"
            )
        return v

    @field_validator("temperatura")
    @classmethod
    def validar_temperatura(cls, v: float) -> float:
        lim = LIMITS["temperatura"]
        if not lim["min"] <= v <= lim["max"]:
            raise ValueError(
                f"Temperatura fuera de rango válido ({lim['min']} - {lim['max']} {lim['unit']})"
            )
        return v

    @field_validator("diametro")
    @classmethod
    def validar_diametro(cls, v: float) -> float:
        lim = LIMITS["diametro"]
        if not lim["min"] <= v <= lim["max"]:
            raise ValueError(
                f"Diámetro fuera de rango válido ({lim['min']} - {lim['max']} {lim['unit']})"
            )
        return v

    @field_validator("velocidad")
    @classmethod
    def validar_velocidad(cls, v: float) -> float:
        lim = LIMITS["velocidad"]
        if not lim["min"] <= v <= lim["max"]:
            raise ValueError(
                f"Velocidad fuera de rango válido ({lim['min']} - {lim['max']} {lim['unit']})"
            )
        return v
    
    @field_validator("longitud")
    @classmethod
    def validar_longitud(cls, v: float) -> float:
        lim = LIMITS["longitud"]
        if not lim["min"] <= v <= lim["max"]:
            raise ValueError(
                f"Longitud fuera de rango válido ({lim['min']} - {lim['max']} {lim['unit']})"
            )
        return v


class ResultadoCalculo(BaseModel):
    """Resultado de la simulación hidráulica."""
    
    delta_p: float = Field(..., description="Caída de presión total (Pa)")
    reynolds: int = Field(..., description="Número de Reynolds")
    factor_f: float = Field(..., description="Factor de fricción de Darcy")
    densidad: float = Field(..., description="Densidad del fluido (kg/m³)")
    viscosidad: float = Field(..., description="Viscosidad dinámica (Pa·s)")
    diametro_interno: float = Field(..., description="Diámetro interno calculado (m)")
    regimen: str = Field(..., description="Régimen de flujo")
    advertencias: list[str] = Field(default=[], description="Advertencias de diseño")


class HealthResponse(BaseModel):
    """Respuesta del health check."""
    
    status: str
    version: str
    fluidos_disponibles: list[str]


# ============================================================================
# MOTOR DE CÁLCULO
# ============================================================================

class MotorHidraulico:
    """Motor de cálculo hidráulico con CoolProp y Fluids."""
    
    def __init__(
        self,
        d_ext: float,
        espesor: float = 0.005,
        longitud: float = 100,
        rugosidad: float = 4.5e-5
    ):
        self.espesor = espesor
        self.L = longitud
        self.rugosidad = rugosidad  # Acero comercial estándar (m)
        self.d_int = d_ext - (2 * self.espesor)
        
        if self.d_int <= 0:
            raise ValueError(
                f"Diámetro interno inválido ({self.d_int:.4f}m). "
                f"El espesor de pared ({espesor}m) es mayor que el radio."
            )

    def calcular_resultados(
        self,
        fluido: str,
        P: float,
        T: float,
        v: float,
        k_total: float
    ) -> ResultadoCalculo:
        """
        Ejecuta el cálculo hidráulico completo.
        
        Args:
            fluido: Nombre del fluido (código CoolProp)
            P: Presión absoluta (Pa)
            T: Temperatura absoluta (K)
            v: Velocidad de flujo (m/s)
            k_total: Suma de coeficientes K de accesorios
            
        Returns:
            ResultadoCalculo con todos los parámetros calculados
        """
        advertencias = []
        
        # A. Obtención de propiedades termofísicas reales
        try:
            rho = CP.PropsSI('D', 'P', P, 'T', T, fluido)  # Densidad (kg/m³)
            mu = CP.PropsSI('V', 'P', P, 'T', T, fluido)   # Viscosidad dinámica (Pa·s)
        except Exception as e:
            logger.error(f"Error CoolProp: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error al obtener propiedades del fluido '{fluido}': {str(e)}. "
                       f"Verifique que la combinación presión-temperatura sea válida."
            )

        # B. Cálculo del Número de Reynolds
        if v == 0:
            # Flujo estático
            return ResultadoCalculo(
                delta_p=0.0,
                reynolds=0,
                factor_f=0.0,
                densidad=round(rho, 4),
                viscosidad=mu,
                diametro_interno=round(self.d_int, 4),
                regimen="Estático",
                advertencias=["Velocidad cero: sin flujo"]
            )

        re = fluids.core.Reynolds(V=v, D=self.d_int, rho=rho, mu=mu)
        
        # Determinar régimen de flujo
        if re < 2300:
            regimen = "Laminar"
        elif re < 4000:
            regimen = "Transición"
            advertencias.append("Flujo en zona de transición crítica. Resultados pueden ser inestables.")
        else:
            regimen = "Turbulento"

        # C. Cálculo del Factor de Fricción
        try:
            f = fluids.friction.friction_factor(Re=re, eD=self.rugosidad / self.d_int)
        except Exception as e:
            logger.error(f"Error calculando fricción: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al calcular factor de fricción: {str(e)}"
            )

        # D. Cálculo de Caída de Presión (Darcy-Weisbach Extendida)
        factor_tuberia = f * (self.L / self.d_int)
        termino_energia = (rho * v**2) / 2
        delta_p = (factor_tuberia + k_total) * termino_energia

        # E. Verificaciones de diseño
        if v > 25:
            advertencias.append("Velocidad excesiva (>25 m/s). Riesgo de erosión y ruido.")
        elif v > 15:
            advertencias.append("Velocidad alta (>15 m/s). Considerar diseño antierosión.")

        return ResultadoCalculo(
            delta_p=round(delta_p, 2),
            reynolds=int(re),
            factor_f=round(float(f), 6),
            densidad=round(rho, 4),
            viscosidad=mu,
            diametro_interno=round(self.d_int, 4),
            regimen=regimen,
            advertencias=advertencias
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """
    Endpoint de health check para monitoreo.
    
    Retorna el estado del servicio y los fluidos disponibles.
    """
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        fluidos_disponibles=FLUIDOS_SOPORTADOS
    )


@app.post(
    "/calcular",
    response_model=ResultadoCalculo,
    tags=["Cálculos"],
    summary="Ejecutar simulación hidráulica",
    responses={
        200: {"description": "Cálculo exitoso"},
        422: {"description": "Datos de entrada inválidos o fuera de rango físico"},
        500: {"description": "Error interno del motor de cálculo"}
    }
)
async def ejecutar_simulacion(datos: DatosEntrada):
    """
    Recibe los datos del sistema y devuelve el análisis hidráulico detallado.
    
    ## Parámetros de Entrada
    
    - **fluido**: Código CoolProp del fluido (Methane, Water, Ethane, Hydrogen, etc.)
    - **presion**: Presión absoluta en Pascales
    - **temperatura**: Temperatura absoluta en Kelvin
    - **diametro**: Diámetro exterior de la tubería en metros
    - **velocidad**: Velocidad del flujo en m/s
    - **longitud**: Longitud de la tubería en metros
    - **k_accesorios**: Suma de coeficientes K de todos los accesorios
    
    ## Resultados
    
    - **delta_p**: Caída de presión total (Pa)
    - **reynolds**: Número de Reynolds
    - **factor_f**: Factor de fricción de Darcy
    - **densidad**: Densidad real del fluido (kg/m³)
    - **regimen**: Tipo de flujo (Laminar/Transición/Turbulento)
    - **advertencias**: Alertas de diseño si aplican
    """
    logger.info(f"📊 Calculando: {datos.fluido} @ {datos.presion/1e5:.1f} bar, {datos.temperatura-273.15:.1f}°C")
    
    try:
        motor = MotorHidraulico(d_ext=datos.diametro, longitud=datos.longitud)
        
        resultado = motor.calcular_resultados(
            fluido=datos.fluido,
            P=datos.presion,
            T=datos.temperatura,
            v=datos.velocidad,
            k_total=datos.k_accesorios
        )
        
        logger.info(f"✅ Resultado: ΔP={resultado.delta_p:.2f} Pa, Re={resultado.reynolds}")
        return resultado
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"⚠️ Validación fallida: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


# Para ejecutar: uvicorn main:app --reload --host 0.0.0.0 --port 8000