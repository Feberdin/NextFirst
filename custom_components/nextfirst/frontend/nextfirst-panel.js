/*
Purpose:
- Render NextFirst as a Home Assistant sidebar panel with core list workflows.

Input/Output:
- Input: authenticated Home Assistant session + NextFirst API endpoints.
- Output: interactive UI for open/skipped/experienced/protocol/album views.

Invariants:
- UI actions call backend APIs and refresh state after each mutation.
- Upload uses authenticated HA API call (JSON base64) to avoid browser auth issues.
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
    this._shareData = null;
    this._debugEnabled = false;
    this._aiPromptPreviewText = "";
    this._aiGenerating = false;
    this._aiProgressValue = 0;
    this._aiProgressStartedAt = 0;
    this._aiProgressTimer = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._ready) {
      this._ready = true;
      this._render();
      this._load();
    }
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
      this._debugEnabled = Boolean(data.debug_enabled);
      const history = await this._api("get", "nextfirst/protocol?limit=50");
      this._protocolHistory = history.history || [];
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _escape(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  _formatError(err) {
    if (!err) return "Unbekannter Fehler";
    if (typeof err === "string") return err;
    if (err?.message && typeof err.message === "string") return err.message;
    if (err?.error && typeof err.error === "string") return err.error;
    try {
      return JSON.stringify(err);
    } catch (jsonErr) {
      return String(err);
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

  _resolveMediaUrl(path) {
    const clean = String(path || "").trim();
    if (!clean) return "";
    if (clean.startsWith("/media/")) return "";
    return clean;
  }

  async _create() {
    const title = prompt("Titel des neuen Erlebnisses:");
    if (!title || !title.trim()) return;
    try {
      await this._api("post", "nextfirst/experiences", { title: title.trim() });
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
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
      this._error = this._formatError(err);
      this._render();
    }
  }

  async _delete(id) {
    if (!confirm("Eintrag wirklich löschen?")) return;
    try {
      await this._api("delete", `nextfirst/experiences/${id}`);
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    }
  }

  async _action(id, action, body = {}) {
    try {
      await this._api("post", `nextfirst/experiences/${id}/${action}`, body);
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
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

  _fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("Datei-Lesen fehlgeschlagen."));
      reader.readAsDataURL(file);
    });
  }

  async _uploadMediaFile(file) {
    if (!file || !this._pendingMediaExperienceId) return;
    try {
      const dataUrl = await this._fileToDataUrl(file);
      const contentBase64 = String(dataUrl).split(",")[1] || "";
      if (!contentBase64) throw new Error("Datei konnte nicht gelesen werden.");

      const res = await this._api(
        "post",
        `nextfirst/experiences/${this._pendingMediaExperienceId}/media/upload_json`,
        {
          filename: file.name || "upload.jpg",
          mime_type: file.type || "image/jpeg",
          content_base64: contentBase64,
        }
      );
      if (!res?.ok) throw new Error(res?.error || "Upload fehlgeschlagen.");
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
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
    if (this._aiGenerating) return;
    if (this._debugEnabled && !this._aiPromptPreviewText) {
      try {
        const res = await this._api("get", "nextfirst/ai/prompt_preview");
        const preview = res.preview || {};
        this._aiPromptPreviewText = [
          `Provider: ${preview.provider || "-"}`,
          `Modell: ${preview.model || "-"}`,
          "",
          "[System Prompt]",
          String(preview.system_prompt || ""),
          "",
          "[User Prompt JSON]",
          JSON.stringify(preview.user_prompt || {}, null, 2),
        ].join("\n");
        this._render();
        return;
      } catch (err) {
        this._error = this._formatError(err);
        this._render();
        return;
      }
    }

    this._startAiProgress();
    try {
      await this._api("post", "nextfirst/ai/generate", {});
      this._aiPromptPreviewText = "";
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    } finally {
      this._stopAiProgress();
    }
  }

  _startAiProgress() {
    this._aiGenerating = true;
    this._aiProgressValue = 5;
    this._aiProgressStartedAt = Date.now();
    if (this._aiProgressTimer) clearInterval(this._aiProgressTimer);
    this._aiProgressTimer = setInterval(() => {
      if (!this._aiGenerating) return;
      this._aiProgressValue = Math.min(90, this._aiProgressValue + 3);
      this._render();
    }, 400);
    this._render();
  }

  _stopAiProgress() {
    this._aiGenerating = false;
    this._aiProgressValue = 100;
    if (this._aiProgressTimer) {
      clearInterval(this._aiProgressTimer);
      this._aiProgressTimer = null;
    }
    this._render();
    setTimeout(() => {
      if (this._aiGenerating) return;
      this._aiProgressValue = 0;
      this._render();
    }, 700);
  }

  async _previewMonthlySummary() {
    try {
      const res = await this._api("get", "nextfirst/monthly_summary/preview");
      this._summaryPreview = res.summary || null;
      this._render();
    } catch (err) {
      this._error = this._formatError(err);
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
      this._openShareBox(result.text, result.share_urls || {});
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    }
  }

  async _shareExperience(id, defaultTitle) {
    const text = prompt("Optional eigener Share-Text:", `Neues NextFirst Erlebnis: ${defaultTitle}`) ?? "";
    const hashtags = prompt("Hashtags (kommasepariert, optional):", "") ?? "";
    try {
      const result = await this._api("post", `nextfirst/share/experience/${id}`, {
        text: text.trim() || undefined,
        hashtags: hashtags.trim() || undefined,
      });
      this._openShareBox(result.text, result.share_urls || {});
      await this._load();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    }
  }

  _mapsUrl(location) {
    const query = encodeURIComponent(String(location || "").trim());
    return query ? `https://www.google.com/maps/search/?api=1&query=${query}` : "";
  }

  _calendarUrl(item) {
    const title = encodeURIComponent(String(item?.title || "NextFirst Erlebnis"));
    const location = encodeURIComponent(String(item?.location || ""));
    const details = encodeURIComponent(
      String(item?.description || "Neues Erlebnis mit NextFirst")
    );
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&location=${location}&details=${details}`;
  }

  _calendarIcs(item) {
    const now = new Date();
    const start = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    start.setHours(10, 0, 0, 0);
    const end = new Date(start.getTime() + 2 * 60 * 60 * 1000);

    const formatUtc = (date) => {
      const pad = (n) => String(n).padStart(2, "0");
      return `${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}T${pad(
        date.getUTCHours()
      )}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}Z`;
    };

    const esc = (value) =>
      String(value || "")
        .replaceAll("\\", "\\\\")
        .replaceAll("\n", "\\n")
        .replaceAll(",", "\\,")
        .replaceAll(";", "\\;");

    const uid = `${item?.id || "nextfirst"}@nextfirst.local`;
    const summary = esc(item?.title || "NextFirst Erlebnis");
    const location = esc(item?.location || "");
    const description = esc(item?.description || "Neues Erlebnis mit NextFirst");

    return [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//NextFirst//Home Assistant//DE",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
      "BEGIN:VEVENT",
      `UID:${uid}`,
      `DTSTAMP:${formatUtc(now)}`,
      `DTSTART:${formatUtc(start)}`,
      `DTEND:${formatUtc(end)}`,
      `SUMMARY:${summary}`,
      `LOCATION:${location}`,
      `DESCRIPTION:${description}`,
      "END:VEVENT",
      "END:VCALENDAR",
      "",
    ].join("\r\n");
  }

  _downloadCalendarIcs(item) {
    const content = this._calendarIcs(item);
    const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
    const link = document.createElement("a");
    const title = String(item?.title || "nextfirst-erlebnis")
      .toLowerCase()
      .replaceAll(/[^a-z0-9]+/g, "-")
      .replaceAll(/^-+|-+$/g, "");
    link.href = URL.createObjectURL(blob);
    link.download = `${title || "nextfirst-erlebnis"}.ics`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  _openShareBox(text, urls) {
    this._shareData = { text: text || "", urls: urls || {} };
    this._render();
  }

  _closeShareBox() {
    this._shareData = null;
    this._render();
  }

  _shareVia(provider) {
    if (!this._shareData) return;
    const text = this._shareData.text || "";
    const url = this._shareData.urls?.[provider];
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  _renderCard(item) {
    const mediaCount = item.media?.length || 0;
    const category = item.category ? `<span class="pill">${this._escape(item.category)}</span>` : "";
    const courage = item.courage_level ? `<span class="pill">Mut: ${this._escape(item.courage_level)}</span>` : "";
    const location = item.location ? `<span class="pill">Ort: ${this._escape(item.location)}</span>` : "";
    const budgetRaw = item.budget_per_person_eur ?? item.extra?.estimated_budget_per_person_eur;
    const budgetText = String(budgetRaw ?? "").trim();
    const budgetValue = budgetText ? Number(budgetText) : NaN;
    const budget = Number.isFinite(budgetValue)
      ? `<span class="pill">Budget/Person: ${this._escape(budgetValue)} EUR</span>`
      : "";
    const mapsUrl = this._mapsUrl(item.location);
    const calendarUrl = this._calendarUrl(item);

    let actions = "";
    if (item.status === "open") {
      actions = `
        <button data-action="edit" data-id="${item.id}">Bearbeiten</button>
        <button data-action="skip" data-id="${item.id}">Überspringen</button>
        <button data-action="experience" data-id="${item.id}">Als erlebt markieren</button>
        ${mapsUrl ? `<a class="action-link" href="${this._escape(mapsUrl)}" target="_blank" rel="noopener noreferrer">Maps</a>` : ""}
        <button data-action="calendar_ics" data-id="${item.id}">Kalender (.ics)</button>
        <a class="action-link" href="${this._escape(calendarUrl)}" target="_blank" rel="noopener noreferrer">Google Kalender</a>
        <button class="danger" data-action="delete" data-id="${item.id}">Löschen</button>
      `;
    } else if (item.status === "skipped") {
      actions = `
        <button data-action="reactivate" data-id="${item.id}">Zurück zu offen</button>
        <button data-action="edit" data-id="${item.id}">Bearbeiten</button>
        ${mapsUrl ? `<a class="action-link" href="${this._escape(mapsUrl)}" target="_blank" rel="noopener noreferrer">Maps</a>` : ""}
        <button data-action="calendar_ics" data-id="${item.id}">Kalender (.ics)</button>
        <a class="action-link" href="${this._escape(calendarUrl)}" target="_blank" rel="noopener noreferrer">Google Kalender</a>
        <button class="danger" data-action="delete" data-id="${item.id}">Löschen</button>
      `;
    } else {
      actions = `
        <button data-action="note" data-id="${item.id}">Notiz bearbeiten</button>
        <button data-action="media" data-id="${item.id}">Bild hinzufügen</button>
        <button data-action="share" data-id="${item.id}">Teilen</button>
        ${mapsUrl ? `<a class="action-link" href="${this._escape(mapsUrl)}" target="_blank" rel="noopener noreferrer">Maps</a>` : ""}
        <button data-action="calendar_ics" data-id="${item.id}">Kalender (.ics)</button>
        <a class="action-link" href="${this._escape(calendarUrl)}" target="_blank" rel="noopener noreferrer">Google Kalender</a>
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
          ${location}
          ${budget}
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
    const safeImageUrl = this._resolveMediaUrl(first);
    const mediaHint = first && !safeImageUrl
      ? `<p class="note">Bildpfad ${this._escape(first)} ist im Browser nicht direkt lesbar. Bitte neu hochladen.</p>`
      : "";

    return `
      <article class="album-card">
        ${safeImageUrl ? `<img src="${this._escape(safeImageUrl)}" alt="${this._escape(item.title)}" />` : `<div class="img-fallback">Kein Bild</div>`}
        <div class="album-content">
          <h3>${this._escape(item.title)}</h3>
          <p>${this._escape(item.completed_at || "Kein Abschlussdatum")}</p>
          ${item.location ? `<p>Ort: ${this._escape(item.location)}</p>` : ""}
          ${item.notes ? `<p>${this._escape(item.notes)}</p>` : ""}
          ${mediaHint}
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

    if (this._tab === "protocol") {
      const preview = this._summaryPreview
        ? `<div class="state"><strong>Monatsvorschau:</strong><br>${this._escape(this._summaryPreview.summary_text || "")}</div>`
        : `<div class="state">Noch keine Monatsvorschau geladen.</div>`;
      const history = this._protocolHistory.length
        ? `<ul class="history">${this._protocolHistory
            .map((h) => `<li><strong>${this._escape(h.timestamp || "-")}</strong> | ${this._escape(h.level || "-")} | ${this._escape(h.action || "-")}<br>${this._escape(h.message || "")}</li>`)
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
    this.shadowRoot.getElementById("aiPromptSendBtn")?.addEventListener("click", () => this._generateAI());
    this.shadowRoot.getElementById("aiPromptCancelBtn")?.addEventListener("click", () => {
      this._aiPromptPreviewText = "";
      this._render();
    });
    this.shadowRoot.getElementById("previewMonthlyBtn")?.addEventListener("click", () => this._previewMonthlySummary());
    this.shadowRoot.getElementById("shareMonthlyBtn")?.addEventListener("click", () => this._shareMonthlySummary());

    this.shadowRoot.getElementById("mediaUploadInput")?.addEventListener("change", (event) => {
      const file = event?.target?.files?.[0];
      if (file) this._uploadMediaFile(file);
    });

    this.shadowRoot.getElementById("shareCloseBtn")?.addEventListener("click", () => this._closeShareBox());
    this.shadowRoot.querySelectorAll("button[data-share-provider]").forEach((btn) => {
      btn.addEventListener("click", () => this._shareVia(btn.dataset.shareProvider));
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
        if (action === "calendar_ics") return this._downloadCalendarIcs(item);
      });
    });
  }

  _render() {
    const stats = this._stats || {};
    const elapsed = this._aiGenerating && this._aiProgressStartedAt
      ? Math.max(0, Math.round((Date.now() - this._aiProgressStartedAt) / 1000))
      : 0;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; min-height:100%; color:var(--primary-text-color); background:linear-gradient(135deg, rgba(35,111,146,0.10), rgba(244,163,97,0.12)); font-family:"Avenir Next","Segoe UI",sans-serif; }
        .wrap { max-width:1100px; margin:0 auto; padding:16px; }
        .top { display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:space-between; margin-bottom:12px; }
        h1 { margin:0; font-size:1.4rem; }
        .stats { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 16px; }
        .stat { background:var(--card-background-color); border-radius:12px; padding:10px 12px; border:1px solid rgba(127,127,127,0.2); font-size:0.9rem; }
        .toolbar { display:flex; gap:8px; flex-wrap:wrap; }
        button { border:none; border-radius:10px; padding:8px 12px; cursor:pointer; background:#236f92; color:#fff; font-weight:600; }
        button:hover { filter:brightness(1.08); }
        button.danger { background:#b42318; }
        .tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
        .tab { background:#456c80; opacity:0.7; }
        .tab.active { opacity:1; background:#1f5773; }
        .card { background:var(--card-background-color); border:1px solid rgba(127,127,127,0.2); border-radius:14px; padding:12px; margin-bottom:10px; }
        .card header { display:flex; justify-content:space-between; gap:8px; align-items:baseline; }
        .card h3 { margin:0; }
        .status { border-radius:999px; padding:2px 10px; font-size:0.75rem; text-transform:uppercase; }
        .status-open { background:#d9f2ff; color:#0b3b53; }
        .status-skipped { background:#fff2cc; color:#6a4d00; }
        .status-experienced,.status-archived { background:#dff7e4; color:#12481f; }
        .meta { display:flex; gap:6px; flex-wrap:wrap; margin:8px 0; }
        .pill { border-radius:999px; background:rgba(35,111,146,0.12); padding:2px 10px; font-size:0.78rem; }
        .actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
        .action-link {
          display: inline-flex;
          align-items: center;
          text-decoration: none;
          border-radius: 10px;
          padding: 8px 12px;
          background: #236f92;
          color: #fff;
          font-weight: 600;
        }
        .note { font-style:italic; color:var(--secondary-text-color); }
        .state { background:var(--card-background-color); border-radius:10px; border:1px solid rgba(127,127,127,0.2); padding:14px; }
        .state.error { border-color:#b42318; color:#b42318; }
        .album-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px; }
        .album-card { overflow:hidden; border-radius:12px; background:var(--card-background-color); border:1px solid rgba(127,127,127,0.2); }
        .album-card img, .img-fallback { width:100%; height:180px; object-fit:cover; display:block; background:#d7e7ef; }
        .img-fallback { display:grid; place-items:center; color:#496170; font-weight:600; }
        .album-content { padding:10px; }
        .album-content h3 { margin:0 0 6px; }
        .history { margin:12px 0 0; padding:0 0 0 18px; }
        .history li { margin:8px 0; }
        .share-box { background:var(--card-background-color); border:1px solid rgba(127,127,127,0.2); border-radius:12px; padding:12px; margin-bottom:12px; }
        .share-box pre { white-space:pre-wrap; background:rgba(127,127,127,0.1); padding:8px; border-radius:8px; font-family:monospace; font-size:0.82rem; }
        .ai-progress { background:var(--card-background-color); border:1px solid rgba(127,127,127,0.2); border-radius:12px; padding:10px; margin-bottom:12px; }
        .ai-progress progress { width:100%; height:18px; }
        .ai-preview { background:var(--card-background-color); border:1px solid rgba(127,127,127,0.2); border-radius:12px; padding:12px; margin-bottom:12px; }
        .ai-preview pre { white-space:pre-wrap; background:rgba(127,127,127,0.1); padding:8px; border-radius:8px; font-family:monospace; font-size:0.8rem; max-height:280px; overflow:auto; }
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
          <button class="tab ${this._tab === "protocol" ? "active" : ""}" data-tab="protocol">Protokoll</button>
          <button class="tab ${this._tab === "album" ? "active" : ""}" data-tab="album">Album</button>
        </div>

        ${this._aiProgressValue > 0 ? `
          <div class="ai-progress">
            <strong>KI-Vorschlag wird generiert ...</strong>
            <div>${this._aiProgressValue}%${this._aiGenerating ? ` | ${elapsed}s` : ""}</div>
            <progress value="${this._aiProgressValue}" max="100"></progress>
          </div>
        ` : ""}

        ${this._aiPromptPreviewText ? `
          <div class="ai-preview">
            <strong>Debug: Prompt-Vorschau (vor dem Senden)</strong>
            <pre>${this._escape(this._aiPromptPreviewText)}</pre>
            <div class="actions">
              <button id="aiPromptSendBtn">KI jetzt senden (1 Vorschlag)</button>
              <button id="aiPromptCancelBtn" class="danger">Abbrechen</button>
            </div>
          </div>
        ` : ""}

        ${this._shareData ? `
          <div class="share-box">
            <strong>Teilen</strong>
            <p>Button klicken, dann im jeweiligen Netzwerk posten.</p>
            <pre>${this._escape(this._shareData.text || "")}</pre>
            <div class="actions">
              <button data-share-provider="instagram">Instagram</button>
              <button data-share-provider="x">X</button>
              <button data-share-provider="facebook">Facebook</button>
              <button data-share-provider="whatsapp">WhatsApp</button>
              <button data-share-provider="telegram">Telegram</button>
              <button id="shareCloseBtn" class="danger">Schließen</button>
            </div>
          </div>
        ` : ""}

        <section>${this._renderBody()}</section>
        <input id="mediaUploadInput" type="file" accept="image/*" style="display:none" />
      </div>
    `;

    this._attachEvents();
  }
}

customElements.define("nextfirst-panel", NextFirstPanel);
