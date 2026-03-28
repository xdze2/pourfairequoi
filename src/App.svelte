<script lang="ts">
  import { onMount } from 'svelte';
  import { pfqInit, addNode, importJson, downloadExport } from './lib/pfq.svelte';
  import NodeList from './lib/NodeList.svelte';
  import NodeDetail from './lib/NodeDetail.svelte';

  let selectedId = $state<string | null>(null);
  let importError = $state<string | null>(null);
  let fileInput: HTMLInputElement | undefined = $state();

  onMount(() => {
    pfqInit();
  });

  function newNode() {
    const n = addNode({ description: 'Nouveau nœud' });
    selectedId = n.id;
  }

  function onImportFile(ev: Event) {
    importError = null;
    const input = ev.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === 'string' ? reader.result : '';
      const r = importJson(text);
      if (!r.ok) importError = r.error;
      else selectedId = null;
      input.value = '';
    };
    reader.readAsText(file);
  }

  function exportData() {
    downloadExport();
  }
</script>

<div class="app">
  <header class="header">
    <div class="brand">
      <span class="abbr">pfq</span>
      <span class="title">pourfairequoi</span>
    </div>
    <div class="header-actions">
      <input
        bind:this={fileInput}
        type="file"
        accept="application/json,.json"
        class="sr-only"
        onchange={onImportFile}
      />
      <button type="button" class="btn ghost" onclick={() => fileInput?.click()}>Importer JSON</button>
      <button type="button" class="btn ghost" onclick={exportData}>Exporter JSON</button>
    </div>
  </header>

  {#if importError}
    <p class="banner error" role="alert">{importError}</p>
  {/if}

  <main class="main">
    <aside class="sidebar">
      <NodeList bind:selectedId {newNode} />
    </aside>
    <section class="content">
      {#if selectedId}
        <NodeDetail
          nodeId={selectedId}
          selectNode={(id) => (selectedId = id)}
          onNodeDeleted={() => (selectedId = null)}
        />
      {:else}
        <div class="empty">
          <p>Sélectionnez un nœud dans la liste ou créez-en un.</p>
          <p class="hint">Les liens <strong>why</strong> et <strong>how</strong> structurent le « pourquoi » et le « comment ».</p>
        </div>
      {/if}
    </section>
  </main>
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 100vh;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.65rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .abbr {
    font-weight: 700;
    font-family: var(--mono);
    letter-spacing: -0.02em;
  }

  .title {
    color: var(--muted);
    font-size: 0.9rem;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .btn {
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 0.35rem 0.65rem;
    border-radius: 6px;
  }

  .btn.ghost:hover {
    background: var(--accent-muted);
    border-color: var(--accent);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .banner {
    margin: 0;
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }

  .banner.error {
    background: #fef2f2;
    color: var(--danger);
    border-bottom: 1px solid #fecaca;
  }

  .main {
    display: grid;
    grid-template-columns: minmax(240px, 320px) 1fr;
    flex: 1;
    min-height: 0;
  }

  .sidebar {
    border-right: 1px solid var(--border);
    background: var(--surface);
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .content {
    min-width: 0;
    overflow: auto;
    padding: 1rem 1.25rem;
  }

  .empty {
    max-width: 36rem;
    color: var(--muted);
  }

  .empty .hint {
    font-size: 0.9rem;
    margin-top: 1rem;
  }

  @media (max-width: 720px) {
    .main {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
    }

    .sidebar {
      border-right: none;
      border-bottom: 1px solid var(--border);
      max-height: 45vh;
    }
  }
</style>
