# Contributing

Thank you for helping keep this list useful.

## What belongs here

A project fits when all of these are true:

1. **It is a tool you run.** It helps operate an LLM application in production: tracing, evaluation, gateways and routing, guardrails, red teaming, or prompt management. Papers, courses, tutorials, model benchmarks, awesome lists and general agent frameworks do not fit.
2. **It has a license file.** Open-source and source-available licenses are both accepted. Source-available projects get a † mark. A repo with no license is not listed, because nobody may legally use it.
3. **It works today.** It has a release or install instructions and documentation. There is no star minimum.

## How to add a project

1. Edit `data/projects.toml`. Do not edit `README.md`, because the build script overwrites it.
2. Add one line to the right category:

   ```toml
   { repo = "owner/name", desc = "One neutral sentence about what it does." },
   ```

3. Keep `desc` neutral and short. Say what the tool does. Leave out claims like "fastest" or "best", and leave out funding or accelerator badges.
4. Set `license` only when GitHub shows "Other" or no license for the repo. Set `source_available = true` when the main code is not under an OSI-approved license.
5. Optional: set `homepage = "https://example.com"` when the project has an official site. The table then shows a `[site](...)` link next to the GitHub link. Leave it off when there is no separate site.
6. Optional: run `GITHUB_TOKEN=<token> python scripts/build_readme.py` to check your entry. It needs Python 3.11 or newer and no packages.

Order inside the file does not matter. The build sorts every table by stars.

## Corrections

If a description is wrong, a project is now archived, or a license changed, open an issue or a pull request. Stars, archived status and push dates refresh by themselves every week.
