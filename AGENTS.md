# ha-scheduled-scenes

Home Assistant custom integration. Component code is under
custom_components/scheduled_scenes/; tests live in tests/ and run with pytest.

## Workflow

Use this repository's tasks/ directory for component-scoped work. File
cross-cutting deployment, infrastructure, or HACS pipeline work in the infra
planning hub at ~/dev/infra/tasks/. Shared task-board and CI helpers live
under ~/dev/dev-tools/.

Tool-neutral workflow instructions live in `prompts/<name>.md`; discoverable
agent skills in `.agents/skills/<name>/SKILL.md` route to those prompts. For
`/plan`, `/execute-task`, `/push-changes`, `/verify-task`, `/code-review`,
`/investigate`, `/investigate-logs`, `/list-tasks`, `/intake-issue`, and
`/commit` style work, read the corresponding prompt before acting.

## Security

This repository is public. Never commit tokens, passwords, personal data, or
Home Assistant runtime configuration. Keep secrets in Home Assistant's
runtime configuration or its vault-managed deployment path.

See README.md for development, release, and HACS installation details.

## Forgejo API access

Use the shared `~/dev/dev-tools` Forgejo API client for repository status and
Actions log reads. For the exact `timo/ha-scheduled-scenes` Forgejo origin it
resolves `FORGEJO_TOKEN` from Infisical Production path
`/repo/agents/ha-scheduled-scenes/FORGEJO_TOKEN`, using the environment-local
`~/.config/infisical/repo-agents.env` Service Token (mode `0600`). Do not add a
repo-local token file or pass token values through chat, command arguments, or
logs. Git clone and push remain SSH-authenticated and do not use this API token.
Create the Forgejo token with `write:issue` and `write:repository`, matching
the existing repo-agent tokens, and **Specific repositories** access for
`timo/ha-scheduled-scenes`; Forgejo still permits read-only access to public
repositories outside that selection. Rotate the token by creating a replacement
with the same restriction, updating the Infisical value, verifying API reads
without displaying the value, and revoking the old token.
