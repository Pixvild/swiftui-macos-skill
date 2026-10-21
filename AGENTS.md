# Maintaining swiftui-macos

These rules apply to maintaining this skill directory, not to the host application's architecture.

Keep SKILL.md focused and references task-routed. Do not turn project-specific decisions into universal SwiftUI requirements.

Keep authored Chinese guides separate from retrieved Apple documents. Register sources with their actual evidence and reading state. Automated synchronization cannot set a source to fully read or mark an app compiled.

Use Python 3.9+ standard library. Do not add an installer, telemetry, hidden API calls or arbitrary external download hosts. Network operations must be explicit. Do not overwrite an application's root AGENTS.md.

Before claiming success run from this directory:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py
```

Inspect reports and record missing macOS, live-network and actual-agent evaluation. Offline synthetic fixtures are not a substitute for these checks.

The synchronization script only implements a conservative subset renderer and explicit source-list retrieval. Unknown DocC structures must be surfaced, with raw JSON retained; they must not be silently discarded. Recheck URL allowlists, cache freshness, overload identity and failure behavior after any change.
