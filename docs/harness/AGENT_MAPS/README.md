# Agent Maps

Mapas legibles para que Codex entienda rutas, datos y flujos criticos sin cargar contexto excesivo.

## Mapas disponibles

- [route_map.md](route_map.md): areas de rutas conocidas.
- [db_map.md](db_map.md): mapa prudente de SQLite y reglas de uso.
- [critical_flows.md](critical_flows.md): flujos operativos principales.

## Reglas

- No inventar endpoints.
- No leer DB real para completar mapas.
- Actualizar mapas cuando una tarea verifique codigo real.
- Mantenerlos como indices, no como duplicados completos del codigo.

