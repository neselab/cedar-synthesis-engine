---
pattern: IoT device authorization (capability-based)
difficulty: medium
features:
  - non-User principal (Device entity)
  - capability set for action scoping
  - device status flag for revocation
  - owner-based management path
domain: IoT / smart home
synthesis_difficulty: 2
---

# IoT Device Authorization — Policy Specification

## Context

A smart home platform where `Device` principals interact with
`Endpoint` resources (e.g. thermostat, lock, camera). Devices have a
set of `capabilities` (strings like `"read_sensor"`, `"actuate"`,
`"stream"`) and an `isActive` boolean. Each Endpoint has an `owner`
(a `User` entity).

This scenario tests non-User principals (devices as first-class
Cedar entities) with capability-based scoping.

## Requirements

### 1. Telemetry — Active Devices with read_sensor
A Device may `telemetry` an Endpoint when:
- The device is active (`principal.isActive == true`), AND
- The device's capabilities contain `"read_sensor"`.

### 2. Control — Active Devices with actuate
A Device may `control` an Endpoint when:
- The device is active, AND
- The device's capabilities contain `"actuate"`.

### 3. Stream — Active Devices with stream
A Device may `stream` an Endpoint when:
- The device is active, AND
- The device's capabilities contain `"stream"`.

### 4. Manage — Owner Only
A User may `manage` an Endpoint when:
- `principal == resource.owner`.

Only the endpoint's owner can manage it (configure, provision, etc.).

### 5. Default Deny
All other requests are denied. Inactive devices cannot perform any
action. Devices without the required capability are denied.
