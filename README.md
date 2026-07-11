# neilghosh/skills

[![skills.sh](https://skills.sh/b/neilghosh/skills)](https://skills.sh/neilghosh/skills)

Distributable [Agent Skills](https://agentskills.io) — self-contained folders of
instructions + scripts that an AI coding agent (Claude Code, Claude.ai, Copilot CLI,
etc.) loads dynamically to perform a specialized task in a repeatable way.

Each skill lives under [`skills/`](./skills) with a `SKILL.md` (YAML frontmatter +
instructions) and any helper scripts.

## Skills

| Skill | What it does |
|---|---|
| [**itr-tax**](./skills/itr-tax) | Expert assistant for filing an **Indian ITR-2 (new regime)** via the online e-filing wizard for a **salaried taxpayer with capital gains and foreign assets/income** (RSU/ESPP/ETF/dividends + FTC/Form 67). Encodes the salary/terminal-benefit, capital-gains set-off, foreign-income/FTC, and Schedule OS/CG/112A/FSI/TR/FA/AL workflow; the portal's cross-schedule validation quirks; deterministic **CSV generators** (112A, FA A3, Form 67) and a **final-JSON auditor**; and a pre-submission multi-model audit. Includes a "Currency of Law" gate that requires verifying current-year rates/rules/formats from official sources (rules change yearly). |

## Install

### Claude Code (plugin marketplace)
```
/plugin marketplace add neilghosh/skills
/plugin install itr-tax@neilghosh-skills
```
Then just mention the skill (e.g. "use the itr-tax skill to …").

### Claude.ai / Claude API
Upload the `skills/itr-tax` folder as a custom skill — see
[Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

### Any agent with a skills directory (manual)
```
git clone https://github.com/neilghosh/skills.git
cp -r skills/skills/itr-tax /path/to/your/agent/skills/
```

### skills.sh
This repo is indexed at [skills.sh/neilghosh/skills](https://skills.sh/neilghosh/skills).

## Helper scripts (itr-tax)

Generic, no-personal-data Python helpers under
[`skills/itr-tax/scripts`](./skills/itr-tax/scripts) — they take input JSON + the
freshly-downloaded portal template and emit portal-ready CSVs / audit reports:
`build_112a_csv.py`, `build_fa_a3_csv.py`, `build_form67_csv.py`, `audit_itr_json.py`.
See [scripts/README.md](./skills/itr-tax/scripts/README.md).

## ⚠️ Disclaimer

Provided **for educational/automation assistance only** and is **not** professional tax,
legal, or financial advice. Indian tax law, rates, thresholds, forms, and the e-filing
portal's CSV formats/validations **change every year** — always verify current-year rules
and templates from official sources (`incometax.gov.in`, the relevant Finance Act, CBDT
circulars, and the official DTAA text) before filing, and review every figure independently.
The author accepts no liability for filings made using this skill.

## License

MIT © Neil Ghosh — see [LICENSE](./LICENSE).
