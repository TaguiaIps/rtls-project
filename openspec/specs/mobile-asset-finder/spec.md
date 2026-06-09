# mobile-asset-finder Specification

## Purpose
Enable mobile operators to search for tracked assets by name or identifier, view recent searches, and access location context in a mobile-optimized interface.

## Requirements
### Requirement: Authorized users can search for assets in the mobile app
The RTLS Analytics Platform SHALL provide a mobile Asset Finder workflow that lets an authorized operator search for tracked assets by name, tag identifier, or supported search text.

#### Scenario: Authorized user searches for a tracked asset
- **WHEN** an authorized mobile user enters supported search text in the Asset Finder
- **THEN** the mobile app SHALL request matching live-location results and show a result list with asset identity and last-known location context

#### Scenario: Search finds no matching assets
- **WHEN** an authorized mobile search request completes without any matching tracked assets
- **THEN** the mobile app SHALL show an explicit no-results state instead of leaving the result area blank

### Requirement: Mobile Asset Finder preserves recent searches
The RTLS Analytics Platform SHALL preserve a recent-search list on the mobile device for later quick access.

#### Scenario: User opens a searched asset result
- **WHEN** the user opens one of the returned mobile asset results
- **THEN** the app SHALL add that asset to the recent-search list and keep the list ordered by most recent access

#### Scenario: Asset already exists in recent searches
- **WHEN** the user opens an asset that is already present in the recent-search list
- **THEN** the app SHALL move that asset to the top of the list instead of creating a duplicate recent-search entry

### Requirement: Mobile Asset Finder shows a selected-asset location sheet
The RTLS Analytics Platform SHALL present the selected asset's last-known location context in a mobile-friendly detail sheet.

#### Scenario: User opens a selected asset
- **WHEN** the user selects an asset from search results or recent searches
- **THEN** the app SHALL show a location sheet with the asset name, location context, last-seen time, and confidence or precision context available from the live-location contract

### Requirement: Mobile Asset Finder can hand off into the delivered web Live Map
The RTLS Analytics Platform SHALL let the mobile user open the delivered web Live Map with compatible asset and floor context from the selected mobile asset.

#### Scenario: User chooses open-in-map from the mobile location sheet
- **WHEN** the user invokes the open-in-map action for a selected asset that has current site or floor context
- **THEN** the mobile app SHALL launch the delivered Live Map route with the compatible site, floor, and asset query parameters preserved
