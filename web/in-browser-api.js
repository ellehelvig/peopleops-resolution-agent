/* Runs the demo's Python API inside the visitor's browser when no server is present.
 *
 * Loads a pinned Pyodide from jsDelivr, copies the peopleops package into its
 * in-memory filesystem, and calls peopleops.api.Api, the same code server.py
 * wraps in HTTP. Requests, cases, and approvals never leave the browser, and
 * each visitor gets their own session. */
(function () {
  'use strict';

  var PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
  // Every module in peopleops/. tests/test_api.py fails if this list drifts.
  var MODULES = ['__init__.py', 'api.py', 'data.py', 'engine.py', 'store.py'];

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.crossOrigin = 'anonymous';
      script.onload = resolve;
      script.onerror = function () { reject(new Error('Could not load ' + src)); };
      document.head.appendChild(script);
    });
  }

  async function fetchText(path) {
    var res = await fetch(path, { cache: 'no-cache' });
    if (!res.ok) throw new Error('Could not load ' + path + ' (' + res.status + ')');
    return res.text();
  }

  async function start() {
    await loadScript(PYODIDE + 'pyodide.js');
    var pyodide = await window.loadPyodide({ indexURL: PYODIDE });
    pyodide.FS.mkdirTree('/app/peopleops');
    var sources = await Promise.all(MODULES.map(function (name) { return fetchText('peopleops/' + name); }));
    MODULES.forEach(function (name, i) { pyodide.FS.writeFile('/app/peopleops/' + name, sources[i]); });
    var report = '';
    try { report = await fetchText('evals/latest_report.json'); } catch (e) { report = ''; }
    pyodide.globals.set('report_json', report);
    pyodide.runPython(
      'import json, sys\n' +
      'sys.path.insert(0, "/app")\n' +
      'from peopleops.api import Api\n' +
      'api = Api(json.loads(report_json) if report_json else None)\n'
    );
    var handleJson = pyodide.globals.get('api').handle_json;
    return function call(method, path, body) {
      return JSON.parse(handleJson(method, path, body || ''));
    };
  }

  window.ResolveInBrowser = { start: start };
})();
