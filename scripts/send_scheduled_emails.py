#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.crm_scheduled import enviar_emails_programados_vencidos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Envia emails CRM programados vencidos de forma controlada.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista emails vencidos sin enviar ni modificar registros.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Numero maximo de emails vencidos a procesar. Por defecto: 10.",
    )
    args = parser.parse_args()

    resultado = enviar_emails_programados_vencidos(dry_run=args.dry_run, limit=args.limit)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if resultado["errores"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
