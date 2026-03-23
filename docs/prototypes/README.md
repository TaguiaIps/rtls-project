# Prototypes Inventory

This folder contains high-fidelity prototype outputs generated with Google Stitch.

Each prototype folder now includes:

* `code.html` for the exported HTML prototype

Shared design-system assets for the HTML exports live in:

* [`_shared/prototype-tailwind-config.js`](./_shared/prototype-tailwind-config.js)
* [`_shared/prototype-base.css`](./_shared/prototype-base.css)

The design direction is based on the `Industrial Command Deck` theme defined in [../ux-design.md](../ux-design.md).

## Core Screen Mapping

These folders align directly with the priority frame IDs in the UX spec.

| Prototype Folder | UX Spec Frame ID | Purpose |
| :--- | :--- | :--- |
| `operations_overview` | `WEB-02` | Operations overview / KPI triage screen |
| `live_operations_map` | `WEB-03` | Default live operations map |
| `live_asset_map_selected_asset` | `WEB-04` | Live map with selected asset drawer |
| `alerts_center` | `WEB-08` | Alerts center list / triage |
| `analytics_heatmap_analysis` | `WEB-10` | Heatmap analytics screen |
| `floor_plan_scale_setup` | `WEB-16` | Floor plan upload and scaling |
| `calibration_wizard_walk_path_step` | `WEB-21` | Calibration wizard active step |
| `asset_finder_mobile` | `MOB-02` | Mobile asset finder home |
| `qr_scanner_detected_state` | `MOB-06` | Mobile QR scanner detected state |

## Additional Generated Screens

These outputs are useful, but they do not map one-to-one to the main priority list above.

| Prototype Folder | Likely Role |
| :--- | :--- |
| `sentinel_application_shell` | Base shell / app chrome exploration |
| `operations_dashboard` | Alternate overview/dashboard treatment |
| `live_asset_map` | Alternate live map variant |
| `infrastructure_health` | Likely maps to `WEB-22` infrastructure health |
| `zone_flow_configuration` | Likely maps to zone / flow configuration or `WEB-15` zone editor |
| `aegis_command` | Design-system reference only (`DESIGN.md`) |

## Recommended Review Order

Review the prototypes in this order:

1. `sentinel_application_shell`
2. `operations_overview`
3. `live_operations_map`
4. `live_asset_map_selected_asset`
5. `alerts_center`
6. `analytics_heatmap_analysis`
7. `floor_plan_scale_setup`
8. `calibration_wizard_walk_path_step`
9. `asset_finder_mobile`
10. `qr_scanner_detected_state`
11. `infrastructure_health`
12. `zone_flow_configuration`

## Notes

* Shared palette, typography, and radius behavior now come from the `_shared` files above. Update those first before touching per-screen HTML.
* Some screens appear to overlap in purpose. Keep the strongest variant and archive the weaker duplicate to avoid design drift.
* The exported HTML files use Tailwind CDN patterns, which is fine for prototype review but should not be treated as production frontend architecture.

## Related Docs

* Audit: [AUDIT.md](./AUDIT.md)
* Normalization plan: [NORMALIZATION_PLAN.md](./NORMALIZATION_PLAN.md)
