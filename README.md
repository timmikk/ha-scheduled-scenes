# ha-scheduled-scenes

Dynamic scheduled scenes and circadian lighting for Home Assistant

Home Assistant custom integration. Development happens on
[git.clo.dy.fi/timo/ha-scheduled-scenes](https://git.clo.dy.fi/timo/ha-scheduled-scenes);
the public GitHub mirror at
[timmikk/ha-scheduled-scenes](https://github.com/timmikk/ha-scheduled-scenes) is
HACS-installable. See `info.md` for install/rollback instructions.

## Development

- Component code lives in `custom_components/scheduled_scenes/`.
- Tests: `pytest` (uses `pytest-homeassistant-custom-component`).
- CI: `.forgejo/workflows/ci.yml` runs `hassfest` + `hacs/action` + pytest.
- Release: tag `vX.Y.Z` on Forgejo → mirror syncs → GitHub Actions
  (`.github/workflows/release.yml`) creates a Release object → HACS
  offers the version in the UI.

## Secrets policy

This repo is **public**. Never commit tokens, passwords, or personal data.
Home Assistant fills those at runtime from `configuration.yaml`, config-flow
options, or `secrets.yaml` on the host — none of that touches this repo.

## Pipeline

See [`docs/ha-custom-components.md`](https://git.clo.dy.fi/timo/infra/src/branch/main/docs/ha-custom-components.md)
in the infra repo for the full pipeline (Forgejo primary + public GitHub
mirror + HACS registration + release/rollback flow).
