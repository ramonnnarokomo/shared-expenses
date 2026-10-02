import { splitEqually } from './split';

describe('splitEqually', () => {
  it('gives the extra cents to the first members', () => {
    expect([...splitEqually(1000, [1, 2, 3]).values()]).toEqual([334, 333, 333]);
    expect([...splitEqually(8450, [1, 2, 3]).values()]).toEqual([2817, 2817, 2816]);
  });

  it('follows the order of the list it receives', () => {
    const shares = splitEqually(1000, [3, 1, 2]);
    expect(shares.get(3)).toBe(334);
    expect(shares.get(1)).toBe(333);
    expect(shares.get(2)).toBe(333);
  });

  it('always adds up to the total', () => {
    for (const total of [1, 7, 99, 4910, 123457]) {
      for (const people of [1, 2, 3, 4, 7]) {
        const ids = Array.from({ length: people }, (_, index) => index + 1);
        const sum = [...splitEqually(total, ids).values()].reduce((a, b) => a + b, 0);
        expect(sum).toBe(total);
      }
    }
  });

  it('returns no shares when nobody is selected', () => {
    expect(splitEqually(1000, []).size).toBe(0);
  });
});
