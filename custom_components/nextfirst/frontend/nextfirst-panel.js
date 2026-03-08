/*
Purpose:
- Render NextFirst as a Home Assistant sidebar panel with four main views.

Input/Output:
- Input: authenticated Home Assistant session + NextFirst API endpoints.
- Output: interactive UI for open/skipped/experienced/album workflows.

Invariants:
- UI actions call backend APIs and refresh state after each mutation.
- Tabs always map to one product state: Offen, Übersprungen, Erlebt, Album.

Debugging:
- Open browser devtools and inspect failing requests under /api/nextfirst/*.
*/

class NextFirstPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._items = [];
    this._stats = {};
    this._tab = "open";
    this._loading = false;
    this._error = "";
    this._ready = false;
    this._summaryPreview = null;
    this._protocolHistory = [];
    this._pendingMediaExperienceId = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._ready) {
      this._ready = true;
      this._render();
      this._load();
    }
  }

  getCardSize() {
    return 8;
  }

  async _api(method, path, body) {
    return this._hass.callApi(String(method).toUpperCase(), path, body);
  }

  async _load() {
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const data = await this._api("get", "nextfirst/experiences");
      this._items = data.items || [];
      this._stats = data.stats || {};
      const history = await this._api("get", "nextfirst/protocol?limit=50");
      this._protocolHistory = history.history || [];
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _byStatus(status) {
    return this._items.filter((i) => i.status === status);
  }

  _albumItems() {
    return this._items
      .filter((i) => i.status === "experienced" || i.status === "archived")
      .sort((a, b) => (b.completed_at || "").localeCompare(a.completed_at || ""));
  }

  _escape(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  async _create() {
    const title = prompt("Titel des neuen Erlebnisses:");
    if (!title || !title.trim()) return;

    try {
      await this._api("post", "nextfirst/experiences", { title: title.trim() });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _edit(id, currentTitle, currentCategory) {
    const title = prompt("Titel bearbeiten:", currentTitle || "");
    if (title === null) return;
    const category = prompt("Kategorie (optional):", currentCategory || "");
    if (category === null) return;

    try {
      await this._api("patch", `nextfirst/experiences/${id}`, {
        title: title.trim(),
        category: category.trim() || null,
      });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _delete(id) {
    if (!confirm("Eintrag wirklich löschen?")) return;
    try {
      await this._api("delete", `nextfirst/experiences/${id}`);
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _action(id, action, body = {}) {
    try {
      await this._api("post", `nextfirst/experiences/${id}/${action}`, body);
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _markExperienced(id) {
    const note = prompt("Notiz (optional):", "") ?? "";
    const location = prompt("Ort (optional):", "") ?? "";
    await this._action(id, "experience", {
      note: note.trim() || null,
      location: location.trim() || null,
    });
  }

  async _addMedia(id) {
    this._pendingMediaExperienceId = id;
    this.shadowRoot.getElementById("mediaUploadInput")?.click();
  }

  async _uploadMediaFile(file) {
    if (!file || !this._pendingMediaExperienceId) return;
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(
        `/api/nextfirst/experiences/${this._pendingMediaExperienceId}/media/upload`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this._hass.auth.data.accessToken}`,
          },
          body: form,
        }
      );
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Upload fehlgeschlagen (${response.status})`);
      }
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    } finally {
      this._pendingMediaExperienceId = null;
      const input = this.shadowRoot.getElementById("mediaUploadInput");
      if (input) input.value = "";
    }
  }

  async _addNote(id, currentNote) {
    const note = prompt("Notiz:", currentNote || "");
    if (note === null) return;
    await this._action(id, "note", { note });
  }

  async _generateAI() {
    const countRaw = prompt("Wie viele Vorschläge? (1-20)", "5");
    if (countRaw === null) return;
    const count = Number(countRaw);
    try {
      await this._api("post", "nextfirst/ai/generate", {
        count: Number.isFinite(count) ? count : 5,
      });
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _previewMonthlySummary() {
    try {
      const res = await this._api("get", "nextfirst/monthly_summary/preview");
      this._summaryPreview = res.summary || null;
      this._render();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _shareMonthlySummary() {
    const text = prompt("Optional eigener Text für Monatsrückblick:", "") ?? "";
    const hashtags = prompt("Hashtags (kommasepariert, optional):", "") ?? "";
    try {
      const result = await this._api("post", "nextfirst/share/monthly", {
        text: text.trim() || undefined,
        hashtags: hashtags.trim() || undefined,
      });
      this._openShareChooser(result.text, result.share_urls || {});
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  async _shareExperience(id, defaultTitle) {
    const text =
      prompt("Optional eigener Share-Text:", `Neues NextFirst Erlebnis: ${defaultTitle}`) ?? "";
    const hashtags = prompt("Hashtags (kommasepariert, optional):", "") ?? "";
    try {
      const result = await this._api("post", `nextfirst/share/experience/${id}`, {
        text: text.trim() || undefined,
        hashtags: hashtags.trim() || undefined,
      });
      this._openShareChooser(result.text, result.share_urls || {});
      await this._load();
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  _openShareChooser(text, urls) {
    const selection = prompt(
      "Teilen über: instagram, x, facebook, whatsapp oder telegram\n(Hinweis: Text wird in die Zwischenablage kopiert.)",
      "instagram"
    );
    if (!selection) return;
    const provider = selection.trim().toLowerCase();
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    const url = urls[provider];
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  _renderCard(item) {
    const mediaCount = item.media?.length || 0;
    const category = item.category ? `<span class="pill">${this._escape(item.category)}</span>` : "";
    const courage = item.courage_level
      ? `<span class="pill">Mut: ${this._escape(item.courage_level)}</span>`
      : "";

    let actions = "";
    if (item.status === "open") {
      actions = `
        <button data-action="edit" data-id="${item.id}">Bearbeiten</button>
        <button data-action="skip" data-id="${item.id}">Überspringen</button>
        <button data-action="experience" data-id="${item.id}">Als erlebt markieren</button>
        <button class="danger" data-action="delete" data-id="${item.id}">Löschen</button>
      `;
    } else if (item.status === "skipped") {
      actions = `
        <button data-action="reactivate" data-id="${item.id}">Zurück zu offen</button>
        <button data-action="edit" data-id="${item.id}">Bearbeiten</button>
        <button class="danger" data-action="delete" data-id="${item.id}">Löschen</button>
      `;
    } else {
      actions = `
        <button data-action="note" data-id="${item.id}">Notiz bearbeiten</button>
        <button data-action="media" data-id="${item.id}">Bild hinzufügen</button>
        <button data-action="share" data-id="${item.id}">Teilen</button>
        <button data-action="archive" data-id="${item.id}">Ins Archiv</button>
        <button data-action="reactivate" data-id="${item.id}">Erneut planen</button>
      `;
    }

    return `
      <article class="card" data-card-id="${item.id}">
        <header>
          <h3>${this._escape(item.title)}</h3>
          <span class="status status-${item.status}">${this._escape(item.status)}</span>
        </header>
        <div class="meta">
          ${category}
          ${courage}
          <span class="pill">Bilder: ${mediaCount}</span>
          ${item.completed_at ? `<span class="pill">Abschluss: ${this._escape(item.completed_at)}</span>` : ""}
        </div>
        ${item.description ? `<p>${this._escape(item.description)}</p>` : ""}
        ${item.notes ? `<p class="note">Notiz: ${this._escape(item.notes)}</p>` : ""}
        <div class="actions">${actions}</div>
      </article>
    `;
  }

  _renderAlbumItem(item) {
    const media = item.media || [];
    const first = media[0]?.path || "";
    return `
      <article class="album-card">
        ${first ? `<img src="${this._escape(first)}" alt="${this._escape(item.title)}" />` : `<div class="img-fallback">Kein Bild</div>`}
        <div class="album-content">
          <h3>${this._escape(item.title)}</h3>
          <p>${this._escape(item.completed_at || "Kein Abschlussdatum")}</p>
          ${item.location ? `<p>Ort: ${this._escape(item.location)}</p>` : ""}
          ${item.notes ? `<p>${this._escape(item.notes)}</p>` : ""}
        </div>
      </article>
    `;
  }

  _renderBody() {
    if (this._loading) return `<div class="state">Lade NextFirst Daten ...</div>`;
    if (this._error) return `<div class="state error">${this._escape(this._error)}</div>`;

    if (this._tab === "open") {
      const items = this._byStatus("open");
      if (!items.length) return `<div class="state">Keine offenen Erlebnisse.</div>`;
      return items.map((item) => this._renderCard(item)).join("\n");
    }

    if (this._tab === "skipped") {
      const items = this._byStatus("skipped");
      if (!items.length) return `<div class="state">Keine übersprungenen Erlebnisse.</div>`;
      return items.map((item) => this._renderCard(item)).join("\n");
    }

    if (this._tab === "experienced") {
      const items = this._byStatus("experienced");
      if (!items.length) return `<div class="state">Noch keine erlebten Aktivitäten.</div>`;
      return items.map((item) => this._renderCard(item)).join("\n");
    }

    if (this._tab === "social") {
      const preview = this._summaryPreview
        ? `<div class="state"><strong>Monatsvorschau:</strong><br>${this._escape(this._summaryPreview.summary_text || "")}</div>`
        : `<div class="state">Noch keine Monatsvorschau geladen.</div>`;
      const history = this._protocolHistory.length
        ? `<ul class="history">${this._protocolHistory
            .map(
              (h) =>
                `<li><strong>${this._escape(h.timestamp || "-")}</strong> | ${this._escape(
                  h.level || "-"
                )} | ${this._escape(h.action || "-")}<br>${this._escape(h.message || "")}</li>`
            )
            .join("")}</ul>`
        : `<div class="state">Noch keine NextFirst-Protokolleinträge vorhanden.</div>`;

      return `
        <div class="toolbar">
          <button id="previewMonthlyBtn">Monatsvorschau laden</button>
          <button id="shareMonthlyBtn">Monatsrückblick teilen</button>
        </div>
        ${preview}
        ${history}
      `;
    }

    const album = this._albumItems();
    if (!album.length) return `<div class="state">Album ist noch leer.</div>`;
    return `<section class="album-grid">${album.map((item) => this._renderAlbumItem(item)).join("\n")}</section>`;
  }

  _attachEvents() {
    this.shadowRoot.querySelectorAll(".tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._tab = btn.dataset.tab;
        this._render();
      });
    });

    this.shadowRoot.getElementById("createBtn")?.addEventListener("click", () => this._create());
    this.shadowRoot.getElementById("refreshBtn")?.addEventListener("click", () => this._load());
    this.shadowRoot.getElementById("aiBtn")?.addEventListener("click", () => this._generateAI());
    this.shadowRoot
      .getElementById("previewMonthlyBtn")
      ?.addEventListener("click", () => this._previewMonthlySummary());
    this.shadowRoot
      .getElementById("shareMonthlyBtn")
      ?.addEventListener("click", () => this._shareMonthlySummary());
    this.shadowRoot
      .getElementById("mediaUploadInput")
      ?.addEventListener("change", (event) => {
        const file = event?.target?.files?.[0];
        if (file) this._uploadMediaFile(file);
      });

    this.shadowRoot.querySelectorAll("button[data-action]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        const action = btn.dataset.action;
        const item = this._items.find((it) => it.id === id);
        if (!id || !action) return;

        if (action === "edit") return this._edit(id, item?.title, item?.category);
        if (action === "skip") return this._action(id, "skip");
        if (action === "reactivate") return this._action(id, "reactivate");
        if (action === "experience") return this._markExperienced(id);
        if (action === "delete") return this._delete(id);
        if (action === "media") return this._addMedia(id);
        if (action === "note") return this._addNote(id, item?.notes);
        if (action === "share") return this._shareExperience(id, item?.title || "Unbenannt");
        if (action === "archive") return this._action(id, "archive");
      });
    });
  }

  _render() {
    const stats = this._stats || {};

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100%;
          color: var(--primary-text-color);
          background: linear-gradient(135deg, rgba(35, 111, 146, 0.10), rgba(244, 163, 97, 0.12));
          font-family: "Avenir Next", "Segoe UI", sans-serif;
        }
        .wrap {
          max-width: 1100px;
          margin: 0 auto;
          padding: 16px;
        }
        .top {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        h1 {
          margin: 0;
          font-size: 1.4rem;
        }
        .stats {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin: 8px 0 16px;
        }
        .stat {
          background: var(--card-background-color);
          border-radius: 12px;
          padding: 10px 12px;
          border: 1px solid rgba(127,127,127,0.2);
          font-size: 0.9rem;
        }
        .toolbar {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        button {
          border: none;
          border-radius: 10px;
          padding: 8px 12px;
          cursor: pointer;
          background: #236f92;
          color: #fff;
          font-weight: 600;
        }
        button:hover { filter: brightness(1.08); }
        button.danger { background: #b42318; }
        .tabs {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 14px;
        }
        .tab {
          background: #456c80;
          opacity: 0.7;
        }
        .tab.active {
          opacity: 1;
          background: #1f5773;
        }
        .card {
          background: var(--card-background-color);
          border: 1px solid rgba(127,127,127,0.2);
          border-radius: 14px;
          padding: 12px;
          margin-bottom: 10px;
        }
        .card header {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          align-items: baseline;
        }
        .card h3 { margin: 0; }
        .status {
          border-radius: 999px;
          padding: 2px 10px;
          font-size: 0.75rem;
          text-transform: uppercase;
        }
        .status-open { background: #d9f2ff; color: #0b3b53; }
        .status-skipped { background: #fff2cc; color: #6a4d00; }
        .status-experienced, .status-archived { background: #dff7e4; color: #12481f; }
        .meta {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin: 8px 0;
        }
        .pill {
          border-radius: 999px;
          background: rgba(35,111,146,0.12);
          padding: 2px 10px;
          font-size: 0.78rem;
        }
        .actions {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 10px;
        }
        .note {
          font-style: italic;
          color: var(--secondary-text-color);
        }
        .state {
          background: var(--card-background-color);
          border-radius: 10px;
          border: 1px solid rgba(127,127,127,0.2);
          padding: 14px;
        }
        .state.error {
          border-color: #b42318;
          color: #b42318;
        }
        .album-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
          gap: 10px;
        }
        .album-card {
          overflow: hidden;
          border-radius: 12px;
          background: var(--card-background-color);
          border: 1px solid rgba(127,127,127,0.2);
        }
        .album-card img,
        .img-fallback {
          width: 100%;
          height: 180px;
          object-fit: cover;
          display: block;
          background: #d7e7ef;
        }
        .img-fallback {
          display: grid;
          place-items: center;
          color: #496170;
          font-weight: 600;
        }
        .album-content {
          padding: 10px;
        }
        .album-content h3 {
          margin: 0 0 6px;
        }
        .history {
          margin: 12px 0 0;
          padding: 0 0 0 18px;
        }
        .history li {
          margin: 8px 0;
        }
      </style>
      <div class="wrap">
        <div class="top">
          <h1>NextFirst</h1>
          <div class="toolbar">
            <button id="createBtn">Neu</button>
            <button id="aiBtn">KI-Vorschläge</button>
            <button id="refreshBtn">Aktualisieren</button>
          </div>
        </div>

        <div class="stats">
          <div class="stat">Offen: ${stats.open_count ?? 0}</div>
          <div class="stat">Übersprungen: ${stats.skipped_count ?? 0}</div>
          <div class="stat">Erlebt: ${stats.experienced_count ?? 0}</div>
          <div class="stat">Diesen Monat: ${stats.experienced_this_month ?? 0}</div>
        </div>

        <div class="tabs">
          <button class="tab ${this._tab === "open" ? "active" : ""}" data-tab="open">Offen</button>
          <button class="tab ${this._tab === "skipped" ? "active" : ""}" data-tab="skipped">Übersprungen</button>
          <button class="tab ${this._tab === "experienced" ? "active" : ""}" data-tab="experienced">Erlebt</button>
          <button class="tab ${this._tab === "social" ? "active" : ""}" data-tab="social">Social</button>
          <button class="tab ${this._tab === "album" ? "active" : ""}" data-tab="album">Album</button>
        </div>

        <section>${this._renderBody()}</section>
        <input id="mediaUploadInput" type="file" accept="image/*" style="display:none" />
      </div>
    `;

    this._attachEvents();
  }
}

customElements.define("nextfirst-panel", NextFirstPanel);
