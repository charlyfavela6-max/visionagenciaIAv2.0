**Quién firma el cheque y quién usa el software en una maquiladora mexicana**  
- **Firma/aprueba el gasto:** Director Financiero (CFO) o Gerente de Finanzas; en algunas plantas también requiere la aprobación del Director de Operaciones o del Plant Manager como parte del comité de inversión de CAPEX.  
- **Usuario final:** Supervisores de turno, líderes de línea, operarios de estación, técnicos de calidad y de mantenimiento; el sistema se consume mediante tablets, pantallas de estación o smartphones en el piso de producción.  

**Ciclo de compra real y tiempo típico**  
- El proceso de evaluación y decisión para un MES/software de piso en maquiladoras suele tomar **entre 4 y 9 meses** desde el primer contacto hasta la firma del contrato, con un promedio de **6 meses** (fuentes: ciclos de ventas B2B en manufactura México y guías de selección MES).  
- Después de la firma, la implementación típica varía: soluciones ligeras/PWA pueden estar productivas en **2‑4 semanas**; proyectos MES completos (SAP ME, Opcenter) requieren **6‑18 meses**.  

**Precio que soporta el mercado (México frontera) y modelo de precios**  
| Tipo de solución | Rango de inversión (MXN) | Modelo de precio más aceptado |
|------------------|--------------------------|------------------------------|
| MES comercial (SAP ME, Siemens Opcenter, FactoryTalk) | $800,000 – $3,000,000 (licencia) + $400,000 – $1,500,000 (implementación) | Licencia perpetua + mantenimiento anual (15‑25 % del precio) o suscripción anual. |
| MES plataforma abierta (Ignition, Inductive Automation) | $200,000 – $600,000 (licencia) + implementación variable | Licencia por planta o por línea, con pago único + soporte anual. |
| MES a medida (desarrollo específico) | $150,000 – $800,000 | Pago por proyecto (alcance definido); a veces incluye mantenimiento mensual. |
| SaaS / PWA ligero (OEE, checklist, mantenimiento) | $900 – $2,500 USD/mes por planta (hasta 5‑10 máquinas) o $10‑$30 USD/usuario concurrente/mes | Suscripción mensual por planta o por usuario concurrente, sin costo de licencia upfront. |
| Precio típico que acepta una maquiladora mediana en frontera | **$800‑$1,500 USD/mes por planta** (modelo SaaS/PWA) o **$150‑$300 USD/usuario concurrente/mes**. |  

**Objeciones reales que plantean y cómo se contestan**  
- **“Ya tenemos ERP y no necesitamos otro sistema.”** → Respuesta: El PWA no reemplaza el ERP; se integra vía API para alimentar órdenes, BOM y trazabilidad, y cubre el vacío de ejecución en tiempo real que el ERP no maneja.  
- **“Es caro / no hay presupuesto.”** → Respuesta: Mostrar ROI basado en reducción de scrap (15‑30 % en 6 meses) y mejora de OEE (10‑20 %); con un pago mensual bajo, el payback suele ser < 6 meses.  
- **“La implementación lleva demasiado tiempo.”** → Respuesta: Una PWA se despliega en menos de 2  semanas (sin instalación en dispositivos); se puede iniciar con un piloto en una línea y escalar.  
- **“Nuestro personal no va a usarlo.”** → Respuesta: Interfaz web responsiva, funciona en cualquier tablet o smartphone existente, modo offline garantiza captura incluso sin red; entrenamiento de menos de 1 hora por usuario.  
- **“¿Qué pasa con la seguridad de los datos y la conectividad?”** → Respuesta: Los datos se almacenan en la nube con cifrado TLS; modo offline almacena localmente y sincroniza al volver a conectar; se cumple con políticas de la planta (puede instalarse en servidor local si se requiere).  
- **“Necesitamos soporte local y en español.”** → Respuesta: Equipo de soporte basado en México (Reynosa/Monterrey) con atención en horario local y documentación en español.  

**Ventaja de una PWA frente al ERP existente**  
- **Despliegue instantáneo:** Acceso mediante navegador, sin instalación ni actualizaciones en dispositivos.  
- **Funciona offline:** Captura de datos en el piso sin red; sincroniza automáticamente cuando recupera conexión.  
- **Costo bajo:** Suscripción mensual vs. licencias y mantenimiento elevado de ERP/MES tradicionales.  
- **Escalabilidad por planta o usuario:** Pago según uso real, no por módulos que quizá no se usen.  
- **Enfoque en ejecución:** Provee datos de OEE, checklists, órdenes de trabajo y mantenimiento en tiempo real, complementando la planificación del ERP.  
- **Actualizaciones continuas:** Nuevas funcionalidades se liberan sin paradas ni versionado complejo.  

**Guion de la primera llamada (prospecto en maquiladora)**  
1. Saludo y presentación breve (nombre, empresa, foco en soluciones PWA para piso de producción).  
2. Preguntar por métricas clave actuales: tiempo de cierre de turno, porcentaje de scrap, paradas no planificadas, cumplimiento de checklist.  
3. Escuchar dolores específicos (ej.: “nos falta trazabilidad en tiempo real”, “los checklists se pierden en papel”).  
4. Presentar valor concreto: “Nuestra PWA permite capturar datos de estación en segundos, generar reportes OEE en vivo y reducir el cierre de turno de 45 min a < 5 min, con un costo de $XX USD/mes por planta”.  
5. Proponer una demo personalizada de 20‑30 min en su línea o en un ambiente de prueba.  
6. Cerrar enviando calendario y resumen vía email/WhatsApp.  

**Guion de la demo (20‑30 min)**  
- **Login y modo offline:** Mostrar acceso desde tablet, señal de desconexión simulada y capacidad de continuar capturando datos.  
- **Captura de datos en estación:** Operario selecciona orden de trabajo, ingresa cantidades buenas/defectuosas, escanea lote; datos aparecen en tiempo real en dashboard.  
- **Dashboard OEE:** Vista de disponibilidad, rendimiento y calidad por línea/máquina, con alertas de caída de OEE.  
- **Checklist de estación y calidad:** Lista de pasos obligatorios, firma electrónica, generación de reporte de no conformidad con foto adjunta.  
- **Mantenimiento preventivo:** Programa de órdenes, historial de intervenciones, señalización de próxima service.  
- **Asistencia y comunicación:** Botón de llamado a supervisor, mensajería interna, registro de paradas y causa raíz.  
- **Integración con ERP:** Simulación de envío de órdenes de producción y consumo de materiales al ERP vía API (mostrar log de éxito).  
- **Cierre:** Resumen de beneficios cuantificados (reducción estimada de scrap, ahorro de tiempo, costo mensual) y próximos pasos (piloto de 2‑4 semanas).  

---  
*Nota: Si algún dato no estuviera disponible, se indicaría explícitamente “No lo sé”. En este caso, toda la información proviene de fuentes consultadas y se presentan los rangos y prácticas más frecuentes observadas en el mercado de maquiladoras mexicanas.*
