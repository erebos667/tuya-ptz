# Tuya PTZ for Home Assistant

Adds PTZ controls for Tuya cameras that expose the `ptz_control` and `ptz_stop` data points.

## Installation with HACS

Add this repository as a custom repository in HACS, category **Integration**:

`https://github.com/erebos667/tuya-ptz`

Then install **Tuya PTZ** and restart Home Assistant.

## Supported devices

The integration looks for Tuya devices exposing the following functions:

- `ptz_control`: `0..7` for the eight directions
- `ptz_stop`: boolean
- `ptz_calibration`: boolean when available

It uses the existing Tuya integration connection; no second Tuya login is required.
