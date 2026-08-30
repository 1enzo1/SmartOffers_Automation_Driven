# Legacy Diagnostics Inventory — Phase 08

This inventory is based on references in `templates/index.html`, `app.py`,
`core/legacy_execution`, and the test suite. No legacy surface was removed
without proof that it was unused.

| Surface | Classification | Evidence / disposition |
| --- | --- | --- |
| Scenario generator and saved-scenario flow | LEGACY_BUT_USED | Backed by `/api/questions`, `/api/templates`, scenario generation, dry-run, export, and compatibility tests. Retain in Diagnostics. |
| Legacy execution controls (`/executar`) | DEPRECATED_BUT_REQUIRED | Route and SSE semantics are covered by legacy result/safety tests. Keep guarded and outside the QA-first workspace. |
| Manual real-mode selectors and confirmation | LEGACY_BUT_USED | Explicit guard and runtime-contract tests cover deny/allow behavior. Do not remove until a replacement operator workflow exists. |
| Adapter-run and Standard mock controls | LEGACY_BUT_USED | Mock API/facade/runner/UI tests exercise these controls. Keep secondary and local-only. |
| Historical controlled evidence card | ACTIVE | Current evidence loading and historical isolation are covered; it is distinct from current-run evidence. |
| Product catalog/status logic | ACTIVE | Used by the QA-first workspace and product API tests. |
| Diagnostics navigation/details wrappers | ACTIVE | Native `<details>` controls and accessibility tests cover keyboard operation and separation. |
| Legacy PT-BR labels in diagnostics | LEGACY_BUT_USED | User-facing copy remains in compatibility surfaces; broad translation is deferred because those controls are not the primary product flow. |
| Obsolete/dead handlers or CSS selectors | NOT_PROVEN_DEAD | Static names alone are insufficient; handlers are referenced by inline controls or compatibility tests. No deletion made. |

## Duplicate / leakage assessment

- No duplicate primary QA Execute control was found; mock controls remain in
  the diagnostics workspaces.
- The product page keeps only the current-run result/evidence path; historical
  evidence is loaded in its dedicated history surface.
- Legacy controls are hidden/de-emphasized while the product workspace is
  active by the existing `product-active` selectors.
- No unused backend route was removed; preserving legacy JSON and route
  compatibility is an explicit project requirement.

## Follow-up candidates

1. Deprecate `/executar` and old generator routes only after an owner-approved
   replacement and migration plan.
2. Run a browser-level code-coverage/dead-handler review when the browser
   service is available; static reference analysis cannot prove event-handler
   reachability for inline JavaScript.
3. Normalize remaining diagnostics copy as a separate, low-risk localization
   pass rather than mixing it with compatibility cleanup.
