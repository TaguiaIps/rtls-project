# OpenSpec Project Glossary

This glossary defines the preferred project language for OpenSpec artifacts in this repository.

Use these terms consistently in proposals, designs, specs, and tasks.

## Product

### RTLS Analytics Platform

The product being planned in this repository. It is a real-time indoor location and analytics platform focused primarily on restaurants and large catering operations.

### Indoor Positioning System (IPS)

The broader technical capability used by the product to estimate and track asset locations indoors.

## Personas and Roles

### Administrator

The privileged role responsible for setup, calibration, infrastructure health, gateway provisioning, user access, and auditability.

Preferred persona reference: **Alex**

### General User

The operational role responsible for monitoring live activity, triaging alerts, and using analytics to improve service performance.

Preferred persona reference: **Carlos Mendes**

### Operations Manager

The default real-world label for the General User persona in restaurant and catering contexts.

## Domain Entities

### Asset

Any tracked entity in the system, including staff tags, service carts, equipment, or other tagged objects.

### Asset Tag

A BLE or UWB tag attached to a tracked person or object.

### Waiter Tag

Preferred example term for a staff-worn asset tag in restaurant scenarios.

### Tray Cart

Preferred example term for a mobile equipment asset in restaurant and catering scenarios.

### Gateway

A fixed device that scans for BLE or UWB signals and forwards data into the system, typically via MQTT.

### Tier Profile

The hardware/precision profile assigned to infrastructure or deployment paths.

Examples:
- Economic Tier
- Premium Tier

### Site

A logical location such as a restaurant, venue, or operation.

### Floor

A specific level or mapped area within a site.

### Zone

A named operational area used to interpret location data.

Preferred examples:
- Kitchen
- Dining Hall
- Kitchen Pass
- Service Corridor
- Cold Storage

### POI

Point of Interest. A named location or operational target used in analytics and workflows.

### Table SLA

A service-level agreement tied to restaurant service performance, such as response time, staff presence, or service completion thresholds.

### Dwell Time

The amount of time an asset remains within a given zone.

### Round Trip

The time required for an asset or staff member to travel from one defined point or zone to another and back.

### Trajectory

The historical path of a selected asset over time.

### Heatmap

An aggregated spatial visualization used to reveal high-density traffic, congestion, or bottlenecks.

### Confidence Score

A representation of how precise or reliable a location estimate is.

Preferred user-facing expression:
- High precision point
- Medium confidence radius
- Low-confidence zone fallback

### Geofence

A virtual perimeter defined on the map for monitoring entry, exit, authorization, or dwell-based rules.

### Unauthorized Geofence Alert

An alert triggered when an asset enters or exits a restricted zone without authorization.

## Product Areas

### Operations Overview

The default overview screen for operational users. It summarizes KPIs, live issues, alerts, and infrastructure signals.

### Live Map

The primary real-time map workspace for locating assets, inspecting confidence states, and investigating incidents.

### Analytics

The reporting workspace for heatmaps, dwell time, round-trip analysis, trajectories, and SLA trends.

### Alerts Center

The queue and triage workspace for SLA alerts, unauthorized geofence alerts, maintenance issues, and alert history.

### Admin

The workspace for floor setup, gateway placement, calibration, roles, and asset registry operations.

### Health

The infrastructure monitoring area for gateway status, signal quality, sync health, and maintenance concerns.

### Audit Log

The record of configuration and administrative changes used for traceability and governance.

## Technical Terms

### BLE

Bluetooth Low Energy.

### AoA

Angle of Arrival, used for higher-precision location estimation.

### UWB

Ultra-Wideband, used for higher-precision location estimation.

### MQTT

The messaging protocol used by gateways to publish observations into the platform.

### WebSocket

The real-time channel used to push live updates to the web application.

### TimescaleDB

The planned time-series capable PostgreSQL extension used for historical readings and analytics data.

### Redis Streams or Kafka

The planned internal event/stream backbone for ingestion and processing pipelines.

## Language Rules

Prefer these terms:

- `RTLS Analytics Platform`
- `Operations Overview`
- `Live Map`
- `Analytics`
- `Alerts Center`
- `Admin`
- `Health`
- `Audit Log`
- `Waiter Tag`
- `Tray Cart`
- `Gateway`
- `Kitchen Pass`
- `Service Corridor`
- `Cold Storage`

Avoid these terms unless a change is explicitly about legacy cleanup or cross-domain reuse:

- `Sentinel`
- `Fleet Command`
- `Rover`
- `MHE`
- `Sector Alpha`
- `command deck` as product name
- military or tactical framing
- industrial-only labels when restaurant language is intended
