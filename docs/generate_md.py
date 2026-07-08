#!/usr/bin/env python3
"""Generate MODELS.md from models.json. Run whenever models.json changes."""
import json
from pathlib import Path

DOCS = Path(__file__).resolve().parent

def feat_icon(val):
    if val is True: return "✅"
    if val is False: return "—"
    if isinstance(val, str): return f"🔘 {val}"
    return "—"

def main():
    data = json.loads((DOCS / "models.json").read_text())
    lines = []
    lines.append("# videogenCN — Model Reference")
    lines.append("")
    lines.append(f"> Auto-generated from [models.json](models.json) · Last updated: {data['last_updated']}")
    lines.append(f"> {data['price_note']}")
    lines.append("")
    lines.append("## Quick Reference")
    lines.append("")
    lines.append("| Use case | Model | Provider | Price |")
    lines.append("|----------|-------|----------|-------|")

    for p in data["providers"]:
        for m in p["models"]:
            if m.get("default") and m.get("use_case"):
                lines.append(f"| {m['use_case']} | `{m['name']}` | {p['name']} | {m['price']} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    for p in data["providers"]:
        lines.append(f"## {p['name']} — {p['full_name']}")
        lines.append("")
        lines.append(f"{p['description']}")
        lines.append("")
        lines.append(f"- **API Key**: `{p['api_key_env']}` → [Get Key]({p['api_key_url']})")
        lines.append(f"- **Region**: {p['region']}")
        if p.get("region_note"):
            lines.append(f"- ⚠️ {p['region_note']}")
        lines.append("")
        lines.append("| Model | Family | Modes | Resolution | Duration | Audio | Camera | Multi-shot | Price | Use Case |")
        lines.append("|-------|--------|-------|------------|----------|-------|--------|------------|-------|----------|")

        for m in p["models"]:
            name = m['name']
            if m.get('default'):
                name += ' ⭐'
            if m.get('experimental'):
                name += ' ⚠️'
            modes = ", ".join(m['modes'])
            lines.append(
                f"| `{name}` | {m['family']} | {modes} | {m['resolution']} | "
                f"{m['duration']} | {feat_icon(m['audio'])} | {feat_icon(m['camera_control'])} | "
                f"{feat_icon(m['multi_shot'])} | {m['price']} | {m['use_case']} |")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Legend")
    lines.append("")
    lines.append("| Symbol | Meaning |")
    lines.append("|--------|---------|")
    lines.append("| ⭐ | Default model for this mode |")
    lines.append("| ✅ | Supported |")
    lines.append("| — | Not supported |")
    lines.append("| 🔘 | Optional (enable with flag) |")
    lines.append("| ⚠️ | Experimental — API may change, limited param support |")
    lines.append("")

    for key, desc in data.get("features_legend", {}).items():
        lines.append(f"- **{key}**: {desc}")

    out = DOCS / "MODELS.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"Generated {out} ({len(lines)} lines)")

if __name__ == "__main__":
    main()
