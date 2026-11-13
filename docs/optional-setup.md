# Optional integrations

[Project overview](../README.md)

Run these commands from the repository root. They are separate from the default rules-only demo.

## MCP and model setup

These features are separate from the default browser demo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes --no-deps -r requirements-bootstrap.txt
python -m pip install -r requirements-optional-lock.txt
python mcp_server.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell. The MCP facade exposes three narrow tools and no approval tool. Its store is separate from the HTTP API's store.

Model-screen evaluation can use signed-in Claude Code or an `ANTHROPIC_API_KEY` stored outside the repo. It consumes plan usage or API credits. Follow [the evaluation methodology](evaluation-methodology.md#recording-a-run-after-the-prompt-injection-boundary-change) before running it, and keep practitioner-written sets private. No live model call is needed for the default app or offline unit tests.

The optional dependency lock records exact versions resolved for Python 3.11 and later. To refresh it, use uv 0.13.4 or later and run `uv pip compile requirements-optional.txt --python-version 3.11 --universal --no-header --upgrade --output-file requirements-optional-lock.txt`, install it in a fresh environment, and rerun the offline checks before review.

The [Python security announcement](https://discuss.python.org/t/109576) requires
pip 26.2.2 or later and certifi 2026.10.19 or later after the October 2026
eMudhra incident. The bootstrap file verifies the official pip wheel by SHA-256.
Repeat the bootstrap and locked install in each existing optional environment,
then restart its processes. Rebuild containers with current system certificates.
The default browser demo does not install these optional SDKs.

