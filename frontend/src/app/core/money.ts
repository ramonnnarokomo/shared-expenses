/**
 * Turns the text typed by the user into integer cents: "12,34" and "12.34" -> 1234, "12,5" -> 1250.
 *
 * It works on the text itself (euros + decimals glued together), never multiplying a float
 * by 100, so there are no rounding surprises like 0.29 * 100 = 28.999999999999996.
 * Returns null when the text is not a valid amount with up to 2 decimals.
 */
export function parseEurosToCents(text: string): number | null {
  const match = /^(\d{1,7})(?:[.,](\d{1,2}))?$/.exec(text.trim());
  if (!match) {
    return null;
  }
  const euros = match[1];
  const decimals = (match[2] ?? '').padEnd(2, '0');
  return Number(euros + decimals);
}

/** 123456 cents -> "1234,56 €" (Spanish format). */
export function formatMoney(cents: number, currency: string): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency }).format(cents / 100);
}
