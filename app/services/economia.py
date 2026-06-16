from datetime import date, timedelta


ESTADOS_WORKBENCH_ECONOMICO = (
    "todos",
    "pendientes",
    "cobro_parcial",
    "cobradas",
    "vencidas",
    "sin_facturar",
)

ESTADO_LABELS_WORKBENCH_ECONOMICO = {
    "sin_facturar": "Sin facturar",
    "facturada": "Facturada",
    "cobro_parcial": "Cobro parcial",
    "cobrada": "Cobrada",
    "vencida": "Vencida",
    "borrador": "Borrador",
}

DIAS_VENCIMIENTO_ESTIMADO = 30


def _limpiar_texto(valor) -> str:
    return (valor or "").strip()


def _to_float(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _nombre_cliente(row) -> str:
    razon_social = _limpiar_texto(row["cliente_razon_social"])
    if razon_social:
        return razon_social
    partes = [
        _limpiar_texto(row["cliente_nombre"]),
        _limpiar_texto(row["cliente_apellidos"]),
    ]
    nombre = " ".join(parte for parte in partes if parte)
    return nombre or _limpiar_texto(row["expediente_cliente"]) or "Sin cliente"


def _parse_date(valor: str | None) -> date | None:
    valor_limpio = _limpiar_texto(valor)
    if not valor_limpio:
        return None
    try:
        return date.fromisoformat(valor_limpio[:10])
    except ValueError:
        return None


def _es_vencida(fecha_referencia: str | None, pendiente_cobro: float, hoy: date) -> bool:
    fecha = _parse_date(fecha_referencia)
    if pendiente_cobro <= 0 or not fecha:
        return False
    return fecha <= hoy - timedelta(days=DIAS_VENCIMIENTO_ESTIMADO)


def _resolver_estado_economico(item: dict, hoy: date) -> str:
    total_facturado = item["total_facturado"]
    total_cobrado = item["total_cobrado"]
    pendiente_cobro = max(total_facturado - total_cobrado, 0)

    if _es_vencida(item.get("fecha_factura_referencia"), pendiente_cobro, hoy):
        return "vencida"
    if total_facturado <= 0:
        return "borrador" if item["tiene_borrador"] else "sin_facturar"
    if total_cobrado <= 0:
        return "facturada"
    if total_cobrado < total_facturado:
        return "cobro_parcial"
    return "cobrada"


def _pasa_filtro(item: dict, filtro: str) -> bool:
    estado = item["estado"]
    if filtro == "todos":
        return True
    if filtro == "pendientes":
        return item["pendiente"] > 0
    if filtro == "cobro_parcial":
        return estado == "cobro_parcial"
    if filtro == "cobradas":
        return estado == "cobrada"
    if filtro == "vencidas":
        return estado == "vencida"
    if filtro == "sin_facturar":
        return estado == "sin_facturar"
    return True


def normalizar_filtro_workbench_economico(filtro: str | None) -> str:
    filtro_limpio = _limpiar_texto(filtro) or "todos"
    return filtro_limpio if filtro_limpio in ESTADOS_WORKBENCH_ECONOMICO else "todos"


def _crear_item_base(row, key: str) -> dict:
    total_presupuestado = _to_float(row["total_propuesta"]) or _to_float(row["total"])
    return {
        "key": key,
        "propuesta_id": row["propuesta_id"],
        "numero_propuesta": row["numero_propuesta"],
        "propuesta_fecha": row["propuesta_fecha"],
        "propuesta_estado": row["propuesta_estado"],
        "expediente_id": row["expediente_id"],
        "numero_expediente": row["numero_expediente"],
        "cliente_id": row["cliente_id"],
        "cliente_nombre": _nombre_cliente(row),
        "total_presupuestado": total_presupuestado,
        "total_facturado": 0.0,
        "total_cobrado": 0.0,
        "pendiente": total_presupuestado,
        "pendiente_cobro": 0.0,
        "estado": "sin_facturar",
        "estado_label": ESTADO_LABELS_WORKBENCH_ECONOMICO["sin_facturar"],
        "tiene_borrador": False,
        "facturas": [],
        "factura_principal": None,
        "fecha_factura_referencia": "",
        "fecha_orden": row["propuesta_fecha"] or "",
    }


def _agregar_factura(item: dict, factura) -> None:
    estado = _limpiar_texto(factura["estado"])
    total_factura = _to_float(factura["total"])
    total_cobrado = _to_float(factura["total_cobrado"])
    fecha_factura = factura["fecha_emision"] or factura["fecha"] or ""
    factura_data = {
        "id": factura["factura_id"],
        "numero_factura": factura["numero_factura"],
        "estado": estado,
        "tipo_factura": factura["tipo_factura"],
        "fecha": factura["fecha"],
        "fecha_emision": factura["fecha_emision"],
        "total": total_factura,
        "total_cobrado": total_cobrado,
    }
    item["facturas"].append(factura_data)

    if estado == "borrador":
        item["tiene_borrador"] = True
        if item["factura_principal"] is None:
            item["factura_principal"] = factura_data
        return

    if estado not in {"emitida", "cobrada"}:
        return

    item["total_facturado"] += total_factura
    item["total_cobrado"] += total_cobrado
    if item["factura_principal"] is None or factura["factura_id"] > item["factura_principal"]["id"]:
        item["factura_principal"] = factura_data
    if not item["fecha_factura_referencia"] or fecha_factura < item["fecha_factura_referencia"]:
        item["fecha_factura_referencia"] = fecha_factura
    if fecha_factura and fecha_factura > item["fecha_orden"]:
        item["fecha_orden"] = fecha_factura


def construir_workbench_economico(cur, owner_user_id: int, filtro: str | None = "todos") -> dict:
    filtro_normalizado = normalizar_filtro_workbench_economico(filtro)
    hoy = date.today()
    inicio_mes = hoy.replace(day=1).isoformat()
    fin_mes = hoy.isoformat()

    propuestas = cur.execute(
        """
        SELECT p.id AS propuesta_id, p.numero_propuesta, p.fecha AS propuesta_fecha,
               p.estado AS propuesta_estado, p.total_propuesta, p.total,
               p.cliente_id, p.expediente_id,
               c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
               c.razon_social AS cliente_razon_social,
               e.numero_expediente, e.cliente AS expediente_cliente
        FROM propuestas p
        LEFT JOIN clientes c ON c.id = p.cliente_id
        LEFT JOIN expedientes e ON e.id = p.expediente_id
        WHERE p.owner_user_id = ?
        ORDER BY p.id DESC
        """,
        (owner_user_id,),
    ).fetchall()

    items = {}
    for propuesta in propuestas:
        key = f"propuesta:{propuesta['propuesta_id']}"
        items[key] = _crear_item_base(propuesta, key)

    facturas = cur.execute(
        """
        SELECT f.id AS factura_id, f.numero_factura, f.fecha, f.fecha_emision,
               f.estado, f.tipo_factura, f.total, f.propuesta_id, f.expediente_id,
               f.cliente_id, f.concepto_general,
               c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
               c.razon_social AS cliente_razon_social,
               p.numero_propuesta, p.fecha AS propuesta_fecha,
               p.estado AS propuesta_estado, p.total_propuesta,
               p.total AS propuesta_total,
               e.numero_expediente, e.cliente AS expediente_cliente,
               COALESCE(SUM(CASE WHEN f.estado IN ('emitida', 'cobrada') THEN co.importe ELSE 0 END), 0) AS total_cobrado
        FROM facturas_emitidas f
        LEFT JOIN cobros co ON co.factura_id = f.id AND co.owner_user_id = f.owner_user_id
        LEFT JOIN clientes c ON c.id = f.cliente_id
        LEFT JOIN propuestas p ON p.id = f.propuesta_id
        LEFT JOIN expedientes e ON e.id = f.expediente_id
        WHERE f.owner_user_id = ?
        GROUP BY f.id
        ORDER BY f.id DESC
        """,
        (owner_user_id,),
    ).fetchall()

    for factura in facturas:
        if factura["propuesta_id"]:
            key = f"propuesta:{factura['propuesta_id']}"
        else:
            key = f"factura:{factura['factura_id']}"
        if key not in items:
            base = {
                "propuesta_id": factura["propuesta_id"],
                "numero_propuesta": factura["numero_propuesta"],
                "propuesta_fecha": factura["propuesta_fecha"] or factura["fecha"],
                "propuesta_estado": factura["propuesta_estado"],
                "total_propuesta": factura["total_propuesta"],
                "total": factura["propuesta_total"],
                "expediente_id": factura["expediente_id"],
                "numero_expediente": factura["numero_expediente"],
                "cliente_id": factura["cliente_id"],
                "cliente_nombre": factura["cliente_nombre"],
                "cliente_apellidos": factura["cliente_apellidos"],
                "cliente_razon_social": factura["cliente_razon_social"],
                "expediente_cliente": factura["expediente_cliente"],
            }
            items[key] = _crear_item_base(base, key)
        _agregar_factura(items[key], factura)

    for item in items.values():
        referencia = max(item["total_presupuestado"], item["total_facturado"])
        item["pendiente"] = max(referencia - item["total_cobrado"], 0)
        item["pendiente_cobro"] = max(item["total_facturado"] - item["total_cobrado"], 0)
        item["estado"] = _resolver_estado_economico(item, hoy)
        item["estado_label"] = ESTADO_LABELS_WORKBENCH_ECONOMICO[item["estado"]]

    items_filtrados = [
        item for item in items.values() if _pasa_filtro(item, filtro_normalizado)
    ]
    items_filtrados.sort(key=lambda item: (item["fecha_orden"], item["key"]), reverse=True)

    facturado_mes = cur.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM facturas_emitidas
        WHERE owner_user_id = ?
          AND estado IN ('emitida', 'cobrada')
          AND COALESCE(fecha_emision, fecha) BETWEEN ? AND ?
        """,
        (owner_user_id, inicio_mes, fin_mes),
    ).fetchone()[0]
    cobrado_mes = cur.execute(
        """
        SELECT COALESCE(SUM(c.importe), 0)
        FROM cobros c
        JOIN facturas_emitidas f ON f.id = c.factura_id
        WHERE c.owner_user_id = ?
          AND f.owner_user_id = ?
          AND f.estado IN ('emitida', 'cobrada')
          AND c.fecha BETWEEN ? AND ?
        """,
        (owner_user_id, owner_user_id, inicio_mes, fin_mes),
    ).fetchone()[0]

    resumen = {
        "facturado_mes": _to_float(facturado_mes),
        "cobrado_mes": _to_float(cobrado_mes),
        "pendiente_total": sum(item["pendiente"] for item in items.values()),
        "vencido_estimado": sum(
            item["pendiente_cobro"]
            for item in items.values()
            if _es_vencida(item.get("fecha_factura_referencia"), item["pendiente_cobro"], hoy)
        ),
        "total_items": len(items),
        "items_filtrados": len(items_filtrados),
        "filtro": filtro_normalizado,
        "dias_vencimiento_estimado": DIAS_VENCIMIENTO_ESTIMADO,
    }

    return {
        "items": items_filtrados,
        "resumen": resumen,
        "filtros": ESTADOS_WORKBENCH_ECONOMICO,
        "filtro": filtro_normalizado,
        "estado_labels": ESTADO_LABELS_WORKBENCH_ECONOMICO,
    }


def construir_timeline_economico_propuesta(cur, propuesta_id: int, owner_user_id: int) -> list[dict]:
    propuesta = cur.execute(
        """
        SELECT id, numero_propuesta, fecha, total_propuesta, total
        FROM propuestas
        WHERE id = ? AND owner_user_id = ?
        """,
        (propuesta_id, owner_user_id),
    ).fetchone()
    if not propuesta:
        return []
    return _construir_timeline_economico(
        cur,
        owner_user_id,
        propuesta_id=propuesta_id,
        expediente_id=None,
        propuesta=propuesta,
    )


def construir_timeline_economico_expediente(cur, expediente_id: int, owner_user_id: int) -> list[dict]:
    return _construir_timeline_economico(
        cur,
        owner_user_id,
        propuesta_id=None,
        expediente_id=expediente_id,
        propuesta=None,
    )


def _construir_timeline_economico(
    cur,
    owner_user_id: int,
    propuesta_id: int | None,
    expediente_id: int | None,
    propuesta,
) -> list[dict]:
    eventos = []
    referencia_total = 0.0
    if propuesta:
        referencia_total = _to_float(propuesta["total_propuesta"]) or _to_float(propuesta["total"])
        eventos.append(
            {
                "fecha": propuesta["fecha"],
                "tipo": "Propuesta",
                "descripcion": f"Propuesta {propuesta['numero_propuesta']} registrada",
                "importe": referencia_total,
                "url": f"/propuestas/{propuesta['id']}",
            }
        )

    filtro_sql = "f.propuesta_id = ?"
    params = [propuesta_id, owner_user_id]
    if expediente_id is not None:
        filtro_sql = "f.expediente_id = ?"
        params = [expediente_id, owner_user_id]

    facturas = cur.execute(
        f"""
        SELECT f.id, f.numero_factura, f.fecha, f.fecha_emision, f.estado, f.total,
               COALESCE(SUM(CASE WHEN f.estado IN ('emitida', 'cobrada') THEN c.importe ELSE 0 END), 0) AS total_cobrado
        FROM facturas_emitidas f
        LEFT JOIN cobros c ON c.factura_id = f.id AND c.owner_user_id = f.owner_user_id
        WHERE {filtro_sql}
          AND f.owner_user_id = ?
          AND f.estado != 'anulada'
        GROUP BY f.id
        ORDER BY COALESCE(f.fecha_emision, f.fecha) ASC, f.id ASC
        """,
        params,
    ).fetchall()

    total_facturado = 0.0
    total_cobrado = 0.0
    factura_ids = []
    for factura in facturas:
        factura_ids.append(factura["id"])
        if factura["estado"] in ("emitida", "cobrada"):
            total_facturado += _to_float(factura["total"])
            total_cobrado += _to_float(factura["total_cobrado"])
        numero = factura["numero_factura"] or f"Borrador #{factura['id']}"
        descripcion = (
            f"Factura {numero} emitida"
            if factura["estado"] in ("emitida", "cobrada")
            else f"Factura {numero} en borrador"
        )
        eventos.append(
            {
                "fecha": factura["fecha_emision"] or factura["fecha"],
                "tipo": "Factura",
                "descripcion": descripcion,
                "importe": _to_float(factura["total"]),
                "url": f"/facturacion/facturas/{factura['id']}",
            }
        )

    if factura_ids:
        placeholders = ",".join("?" for _ in factura_ids)
        cobros = cur.execute(
            f"""
            SELECT c.fecha, c.importe, c.metodo, c.factura_id
            FROM cobros c
            JOIN facturas_emitidas f ON f.id = c.factura_id
            WHERE c.factura_id IN ({placeholders})
              AND c.owner_user_id = ?
              AND f.estado IN ('emitida', 'cobrada')
            ORDER BY c.fecha ASC, c.id ASC
            """,
            [*factura_ids, owner_user_id],
        ).fetchall()
        for cobro in cobros:
            metodo = _limpiar_texto(cobro["metodo"])
            detalle_metodo = f" · {metodo}" if metodo else ""
            eventos.append(
                {
                    "fecha": cobro["fecha"],
                    "tipo": "Cobro recibido",
                    "descripcion": f"Cobro recibido{detalle_metodo}",
                    "importe": _to_float(cobro["importe"]),
                    "url": f"/facturacion/facturas/{cobro['factura_id']}",
                }
            )

    referencia_total = max(referencia_total, total_facturado)
    if referencia_total > 0 or total_facturado > 0 or total_cobrado > 0:
        eventos.append(
            {
                "fecha": "",
                "tipo": "Pendiente",
                "descripcion": "Pendiente económico estimado",
                "importe": max(referencia_total - total_cobrado, 0),
                "url": "",
            }
        )

    eventos.sort(key=lambda item: (item["fecha"] or "9999-99-99", item["tipo"]))
    return eventos
