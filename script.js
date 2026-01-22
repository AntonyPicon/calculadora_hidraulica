/**
 * PipeFlow Pro - Frontend Controller
 * Version: 2.0.0
 * Author: Antony Picon
 * 
 * Motor de interfaz para simulación hidráulica industrial
 */

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const CONFIG = {
    API_URL: 'http://127.0.0.1:8000',
    REQUEST_TIMEOUT: 30000,  // 30 segundos
    DECIMAL_PLACES: {
        presion: 2,
        temperatura: 2,
        velocidad: 3,
        factor_f: 6
    }
};

// Catálogo de accesorios basado en Crane TP-410
const CATALOGO_K = {
    "codo_90": { nombre: "Codo 90° Estándar", k: 0.9 },
    "codo_45": { nombre: "Codo 45° Estándar", k: 0.4 },
    "codo_90_largo": { nombre: "Codo 90° Radio Largo", k: 0.6 },
    "tee_flujo": { nombre: "Tee (Flujo Directo)", k: 0.3 },
    "tee_rama": { nombre: "Tee (Flujo por Rama)", k: 1.5 },
    "val_globo": { nombre: "Válvula Globo (Full)", k: 10.0 },
    "val_compuerta": { nombre: "Válvula Compuerta", k: 0.17 },
    "val_cheque": { nombre: "Válvula Retención", k: 2.5 },
    "val_bola": { nombre: "Válvula Bola", k: 0.05 },
    "val_mariposa": { nombre: "Válvula Mariposa", k: 0.35 },
    "entrada_tanque": { nombre: "Entrada de Tanque", k: 0.5 },
    "salida_tanque": { nombre: "Salida de Tanque", k: 1.0 },
    "reduccion": { nombre: "Reducción Gradual", k: 0.15 },
    "expansion": { nombre: "Expansión Gradual", k: 0.30 }
};

// ============================================================================
// ESTADO DE LA APLICACIÓN
// ============================================================================

const AppState = {
    isCalculating: false,
    serverOnline: null,
    lastResult: null
};


// ============================================================================
// UTILIDADES
// ============================================================================

/**
 * Formatea un número con separadores de miles y decimales apropiados
 */
function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    return Number(value).toLocaleString('es-ES', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Muestra un toast de notificación
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Animación de entrada
    requestAnimationFrame(() => toast.classList.add('show'));

    // Auto-remover después de 5 segundos
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}

/**
 * Actualiza el indicador de estado del servidor
 */
function updateServerStatus(online) {
    AppState.serverOnline = online;
    const indicator = document.getElementById('server-status');
    if (indicator) {
        indicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
        indicator.title = online ? 'Servidor conectado' : 'Servidor desconectado';
    }
}


// ============================================================================
// VALIDACIÓN DE INPUTS
// ============================================================================

const VALIDACION = {
    presion: { min: 0.01, max: 10000, nombre: 'Presión', unidad: 'bar' },
    temp: { min: -200, max: 500, nombre: 'Temperatura', unidad: '°C' },
    diametro: { min: 0.001, max: 10, nombre: 'Diámetro', unidad: 'm' },
    velocidad: { min: 0, max: 100, nombre: 'Velocidad', unidad: 'm/s' },
    longitud: { min: 0.1, max: 100000, nombre: 'Longitud', unidad: 'm' }
};

/**
 * Valida todos los inputs del formulario
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validarInputs() {
    const errors = [];

    for (const [id, config] of Object.entries(VALIDACION)) {
        const input = document.getElementById(id);
        const value = parseFloat(input?.value);

        if (isNaN(value)) {
            errors.push(`${config.nombre} debe ser un número válido`);
            input?.classList.add('input-error');
        } else if (value < config.min || value > config.max) {
            errors.push(`${config.nombre} debe estar entre ${config.min} y ${config.max} ${config.unidad}`);
            input?.classList.add('input-error');
        } else {
            input?.classList.remove('input-error');
        }
    }

    return { valid: errors.length === 0, errors };
}

/**
 * Limpia los errores de validación visual
 */
function limpiarErroresValidacion() {
    document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
}


// ============================================================================
// GESTIÓN DE ACCESORIOS
// ============================================================================

/**
 * Agrega una fila de accesorio al formulario
 */
function agregarFilaAccesorio() {
    const contenedor = document.getElementById('contenedor-accesorios');
    const id = Date.now();
    const div = document.createElement('div');
    div.className = 'accesorio-row';
    div.id = `fila-${id}`;

    const opciones = Object.entries(CATALOGO_K)
        .map(([key, data]) =>
            `<option value="${data.k}" data-key="${key}">${data.nombre} (K=${data.k})</option>`
        ).join('');

    div.innerHTML = `
        <div class="accesorio-select-wrapper">
            <select class="select-k" onchange="actualizarAccesorios()">
                ${opciones}
            </select>
        </div>
        <div class="accesorio-cantidad-wrapper">
            <input type="number" 
                   class="input-cantidad" 
                   value="1" 
                   min="1" 
                   max="100"
                   onchange="actualizarAccesorios()"
                   aria-label="Cantidad">
        </div>
        <button type="button" 
                class="btn-remove" 
                onclick="removerAccesorio('${id}')"
                aria-label="Eliminar accesorio">
            ✕
        </button>
    `;

    contenedor.appendChild(div);

    // Animación de entrada
    requestAnimationFrame(() => div.classList.add('fade-in'));

    actualizarAccesorios();
}

/**
 * Remueve una fila de accesorio
 */
function removerAccesorio(id) {
    const fila = document.getElementById(`fila-${id}`);
    if (fila) {
        fila.classList.add('fade-out');
        setTimeout(() => {
            fila.remove();
            actualizarAccesorios();
        }, 200);
    }
}

/**
 * Actualiza K total y regenera el diagrama
 */
function actualizarAccesorios() {
    actualizarKTotal();

    // generarDiagrama(); // Legacy

}

/**
 * Calcula y actualiza el K total de accesorios
 */
function actualizarKTotal() {
    let kTotal = 0;

    document.querySelectorAll('.accesorio-row').forEach(row => {
        const k = parseFloat(row.querySelector('.select-k')?.value) || 0;
        const cant = parseInt(row.querySelector('.input-cantidad')?.value) || 0;
        kTotal += k * cant;
    });

    const display = document.getElementById('res_k');
    if (display) {
        display.innerText = formatNumber(kTotal, 2);
    }

    return kTotal;
}


// ============================================================================
// COMUNICACIÓN CON EL BACKEND
// ============================================================================

/**
 * Verifica el estado del servidor
 */
async function verificarServidor() {
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${CONFIG.API_URL}/health`, {
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (response.ok) {
            const data = await response.json();
            updateServerStatus(true);
            console.log('🟢 Servidor online:', data);
            return true;
        }
    } catch (error) {
        updateServerStatus(false);
        console.warn('🔴 Servidor offline');
    }
    return false;
}

/**
 * Envía los datos al backend y procesa la respuesta
 */
async function enviarDatos() {
    // Prevenir envíos duplicados
    if (AppState.isCalculating) {
        showToast('Cálculo en progreso, espere...', 'info');
        return;
    }

    // Validación de inputs
    limpiarErroresValidacion();
    const validacion = validarInputs();

    if (!validacion.valid) {
        validacion.errors.forEach(err => showToast(err, 'error'));
        return;
    }

    // Preparar UI para cálculo
    AppState.isCalculating = true;
    const btn = document.getElementById('btn-calcular');
    const loading = document.getElementById('loading');
    const alertBox = document.getElementById('design-alert');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> CALCULANDO...';
    loading.classList.remove('hidden');
    alertBox.classList.add('hidden');

    // Preparar datos con conversiones de unidades
    const datos = {
        fluido: document.getElementById('fluido').value,
        presion: parseFloat(document.getElementById('presion').value) * 100000,  // bar -> Pa
        temperatura: parseFloat(document.getElementById('temp').value) + 273.15, // °C -> K
        diametro: parseFloat(document.getElementById('diametro').value),
        velocidad: parseFloat(document.getElementById('velocidad').value),
        longitud: parseFloat(document.getElementById('longitud').value),
        k_accesorios: actualizarKTotal()
    };

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);

        const response = await fetch(`${CONFIG.API_URL}/calcular`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Error del servidor (${response.status})`);
        }

        const res = await response.json();
        AppState.lastResult = res;

        // Renderizar resultados con animación
        renderizarResultados(res);

        // Mostrar advertencias si existen
        if (res.advertencias && res.advertencias.length > 0) {
            mostrarAdvertencias(res.advertencias, res.regimen);
        }

        updateServerStatus(true);
        showToast('Cálculo completado exitosamente', 'success');

    } catch (error) {
        console.error('Error en cálculo:', error);

        if (error.name === 'AbortError') {
            showToast('Tiempo de espera agotado. Verifique la conexión.', 'error');
        } else if (error.message.includes('Failed to fetch')) {
            showToast('No se puede conectar al servidor. ¿Está ejecutando el backend?', 'error');
            updateServerStatus(false);
        } else {
            showToast(error.message, 'error');
        }

    } finally {
        // Restaurar UI
        AppState.isCalculating = false;
        btn.disabled = false;
        btn.innerHTML = 'EJECUTAR CÁLCULO SISTEMA';
        loading.classList.add('hidden');
    }
}

/**
 * Renderiza los resultados en la UI
 */
function renderizarResultados(res) {
    const elementos = {
        'res_dp': { value: res.delta_p, decimals: 2 },
        'res_rho': { value: res.densidad, decimals: 4 },
        'res_re': { value: res.reynolds, decimals: 0 },
        'res_f': { value: res.factor_f, decimals: 6 },
        'res_regimen': { value: res.regimen, isText: true }
    };

    for (const [id, config] of Object.entries(elementos)) {
        const el = document.getElementById(id);
        if (el) {
            if (config.isText) {
                el.innerText = config.value || '--';
            } else {
                el.innerText = formatNumber(config.value, config.decimals);
            }
            // Animación de actualización
            el.classList.add('value-updated');
            setTimeout(() => el.classList.remove('value-updated'), 500);
        }
    }
}

/**
 * Muestra las advertencias de diseño
 */
function mostrarAdvertencias(advertencias, regimen) {
    const alertBox = document.getElementById('design-alert');
    if (!alertBox || advertencias.length === 0) return;

    const isCritical = advertencias.some(a =>
        a.includes('excesiva') || a.includes('erosión')
    );

    alertBox.innerHTML = advertencias.map(adv =>
        `<div class="alert-item">
            <strong>${isCritical ? '⚠️ Crítico:' : 'ℹ️ Aviso:'}</strong> ${adv}
        </div>`
    ).join('');

    alertBox.className = `alert ${isCritical ? 'critical' : ''}`;
    alertBox.classList.remove('hidden');
}


// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 PipeFlow Pro v2.0.0 iniciando...');

    // Verificar estado del servidor
    verificarServidor();

    // Verificar periódicamente (cada 30 segundos)
    setInterval(verificarServidor, 30000);


    // Inicializar lista vacía (se llenará con el editor)
    // agregarFilaAccesorio();


    // Configurar validación en tiempo real
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', () => {
            input.classList.remove('input-error');
        });
    });

    // Renderizar fórmulas LaTeX si KaTeX está disponible
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false }
            ]
        });
    }


    // El diagrama ahora es manejado por editor.js
    // generarDiagrama(); 


    console.log('✅ PipeFlow Pro listo');
});



// Exportar funciones para uso global
window.agregarFilaAccesorio = agregarFilaAccesorio;
window.removerAccesorio = removerAccesorio;
window.enviarDatos = enviarDatos;
window.actualizarKTotal = actualizarKTotal;
window.actualizarAccesorios = actualizarAccesorios;