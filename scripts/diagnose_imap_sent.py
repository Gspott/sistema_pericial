#!/usr/bin/env python3
"""Diagnostico seguro de carpeta IMAP Enviados para Sistema Pericial."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services import email_sender


ASUNTO_PRUEBA = "[Sistema Pericial] Prueba IMAP Enviados"


def _mensaje_prueba():
    destinatario = email_sender._remitente_email()
    cuerpo = (
        "Prueba local de guardado IMAP en carpeta Enviados.\n\n"
        "Este mensaje no se ha enviado por SMTP; solo se ha guardado mediante IMAP APPEND."
    )
    html = (
        "<p>Prueba local de guardado IMAP en carpeta Enviados.</p>"
        "<p>Este mensaje no se ha enviado por SMTP; solo se ha guardado mediante IMAP APPEND.</p>"
    )
    return email_sender.crear_mensaje_email(destinatario, ASUNTO_PRUEBA, cuerpo, html)


def _resultado_seguro(resultado: dict) -> dict:
    seguro = dict(resultado)
    seguro.pop("password", None)
    return seguro


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostica la carpeta IMAP de enviados.")
    parser.add_argument(
        "--append-test",
        action="store_true",
        help="Guarda por IMAP un mensaje de prueba. No envia por SMTP ni toca CRM.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    mensaje = _mensaje_prueba() if args.append_test else None
    resultado = email_sender.diagnosticar_imap_enviados(mensaje, append_test=args.append_test)
    print(json.dumps(_resultado_seguro(resultado), ensure_ascii=False, indent=2))

    if args.append_test and resultado.get("ok"):
        print(f"\nOK: mensaje de prueba guardado en carpeta: {resultado.get('carpeta')}")
        print(f"Asunto: {ASUNTO_PRUEBA}")
        return 0

    if not args.append_test and resultado.get("carpeta_enviados_detectada"):
        print(f"\nOK: carpeta de enviados detectada: {resultado.get('carpeta_enviados_detectada')}")
        return 0

    print(f"\nAVISO: diagnostico incompleto o fallido: {resultado.get('error')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
