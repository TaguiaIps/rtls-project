## 1. Mobile contracts and dependencies

- [x] 1.1 Add the shared mobile contract and local-storage dependencies needed for the Asset Finder workflow.
- [x] 1.2 Define the mobile helper modules for recent-search persistence, last-seen formatting, and web Live Map handoff URL generation.

## 2. Asset Finder workflow

- [x] 2.1 Implement the search-first mobile Asset Finder screen with session input, live search, and explicit loading or empty states.
- [x] 2.2 Implement recent searches and the selected-asset location sheet with confidence or precision context.
- [x] 2.3 Implement the open-in-map handoff into the delivered web Live Map route using asset, site, and floor query parameters.

## 3. Verification and docs

- [x] 3.1 Add mobile tests for recent-search behavior, handoff URL generation, and helper logic.
- [x] 3.2 Update system and UX documentation to describe the delivered mobile Asset Finder baseline and the deferred mobile-auth or commissioning work.
- [x] 3.3 Validate the change with `openspec validate implement-mobile-asset-finder --strict`, `npm run test --workspace @rtls/mobile`, and `npm run build --workspace @rtls/mobile`.
