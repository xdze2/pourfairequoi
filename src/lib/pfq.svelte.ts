import type { Link, Node, PfqSnapshot } from './types';
import { newId } from './id';

const STORAGE_KEY = 'pfq-v1';

function nowIso(): string {
  return new Date().toISOString();
}

function emptySnapshot(): PfqSnapshot {
  return { version: 1, nodes: [], links: [] };
}

function loadFromStorage(): PfqSnapshot {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptySnapshot();
    const data = JSON.parse(raw) as PfqSnapshot;
    if (data?.version !== 1 || !Array.isArray(data.nodes) || !Array.isArray(data.links)) {
      return emptySnapshot();
    }
    return data;
  } catch {
    return emptySnapshot();
  }
}

function persist(): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, nodes, links } satisfies PfqSnapshot));
}

let nodes = $state<Node[]>([]);
let links = $state<Link[]>([]);
let hydrated = $state(false);

export function pfqInit(): void {
  if (hydrated) return;
  const s = loadFromStorage();
  nodes = s.nodes;
  links = s.links;
  hydrated = true;
}

export function getNodes(): Node[] {
  return nodes;
}

export function getLinks(): Link[] {
  return links;
}

export function addNode(partial: Partial<Omit<Node, 'id' | 'creation_date' | 'last_modification_date'>> & { description: string }): Node {
  const t = nowIso();
  const n: Node = {
    id: newId(),
    description: partial.description,
    context: partial.context ?? '',
    type: partial.type ?? 'goal',
    status: partial.status ?? 'open',
    creation_date: t,
    last_modification_date: t,
  };
  nodes = [...nodes, n];
  persist();
  return n;
}

export function updateNode(id: string, patch: Partial<Pick<Node, 'description' | 'context' | 'type' | 'status'>>): void {
  const t = nowIso();
  nodes = nodes.map((n) =>
    n.id === id ? { ...n, ...patch, last_modification_date: t } : n,
  );
  persist();
}

export function removeNode(id: string): void {
  nodes = nodes.filter((n) => n.id !== id);
  links = links.filter((l) => l.src_id !== id && l.tgt_id !== id);
  persist();
}

export function nodeById(id: string | null): Node | undefined {
  if (!id) return undefined;
  return nodes.find((n) => n.id === id);
}

export function addLink(src_id: string, tgt_id: string, type: string): Link | null {
  if (src_id === tgt_id) return null;
  const dup = links.some((l) => l.src_id === src_id && l.tgt_id === tgt_id && l.type === type);
  if (dup) return null;
  const l: Link = {
    id: newId(),
    src_id,
    tgt_id,
    type: type.trim() || 'how',
    creation_date: nowIso(),
  };
  links = [...links, l];
  persist();
  return l;
}

export function removeLink(linkId: string): void {
  links = links.filter((l) => l.id !== linkId);
  persist();
}

/** Outgoing links from node, grouped for UI */
export function outgoingGrouped(nodeId: string): { why: Link[]; how: Link[]; rest: Link[] } {
  const out = links.filter((l) => l.src_id === nodeId);
  const why: Link[] = [];
  const how: Link[] = [];
  const rest: Link[] = [];
  for (const l of out) {
    const lt = l.type.toLowerCase();
    if (lt === 'why') why.push(l);
    else if (lt === 'how') how.push(l);
    else rest.push(l);
  }
  return { why, how, rest };
}

export function exportJson(): string {
  return JSON.stringify({ version: 1 as const, nodes, links }, null, 2);
}

function normalizeImportedLinks(raw: unknown[]): Link[] {
  const out: Link[] = [];
  for (const r of raw) {
    if (!r || typeof r !== 'object') continue;
    const o = r as Record<string, unknown>;
    const src = o.src_id;
    const tgt = o.tgt_id;
    const typ = o.type;
    if (typeof src !== 'string' || typeof tgt !== 'string' || typeof typ !== 'string') continue;
    const id = typeof o.id === 'string' ? o.id : newId();
    const cd = typeof o.creation_date === 'string' ? o.creation_date : nowIso();
    out.push({ id, src_id: src, tgt_id: tgt, type: typ, creation_date: cd });
  }
  return out;
}

export function importJson(text: string): { ok: true } | { ok: false; error: string } {
  try {
    const data = JSON.parse(text) as Record<string, unknown>;
    if (data?.version !== 1 || !Array.isArray(data.nodes) || !Array.isArray(data.links)) {
      return { ok: false, error: 'Format JSON invalide (attendu: version 1, nodes, links).' };
    }
    const nextNodes: Node[] = [];
    for (const n of data.nodes) {
      if (!n || typeof n !== 'object') continue;
      const o = n as Record<string, unknown>;
      if (typeof o.id !== 'string' || typeof o.description !== 'string') continue;
      nextNodes.push({
        id: o.id,
        description: o.description,
        context: typeof o.context === 'string' ? o.context : '',
        type: typeof o.type === 'string' ? o.type : 'goal',
        status: typeof o.status === 'string' ? o.status : 'open',
        creation_date: typeof o.creation_date === 'string' ? o.creation_date : nowIso(),
        last_modification_date:
          typeof o.last_modification_date === 'string' ? o.last_modification_date : nowIso(),
      });
    }
    nodes = nextNodes;
    links = normalizeImportedLinks(data.links);
    persist();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : 'Erreur de lecture JSON.' };
  }
}

export function downloadExport(filename = 'pfq-export.json'): void {
  const blob = new Blob([exportJson()], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
