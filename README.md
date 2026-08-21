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

## Notes

PTZ commands are sent directly through the already configured Tuya integration. Depending on the camera firmware, a direction can continue moving until **Stop** is pressed.
