# PG Machine — Guia del Usuario

## 1. Bienvenida

PG Machine es una plataforma de **gestion de oportunidades y actividades comerciales** para equipos de ventas. Permite organizar tus oportunidades (proyectos/deals), crear y dar seguimiento a actividades (emails, llamadas, reuniones, asignaciones), monitorear SLAs y colaborar con tu equipo.

### Como acceder

- **Web**: abre la URL de tu aplicacion (proporcionada por tu administrador) en cualquier navegador
- **Movil**: abre la misma URL desde el navegador de tu celular. La app se adapta automaticamente a pantallas pequenas

---

## 2. Registro e Inicio de Sesion

Al abrir PG Machine por primera vez, veras tres opciones:

### Iniciar Sesion

Si ya tienes cuenta, ingresa tu email y contrasena.

### Crear Equipo

Para crear un equipo nuevo:

1. Ingresa tu **nombre completo**
2. Ingresa tu **email**
3. Crea una **contrasena** (minimo 6 caracteres)
4. Ingresa el **nombre de tu equipo**
5. Haz clic en **"Crear Cuenta y Equipo"**

El primer usuario de un equipo recibe automaticamente el rol de **Admin**.

### Unirse a Equipo

Si tu administrador te compartio un ID de equipo:

1. Ingresa tu **nombre completo**
2. Ingresa tu **email**
3. Crea una **contrasena**
4. Ingresa el **ID del equipo** que te compartieron
5. Selecciona tu **rol** (consulta con tu admin cual elegir)
6. Haz clic en **"Unirse al Equipo"**

---

## 3. Tu Rol

PG Machine tiene 8 roles con diferentes niveles de acceso:

| Rol | Que puede ver | Panel de Control | Gestion de Equipo |
|-----|--------------|-----------------|-------------------|
| **Admin** | Todas las oportunidades | Si | Completa (miembros, equipos, config) |
| **VP** | Todas las oportunidades | Si | No |
| **Account Manager** | Sus oportunidades + asignadas | Si | No |
| **Regional Sales Manager** | Sus oportunidades + asignadas | Si | No |
| **Partner Manager** | Sus oportunidades + asignadas | Si | No |
| **Regional Partner Manager** | Sus oportunidades + asignadas | Si | No |
| **Presales Manager** | Sus oportunidades + asignadas | Si | No |
| **Presales** | Sus oportunidades + asignadas | No | No |

**"Sus oportunidades + asignadas"** significa: las oportunidades que tu creaste, mas aquellas donde tienes actividades asignadas.

---

## 4. Tablero

Es la vista principal al entrar. Muestra tus oportunidades organizadas como **tarjetas (scorecards)**.

### Barra de usuario

En la parte superior veras tu nombre, iniciales y rol.

### Botones de categoria

Arriba de las tarjetas hay un boton por cada categoria (ej. LEADS, OFFICIAL, GTM) que muestra el total ACV de cada una:

- **Clic en una categoria**: filtra para ver solo esa categoria
- **Clic en "Ver todas"**: vuelve a mostrar todas las categorias

### Toggle PROTECT / Growth

Activa **"Solo Growth"** para ocultar oportunidades de tipo Renewal/PROTECT y enfocarte en crecimiento.

### Filtro por trimestre

Filtra oportunidades por trimestre fiscal basado en su fecha de cierre:

- **Todas**: sin filtro
- **Prox. 4 Quarters**: las que cierran en los proximos 4 trimestres
- **Q actual**: solo el trimestre actual
- **Q actual + 1 / + 2**: trimestres futuros

### Tarjetas de oportunidad

Cada tarjeta muestra:

- **Nombre del proyecto** (texto grande)
- **Stage** (badge violeta, si tiene)
- **Monto ACV** en USD (verde, alineado a la derecha)
- **ID de oportunidad** (codigo gris, si tiene)
- **Fecha de cierre** (badge rojo, si tiene)
- **Partner** (badge celeste, si tiene)
- **Actividades**: debajo de una linea punteada, cada actividad muestra su semaforo, asignado, destinatario, objetivo y estado

**Acciones en las tarjetas:**

- **Clic en la tarjeta**: abre la vista de detalle de la oportunidad
- **Clic en x** (abajo a la derecha): elimina la oportunidad (con confirmacion)

### Eliminacion en lote

Debajo de los botones de categoria hay un selector multiple para seleccionar varias oportunidades y eliminarlas de una vez.

### Agrupacion por cuenta

Las tarjetas se agrupan por **cuenta (empresa)**. Cada grupo muestra el nombre de la cuenta, el total ACV y la cantidad de oportunidades.

---

## 5. Vista de Detalle

Al hacer clic en una tarjeta del Tablero, se abre la vista de detalle de esa oportunidad.

### Barra de metadatos

Una barra compacta muestra toda la informacion de la oportunidad: nombre, cuenta, categoria, stage, partner, monto, ID y fecha de cierre.

**Botones en la barra:**

- **Editar**: abre el formulario para editar la oportunidad
- **+ Nueva**: abre el formulario para crear una nueva actividad
- **Volver**: regresa al Tablero
- **Eliminar**: elimina la oportunidad (con confirmacion)

### Historial de actividades

Debajo de la barra se muestran todas las actividades de la oportunidad, ordenadas por prioridad (bloqueadas primero, luego pendientes, enviadas y respondidas).

Cada actividad muestra:

- **Tipo** (badge de color): Email, Llamada, Reunion, Asignacion
- **Asignado a** (iniciales + nombre)
- **Destinatario**
- **Objetivo**
- **Estado** (semaforo + texto)
- **Fecha**
- **Descripcion** (si tiene)
- **Feedback** (si fue respondida)

**Acciones por actividad:**

- **Enviado**: marca la actividad como enviada (inicia el SLA de respuesta)
- **Respondida**: abre formulario para registrar feedback del cliente
- **Reenviar**: vuelve al estado Pendiente para reenviar
- **Editar**: abre formulario de edicion inline
- **Eliminar**: elimina la actividad (con confirmacion)

### Formulario de respuesta

Al hacer clic en "Respondida":

1. Escribe el **feedback del cliente**
2. Selecciona la **fecha de respuesta**
3. Opcionalmente marca **"Crear actividad de seguimiento"** para programar la proxima accion
4. Haz clic en **"Confirmar Respuesta"**

### Editar oportunidad

Al hacer clic en "Editar" en la barra, se muestra un formulario con todos los campos de la oportunidad: cuenta, proyecto, monto, categoria, ID, stage, partner, fecha de cierre y cualquier campo dinamico adicional.

### Nueva actividad

Al hacer clic en "+ Nueva", se muestra el formulario de creacion:

1. Selecciona el **canal**: Email, Llamada, Reunion o Asignacion
2. Elige el **SLA** (urgencia)
3. Selecciona la **fecha**
4. Escribe el **objetivo**
5. Indica el **destinatario** (la persona externa a quien va dirigida la actividad)
6. Si es tipo Asignacion, selecciona el **miembro del equipo** asignado
7. Selecciona el **SLA de respuesta** (cuanto tiempo tiene el cliente para responder)
8. Agrega **descripcion** o notas
9. Haz clic en **"Guardar Actividad"**

Si asignas a un miembro, recibira un email de notificacion con los detalles y un link para responder.

---

## 6. Actividades

La pestana **Actividades** muestra una tabla con todas las actividades de tus oportunidades.

### Filtro de alcance

- **Mis tareas**: solo actividades creadas por ti o asignadas a ti
- **Tareas del equipo**: actividades de otros miembros
- **Todas**: todas las actividades visibles segun tu rol

### Selector de columnas

Elige que columnas mostrar en la tabla. Las columnas disponibles incluyen: Semaforo, Estado, Categoria, Cuenta, Proyecto, Monto USD, Canal, Objetivo, Destinatario, Asignado a, Fecha, SLA, SLA Respuesta, Estado Interno, Feedback, Descripcion.

### Filtros de tabla

Cuatro filtros multiples para refinar la vista:

- **Categoria**: LEADS, OFFICIAL, GTM
- **Estado**: Pendiente, Enviada, Respondida
- **Canal**: Email, Llamada, Reunion, Asignacion
- **Cuenta**: filtrar por empresa

### Metricas rapidas

Encima de la tabla se muestran 5 contadores: Total, Pendientes, Enviadas, Respondidas, Bloqueadas/Vencidas.

### Edicion inline

Haz clic en el icono de lapiz a la derecha de cualquier fila para editar todos los campos de la actividad directamente en la tabla, incluyendo cambio de estado, asignacion y feedback.

---

## 7. Historial

La pestana **Historial** muestra una vista cronologica de todas las interacciones, agrupadas para facilitar el seguimiento.

### Agrupar por

Selecciona como agrupar las actividades:

- **Cuenta**: por empresa
- **Proyecto**: por oportunidad
- **Destinatario**: por persona externa
- **Asignado a**: por miembro del equipo

### Busqueda

Usa el campo de busqueda para filtrar grupos por nombre.

### Vista de grupos (izquierda)

Cada grupo muestra:

- **Nombre** del grupo
- **Cantidad** de actividades
- **Indicadores de estado**: puntos de colores (amarillo = pendiente, violeta = enviada, verde = respondida, rojo = bloqueada)

Haz clic en un grupo para seleccionarlo.

### Timeline (derecha)

Al seleccionar un grupo, se muestra su timeline cronologico con:

- **Encabezado** oscuro con nombre del grupo y contadores
- **Tarjetas de actividad** con toda la informacion: tipo, asignado, destinatario, objetivo, estado, fecha, descripcion y feedback
- **Contexto**: indica la oportunidad y cuenta a la que pertenece cada actividad

---

## 8. Control

La pestana **Control** esta disponible para Admin, VP y todos los roles de manager. Muestra un dashboard de analitica del equipo.

### Resumen General

Cuatro metricas principales: Total Actividades, Pendientes, Enviadas, Respondidas. Si hay actividades bloqueadas, se muestra una alerta roja.

### Actividad por Dia

Grafico de barras con la actividad de los ultimos 7 dias, mostrando actividades Programadas, Enviadas y Respondidas por dia.

Debajo, metricas de hoy vs ayer para programadas y respondidas.

### Resumen Semanal

Comparativa de la semana actual vs la anterior:

- Programadas esta semana (con delta vs anterior)
- Respondidas esta semana (con delta vs anterior)
- Tasa de cierre (barra de progreso)

### Proximas Actividades Programadas

Contadores de actividades pendientes: proximos 7 dias, 14 dias, 30 dias, y actividades vencidas (sin enviar).

### Rendimiento por Miembro

Tabla con el desglose por cada miembro del equipo: Total, Pendientes, Enviadas, Respondidas, Bloqueadas, Vencidas, Proximas 7 dias y tasa de cierre.

Debajo, grafico de barras con respondidas por miembro.

---

## 9. Equipo

La pestana **Equipo** varia segun tu rol.

### Vista Admin

Los administradores ven 4 sub-pestanas:

#### Miembros

Lista de todos los miembros del equipo (activos e inactivos). Para cada miembro:

- **Indicador**: verde (activo) o rojo (inactivo)
- **Expandir** para editar: nombre, email, rol (8 opciones), especialidad, telefono, activo/inactivo
- **Eliminar miembro** (no puedes eliminarte a ti mismo)

#### Equipos

Gestion de multiples equipos:

- **Editar equipo actual**: cambiar el nombre
- **Crear nuevo equipo**: ingresa nombre y crea
- **Lista de todos los equipos**: cada equipo muestra:
  - Cantidad de miembros
  - **Roles sin cubrir**: alerta con los roles que faltan del sistema de 8 roles
  - Editar miembros de cualquier equipo (nombre, rol, especialidad, telefono, activo)
  - **Mover miembro**: transferir un miembro a otro equipo
  - **Eliminar equipo**: solo si no tiene miembros y no es el equipo actual
  - Eliminar miembros de otros equipos

#### Configuracion

Editor JSON para tres configuraciones del equipo:

**Opciones de SLA** — define los niveles de urgencia disponibles:
```json
{
  "Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
  "Importante (2d)": {"dias": 2, "color": "#f59e0b"},
  "No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
}
```

**SLA de Respuesta** — tiempos de espera para respuesta del cliente:
```json
{
  "3 dias": 3,
  "1 semana": 7,
  "2 semanas": 14,
  "1 mes": 30
}
```

**Categorias** — nombres de las categorias de oportunidades:
```json
["LEADS", "OFFICIAL", "GTM"]
```

#### Invitaciones

Para invitar nuevos miembros:

1. Selecciona el **equipo destino**
2. Comparte el **enlace de la app** y el **ID del equipo** con el invitado
3. Opcionalmente, envia una **invitacion por email** (requiere configuracion de SendGrid)
4. El invitado abre el enlace, selecciona "Unirse a Equipo" y se registra con el ID

### Vista No-Admin

Los miembros que no son admin ven 2 sub-pestanas:

#### Miembros

Lista de solo lectura de los miembros activos del equipo con su rol y especialidad.

#### Invitaciones

Pueden compartir el enlace y el ID del equipo para invitar a nuevos miembros.

---

## 10. Importar desde Excel

En la barra lateral, dentro de **"CARGA MASIVA (EXCEL)"**, puedes importar oportunidades desde archivos Excel.

### Paso 1: Seleccionar formato

- **Leads Propios**: para leads generados internamente
- **Forecast BMC**: para exportaciones de Salesforce/BMC

### Paso 2: Descargar plantilla (opcional)

Haz clic en **"Descargar plantilla"** para obtener un archivo Excel con las columnas correctas para tu formato.

### Paso 3: Subir archivo

Arrastra o selecciona tu archivo `.xlsx`.

### Paso 4: Analizar

Haz clic en **"Analizar Archivo"**. El sistema comparara las oportunidades del Excel con las existentes y mostrara:

- **Nuevas**: oportunidades que no existen. Puedes marcar/desmarcar individualmente cuales importar.
- **Sin cambios**: oportunidades que ya existen con los mismos datos. Se omiten automaticamente.
- **Con diferencias**: oportunidades que existen pero tienen datos diferentes. Puedes ver el detalle de cada diferencia (tooltip) y elegir cuales sobrescribir.

### Paso 5: Ejecutar

Haz clic en **"Ejecutar Importacion"** para confirmar. Veras un resumen: "X creadas, Y actualizadas, Z sin cambios, W omitidas".

### Mapeo de columnas — Leads Propios

| Columna Excel | Campo en PG Machine |
|--------------|-------------------|
| Proyecto | Proyecto |
| Empresa (o Cuenta) | Cuenta |
| Annual Contract Value (ACV) (o Valor, Monto) | Monto USD |
| Close Date | Fecha de cierre |
| Partner | Partner |
| *(automatico)* | Categoria = "LEADS" |

### Mapeo de columnas — Forecast BMC

| Columna Excel | Campo en PG Machine |
|--------------|-------------------|
| Opportunity Name | Proyecto |
| Account Name | Cuenta |
| Annual Contract Value (ACV) (o Amount USD) | Monto USD |
| SFDC Opportunity Id (o BMC Opportunity Id) | Opportunity ID |
| Stage | Stage |
| Close Date | Fecha de cierre |
| Partner | Partner |
| *(automatico)* | Categoria = "OFFICIAL" |

---

## 11. Crear Oportunidad Manual

En la barra lateral, debajo de la carga masiva, esta el formulario **"ALTA MANUAL"**:

1. **Cuenta**: nombre de la empresa
2. **Proyecto**: nombre del proyecto u oportunidad
3. **Monto USD**: valor en dolares (ACV)
4. **Categoria**: LEADS, OFFICIAL, GTM (u otra configurada)
5. **Opportunity ID**: identificador externo (ej. SFDC ID)
6. **Stage**: etapa del deal
7. **Partner**: nombre del partner
8. **Close Date**: fecha esperada de cierre
9. **Campos dinamicos**: si tu equipo tiene campos adicionales, apareceran aqui automaticamente

Haz clic en **"Anadir Individual"** para crear la oportunidad.

---

## 12. Flujo de Actividades (Semaforo)

Cada actividad pasa por un flujo de estados representado visualmente con emojis de semaforo:

### Estado: Pendiente

```
Creada → Estado segun fecha y SLA:

  🔵 Programada DD/MM    La fecha es en el futuro
  🟧 Hoy                 La fecha es hoy
  🟩 Xh/Xd restantes    SLA > 50% de tiempo restante
  🟨 Xh/Xd restantes    SLA < 50% de tiempo restante
  🟥 Vencida             SLA expirado
```

### Transicion: Pendiente → Enviada

Al marcar como **"Enviado"**, la actividad pasa a estado Enviada y comienza el conteo del SLA de respuesta.

### Estado: Enviada

```
  🟪 Esp. rpta Xd        Esperando respuesta, dentro del SLA
  🟥 Bloqueada            El SLA de respuesta ha vencido
```

### Transicion: Enviada → Respondida

Al marcar como **"Respondida"**, se registra el feedback del cliente y la fecha de respuesta.

```
  🟩 Respondida           Actividad completada
```

### Acciones adicionales

- **Reenviar** (desde Enviada): vuelve a Pendiente para reenviar
- **Crear seguimiento** (al marcar Respondida): crea automaticamente una nueva actividad de seguimiento

### Diagrama completo

```
       ┌─────────┐
       │ Creada  │
       │(Pendien)│
       └────┬────┘
            │
     ┌──────┼──────┐
     │      │      │
  🔵 Futura  🟧 Hoy   🟩🟨🟥 SLA
     │      │      │
     └──────┼──────┘
            │
            ▼ [Enviado]
       ┌─────────┐
       │ Enviada │──── 🟪 Esperando respuesta
       │         │──── 🟥 Bloqueada (SLA vencido)
       └────┬────┘
            │         ┌───────────┐
            │ [Reenv] │ Pendiente │ (reinicio)
            │ ◄───────┘           │
            │                     │
            ▼ [Respondida]
       ┌─────────┐
       │Respondida│──── 🟩 Completada
       │ +feedback│
       └─────────┘
```

---

## 13. SLAs

Los SLAs (Service Level Agreements) son tiempos limite configurables que ayudan a mantener la disciplina en el seguimiento de actividades.

### SLA de Actividad

Define cuanto tiempo tiene una actividad en estado Pendiente antes de considerarse vencida.

**Opciones por defecto:**
- Urgente: 2-4 horas
- Importante: 2 dias
- No urgente: 7 dias

Se selecciona al crear o editar una actividad.

### SLA de Respuesta

Define cuanto tiempo tiene el cliente para responder despues de que una actividad se marca como Enviada.

**Opciones por defecto:**
- 3 dias
- 1 semana
- 2 semanas
- 1 mes

Si el cliente no responde dentro del SLA, la actividad se marca visualmente como **Bloqueada** (rojo).

### Configurar SLAs (Admin)

Ve a **Equipo → Configuracion** y edita los JSON de "Opciones de SLA" y "SLA de Respuesta". Los cambios aplican inmediatamente a todo el equipo.

---

## 14. Notificaciones

PG Machine envia notificaciones por email en estos casos:

| Tipo | Cuando se envia | A quien |
|------|-----------------|---------|
| **Asignacion** | Al crear una actividad con asignado | Miembro asignado |
| **Advertencia SLA** | Cuando queda menos del 50% del SLA | Miembro asignado o creador |
| **SLA Vencido** | Cuando el SLA de actividad expira | Miembro asignado o creador |
| **Bloqueada** | Cuando el SLA de respuesta expira | Creador de la actividad |

### Email de asignacion

Incluye todos los detalles de la actividad y un boton **"Responder desde el celular"** que permite al destinatario completar la actividad sin necesidad de iniciar sesion en la app.

### Configuracion

Las notificaciones por email requieren una configuracion de SendGrid. Si no esta configurada, la app funciona normalmente pero no envia emails.

---

## 15. Tour Guiado

PG Machine incluye un tour interactivo que te guia por las principales secciones de la plataforma.

### Inicio automatico

La primera vez que entras con un rol, el tour se inicia automaticamente. Te mostrara paso a paso las secciones relevantes para tu rol.

### Repetir el tour

En cualquier momento, haz clic en el boton **"Tour"** en la barra lateral para repetir el tour.

### Contenido del tour

El tour se adapta a tu rol:

- **Bienvenida** con tu rol y descripcion
- **Barra lateral** (solo desktop): perfil, Excel, Tour
- **Pestanas de navegacion**: Tablero, Actividades, Historial
- **Control** (si tienes acceso): dashboard de analitica
- **Equipo**: gestion segun tu rol
- **Carga masiva** (solo desktop): importacion Excel
- **Paso extra para Presales**: enfasis en "Mis tareas"

---

## 16. Preguntas Frecuentes

### Como agrego nuevas categorias?

El admin va a **Equipo → Configuracion → Categorias** y edita el JSON. Por ejemplo, para agregar "PARTNERS":
```json
["LEADS", "OFFICIAL", "GTM", "PARTNERS"]
```

### Como agrego columnas personalizadas a las oportunidades?

El admin (o DBA) agrega la columna directamente en la base de datos:
```sql
ALTER TABLE opportunities ADD COLUMN region TEXT DEFAULT '';
```
La columna aparecera automaticamente en formularios, tarjetas e importacion Excel.

### Como muevo un miembro a otro equipo?

El admin va a **Equipo → Equipos**, expande el equipo de origen, y al final de la seccion de miembros hay un formulario **"Mover miembro a otro equipo"** donde selecciona el miembro y el equipo destino.

### Puedo tener multiples equipos?

Si. El admin puede crear multiples equipos desde **Equipo → Equipos → Crear Nuevo Equipo**. Cada equipo tiene su propia data aislada (oportunidades, actividades, configuracion).

### Que pasa si no tengo SendGrid configurado?

La app funciona normalmente, pero no se enviaran emails de notificacion ni invitaciones por email. Los miembros pueden invitarse compartiendo el enlace y el ID del equipo manualmente.

### Como cambio el rol de un miembro?

El admin va a **Equipo → Miembros**, expande el miembro, cambia el rol en el selector y hace clic en "Guardar".

### Puedo eliminar un equipo?

Si, pero solo si el equipo no tiene miembros y no es tu equipo actual. Primero mueve o elimina todos los miembros, luego podras eliminarlo desde **Equipo → Equipos**.

### Que significa cada color de semaforo?

| Semaforo | Significado |
|----------|-------------|
| 🔵 | Actividad programada para el futuro |
| 🟧 | Actividad programada para hoy |
| 🟩 (Pendiente) | Mas del 50% del SLA disponible |
| 🟨 | Menos del 50% del SLA disponible |
| 🟥 (Pendiente) | SLA vencido |
| 🟪 | Enviada, esperando respuesta |
| 🟥 (Enviada) | Bloqueada, respuesta vencida |
| 🟩 (Respondida) | Actividad completada |

### Como configuro los SLAs?

El admin va a **Equipo → Configuracion** y edita los JSON de SLA. Por ejemplo, para agregar un SLA de 1 hora:
```json
{
  "Urgente (1h)": {"horas": 1, "color": "#dc2626"},
  "Importante (2d)": {"dias": 2, "color": "#f59e0b"},
  "No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
}
```

### Puedo responder una actividad desde el email?

Si. Cuando te asignan una actividad, recibes un email con un boton **"Responder desde el celular"**. Al hacer clic, se abre un formulario web donde puedes escribir tu feedback sin necesidad de iniciar sesion.

### Que es el filtro PROTECT / Growth?

El toggle **"Solo Growth"** oculta las oportunidades cuyo nombre de proyecto contiene "Renewal" (renovaciones), permitiendote enfocarte solo en oportunidades de crecimiento.

### Como veo el historial de una cuenta especifica?

Ve a la pestana **Historial**, selecciona **"Agrupar por: Cuenta"**, y haz clic en la cuenta que te interesa. Veras el timeline completo de todas las actividades asociadas.
