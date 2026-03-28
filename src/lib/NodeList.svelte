<script lang="ts">
  import { getNodes } from './pfq.svelte';
  import { rankByFuzzy } from './fuzzy';

  interface Props {
    selectedId: string | null;
    newNode: () => void;
  }

  let { selectedId = $bindable(null), newNode }: Props = $props();

  let query = $state('');

  const all = $derived(getNodes());

  const filtered = $derived.by(() => {
    const q = query.trim();
    if (!q) return [...all].sort((a, b) => b.last_modification_date.localeCompare(a.last_modification_date));
    return rankByFuzzy(all, q, (n) => `${n.description} ${n.context} ${n.type} ${n.status}`);
  });

  function select(id: string) {
    selectedId = id;
  }
</script>

<div class="panel">
  <div class="toolbar">
    <input
      type="search"
      class="search"
      placeholder="Recherche floue…"
      bind:value={query}
      autocomplete="off"
    />
    <button type="button" class="btn primary" onclick={newNode}>+ Nouveau</button>
  </div>

  <ul class="list" role="listbox" aria-label="Nœuds">
    {#each filtered as n (n.id)}
      <li>
        <button
          type="button"
          class="row"
          class:active={selectedId === n.id}
          onclick={() => select(n.id)}
        >
          <span class="desc">{n.description || '—'}</span>
          <span class="meta">{n.type}</span>
        </button>
      </li>
    {:else}
      <li class="empty-li">Aucun nœud{query.trim() ? ' correspondant' : ''}.</li>
    {/each}
  </ul>
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }

  .btn {
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 0.35rem 0.55rem;
    border-radius: 6px;
    font-size: 0.88rem;
  }

  .toolbar {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .search {
    width: 100%;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
  }

  .btn.primary {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }

  .btn.primary:hover {
    filter: brightness(1.05);
  }

  .list {
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
    overflow: auto;
    flex: 1;
  }

  .row {
    width: 100%;
    text-align: left;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.15rem;
    padding: 0.45rem 0.75rem;
    border: none;
    background: transparent;
    border-left: 3px solid transparent;
  }

  .row:hover {
    background: var(--bg);
  }

  .row.active {
    background: var(--accent-muted);
    border-left-color: var(--accent);
  }

  .desc {
    font-size: 0.92rem;
    line-clamp: 2;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .meta {
    font-size: 0.75rem;
    color: var(--muted);
    font-family: var(--mono);
  }

  .empty-li {
    padding: 1rem 0.75rem;
    color: var(--muted);
    font-size: 0.9rem;
  }
</style>
