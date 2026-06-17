from html import escape


CORPORATE_NAME = "Carlos Blanco"
CORPORATE_ROLE = "Arquitecto Técnico · Perito Judicial"
CORPORATE_EMAIL = "contacto@carlosblancoperito.es"
CORPORATE_PHONE = "623 829 228"
CORPORATE_WEB = "www.carlosblancoperito.es"
CORPORATE_WHATSAPP_URL = "https://wa.me/34623829228"

COLOR_PRIMARY = "#10233f"
COLOR_ACCENT = "#b89b68"
COLOR_BACKGROUND = "#f7f5f0"
COLOR_BORDER = "#e4e0d8"
DEFAULT_FOOTER_TEXT = "Email enviado desde Sistema Pericial."
CONFIDENTIALIDAD_PROPUESTAS = (
    "Este correo y sus adjuntos pueden contener información profesional y confidencial "
    "dirigida exclusivamente a su destinatario."
)


def construir_email_texto(
    contenido: str,
    destacado: str | None = None,
    cierre: str | None = None,
    footer_text: str | None = DEFAULT_FOOTER_TEXT,
    footer_note: str | None = None,
) -> str:
    partes = [contenido.strip()]
    if destacado:
        partes.append(destacado.strip())
    if cierre:
        partes.append(cierre.strip())

    partes.append(construir_firma_texto())

    if footer_text:
        partes.append(footer_text.strip())
    if footer_note:
        partes.append(footer_note.strip())

    return "\n\n".join(partes)


def texto_a_html(texto: str) -> str:
    bloques = []
    for bloque in texto.strip().split("\n\n"):
        lineas = "<br>".join(escape(linea) for linea in bloque.splitlines())
        if lineas:
            bloques.append(
                f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">{lineas}</p>'
            )
    return "\n        ".join(bloques)


def construir_bloque_destacado_html(destacado_html: str | None = None) -> str:
    if not destacado_html:
        return ""
    return f"""
        <div style="margin:22px 0;padding:18px;border:1px solid {COLOR_BORDER};border-left:4px solid {COLOR_ACCENT};background:{COLOR_BACKGROUND};border-radius:6px;">
          {destacado_html}
        </div>"""


def construir_firma_html() -> str:
    return f"""
        <div style="margin-top:6px;font-size:14px;line-height:1.4;color:{COLOR_PRIMARY};">
          <span style="font-weight:700;">{CORPORATE_NAME}</span><br>
          <span>{CORPORATE_ROLE}</span><br>
          <span>{CORPORATE_PHONE} · <a href="{CORPORATE_WHATSAPP_URL}" style="color:{COLOR_PRIMARY};text-decoration:underline;">WhatsApp</a></span><br>
          <span>{CORPORATE_EMAIL}</span><br>
          <span>{CORPORATE_WEB}</span>
        </div>"""


def construir_firma_texto() -> str:
    return "\n".join(
        [
            CORPORATE_NAME,
            CORPORATE_ROLE,
            f"{CORPORATE_PHONE} · WhatsApp: {CORPORATE_WHATSAPP_URL}",
            CORPORATE_EMAIL,
            CORPORATE_WEB,
        ]
    )


def contexto_identidad_email(from_name: str | None = None, from_email: str | None = None) -> dict:
    nombre = (from_name or "").strip() or CORPORATE_NAME
    email = (from_email or "").strip() or CORPORATE_EMAIL
    return {
        "nombre": nombre,
        "cargo": CORPORATE_ROLE,
        "email": email,
        "telefono": CORPORATE_PHONE,
        "web": CORPORATE_WEB,
        "whatsapp_url": CORPORATE_WHATSAPP_URL,
        "firma_texto": construir_firma_texto(),
    }


def construir_footer_html(footer_text: str | None = None, footer_note: str | None = None) -> str:
    if footer_text == "":
        return ""
    texto = footer_text or DEFAULT_FOOTER_TEXT
    nota_html = ""
    if footer_note:
        nota_html = f'<div style="margin-top:4px;color:#7a7469;">{escape(footer_note)}</div>'
    return f"""
      <div style="padding:10px 28px;background:{COLOR_BACKGROUND};border-top:1px solid {COLOR_BORDER};font-size:11px;line-height:1.4;color:#6f6a60;">
        {escape(texto)}
        {nota_html}
      </div>"""


def construir_email_html_base(
    titulo: str,
    contenido_central_html: str,
    footer_text: str | None = None,
    footer_note: str | None = None,
) -> str:
    return f"""\
<!doctype html>
<html lang="es">
<body style="margin:0;padding:0;background:{COLOR_BACKGROUND};font-family:Arial,Helvetica,sans-serif;color:{COLOR_PRIMARY};">
  <div style="width:100%;background:{COLOR_BACKGROUND};padding:24px 12px;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid {COLOR_BORDER};border-radius:8px;overflow:hidden;">
      <div style="background:{COLOR_PRIMARY};color:#ffffff;padding:24px 28px;border-bottom:4px solid {COLOR_ACCENT};">
        <div style="font-size:22px;font-weight:700;line-height:1.2;">{CORPORATE_NAME}</div>
        <div style="font-size:14px;line-height:1.5;color:{COLOR_BACKGROUND};">{CORPORATE_ROLE}</div>
        <div style="margin-top:14px;font-size:16px;font-weight:700;color:{COLOR_ACCENT};">{escape(titulo)}</div>
      </div>
      <div style="padding:24px 28px 22px;">
        {contenido_central_html}
        {construir_firma_html()}
      </div>{construir_footer_html(footer_text, footer_note)}
    </div>
  </div>
</body>
</html>"""


def construir_email_html(
    titulo: str,
    contenido_html: str,
    destacado_html: str | None = None,
    cierre_html: str | None = None,
    footer_text: str = DEFAULT_FOOTER_TEXT,
    footer_note: str | None = None,
) -> str:
    contenido_central = "\n".join(
        bloque
        for bloque in [
            contenido_html,
            construir_bloque_destacado_html(destacado_html),
            cierre_html or "",
        ]
        if bloque
    )
    return construir_email_html_base(titulo, contenido_central, footer_text, footer_note)
