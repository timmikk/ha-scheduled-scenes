# ha-scheduled-scenes

Dynamic scheduled scenes and circadian lighting for Home Assistant.

Home Assistant custom integration. Development happens on
[git.clo.dy.fi/timo/ha-scheduled-scenes](https://git.clo.dy.fi/timo/ha-scheduled-scenes);
the public GitHub mirror at
[timmikk/ha-scheduled-scenes](https://github.com/timmikk/ha-scheduled-scenes) is
HACS-installable. See `info.md` for install/rollback instructions.

## Features

- **Continuous Circadian & Schedule Interpolation**: Seamlessly interpolates brightness and color temperature (Kelvin) between defined time checkpoints across 24 hours.
- **Interactive Brightness Stepping & Manual Override**: Increase or decrease room brightness in discrete steps (e.g. +10% / -10%) via wall buttons, remotes, or automations. Setting manual brightness suspends automated schedule transitions so periodic updates don't revert user adjustments.
- **Start Brightness Estimation**: When brightness stepping is triggered, the integration estimates the room's current brightness level by inspecting active physical light states and inverting brightness curves, preventing abrupt jumps or wrong-direction stepping.
- **Room Brightness Distribution Curves**: Define non-linear light distribution across room brightness levels (e.g. mood lights at 100% while ceiling downlights are only at 30% when room brightness is 50%).
- **Dim-to-Warm Synergy**: Brightness adjustments automatically evaluate each fixture's configured dim-to-warm curve, smoothly warming or cooling the room as it dims or brightens.
- **Status & Diagnostic Entities**: Complete suite of entities per room program for operational mode, live room brightness, command history, curve usage, and problem monitoring.
- **Unified Device Grouping**: Automatically groups all switches, sensors, and diagnostic binary sensors into a clean Home Assistant Device per room.
- **Midnight Wrapping**: Full mathematical support for schedules crossing midnight (e.g. 23:00 to 07:00).
- **Per-Light Overrides**: Override brightness or color temperature for specific lights within a multi-light room program.
- **Smart Light Automation**: Automatically adapts transitions when lights are turned on or off.
- **Two-Tier Configuration**: Configure effortlessly via YAML under `scheduled_scenes:` or directly via the Home Assistant UI / Config Flow.
- **Domain Services**: Provides `scheduled_scenes.turn_on`, `turn_off`, `enable`, `disable`, `adjust_brightness`, `step_brightness`, `resume_schedule`, and `reload`, plus legacy alias services (`<name>_adjust_brightness`, etc.).

## Status & Diagnostic Entities

Each configured room program registers a Home Assistant Device grouping the following entities:

| Entity | Platform | ID Pattern | Description |
|--------|----------|------------|-------------|
| **Schedule Switch** | `switch` | `switch.schedule_<room>` | Enable or disable automated schedule transitions for the room. |
| **Schedule Phase** | `sensor` | `sensor.<room>_schedule_phase` | Current active schedule interval (`HH:MM-HH:MM` or `idle`), with start/end brightness and Kelvin in attributes. |
| **Current Mode** | `sensor` | `sensor.<room>_mode` | Operational mode: `off` (disabled manually), `auto-off` (lights off/standby), `auto` (schedule actively driving lights), or `manual` (manual brightness override active). |
| **Current Room Brightness** | `sensor` | `sensor.<room>_current_brightness` | Live overall room brightness percentage (`0-100%`), evaluated from manual overrides, inverted room curves, or schedule transitions. |
| **Last Command** | `sensor` *(diagnostic)* | `sensor.<room>_last_command` | Last command or trigger dispatched (`turn on`, `turn off`, `auto on`, `auto off`, `set brightness`, `step brightness`, `resume schedule`, `enable`, `disable`, `periodic update`), with execution timestamp and parameters in attributes. |
| **Dim-to-Warm In Use** | `binary_sensor` *(diagnostic)* | `binary_sensor.<room>_dim_to_warm_in_use` | `on` if dim-to-warm curves are configured, listing configured curves, assigned light entities, and currently active fixtures in attributes. |
| **Brightness Curve In Use** | `binary_sensor` *(diagnostic)* | `binary_sensor.<room>_brightness_curve_in_use` | `on` if room brightness distribution curves are configured, exposing mapped curves and fixtures in attributes. |
| **Problem State** | `binary_sensor` *(diagnostic, problem)* | `binary_sensor.<room>_problem` | `on` if missing or unavailable light entities, invalid schedules, or runtime service failures occur, exposing unavailable entity IDs and error logs in attributes. |

## Configuration

### Option 1: YAML

#### Basic Schedule (Explicit Brightness & Color Temp)

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

#### Dim-to-Warm Curves & Room Brightness Distribution

Define shared curves once by light model or entity group. When schedule steps specify `brightness` without `temp`, any entity mapped to a curve derives its color temperature automatically via piecewise linear interpolation along that curve:

```yaml
scheduled_scenes:
  curves:
    warm_glow_spots:
      lights:
        - light.kitchen_spot_1
        - light.kitchen_spot_2
        - light.hallway_spot_1
      curve:
        - brightness: 1
          temp: 2200
        - brightness: 50
          temp: 2700
        - brightness: 100
          temp: 4000
    ambient_led_strip:
      lights:
        - light.living_room_cove
      curve:
        - [1, 2000]
        - [50, 2600]
        - [100, 3500]

  # Optional room brightness curves mapping overall room % to individual fixtures
  brightness_curves:
    living_room_accent:
      lights:
        - light.living_room_cove
      points:
        - [0, 0]
        - [50, 100]    # Mood light is at 100% when room is at 50%
        - [100, 100]
    living_room_main:
      lights:
        - light.living_room_ceiling
      points:
        - [0, 0]
        - [30, 0]      # Ceiling stays off below 30% room brightness
        - [50, 30]     # Ceiling is at 30% when room is at 50%
        - [100, 100]

  programs:
    - name: living_room
      lights:
        - light.living_room_cove
        - light.living_room_ceiling
      schedule:
        - time: "07:00"
          brightness: 30
        - time: "13:00"
          brightness: 80
        - time: "21:00"
          brightness: 40
```

Curve checkpoints support both dictionary mappings (`[{brightness: 1, temp: 2200}, ...]`) and compact coordinate pairs (`[[1, 2200], [100, 4000]]`). Curves can also be defined directly inside individual room programs under `curves:` and `brightness_curves:`.

### Interactive Brightness Control & Wall Buttons

Use `scheduled_scenes.adjust_brightness` (or `scheduled_scenes.step_brightness`) to adjust brightness in steps or set an absolute target.

#### Service Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Target scheduled scene switch (e.g. `switch.schedule_living_room`). |
| `step` | int | Relative brightness change percentage (e.g. `+10` or `-10`). |
| `brightness` | int | Optional absolute target room brightness percentage (`0-100%`). Setting `0` turns lights off. |
| `transition` | float | Optional transition time in seconds (defaults to `transition_time_on`, typically 0.3s). |

#### Automation Example: Zigbee Remote Button

```yaml
automation:
  - alias: "Living Room Remote - Brightness Up"
    trigger:
      - platform: device
        domain: mqtt
        device_id: <your_device_id>
        type: action
        subtype: brightness_move_up
    action:
      - service: scheduled_scenes.adjust_brightness
        target:
          entity_id: switch.schedule_living_room
        data:
          step: 10
          transition: 0.3

  - alias: "Living Room Remote - Brightness Down"
    trigger:
      - platform: device
        domain: mqtt
        device_id: <your_device_id>
        type: action
        subtype: brightness_move_down
    action:
      - service: scheduled_scenes.adjust_brightness
        target:
          entity_id: switch.schedule_living_room
        data:
          step: -10
          transition: 0.3

  - alias: "Living Room Remote - Resume Automated Schedule"
    trigger:
      - platform: device
        domain: mqtt
        device_id: <your_device_id>
        type: action
        subtype: arrow_right_click
    action:
      - service: scheduled_scenes.resume_schedule
        target:
          entity_id: switch.schedule_living_room
```

### Option 2: Home Assistant UI / Config Flow

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **Dynamic scheduled scenes**.
3. Fill in the program name, select light entities from the dropdown, and paste or customize your YAML schedule (and optional curves).
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
