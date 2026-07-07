(function () {
  'use strict';

  var STATUS_URL     = '/api/status';
  var STRUCTURES_URL = '/api/structures';
  var LOG_URL        = '/api/log';
  var REFRESH_MS     = 3000;

  // Track last-seen SMILES per index to avoid SVG flicker (D-10)
  var lastSmiles = {};

  // ------------------------------------------------------------------
  // refreshStatus
  // ------------------------------------------------------------------
  function refreshStatus() {
    fetch(STATUS_URL)
      .then(function (r) { return r.json(); })
      .then(function (data) { renderStatus(data); })
      .catch(function (e) { console.warn('status fetch failed:', e); });
  }

  function renderStatus(data) {
    var state = data.state || 'waiting';

    // State badge
    var badgeClass = 'badge-waiting';
    if (state === 'running')  { badgeClass = 'badge-running'; }
    if (state === 'complete') { badgeClass = 'badge-complete'; }
    if (state === 'error')    { badgeClass = 'badge-error'; }

    var stateEl = document.getElementById('status-state');
    var badge = document.createElement('span');
    badge.className = 'badge ' + badgeClass;
    badge.textContent = state;
    stateEl.textContent = '';
    stateEl.appendChild(badge);

    // Iteration
    var iterEl = document.getElementById('status-iter');
    iterEl.textContent = (data.iteration != null)
      ? 'Iteration ' + data.iteration : '';

    // Active phase
    var phaseEl = document.getElementById('status-phase');
    phaseEl.textContent = data.active_phase ? data.active_phase : '';

    // Elapsed
    var elapsedEl = document.getElementById('status-elapsed');
    if (data.elapsed_s != null) {
      elapsedEl.textContent = formatElapsed(data.elapsed_s);
    } else {
      elapsedEl.textContent = '';
    }
  }

  function formatElapsed(s) {
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    if (h > 0) {
      return h + 'h ' + pad(m) + 'm ' + pad(sec) + 's';
    }
    if (m > 0) {
      return m + 'm ' + pad(sec) + 's';
    }
    return sec + 's';
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  // ------------------------------------------------------------------
  // refreshStructures
  // ------------------------------------------------------------------
  function refreshStructures() {
    fetch(STRUCTURES_URL)
      .then(function (r) { return r.json(); })
      .then(function (data) { renderStructures(data); })
      .catch(function (e) { console.warn('structures fetch failed:', e); });
  }

  function renderStructures(data) {
    var grid = document.getElementById('structure-grid');
    var hint = document.getElementById('structure-hint');

    var structures = data.structures || [];
    var total = (data.total != null) ? data.total : structures.length;

    if (structures.length === 0) {
      // Show waiting message (textContent only — XSS guard)
      var waiting = document.getElementById('structure-waiting');
      if (!waiting) {
        waiting = document.createElement('div');
        waiting.id = 'structure-waiting';
        grid.appendChild(waiting);
      }
      waiting.textContent = 'Waiting for candidates...';
      hint.textContent = '';
      return;
    }

    // Remove waiting placeholder if present
    var waitingEl = document.getElementById('structure-waiting');
    if (waitingEl) { waitingEl.remove(); }

    // Build or update tiles
    structures.forEach(function (item) {
      var idx = item.index;
      var tileId = 'tile-' + idx;
      var tile = document.getElementById(tileId);

      if (!tile) {
        // Create new tile
        tile = document.createElement('div');
        tile.className = 'tile';
        tile.id = tileId;

        var img = document.createElement('img');
        img.id = 'img-' + idx;
        img.alt = 'Structure ' + idx;

        var labelEl = document.createElement('div');
        labelEl.className = 'tile-label';
        labelEl.id = 'label-' + idx;

        tile.appendChild(img);
        tile.appendChild(labelEl);
        grid.appendChild(tile);
      }

      // Re-fetch SVG only if SMILES changed (D-10: no flicker).
      // Direct compare — a `|| null` coercion made empty-string SMILES
      // ("" || null === null) re-fetch forever every tick.
      var smiles = item.smiles || '';
      if (smiles !== lastSmiles[idx]) {
        var img2 = document.getElementById('img-' + idx);
        if (img2) {
          img2.src = '/api/structure/' + idx + '.svg?t=' + Date.now();
        }
        lastSmiles[idx] = smiles;
      }

      // Render label (rank / MAE / quality) — D-09: HTML around tile, not in SVG
      var labelDiv = document.getElementById('label-' + idx);
      if (labelDiv) {
        var rankText  = (item.rank  != null) ? 'Rank ' + item.rank : '';
        var maeText   = (item.mae   != null) ? 'MAE ' + item.mae.toFixed(2) + ' ppm' : '';
        var qualText  = item.quality || '';
        var parts = [rankText, maeText, qualText].filter(Boolean);

        // Build label lines safely with textContent nodes
        labelDiv.textContent = '';
        if (parts.length > 0) {
          var rankSpan = document.createElement('span');
          rankSpan.className = 'tile-rank';
          rankSpan.textContent = rankText || ('Index ' + idx);
          labelDiv.appendChild(rankSpan);

          if (maeText || qualText) {
            labelDiv.appendChild(document.createTextNode(' '));
            var qualSpan = document.createElement('span');
            qualSpan.className = 'tile-quality';
            qualSpan.textContent = [maeText, qualText].filter(Boolean).join(' · ');
            labelDiv.appendChild(qualSpan);
          }
        } else {
          labelDiv.textContent = 'Index ' + idx;
        }
      }
    });

    // "+N more" hint when total exceeds shown
    if (total > structures.length) {
      hint.textContent = '+' + (total - structures.length) + ' more candidate'
        + (total - structures.length !== 1 ? 's' : '') + ' not shown';
    } else {
      hint.textContent = total + ' candidate' + (total !== 1 ? 's' : '');
    }
  }

  // ------------------------------------------------------------------
  // refreshLog  — D-13: preserve scroll unless user is at bottom
  // ------------------------------------------------------------------
  function refreshLog() {
    var logEl = document.getElementById('log-panel');
    // Capture scroll position BEFORE the update
    var atBottom = (logEl.scrollHeight - logEl.scrollTop) <= (logEl.clientHeight + 5);

    fetch(LOG_URL)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var content = data.content || '';
        // Use textContent (T-91-09: XSS guard — run-controlled content must not reach the DOM as markup)
        logEl.textContent = content || 'Waiting for log data...';
        if (atBottom) {
          logEl.scrollTop = logEl.scrollHeight;
        }
        // (else: preserve current scrollTop — browser keeps it unchanged after textContent set)
      })
      .catch(function (e) { console.warn('log fetch failed:', e); });
  }

  // ------------------------------------------------------------------
  // Refresh indicator
  // ------------------------------------------------------------------
  function flashDot() {
    var dot = document.getElementById('refresh-dot');
    if (!dot) { return; }
    dot.classList.add('active');
    setTimeout(function () { dot.classList.remove('active'); }, 500);
  }

  function tick() {
    refreshStatus();
    refreshStructures();
    refreshLog();
    flashDot();
  }

  // ------------------------------------------------------------------
  // Bootstrap
  // ------------------------------------------------------------------
  tick();  // immediate load
  setInterval(tick, REFRESH_MS);  // D-15: ~3 s polling

}());
