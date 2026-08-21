# Tuya PTZ for Home Assistant

Adds PTZ controls to Tuya cameras that expose the `ptz_control` and `ptz_stop` functions.

## Supported controls

- Up
- Up-right
- Right
- Down-right
- Down
- Down-left
- Left
- Up-left
- Stop
- Continuous movement for Advanced Camera Card

The integration reuses the existing Home Assistant Tuya connection. No Tuya credentials are requested again.

## Installation with HACS

1. Add this repository as a custom HACS repository.
2. Choose **Integration**.
3. Install **Tuya PTZ**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**.
6. Choose **Tuya PTZ**.
7. Select a Tuya camera exposing `ptz_control` and `ptz_stop`.

The PTZ buttons are attached to the existing Tuya camera device.

## Advanced Camera Card

Advanced Camera Card already has a native PTZ joystick. This integration provides the `tuya_ptz.move` service so the card can use its continuous PTZ controls without modifying Advanced Camera Card.

Add the following to the camera configuration in your Advanced Camera Card YAML. Replace `camera.salon` with your camera entity if needed:

```yaml
ptz:
  service: tuya_ptz.move
  data_up_start:
    direction: up
    phase: start
  data_up_stop:
    direction: up
    phase: stop
  data_right_start:
    direction: right
    phase: start
  data_right_stop:
    direction: right
    phase: stop
  data_down_start:
    direction: down
    phase: start
  data_down_stop:
    direction: down
    phase: stop
  data_left_start:
    direction: left
    phase: start
  data_left_stop:
    direction: left
    phase: stop
```

The card will then expose its PTZ controls as continuous start/stop actions. The Tuya camera does not expose a speed DP, so the camera's own PTZ speed is used.

For diagonal directions, the Tuya DP supports `up_right`, `down_right`, `down_left`, and `up_left`; those can be configured with the same `data_<direction>_start/stop` pattern if your Advanced Camera Card version exposes diagonal controls.

## Notes

PTZ commands are sent directly through the already configured Tuya integration. The LSC PTZ Camera Dualband diagnostic exposes `ptz_control` values `0..7` and the boolean `ptz_stop`, which this integration maps to the eight directions and stop command.
