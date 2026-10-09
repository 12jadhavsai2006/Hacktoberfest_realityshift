"""
graph_ui.py – Interactive Web Dashboard for RealityShift
========================================================
Glassmorphic, responsive Web UI with live Mermaid.js causal graph rendering,
side-by-side image comparison, and consequence risk breakdown.
"""

GRAPH_VIEWER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RealityShift — Multimodal Counterfactual Causal Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0f172a',
        primaryColor: '#38bdf8',
        primaryBorderColor: '#0284c7',
        lineColor: '#94a3b8',
        fontFamily: 'Outfit, sans-serif'
      }
    });
    window.mermaid = mermaid;
  </script>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(17, 24, 39, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.25);
      --cyan: #06b6d4;
      --green: #22c55e;
      --red: #ef4444;
      --amber: #f59e0b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Outfit', sans-serif;
      background: radial-gradient(circle at 15% 15%, #1e1b4b 0%, var(--bg) 60%), radial-gradient(circle at 85% 85%, #0c4a6e 0%, var(--bg) 60%);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem 1.5rem;
      overflow-x: hidden;
    }

    .container {
      max-width: 1280px;
      margin: 0 auto;
    }

    /* Header */
    header {
      text-align: center;
      margin-bottom: 2.5rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #818cf8;
      font-size: 0.85rem;
      font-weight: 500;
      margin-bottom: 1rem;
    }
    h1 {
      font-size: 2.75rem;
      font-weight: 700;
      background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.75rem;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 1.1rem;
      max-width: 650px;
      margin: 0 auto;
    }

    /* Glass Card */
    .glass-card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.75rem;
      margin-bottom: 2rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    /* Upload Grid */
    .upload-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .upload-box {
      border: 2px dashed rgba(255, 255, 255, 0.15);
      border-radius: 0.75rem;
      padding: 1.5rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.25s ease;
      background: rgba(15, 23, 42, 0.5);
      position: relative;
    }
    .upload-box:hover {
      border-color: var(--accent);
      background: rgba(99, 102, 241, 0.05);
    }
    .upload-box input[type="file"] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
      width: 100%;
      height: 100%;
    }
    .upload-icon {
      font-size: 2.2rem;
      margin-bottom: 0.5rem;
      display: block;
    }
    .upload-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
    }
    .upload-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .preview-img {
      max-height: 180px;
      max-width: 100%;
      border-radius: 0.5rem;
      margin-top: 0.75rem;
      display: none;
      object-fit: cover;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }
    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: #e2e8f0;
      font-size: 0.95rem;
    }
    input[type="text"] {
      width: 100%;
      padding: 0.85rem 1.1rem;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--card-border);
      border-radius: 0.6rem;
      color: #fff;
      font-size: 0.95rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type="text"]:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    /* Primary Button */
    .btn-primary {
      width: 100%;
      padding: 1rem;
      background: linear-gradient(135deg, #6366f1, #38bdf8);
      color: #fff;
      border: none;
      border-radius: 0.6rem;
      font-size: 1.05rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(99, 102, 241, 0.55);
    }
    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    /* Results Dashboard */
    #resultsSection {
      display: none;
      animation: fadeIn 0.4s ease-out forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .summary-banner {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(6, 182, 212, 0.15));
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 1.25rem 1.5rem;
      border-radius: 0.75rem;
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .summary-text {
      font-size: 1.05rem;
      line-height: 1.6;
      flex: 1;
    }
    .severity-pill {
      padding: 0.4rem 1rem;
      border-radius: 9999px;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 0.85rem;
      letter-spacing: 0.05em;
    }
    .sev-low { background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }
    .sev-medium { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }
    .sev-high { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #f87171; }

    /* Graph Container */
    .graph-card {
      background: #0b1120;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 0.75rem;
      padding: 1.5rem;
      margin-bottom: 2rem;
      overflow-x: auto;
      text-align: center;
    }
    .graph-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .graph-title {
      font-size: 1.2rem;
      font-weight: 600;
    }

    /* Cards Grid */
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    .section-card {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem;
    }
    .section-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .item-row {
      background: rgba(30, 41, 59, 0.6);
      border-radius: 0.5rem;
      padding: 0.75rem 1rem;
      border-left: 4px solid var(--cyan);
    }
    .item-row.broken { border-left-color: var(--red); }
    .item-row.formed { border-left-color: var(--green); }
    .item-row.strained { border-left-color: var(--amber); }

    .item-header {
      display: flex;
      justify-content: space-between;
      font-weight: 600;
      margin-bottom: 0.25rem;
      font-size: 0.95rem;
    }
    .item-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* Loading Spinner */
    .spinner {
      display: none;
      margin: 1.5rem auto;
      text-align: center;
    }
    .spinner-ring {
      display: inline-block;
      width: 40px;
      height: 40px;
      border: 4px solid rgba(255, 255, 255, 0.1);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* JSON Box */
    .json-box {
      background: #020617;
      border: 1px solid var(--card-border);
      border-radius: 0.6rem;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      max-height: 250px;
      overflow-y: auto;
      color: #93c5fd;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">Powered by Gemma 4 Multimodal Reasoning</div>
      <h1>RealityShift</h1>
      <p class="subtitle">Multimodal counterfactual engine: detecting visual state deltas, disrupted physical dependencies, and downstream causal risk.</p>
    </header>

    <!-- Upload & Config Card -->
    <div class="glass-card">
      <form id="shiftForm">
        <div class="upload-grid">
          <!-- Image A -->
          <div class="upload-box" id="boxA">
            <input type="file" id="fileA" name="file_a" accept="image/*" required>
            <span class="upload-icon">📷</span>
            <div class="upload-title">Image A — Reality State A</div>
            <div class="upload-desc">Baseline / "Before" state of reality</div>
            <img id="prevA" class="preview-img" alt="Preview Image A">
          </div>

          <!-- Image B -->
          <div class="upload-box" id="boxB">
            <input type="file" id="fileB" name="file_b" accept="image/*" required>
            <span class="upload-icon">🔄</span>
            <div class="upload-title">Image B — Reality State B</div>
            <div class="upload-desc">Counterfactual / "After" delta state</div>
            <img id="prevB" class="preview-img" alt="Preview Image B">
          </div>
        </div>

        <div class="form-group">
          <label for="userDesc">Optional User Change Hint / Context:</label>
          <input type="text" id="userDesc" name="user_change_description" placeholder="e.g., I moved the object on the desk, or The wire was disconnected.">
        </div>

        <button type="submit" id="submitBtn" class="btn-primary">
          Analyze Reality Shift & Generate Causal Graph
        </button>

        <div class="spinner" id="loadingSpinner">
          <div class="spinner-ring"></div>
          <div style="margin-top: 0.75rem; color: #94a3b8; font-size: 0.9rem;">
            Gemma 4 is reasoning through causal chains & relationship deltas...
          </div>
        </div>
      </form>
    </div>

    <!-- Results Section -->
    <div id="resultsSection">
      <!-- Summary Banner -->
      <div class="summary-banner">
        <div class="summary-text" id="summaryText"></div>
        <div class="severity-pill" id="severityBadge"></div>
      </div>

      <!-- Causal Graph Card -->
      <div class="graph-card">
        <div class="graph-header">
          <div class="graph-title">Interactive Causal Graph</div>
          <div style="font-size: 0.85rem; color: #94a3b8;" id="graphTopology"></div>
        </div>
        <div id="mermaidContainer"></div>
      </div>

      <!-- Details Grid -->
      <div class="cards-grid">
        <!-- Entity Changes -->
        <div class="section-card">
          <div class="section-title"><span>📦</span> Observed Entity Changes</div>
          <div class="item-list" id="entitiesList"></div>
        </div>

        <!-- Relationship Changes -->
        <div class="section-card">
          <div class="section-title"><span>🔗</span> Broken & Formed Relationships</div>
          <div class="item-list" id="relationshipsList"></div>
        </div>

        <!-- Downstream Consequences -->
        <div class="section-card">
          <div class="section-title"><span>⚠️</span> Downstream Consequences</div>
          <div class="item-list" id="consequencesList"></div>
        </div>
      </div>

      <!-- Raw JSON Accordion -->
      <details class="glass-card" style="margin-bottom: 0;">
        <summary style="cursor: pointer; font-weight: 600; color: #94a3b8;">
          View Raw Structured JSON Output
        </summary>
        <div class="json-box" id="jsonOutput" style="margin-top: 1rem;"></div>
      </details>
    </div>
  </div>

  <script>
    // Image Preview Handlers
    function setupPreview(inputId, imgId) {
      document.getElementById(inputId).addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function(evt) {
            const img = document.getElementById(imgId);
            img.src = evt.target.result;
            img.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      });
    }
    setupPreview('fileA', 'prevA');
    setupPreview('fileB', 'prevB');

    // Form Submission
    const form = document.getElementById('shiftForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('loadingSpinner');
    const resultsSection = document.getElementById('resultsSection');

    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      submitBtn.disabled = true;
      spinner.style.display = 'block';
      resultsSection.style.display = 'none';

      const formData = new FormData(form);

      try {
        const res = await fetch('/api/v1/analyze-shift', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Analysis request failed.');
        }

        const data = await res.json();
        renderResults(data);
      } catch (err) {
        alert('Error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        spinner.style.display = 'none';
      }
    });

    async function renderResults(data) {
      resultsSection.style.display = 'block';

      // Summary & Severity
      document.getElementById('summaryText').textContent = data.summary;
      const badge = document.getElementById('severityBadge');
      badge.textContent = 'Overall Risk: ' + data.overall_severity;
      badge.className = 'severity-pill sev-' + data.overall_severity.toLowerCase();

      // Entity Changes
      const entList = document.getElementById('entitiesList');
      entList.innerHTML = '';
      data.entity_changes.forEach(ent => {
        const row = document.createElement('div');
        row.className = 'item-row';
        row.innerHTML = `
          <div class="item-header">
            <span>${ent.entity_label}</span>
            <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--cyan);">${ent.change_type}</span>
          </div>
          <div class="item-desc">${ent.description_in_b || ent.description_in_a || ''}</div>
        `;
        entList.appendChild(row);
      });

      // Relationship Changes
      const relList = document.getElementById('relationshipsList');
      relList.innerHTML = '';
      data.relationship_changes.forEach(rel => {
        const row = document.createElement('div');
        row.className = 'item-row ' + rel.status.toLowerCase();
        row.innerHTML = `
          <div class="item-header">
            <span>${rel.from_entity_id} &rarr; ${rel.to_entity_id}</span>
            <span style="font-size: 0.8rem; text-transform: uppercase;">${rel.status}</span>
          </div>
          <div class="item-desc">${rel.explanation || rel.relationship_type}</div>
        `;
        relList.appendChild(row);
      });

      // Consequences
      const consList = document.getElementById('consequencesList');
      consList.innerHTML = '';
      data.consequences.forEach(c => {
        const row = document.createElement('div');
        row.className = 'item-row';
        row.innerHTML = `
          <div class="item-header">
            <span>${c.title}</span>
            <span style="font-size: 0.8rem; text-transform: uppercase;">${c.severity}</span>
          </div>
          <div class="item-desc">${c.description}</div>
          <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">Confidence: ${Math.round(c.confidence * 100)}%</div>
        `;
        consList.appendChild(row);
      });

      // Render Causal Graph (Mermaid)
      if (data.causal_graph && data.causal_graph.mermaid) {
        document.getElementById('graphTopology').textContent = data.causal_graph.summary || '';
        const container = document.getElementById('mermaidContainer');
        container.innerHTML = '<pre class="mermaid">' + data.causal_graph.mermaid + '</pre>';
        if (window.mermaid) {
          await window.mermaid.run({ nodes: container.querySelectorAll('.mermaid') });
        }
      }

      // JSON output
      document.getElementById('jsonOutput').textContent = JSON.stringify(data, null, 2);

      // Smooth scroll to results
      resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
  </script>
</body>
</html>
"""
