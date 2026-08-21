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
- RTSP stream diagnostic using the same Tuya API as Home Assistant

The integration reuses the existing Home Assistant Tuya connection. No Tuya credentials are requested again.

## Installation with HACS

1. Add this repository as a custom HACS repository.
2. Choose **Integration**.
3. Install **Tuya PTZ**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**.
6. Choose **Tuya PTZ**.
7. Select each Tuya camera that exposes `ptz_control` and `ptz_stop`.

You can configure more than one PTZ camera. Each configured camera is stored separately and can be selected by its Home Assistant camera entity.

## Advanced Camera Card

Advanced Camera Card has a native PTZ joystick. This integration provides the `tuya_ptz.move` service so the card can use continuous PTZ controls without modifying Advanced Camera Card.

### Important when multiple PTZ cameras are configured

When only one Tuya PTZ camera is configured, `tuya_ptz.move` can use that camera automatically.

When two or more PTZ cameras are configured, you **must identify the target camera** in the Advanced Camera Card actions. Add `camera_entity` to every `data_*_start` and `data_*_stop` action.

Example for `camera.salon`:

```yaml
type: custom:advanced-camera-card
cameras:
  - camera_entity: camera.salon
    live_provider: auto
    title: Salon
    icon: mdi:sofa

    ptz:
      service: tuya_ptz.move

      data_up_start:
        direction: up
        phase: start
        camera_entity: camera.salon
      data_up_stop:
        direction: up
        phase: stop
        camera_entity: camera.salon

      data_right_start:
        direction: right
        phase: start
        camera_entity: camera.salon
      data_right_stop:
        direction: right
        phase: stop
        camera_entity: camera.salon

      data_down_start:
        direction: down
        phase: start
        camera_entity: camera.salon
      data_down_stop:
        direction: down
        phase: stop
        camera_entity: camera.salon

      data_left_start:
        direction: left
        phase: start
        camera_entity: camera.salon
      data_left_stop:
        direction: left
        phase: stop
        camera_entity: camera.salon

view:
  default: live
status_bar:
  style: overlay
live:
  preload: true
```

For another camera, replace every `camera.salon` with that camera's entity ID, for example `camera.lsc_smart_camera_ptz_dualband_indoor`.

### Diagonal directions

The Tuya DP supports all eight directions:

| Direction | Tuya value |
|---|---:|
| Up | `0` |
| Up-right | `1` |
| Right | `2` |
| Down-right | `3` |
| Down | `4` |
| Down-left | `5` |
| Left | `6` |
| Up-left | `7` |

If your Advanced Camera Card version exposes diagonal PTZ actions, use the same `data_<direction>_start` / `data_<direction>_stop` pattern.

## How movement works

- `phase: start` sends `ptz_control` and starts the camera movement.
- `phase: stop` sends `ptz_stop` and stops the movement.
- This makes the integration suitable for a joystick or press-and-hold PTZ control.
- The camera does not expose a PTZ speed data point, so the camera's own PTZ speed is used.

## Stream diagnostic

Home Assistant's official Tuya camera integration requests an RTSP stream source from Tuya using `get_device_stream_allocate(device_id, "rtsp")`. The `tuya_ptz.diagnose_stream` service performs the same request and writes a **sanitized** result to the Home Assistant log. Query parameters such as `signInfo` are deliberately removed from the log so stream credentials are not exposed.

This is useful when investigating video quality, stream errors, or whether Tuya is returning a usable main stream.

### Run the diagnostic

Go to **Developer Tools → Actions**, select:

```text
tuya_ptz.diagnose_stream
```

For a setup with multiple PTZ cameras, target the camera explicitly:

```yaml
camera_entity: camera.lsc_smart_camera_ptz_dualband_indoor
```

Then check **Settings → System → Logs** for a line beginning with:

```text
Tuya PTZ stream diagnostic
```

The log contains the RTSP scheme, host, port and path, but **never logs the signed query parameters**.

If Tuya returns no URL or an error, the diagnostic records that result. The diagnostic does not change the camera configuration and does not send any PTZ command.

## Notes

PTZ commands are sent directly through the already configured Tuya integration. The LSC PTZ Camera Dualband exposes `ptz_control` values `0..7` and the boolean `ptz_stop`, which this integration maps to the eight directions and stop command.
