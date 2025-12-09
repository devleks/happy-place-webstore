# PerfSmith Hotspots
Generated: 2025-11-26 07:09:06 UTC

## Python Functions ≥ 60 lines
| File | Function | Lines |
| --- | --- | --- |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/scripts/seed_products_with_variants.py` | `seed_products_with_variants` | 412 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/seed.py` | `seed_database` | 217 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/scripts/seed_extended_data.py` | `seed_categories_with_closure` | 169 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/services/order_service.py` | `create_order` | 168 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/routes/returns_api.py` | `create_return_request` | 146 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/routes/auth.py` | `customer_register` | 109 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/routes/orders.py` | `create_order` | 108 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/routes/promotions.py` | `validate_promotion` | 105 |

## Largest Frontend Modules (by lines)
| File | Lines |
| --- | --- |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/Checkout.js` | 616 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/ProductDetail.js` | 424 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/OrderHistory.js` | 302 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/ReturnPolicy.js` | 292 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/OrderConfirmation.js` | 273 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/TermsOfService.js` | 272 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/pages/PrivacyPolicy.js` | 228 |
| `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/frontend/src/services/api.js` | 219 |

## Recommendations
- Break down functions above 60 lines into smaller helpers.
- Consider lazy loading or code splitting for the largest React modules.
- Pair this report with runtime data via `RUN_PERF_BUILD=1 ci_workflows/agent_perfsmith.sh`.

> Bundle stats were skipped. Run with RUN_PERF_BUILD=1 for bundle size JSON.
