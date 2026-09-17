/* Resolve demo UI. No framework, no build step, no inline scripts (CSP). */
(function () {
  'use strict';

  var state = { employees: [], cases: [], metrics: {}, audit: [], policies: [], evaluation: null };

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function statusClass(status) {
    switch (status) {
      case 'approved': case 'resolved': return 'pill pill-good';
      case 'waiting_approval': return 'pill pill-warn';
      case 'refused': case 'rejected': return 'pill pill-bad';
      case 'escalated': return 'pill pill-info';
      default: return 'pill pill-muted';
    }
  }
  function riskClass(risk) {
    return risk === 'critical' ? 'pill pill-bad' : risk === 'high' ? 'pill pill-warn' : 'pill pill-muted';
  }
  function label(s) { return String(s || '').replace(/_/g, ' '); }
  function shortTime(iso) { return iso ? iso.replace('T', ' ').slice(0, 19) : ''; }

  async function api(path, options) {
    var res = await fetch(path, options);
    var body = await res.json();
    if (!res.ok) throw new Error(body.error || ('Request failed: ' + res.status));
    return body;
  }

  async function bootstrap() {
    var data = await api('/api/bootstrap');
    state.employees = data.employees;
    state.cases = data.cases;
    state.metrics = data.metrics;
    state.audit = data.audit;
    state.policies = data.policies;
    try { state.evaluation = await api('/api/evaluation'); } catch (e) { state.evaluation = null; }
    renderEmployees();
    renderAll();
  }

  function renderEmployees() {
    var select = $('employee');
    if (select.options.length) return;
    state.employees.forEach(function (e) {
      var opt = el('option', null, e.name + ' (' + e.id + ', ' + e.region + ', ' + label(e.role_category) + ')');
      opt.value = e.id;
      select.appendChild(opt);
    });
    var ghost = el('option', null, 'Unknown employee ID (E-0000)');
    ghost.value = 'E-0000';
    select.appendChild(ghost);
  }

  function renderAll() {
    renderQueue();
    renderCases();
    renderMetrics();
    renderEvaluation();
    renderAudit();
    $('pending-count').textContent = state.metrics.pending_approvals || 0;
  }

  function renderResult(r) {
    $('result-empty').hidden = true;
    var box = $('result');
    box.hidden = false;
    var s = $('r-status'); s.textContent = label(r.status); s.className = statusClass(r.status);
    var k = $('r-risk'); k.textContent = 'risk: ' + r.risk; k.className = riskClass(r.risk);
    $('r-intent').textContent = 'intent: ' + label(r.intent);
    $('r-confidence').textContent = 'confidence: ' + Math.round(r.confidence * 100) + '%';
    $('r-answer').textContent = r.answer;
    $('r-action').textContent = r.recommended_action;
    $('r-approval').textContent = r.approval_required ? 'Yes' : 'No';
    $('r-role').textContent = r.approval_role ? label(r.approval_role) : 'None';
    $('r-data').textContent = r.data_accessed.length ? r.data_accessed.join(', ') : 'None';
    $('r-flags').textContent = r.safety_flags.length ? r.safety_flags.join(', ') : 'None';
    $('r-latency').textContent = r.latency_ms + ' ms';
    $('r-case').textContent = r.case_id;
    var cites = $('r-citations'); clear(cites);
    if (!r.citations.length) cites.appendChild(el('li', 'muted', 'No policy cited. The engine stopped before retrieval.'));
    r.citations.forEach(function (c) {
      cites.appendChild(el('li', null, c.policy_id + ' · ' + c.title + ' · v' + c.version + ' · effective ' + c.effective_date));
    });
    var trace = $('r-trace'); clear(trace);
    r.decision_trace.forEach(function (t) { trace.appendChild(el('li', null, t)); });
  }

  async function submit() {
    var btn = $('submit');
    var status = $('submit-status');
    var request = $('request').value.trim();
    if (!request) { status.textContent = 'Write a request first.'; return; }
    btn.disabled = true; status.textContent = 'Resolving...';
    try {
      var result = await api('/api/resolve', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: request, employee_id: $('employee').value, actor_role: $('actor').value })
      });
      renderResult(result);
      status.textContent = '';
      await refresh();
    } catch (err) {
      status.textContent = err.message;
    } finally {
      btn.disabled = false;
    }
  }

  async function refresh() {
    var data = await api('/api/bootstrap');
    state.cases = data.cases; state.metrics = data.metrics; state.audit = data.audit;
    renderAll();
  }

  function renderQueue() {
    var queue = $('queue'); clear(queue);
    var pending = state.cases.filter(function (c) { return c.status === 'waiting_approval'; });
    if (!pending.length) { queue.appendChild(el('div', 'empty', 'Nothing waiting. Submit a parental leave, remote work, relocation, or manager change request to create one.')); return; }
    pending.forEach(function (c) {
      var item = el('div', 'queue-item');
      var head = el('div', 'head');
      var left = el('div');
      left.appendChild(el('div', 'req', c.request || c.answer || c.case_id));
      left.appendChild(el('div', 'small muted', (c.case_id || c.id) + ' · employee ' + (c.employee_id || 'n/a') + ' · approver: ' + label(c.approval_role || 'people partner')));
      head.appendChild(left);
      var risk = el('span', riskClass(c.risk), 'risk: ' + c.risk); head.appendChild(risk);
      item.appendChild(head);
      if (c.answer) { var ans = el('p', 'small', c.answer); ans.style.margin = '8px 0 0'; item.appendChild(ans); }
      if (c.recommended_action) item.appendChild(el('p', 'small muted', 'Recommended: ' + c.recommended_action));
      var note = el('input', 'note'); note.placeholder = 'Reviewer note (optional)'; item.appendChild(note);
      var btns = el('div', 'btns');
      var approve = el('button', 'btn btn-good', 'Approve');
      var reject = el('button', 'btn btn-bad', 'Reject');
      var id = c.case_id || c.id;
      approve.addEventListener('click', function () { decide(id, 'approve', note.value); });
      reject.addEventListener('click', function () { decide(id, 'reject', note.value); });
      btns.appendChild(approve); btns.appendChild(reject); item.appendChild(btns);
      queue.appendChild(item);
    });
  }

  async function decide(caseId, decision, note) {
    try {
      await api('/api/cases/' + encodeURIComponent(caseId) + '/decision', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision: decision, reviewer: $('reviewer').value.trim(), note: note || '' })
      });
      await refresh();
    } catch (err) {
      alert(err.message);
    }
  }

  function renderCases() {
    var tbody = $('cases-table').querySelector('tbody'); clear(tbody);
    state.cases.forEach(function (c) {
      var tr = el('tr');
      tr.appendChild(el('td', null, c.case_id || c.id));
      tr.appendChild(el('td', null, c.employee_id || ''));
      tr.appendChild(el('td', null, c.request || (c.intent ? label(c.intent) : '')));
      var st = el('td'); st.appendChild(el('span', statusClass(c.status), label(c.status))); tr.appendChild(st);
      var rk = el('td'); rk.appendChild(el('span', riskClass(c.risk), c.risk || '')); tr.appendChild(rk);
      tr.appendChild(el('td', null, c.reviewer || ''));
      tbody.appendChild(tr);
    });
  }

  function renderMetrics() {
    var m = state.metrics; var box = $('metrics'); clear(box);
    var rows = [
      ['Total cases', m.total_cases, 'in this session'],
      ['Pending approvals', m.pending_approvals, 'waiting on a human'],
      ['Completion rate', m.completion_rate + '%', 'resolved or approved'],
      ['Escalation rate', m.escalation_rate + '%', 'routed to a specialist'],
      ['Human override rate', m.human_override_rate + '%', 'observed'],
      ['Estimated hours saved', m.estimated_hours_saved, 'assumes 14 min per case; an estimate, not a measure']
    ];
    rows.forEach(function (r) {
      var card = el('div', 'metric');
      card.appendChild(el('div', 'label', r[0]));
      card.appendChild(el('div', 'value', String(r[1])));
      card.appendChild(el('div', 'hint', r[2]));
      box.appendChild(card);
    });
  }

  function renderEvaluation() {
    var box = $('evals'); clear(box);
    var ev = state.evaluation;
    if (!ev) { box.appendChild(el('p', 'muted small', 'Evaluation report not served by this build. Run python -m evals.run and see evals/latest_report.json.')); return; }
    var grid = el('div', 'metrics');
    var head = el('div', 'metric');
    head.appendChild(el('div', 'label', 'Baseline pass rate'));
    head.appendChild(el('div', 'value', ev.passed + '/' + ev.total));
    head.appendChild(el('div', 'hint', ev.pass_rate + '% · suite v' + ev.suite_version + ' · ' + shortTime(ev.generated_at)));
    grid.appendChild(head);
    Object.keys(ev.metrics || {}).forEach(function (k) {
      var c = el('div', 'metric');
      c.appendChild(el('div', 'label', label(k)));
      c.appendChild(el('div', 'value', ev.metrics[k] + '%'));
      grid.appendChild(c);
    });
    box.appendChild(grid);
    var table = el('table', 'table');
    var thead = el('thead'); var hr = el('tr');
    ['Risk category', 'Passed'].forEach(function (h) { hr.appendChild(el('th', null, h)); });
    thead.appendChild(hr); table.appendChild(thead);
    var tbody = el('tbody');
    Object.keys(ev.categories || {}).forEach(function (k) {
      var tr = el('tr');
      tr.appendChild(el('td', null, label(k)));
      tr.appendChild(el('td', null, ev.categories[k].passed + ' / ' + ev.categories[k].total));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    table.style.marginTop = '12px';
    box.appendChild(table);
  }

  function renderAudit() {
    var tbody = $('audit-table').querySelector('tbody'); clear(tbody);
    if (!state.audit.length) { var tr0 = el('tr'); var td0 = el('td', 'muted', 'No events yet this session.'); td0.colSpan = 5; tr0.appendChild(td0); tbody.appendChild(tr0); return; }
    state.audit.slice().reverse().forEach(function (a) {
      var tr = el('tr');
      tr.appendChild(el('td', null, shortTime(a.timestamp)));
      tr.appendChild(el('td', null, a.case_id));
      tr.appendChild(el('td', null, a.actor));
      tr.appendChild(el('td', null, label(a.event)));
      tr.appendChild(el('td', null, JSON.stringify(a.details)));
      tbody.appendChild(tr);
    });
  }

  function wire() {
    document.querySelectorAll('.tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        document.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('is-active'); });
        document.querySelectorAll('.view').forEach(function (v) { v.classList.remove('is-active'); });
        tab.classList.add('is-active');
        $('view-' + tab.getAttribute('data-view')).classList.add('is-active');
      });
    });
    document.querySelectorAll('.chip').forEach(function (chip) {
      chip.addEventListener('click', function () { $('request').value = chip.getAttribute('data-example'); });
    });
    $('submit').addEventListener('click', submit);
    $('request').addEventListener('keydown', function (e) { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit(); });
  }

  wire();
  bootstrap().catch(function (err) { $('submit-status').textContent = 'Could not reach the API: ' + err.message; });
})();
