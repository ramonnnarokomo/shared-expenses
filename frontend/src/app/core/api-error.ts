import { HttpErrorResponse } from '@angular/common/http';

export const CONNECTION_ERROR_MESSAGE =
  'No se puede conectar con la API. ¿Está arrancado el backend en el puerto 8000?';

/** Turns any error from an API call into a message we can show to the user. */
export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof HttpErrorResponse)) {
    return 'Ha ocurrido un error inesperado.';
  }
  // 0: the browser could not reach the server at all.
  // 502/503/504: the dev-server proxy is up, but it could not reach the backend.
  if ([0, 502, 503, 504].includes(error.status)) {
    return CONNECTION_ERROR_MESSAGE;
  }
  // Our backend sends business errors and 404s as {"detail": "mensaje en español"}.
  if (typeof error.error?.detail === 'string') {
    return error.error.detail;
  }
  if (error.status === 422) {
    return 'Hay algún dato no válido. Revisa el formulario.';
  }
  return `Ha ocurrido un error inesperado (código ${error.status}).`;
}
