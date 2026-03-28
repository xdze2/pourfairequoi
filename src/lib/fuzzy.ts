/** Lightweight fuzzy match: returns score 0–1 (higher is better). */
export function fuzzyScore(query: string, text: string): number {
  const q = query.trim().toLowerCase();
  const t = text.toLowerCase();
  if (!q) return 1;
  if (!t) return 0;
  if (t.includes(q)) return 1;
  const qChars = [...q];
  let ti = 0;
  let consecutive = 0;
  let best = 0;
  for (const ch of qChars) {
    const j = t.indexOf(ch, ti);
    if (j === -1) return 0;
    consecutive = j === ti ? consecutive + 1 : 1;
    best += consecutive;
    ti = j + 1;
  }
  const norm = best / (qChars.length * (t.length + 1));
  return Math.min(1, norm * 2);
}

export function rankByFuzzy<T>(items: T[], query: string, getText: (item: T) => string): T[] {
  if (!query.trim()) return [...items];
  return [...items]
    .map((item) => ({ item, s: fuzzyScore(query, getText(item)) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s)
    .map((x) => x.item);
}
