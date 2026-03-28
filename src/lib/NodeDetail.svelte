<script lang="ts">
  import {
    nodeById,
    getNodes,
    updateNode,
    removeNode,
    addLink,
    removeLink,
    outgoingGrouped,
    addNode,
  } from './pfq.svelte';
  import { rankByFuzzy } from './fuzzy';
  import { LINK_TYPES_SUGGESTED } from './types';

  interface Props {
    nodeId: string;
    selectNode: (id: string) => void;
    onNodeDeleted?: () => void;
  }

  let { nodeId, selectNode, onNodeDeleted }: Props = $props();

  let description = $state('');
  let context = $state('');
  let type = $state('');
  let status = $state('');

  let linkType = $state('how');
  let linkCustomType = $state('');
  let linkSearch = $state('');
  let createDesc = $state('');
  let showCreate = $state(false);

  $effect(() => {
    const n = nodeById(nodeId);
    if (n) {
      description = n.description;
      context = n.context;
      type = n.type;
      status = n.status;
    }
  });

  const grouped = $derived(outgoingGrouped(nodeId));

  const existingTgtIds = $derived(
    new Set([...grouped.why, ...grouped.how, ...grouped.rest].map((l) => l.tgt_id)),
  );

  const linkCandidates = $derived.by(() => {
    const all = getNodes().filter((n) => n.id !== nodeId && !existingTgtIds.has(n.id));
    const q = linkSearch.trim();
    if (!q) return all.slice(0, 12);
    return rankByFuzzy(all, q, (n) => `${n.description} ${n.context}`).slice(0, 12);
  });

  function resolvedLinkType(): string {
    if (linkType === '__custom__') return linkCustomType.trim() || 'how';
    return linkType;
  }

  function save() {
    updateNode(nodeId, { description, context, type, status });
  }

  function delNode() {
    if (!confirm('Supprimer ce nœud et ses liens ?')) return;
    removeNode(nodeId);
    onNodeDeleted?.();
  }

  function linkTo(tgtId: string) {
    const t = resolvedLinkType();
    addLink(nodeId, tgtId, t);
    linkSearch = '';
    showCreate = false;
  }

  function createAndLink() {
    const d = createDesc.trim();
    if (!d) return;
    const n = addNode({ description: d });
    addLink(nodeId, n.id, resolvedLinkType());
    createDesc = '';
    showCreate = false;
    linkSearch = '';
  }

  function tgtNode(id: string) {
    return nodeById(id);
  }
</script>

{#if nodeById(nodeId)}
  <article class="detail">
    <header class="head">
      <h1>Édition</h1>
      <button type="button" class="btn danger" onclick={delNode}>Supprimer</button>
    </header>

    <div class="fields">
      <label class="field">
        <span>Description</span>
        <input type="text" bind:value={description} onchange={save} />
      </label>
      <label class="field">
        <span>Contexte</span>
        <textarea rows="5" bind:value={context} onchange={save}></textarea>
      </label>
      <div class="row2">
        <label class="field">
          <span>Type</span>
          <input type="text" bind:value={type} onchange={save} />
        </label>
        <label class="field">
          <span>Statut</span>
          <input type="text" bind:value={status} onchange={save} />
        </label>
      </div>
      <p class="dates">
        <small
          >Créé : {nodeById(nodeId)!.creation_date.slice(0, 19).replace('T', ' ')} · Modifié : {nodeById(
            nodeId,
          )!.last_modification_date.slice(0, 19).replace('T', ' ')}</small
        >
      </p>
    </div>

    <section class="relations">
      <h2>Pourquoi (liens <code>why</code>)</h2>
      <p class="help">Objectifs ou raisons vers lesquels ce nœud pointe — le « pourquoi » au-dessus.</p>
      <ul class="link-list">
        {#each grouped.why as l (l.id)}
          <li>
            <span class="lt">{l.type}</span>
            {#if tgtNode(l.tgt_id)}
              <button type="button" class="node-ref linkish" onclick={() => selectNode(l.tgt_id)}>
                {tgtNode(l.tgt_id)!.description}
              </button>
            {:else}
              <em>(nœud manquant)</em>
            {/if}
            <button type="button" class="btn mini" onclick={() => removeLink(l.id)}>Retirer</button>
          </li>
        {:else}
          <li class="empty">Aucun lien « why » sortant.</li>
        {/each}
      </ul>

      <h2>Comment & autres</h2>
      <p class="help">Sous-objectifs (<code>how</code>) puis autres types de liens.</p>

      <h3 class="subh">Comment (<code>how</code>)</h3>
      <ul class="link-list">
        {#each grouped.how as l (l.id)}
          <li>
            <span class="lt">{l.type}</span>
            {#if tgtNode(l.tgt_id)}
              <button type="button" class="node-ref linkish" onclick={() => selectNode(l.tgt_id)}>
                {tgtNode(l.tgt_id)!.description}
              </button>
            {:else}
              <em>(nœud manquant)</em>
            {/if}
            <button type="button" class="btn mini" onclick={() => removeLink(l.id)}>Retirer</button>
          </li>
        {:else}
          <li class="empty">Aucun lien « how ».</li>
        {/each}
      </ul>

      {#if grouped.rest.length > 0}
        <h3 class="subh">Autres types</h3>
        <ul class="link-list">
          {#each grouped.rest as l (l.id)}
            <li>
              <span class="lt">{l.type}</span>
              {#if tgtNode(l.tgt_id)}
                <button type="button" class="node-ref linkish" onclick={() => selectNode(l.tgt_id)}>
                  {tgtNode(l.tgt_id)!.description}
                </button>
              {:else}
                <em>(nœud manquant)</em>
              {/if}
              <button type="button" class="btn mini" onclick={() => removeLink(l.id)}>Retirer</button>
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    <section class="add-link">
      <h2>Ajouter un lien sortant</h2>
      <p class="help">Depuis ce nœud vers un autre : choisissez le type, puis un nœud existant ou un nouveau.</p>

      <div class="link-form">
        <label>
          Type
          <select bind:value={linkType}>
            {#each LINK_TYPES_SUGGESTED as t}
              <option value={t}>{t}</option>
            {/each}
            <option value="__custom__">(autre…)</option>
          </select>
        </label>
        {#if linkType === '__custom__'}
          <input type="text" placeholder="type personnalisé" bind:value={linkCustomType} />
        {/if}
      </div>

      <div class="pick">
        <input
          type="search"
          placeholder="Rechercher un nœud cible…"
          bind:value={linkSearch}
          autocomplete="off"
        />
        {#if !showCreate}
          <button type="button" class="btn" onclick={() => (showCreate = true)}>Créer un nœud…</button>
        {/if}
      </div>

      {#if showCreate}
        <div class="create-box">
          <input type="text" placeholder="Description du nouveau nœud" bind:value={createDesc} />
          <button type="button" class="btn primary" onclick={createAndLink}>Créer et lier</button>
          <button type="button" class="btn ghost" onclick={() => (showCreate = false)}>Annuler</button>
        </div>
      {/if}

      <ul class="candidates">
        {#each linkCandidates as n (n.id)}
          <li>
            <button type="button" class="cand" onclick={() => linkTo(n.id)}>
              <span>{n.description}</span>
              <span class="meta">{n.type}</span>
            </button>
          </li>
        {:else}
          <li class="empty">Aucun résultat (ou tous déjà liés).</li>
        {/each}
      </ul>
    </section>
  </article>
{:else}
  <p class="missing">Nœud introuvable.</p>
{/if}

<style>
  .detail {
    max-width: 52rem;
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  h1 {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0;
  }

  h2 {
    font-size: 1rem;
    margin: 1.5rem 0 0.35rem;
    font-weight: 600;
  }

  .subh {
    font-size: 0.9rem;
    margin: 1rem 0 0.35rem;
    font-weight: 600;
    color: var(--muted);
  }

  .help {
    margin: 0 0 0.5rem;
    font-size: 0.85rem;
    color: var(--muted);
  }

  .fields {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }

  .field span {
    color: var(--muted);
  }

  .field input,
  .field textarea {
    padding: 0.45rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    width: 100%;
  }

  .row2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  @media (max-width: 520px) {
    .row2 {
      grid-template-columns: 1fr;
    }
  }

  .dates {
    margin: 0;
    color: var(--muted);
  }

  .link-list {
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }

  .link-list li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 0.65rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.92rem;
  }

  .link-list li:last-child {
    border-bottom: none;
  }

  .link-list .empty {
    color: var(--muted);
    font-style: italic;
  }

  .lt {
    font-family: var(--mono);
    font-size: 0.8rem;
    background: var(--bg);
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
  }

  .node-ref {
    flex: 1;
    min-width: 0;
    text-align: left;
  }

  .node-ref.linkish {
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 2px;
    font: inherit;
  }

  .node-ref.linkish:hover {
    color: #1d4ed8;
  }

  .btn {
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .btn.mini {
    margin-left: auto;
  }

  .btn.danger {
    color: var(--danger);
    border-color: #fecaca;
  }

  .btn.primary {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }

  .btn.ghost {
    background: transparent;
  }

  .add-link {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  .link-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: flex-end;
    margin-bottom: 0.75rem;
  }

  .link-form label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
    color: var(--muted);
  }

  .pick {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .pick input[type='search'] {
    flex: 1;
    min-width: 12rem;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
  }

  .create-box {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.75rem;
    padding: 0.75rem;
    background: var(--bg);
    border-radius: 8px;
  }

  .create-box input {
    flex: 1;
    min-width: 10rem;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
  }

  .candidates {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .cand {
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.4rem 0.5rem;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
  }

  .cand:hover {
    background: var(--accent-muted);
  }

  .cand .meta {
    font-size: 0.75rem;
    color: var(--muted);
    font-family: var(--mono);
  }

  .missing {
    color: var(--muted);
  }

  code {
    font-family: var(--mono);
    font-size: 0.88em;
  }
</style>
