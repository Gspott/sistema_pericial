from dataclasses import dataclass

from app.services.email_templates import (
    CORPORATE_EMAIL,
    CORPORATE_NAME,
    CORPORATE_PHONE,
    CORPORATE_WEB,
)

FALLBACK_NOMBRE_CONTACTO = "equipo"
FALLBACK_EMPRESA = "su administración"
FALLBACK_MI_NOMBRE = CORPORATE_NAME
FALLBACK_TELEFONO = CORPORATE_PHONE
FALLBACK_EMAIL = CORPORATE_EMAIL
FALLBACK_WEB = CORPORATE_WEB
FALLBACK_TIPO_SERVICIO = "informes periciales, patologías constructivas y valoración de daños"


@dataclass(frozen=True)
class PlantillaComercial:
    slug: str
    tipo_lead: str
    nombre: str
    asunto: str
    cuerpo: str


class VariablesSeguras(dict):
    def __missing__(self, key):
        return ""


PLANTILLA_ADMINISTRADOR_FINCAS = PlantillaComercial(
    slug="presentacion_administrador_fincas",
    tipo_lead="administrador_fincas",
    nombre="Presentación Administradores de fincas",
    asunto="Apoyo técnico para administradores de fincas",
    cuerpo="""Buenos días, {nombre_destinatario}:

Mi nombre es Carlos Blanco y soy arquitecto técnico especializado en informes periciales, patologías constructivas, inspección de edificios y realización de Informes de Evaluación del Edificio (IEE.CV).

Colaboro con administradores de fincas y comunidades de propietarios ofreciendo apoyo técnico en aquellas incidencias que requieren un criterio profesional claro, una respuesta ágil y una documentación rigurosa para la toma de decisiones.

Puedo ayudarles especialmente en casos como:

• Humedades y filtraciones en viviendas y elementos comunes.
• Fisuras, grietas y otras patologías constructivas.
• Informes de Evaluación del Edificio (IEE.CV).
• Valoración de daños y reparaciones.
• Informes para reclamaciones a seguros, propietarios, constructoras o empresas intervinientes.
• Inspecciones técnicas de edificios y viviendas.
• Asistencia técnica previa a una negociación o procedimiento judicial.

Mi forma de trabajar se basa en inspecciones ordenadas, reportaje fotográfico estructurado y elaboración de informes claros, visuales y útiles para administradores y comunidades de propietarios.

Adjunto una breve presentación para que puedan conocer mejor mi forma de trabajo.

Si actualmente tienen alguna comunidad con un IEE.CV pendiente, una incidencia de humedades o cualquier otra patología constructiva, estaré encantado de comentar el caso sin compromiso.

Muchas gracias por su tiempo y quedo a su disposición para cualquier consulta o futura colaboración.

P.D.: Si actualmente gestionan alguna comunidad con un IEE.CV pendiente, humedades o una patología constructiva, pueden responder directamente a este correo y estaré encantado de valorar el caso.""",
)

PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D = PlantillaComercial(
    slug="seguimiento_administrador_fincas_10d",
    tipo_lead="administrador_fincas",
    nombre="Seguimiento Administradores de fincas 10 días",
    asunto="Disponibilidad para incidencias técnicas e IEE.CV",
    cuerpo="""Buenos días, {nombre_destinatario}:

Hace unos días tuve la oportunidad de remitirles una breve presentación profesional como arquitecto técnico especializado en informes periciales, inspección de edificios y realización de Informes de Evaluación del Edificio (IEE.CV).

Aprovecho la ocasión para reiterar mi disponibilidad para colaborar con su despacho en aquellas incidencias técnicas que puedan surgir en las comunidades que gestionan, especialmente en casos de:

• Humedades y filtraciones.
• Patologías y defectos constructivos.
• Inspecciones de edificios y viviendas.
• Informes de Evaluación del Edificio (IEE.CV).
• Valoración de daños y reclamaciones técnicas.

Mi forma de trabajo se basa en una gestión ágil y digital de los encargos, con documentación técnica clara y visual que facilite la toma de decisiones y la gestión de incidencias por parte de las comunidades de propietarios y de sus administradores.

Si actualmente tienen alguna comunidad con un IEE.CV pendiente o alguna incidencia técnica en la que pueda aportar criterio y apoyo profesional, estaré encantado de comentar el caso sin ningún compromiso.

Muchas gracias por su tiempo y quedo a su disposición para cualquier consulta o futura colaboración.""",
)

PLANTILLAS_COMERCIALES = {
    PLANTILLA_ADMINISTRADOR_FINCAS.slug: PLANTILLA_ADMINISTRADOR_FINCAS,
    PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D.slug: PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D,
}

PLANTILLA_PRESENTACION_POR_TIPO_LEAD = {
    PLANTILLA_ADMINISTRADOR_FINCAS.tipo_lead: PLANTILLA_ADMINISTRADOR_FINCAS.slug,
}

PLANTILLA_SEGUIMIENTO_10D_POR_TIPO_LEAD = {
    PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D.tipo_lead: PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D.slug,
}

TIPOS_PREPARADOS = (
    "administrador_fincas",
    "abogado",
    "particular",
    "comunidad",
    "aseguradora",
    "empresa",
)


def limpiar_texto(valor) -> str:
    return (str(valor) if valor is not None else "").strip()


def valor_mapping(mapping, clave: str, default=""):
    try:
        return mapping[clave]
    except (KeyError, TypeError, IndexError):
        return default


def nombre_usuario(current_user) -> str:
    nombre = limpiar_texto(valor_mapping(current_user, "nombre"))
    apellido1 = limpiar_texto(valor_mapping(current_user, "apellido1"))
    return " ".join(parte for parte in (nombre, apellido1) if parte) or FALLBACK_MI_NOMBRE


def variables_para_lead(lead, current_user) -> dict:
    nombre = limpiar_texto(valor_mapping(lead, "nombre"))
    nombre_destinatario = nombre or FALLBACK_NOMBRE_CONTACTO
    return {
        "nombre_contacto": nombre_destinatario,
        "nombre_destinatario": nombre_destinatario,
        "empresa": nombre or FALLBACK_EMPRESA,
        "localidad": "",
        "mi_nombre": nombre_usuario(current_user),
        "telefono": FALLBACK_TELEFONO,
        "email": FALLBACK_EMAIL,
        "web": FALLBACK_WEB,
        "tipo_servicio": FALLBACK_TIPO_SERVICIO,
    }


def obtener_plantilla_comercial(slug: str) -> PlantillaComercial | None:
    return PLANTILLAS_COMERCIALES.get(slug)


def plantillas_disponibles() -> tuple[PlantillaComercial, ...]:
    return tuple(PLANTILLAS_COMERCIALES.values())


def plantilla_para_tipo(tipo_lead: str) -> PlantillaComercial:
    slug = PLANTILLA_PRESENTACION_POR_TIPO_LEAD.get(tipo_lead, PLANTILLA_ADMINISTRADOR_FINCAS.slug)
    return PLANTILLAS_COMERCIALES[slug]


def plantilla_seguimiento_para_tipo(tipo_lead: str) -> PlantillaComercial:
    slug = PLANTILLA_SEGUIMIENTO_10D_POR_TIPO_LEAD.get(
        tipo_lead,
        PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D.slug,
    )
    return PLANTILLAS_COMERCIALES[slug]


def renderizar_plantilla_comercial(
    plantilla: PlantillaComercial,
    variables: dict,
) -> tuple[str, str]:
    datos = {clave: limpiar_texto(valor) for clave, valor in variables.items()}
    if not datos.get("nombre_destinatario") and datos.get("nombre_contacto"):
        datos["nombre_destinatario"] = datos["nombre_contacto"]
    if not datos.get("nombre_contacto") and datos.get("nombre_destinatario"):
        datos["nombre_contacto"] = datos["nombre_destinatario"]
    valores = VariablesSeguras(datos)
    return plantilla.asunto.format_map(valores), plantilla.cuerpo.format_map(valores)


def construir_email_comercial(
    tipo_lead: str,
    lead,
    current_user,
    proposito: str = "presentacion",
) -> dict:
    if proposito == "seguimiento_10d":
        plantilla = plantilla_seguimiento_para_tipo(tipo_lead)
    else:
        plantilla = plantilla_para_tipo(tipo_lead)
    asunto, cuerpo = renderizar_plantilla_comercial(
        plantilla,
        variables_para_lead(lead, current_user),
    )
    return {
        "plantilla": plantilla,
        "asunto": asunto,
        "cuerpo": cuerpo,
    }
