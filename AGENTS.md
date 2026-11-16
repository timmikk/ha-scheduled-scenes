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
