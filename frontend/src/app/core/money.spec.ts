import { formatMoney, parseEurosToCents } from './money';

describe('parseEurosToCents', () => {
  it('accepts a comma or a dot as decimal separator', () => {
    expect(parseEurosToCents('12,34')).toBe(1234);
    expect(parseEurosToCents('12.34')).toBe(1234);
  });

  it('accepts whole amounts and a single decimal', () => {
    expect(parseEurosToCents('12')).toBe(1200);
    expect(parseEurosToCents('12,5')).toBe(1250);
    expect(parseEurosToCents('0,05')).toBe(5);
  });

  it('ignores spaces around the number', () => {
    expect(parseEurosToCents('  84,50 ')).toBe(8450);
  });

  it('is exact where multiplying floats is not', () => {
    // In JavaScript 0.29 * 100 === 28.999999999999996 and 4.35 * 100 === 434.99999999999994
    expect(parseEurosToCents('0,29')).toBe(29);
    expect(parseEurosToCents('4.35')).toBe(435);
    expect(parseEurosToCents('1,15')).toBe(115);
  });

  it.each(['', 'abc', '12,345', '-5', '1.234,56', '12,', ',5', '1e3', '12 34'])(
    'rejects "%s"',
    (text) => {
      expect(parseEurosToCents(text)).toBeNull();
    },
  );
});

describe('formatMoney', () => {
  // Intl puts a non-breaking space before the symbol; we normalize it to compare.
  const format = (cents: number, currency = 'EUR') =>
    formatMoney(cents, currency).replace(/\s/g, ' ');

  it('formats cents the Spanish way', () => {
    expect(format(2340)).toBe('23,40 €');
    expect(format(5)).toBe('0,05 €');
    expect(format(1234567)).toBe('12.345,67 €');
  });

  it('uses the currency of the group', () => {
    expect(format(2340, 'USD')).toBe('23,40 US$');
  });
});
