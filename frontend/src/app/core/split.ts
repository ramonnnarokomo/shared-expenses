/**
 * Splits an amount in equal parts, with the same rule as the backend: the cents that
 * cannot be divided go one by one to the first members of the list.
 * Example: 1000 cents among 3 members -> 334, 333, 333.
 *
 * Returns a map of member id -> cents, used to preview the split before saving.
 */
export function splitEqually(totalCents: number, memberIds: number[]): Map<number, number> {
  const shares = new Map<number, number>();
  if (memberIds.length === 0) {
    return shares;
  }
  const remainder = totalCents % memberIds.length;
  const base = (totalCents - remainder) / memberIds.length; // exact integer division
  memberIds.forEach((memberId, position) => {
    shares.set(memberId, position < remainder ? base + 1 : base);
  });
  return shares;
}
