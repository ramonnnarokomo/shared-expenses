# Gastos compartidos · frontend

Interfaz en Angular 21 para la API de `../backend`. Componentes standalone, signals,
control flow nuevo (`@if`, `@for`), `inject()` y `HttpClient` con `withFetch()`. Sin librerías de UI.

## Requisitos

- Node.js 20.19+, 22.12+ o 24+ (lo pide Angular CLI 21)
- El backend arrancado en `http://localhost:8000`

## Arrancar

```bash
npm install
npm start          # ng serve en http://localhost:4200
```

`proxy.conf.json` redirige `/api` al backend, así que no hace falta configurar CORS.

## Tests y build

```bash
npx ng test --watch=false   # Vitest + jsdom
npx ng build
```

## Estructura

```
src/app/
  core/           API, modelos, dinero (parseo y formato), reparto a partes iguales, toasts
  groups/         Pantalla "Grupos": listado + formulario de nuevo grupo
  group-detail/   Detalle de grupo: gastos, balances, cómo saldar cuentas, personas, pagos
```

El dinero siempre viaja en céntimos enteros. El importe que escribe el usuario ("12,34" o "12.34")
se convierte a céntimos trabajando con el texto, nunca multiplicando decimales (ver `core/money.ts`).
