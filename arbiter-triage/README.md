# Arbiter Triage Engine

Policy enforcement layer for AI query routing. The triage engine inspects
incoming queries through a 9-stage pipeline and classifies each into a
security zone before the query reaches any model backend.

## Architecture

The engine runs a sequential 9-stage inspection pipeline:

1. **Tokenization** -- normalize and split the input.
2. **Schema validation** -- verify the request envelope.
3. **Rate-limit check** -- per-user and per-org quotas.
4. **Content fingerprinting** -- hash-based deduplication.
5. **Policy rule matching** -- evaluate declarative allow/deny rules.
6. **Semantic analysis** -- lightweight embedding similarity against known risk patterns.
7. **Context window audit** -- detect prompt-injection markers.
8. **PII scan** -- flag or redact personally identifiable information.
9. **Zone assignment** -- produce the final classification.

## Zone Classification

Every query exits the pipeline with exactly one zone label:

| Zone      | Meaning                                    | Action              |
|-----------|--------------------------------------------|----------------------|
| **GREEN** | No policy concerns detected                | Route to backend     |
| **AMBER** | Elevated risk; additional review needed     | Hold for supervisor  |
| **RED**   | Policy violation or high-confidence threat  | Reject immediately   |

## Directory Structure

```
arbiter-triage/
  systemd/
    arbiter-triage.service   # systemd unit file
  src/
    arbiter_triage/
      api/
        socket_server.py     # Unix socket listener
      pipeline/
        stages/              # One module per inspection stage
      policy/
        rules/               # Declarative YAML policy rules
      crypto/
        record_seal.py       # Encrypt triage records at rest
  tests/
    unit/
    integration/
  pyproject.toml
```

## Running

### Via systemd (production)

```bash
sudo cp systemd/arbiter-triage.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now arbiter-triage
```

The service listens on a Unix socket at `/var/run/arbiter/triage.sock`.

### Manually (development)

```bash
cd /opt/arbiter
./venv/bin/python -m arbiter_triage.api.socket_server
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/unit/ -k "pipeline"     # run only pipeline unit tests
pytest tests/integration/            # requires a running socket server
```

## Dependencies

- Python 3.11+
- systemd 252+ (for MemoryMax / CPUQuota cgroup v2 controls)
- Runtime Python packages are declared in `pyproject.toml`

## Security Properties

- **No network access.** The systemd unit sets `PrivateNetwork=true`; the
  engine communicates exclusively over a local Unix socket.
- **No raw query logging.** Log output contains zone labels, stage timings,
  and request IDs only. Query text never appears in the journal.
- **Encrypted records.** Every triage decision record is sealed with
  AES-256-GCM before being written to `/var/lib/arbiter/triage`.
- **Strict filesystem isolation.** `ProtectSystem=strict`, `ProtectHome=true`,
  and explicit `ReadWritePaths` limit what the process can touch.
- **No privilege escalation.** `NoNewPrivileges=true` and
  `RestrictSUIDSGID=true` prevent any capability gain after startup.

## License

Internal use only. See repository root for terms.
