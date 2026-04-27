import hashlib
from datetime import datetime


def _texto(valor) -> str:
    return str(valor if valor is not None else "").strip()


def _numero(valor) -> str:
    try:
        return f"{float(valor or 0):.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _campo(nombre: str, valor) -> str:
    return f"{nombre}={_texto(valor)}"


def construir_cadena_factura(factura, lineas, cliente, configuracion_fiscal) -> str:
    """Construye una cadena técnica estable, reproducible y sin datos volátiles."""
    partes = [
        _campo("numero_factura", factura["numero_factura"]),
        _campo("fecha", factura["fecha"]),
        _campo("tipo_factura", factura["tipo_factura"] or "ordinaria"),
        _campo("factura_rectificada_id", factura["factura_rectificada_id"]),
        _campo("motivo_rectificacion", factura["motivo_rectificacion"]),
        _campo("nif_emisor", configuracion_fiscal["nif_cif"] if configuracion_fiscal else ""),
        _campo("nif_cliente", cliente["nif_cif"] if cliente else factura["cliente_nif_cif"] if "cliente_nif_cif" in factura.keys() else ""),
        _campo("base_imponible", _numero(factura["base_imponible"])),
        _campo("iva", _numero(factura["iva"])),
        _campo("irpf", _numero(factura["irpf"])),
        _campo("total", _numero(factura["total"])),
        _campo("hash_anterior", factura["hash_anterior"]),
    ]

    for linea in lineas:
        partes.extend(
            [
                _campo("linea", linea["orden"] or linea["id"]),
                _campo("concepto", linea["concepto"]),
                _campo("cantidad", _numero(linea["cantidad"])),
                _campo("precio_unitario", _numero(linea["precio_unitario"])),
                _campo("subtotal", _numero(linea["subtotal"])),
                _campo("iva_porcentaje", _numero(linea["iva_porcentaje"])),
                _campo("iva_importe", _numero(linea["iva_importe"])),
                _campo("irpf_porcentaje", _numero(linea["irpf_porcentaje"])),
                _campo("irpf_importe", _numero(linea["irpf_importe"])),
                _campo("total_linea", _numero(linea["total"])),
            ]
        )
    return "|".join(partes)


def calcular_hash_factura(cadena: str) -> str:
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


def obtener_hash_anterior(owner_user_id, factura_id_actual=None, conn=None) -> str | None:
    if conn is None:
        from app.database import get_connection

        with get_connection() as conn_local:
            return obtener_hash_anterior(owner_user_id, factura_id_actual, conn_local)

    params = [owner_user_id]
    filtro_actual = ""
    if factura_id_actual:
        filtro_actual = " AND id <> ?"
        params.append(factura_id_actual)

    row = conn.execute(
        f"""
        SELECT hash_factura
        FROM facturas_emitidas
        WHERE owner_user_id = ?
          AND hash_factura IS NOT NULL
          AND hash_factura <> ''
          AND estado IN ('emitida', 'cobrada', 'anulada')
          {filtro_actual}
        ORDER BY id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return row["hash_factura"] if row else None


def generar_payload_qr_interno(factura, cliente, configuracion_fiscal) -> str:
    nif_emisor = configuracion_fiscal["nif_cif"] if configuracion_fiscal else ""
    return (
        f"FACTURA:{_texto(factura['numero_factura'])}"
        f"|FECHA:{_texto(factura['fecha'])}"
        f"|NIF:{_texto(nif_emisor)}"
        f"|TOTAL:{_numero(factura['total'])}"
        f"|HASH:{_texto(factura['hash_factura'])}"
    )


def preparar_registro_verifactu(conn, factura_id, owner_user_id) -> dict:
    cur = conn.cursor()
    factura = cur.execute(
        """
        SELECT f.*,
               c.nif_cif AS cliente_nif_cif
        FROM facturas_emitidas f
        LEFT JOIN clientes c ON c.id = f.cliente_id
        WHERE f.id = ? AND f.owner_user_id = ?
        """,
        (factura_id, owner_user_id),
    ).fetchone()
    if not factura:
        raise ValueError("Factura no encontrada")
    if factura["hash_factura"]:
        return {
            "hash_factura": factura["hash_factura"],
            "hash_anterior": factura["hash_anterior"],
            "cadena_hash": factura["cadena_hash"],
            "qr_payload": factura["qr_payload"],
            "ya_existia": True,
        }

    lineas = cur.execute(
        """
        SELECT *
        FROM factura_lineas
        WHERE factura_id = ?
        ORDER BY orden ASC, id ASC
        """,
        (factura_id,),
    ).fetchall()
    cliente = (
        cur.execute(
            "SELECT * FROM clientes WHERE id = ? AND owner_user_id = ?",
            (factura["cliente_id"], owner_user_id),
        ).fetchone()
        if factura["cliente_id"]
        else None
    )
    configuracion_fiscal = cur.execute(
        """
        SELECT *
        FROM configuracion_fiscal
        WHERE owner_user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (owner_user_id,),
    ).fetchone()

    hash_anterior = obtener_hash_anterior(owner_user_id, factura_id, conn)
    cur.execute(
        """
        UPDATE facturas_emitidas
        SET hash_anterior = ?
        WHERE id = ? AND owner_user_id = ?
        """,
        (hash_anterior, factura_id, owner_user_id),
    )
    factura = cur.execute(
        "SELECT * FROM facturas_emitidas WHERE id = ? AND owner_user_id = ?",
        (factura_id, owner_user_id),
    ).fetchone()
    cadena_hash = construir_cadena_factura(
        factura,
        lineas,
        cliente,
        configuracion_fiscal,
    )
    hash_factura = calcular_hash_factura(cadena_hash)
    factura_payload = dict(factura)
    factura_payload["hash_factura"] = hash_factura
    qr_payload = generar_payload_qr_interno(
        factura_payload,
        cliente,
        configuracion_fiscal,
    )
    fecha_generacion = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        """
        UPDATE facturas_emitidas
        SET hash_factura = ?, hash_anterior = ?, cadena_hash = ?,
            qr_payload = ?, verifactu_estado = 'generado',
            verifactu_fecha_generacion = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND owner_user_id = ?
        """,
        (
            hash_factura,
            hash_anterior,
            cadena_hash,
            qr_payload,
            fecha_generacion,
            factura_id,
            owner_user_id,
        ),
    )
    return {
        "hash_factura": hash_factura,
        "hash_anterior": hash_anterior,
        "cadena_hash": cadena_hash,
        "qr_payload": qr_payload,
        "ya_existia": False,
    }
