# site-and-floor-management Specification

## Purpose
Define the Administrator-managed site and floor hierarchy that provides the canonical spatial structure for floor plans, gateway placement, live map context, and analytics scope.

## Requirements
### Requirement: Administrator-managed site hierarchy
The RTLS Analytics Platform SHALL allow authenticated Administrators to create and manage sites and their floors using "Command" style interaction standards and technical input masks for identifiers.

#### Scenario: Administrator creates a site
- **WHEN** an authenticated Administrator submits valid site details through a "Command" style form
- **THEN** the system SHALL persist a site record and confirm with semantic form feedback

#### Scenario: General User attempts to manage sites
- **WHEN** a General User requests a site-management action
- **THEN** the system SHALL deny the request with an authorization error

### Requirement: Floor registration per site
The RTLS Analytics Platform SHALL allow authenticated Administrators to create floors under a site with floor metadata required for map and analytics context.

#### Scenario: Administrator creates a floor
- **WHEN** an authenticated Administrator submits valid floor details for an existing site
- **THEN** the system SHALL persist the floor and associate it with the selected site

#### Scenario: Site floors are requested
- **WHEN** an authorized user retrieves a site's floors
- **THEN** the system SHALL return the floor records with the metadata needed to identify and select them in later workflows
