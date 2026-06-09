## MODIFIED Requirements

### Requirement: The Live Map supports search and filtering
The RTLS Analytics Platform SHALL allow users to narrow the visible live-map context using a faceted search system that supports simultaneous combination of category, confidence, and status filters.

#### Scenario: User applies multiple filter facets
- **WHEN** an authorized user selects a specific asset category AND a specific confidence threshold in the search sidebar
- **THEN** the Live Map SHALL reduce the visible result set to only those assets satisfying BOTH facets simultaneously
