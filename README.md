# ha-scheduled-scenes

Dynamic scheduled scenes and circadian lighting for Home Assistant.

Home Assistant custom integration. Development happens on
[git.clo.dy.fi/timo/ha-scheduled-scenes](https://git.clo.dy.fi/timo/ha-scheduled-scenes);
the public GitHub mirror at
[timmikk/ha-scheduled-scenes](https://github.com/timmikk/ha-scheduled-scenes) is
HACS-installable. See `info.md` for install/rollback instructions.

## Features

- **Continuous Circadian & Schedule Interpolation**: Seamlessly interpolates brightness and color temperature (Kelvin) between defined time checkpoints across 24 hours.
- **Midnight Wrapping**: Full mathematical support for schedules crossing midnight (e.g. 23:00 to 07:00).
- **Per-Light Overrides**: Override brightness or color temperature for specific lights within a multi-light room program.
- **Smart Light Automation**: Automatically adapts transitions when lights are turned on or off.
- **Two-Tier Configuration**: Configure effortlessly via YAML under `scheduled_scenes:` or directly via the Home Assistant UI / Config Flow.
- **Switches & Diagnostic Sensors**: Exposes a toggle switch (`switch.schedule_<name>`) and a diagnostic sensor (`sensor.<name>_schedule_phase`) for every configured program.
- **Domain Services**: Provides `scheduled_scenes.turn_on`, `scheduled_scenes.turn_off`, `scheduled_scenes.enable`, `scheduled_scenes.disable`, and `scheduled_scenes.reload`, plus legacy alias services (`<name>_turn_on`, `<name>_turn_off`, etc.).

## Configuration

### Option 1: YAML

Add to your `configuration.yaml`:

```yaml
scheduled_scenes:
  - name: study
    lights:
      - light.desk_lamp
      - light.ceiling_light
    transition_time: 120
    transition_interval: 120
    schedule:
      - time: "07:00"
        brightness: 40
        temp: 2700
      - time: "09:00"
        brightness: 100
        temp: 4500
      - time: "18:00"
        brightness: 80
        temp: 3500
      - time: "22:30"
        brightness: 20
        temp: 2200
```

### Option 2: Home Assistant UI / Config Flow

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **Dynamic scheduled scenes**.
3. Fill in the program name, select light entities from the dropdown, and paste or customize your YAML schedule.
4. Future adjustments can be made anytime by clicking **Configure** on the integration card.

## Development

- Component code lives in `custom_components/scheduled_scenes/`.
- Tests: `pytest` (uses `pytest-homeassistant-custom-component`).
- CI: `.forgejo/workflows/ci.yml` runs `hassfest` + `hacs/action` + pytest.
- Release: tag `vX.Y.Z` on Forgejo -> mirror syncs -> GitHub Actions creates release assets.

## Secrets policy

This repo is **public**. Never commit tokens, passwords, or personal data.
Home Assistant fills those at runtime from `configuration.yaml`, config-flow
options, or `secrets.yaml` on the host - none of that touches this repo.
