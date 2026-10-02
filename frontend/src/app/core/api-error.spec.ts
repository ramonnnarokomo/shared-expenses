import { HttpErrorResponse } from '@angular/common/http';

import { CONNECTION_ERROR_MESSAGE, apiErrorMessage } from './api-error';

describe('apiErrorMessage', () => {
  it('explains that the backend is not running', () => {
    expect(apiErrorMessage(new HttpErrorResponse({ status: 0 }))).toBe(CONNECTION_ERROR_MESSAGE);
    // What the Angular dev-server proxy answers when nothing listens on port 8000.
    expect(apiErrorMessage(new HttpErrorResponse({ status: 502, error: '' }))).toBe(
      CONNECTION_ERROR_MESSAGE,
    );
  });

  it('shows the Spanish message sent by the backend', () => {
    const error = new HttpErrorResponse({ status: 404, error: { detail: 'Grupo no encontrado' } });
    expect(apiErrorMessage(error)).toBe('Grupo no encontrado');
  });

  it('uses a generic message for FastAPI validation errors', () => {
    const error = new HttpErrorResponse({
      status: 422,
      error: { detail: [{ msg: 'Field required' }] },
    });
    expect(apiErrorMessage(error)).toBe('Hay algún dato no válido. Revisa el formulario.');
  });

  it('includes the status code of unexpected errors', () => {
    const error = new HttpErrorResponse({ status: 500, error: 'Internal Server Error' });
    expect(apiErrorMessage(error)).toBe('Ha ocurrido un error inesperado (código 500).');
  });
});
