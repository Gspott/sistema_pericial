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
    asunto="Servicios de informes periciales para comunidades administradas",
    cuerpo="""Buenos días, {nombre_contacto}:

Me presento, soy Carlos Blanco, arquitecto técnico especializado en informes periciales, patologías constructivas y valoración de daños en edificios y viviendas.

Me pongo en contacto con ustedes porque colaboro con comunidades de propietarios, administradores de fincas y particulares en la emisión de informes técnicos claros, documentados y útiles para la toma de decisiones, reclamaciones, reparaciones o procedimientos judiciales.

Puedo ayudarles especialmente en casos como:

* humedades y filtraciones;
* fisuras y grietas;
* daños en elementos comunes;
* defectos constructivos;
* valoración de reparaciones;
* informes para reclamaciones a seguros, propietarios, comunidades o empresas intervinientes;
* asistencia técnica previa a una demanda o negociación.

Mi forma de trabajar se basa en visitas técnicas ordenadas, reportaje fotográfico, análisis claro de causas probables, valoración de daños cuando procede y entrega de informe profesional en PDF.

Si en algún momento necesitan apoyo técnico para una comunidad administrada, estaré encantado de colaborar con ustedes.

Quedo a vuestra disposición para cualquier consulta o futura colaboración.

Un cordial saludo,""",
)

PLANTILLA_SEGUIMIENTO_ADMINISTRADOR_FINCAS_10D = PlantillaComercial(
    slug="seguimiento_administrador_fincas_10d",
    tipo_lead="administrador_fincas",
    nombre="Seguimiento Administradores de fincas 10 días",
    asunto="Seguimiento de presentación y disponibilidad técnica",
    cuerpo="""Buenos días,

Hace unos días os remití un breve correo de presentación como arquitecto técnico especializado en informes periciales, inspecciones de edificios e Informes de Evaluación del Edificio (IEEV.CV).

Aprovecho la ocasión para reiterar mi disponibilidad para colaborar con vuestro despacho en aquellas incidencias técnicas que puedan surgir en las comunidades que gestionáis, especialmente en casos de humedades, filtraciones, defectos constructivos, inspecciones de edificios o necesidades de evaluación y asesoramiento técnico.

Mi forma de trabajo se basa en una gestión ágil y digital de los encargos, con documentación técnica clara y visual que facilite la toma de decisiones y la gestión de incidencias por parte de las comunidades de propietarios y de sus administradores.

Quedo a vuestra disposición para cualquier consulta o, si lo consideráis oportuno, para mantener una breve reunión de presentación y poder explicaros con más detalle los servicios que ofrezco.

Muchas gracias por vuestro tiempo y atención.

Un cordial saludo,""",
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
    return {
        "nombre_contacto": nombre or FALLBACK_NOMBRE_CONTACTO,
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
    valores = VariablesSeguras({clave: limpiar_texto(valor) for clave, valor in variables.items()})
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
