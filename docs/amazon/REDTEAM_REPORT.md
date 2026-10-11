# Red-team report — phase-2 prototype

Scope: isolated branch `amazon/redteam`, derived from `amazon/mcp-phase2`. This report adds tests and does not modify core security code. All actions are simulated.

## Findings ordered by severity

### Medium — MCP challenge issuance lacks the existing workflow's per-subject time rate limit

- Attack: repeatedly request URL elicitation from one simulated subject/session.
- Expected: the existing challenge issuance rate boundary applies on the MCP path.
- Actual: one thousand pending requests are accepted; the next request is rejected only by the coordinator's global capacity cap.
- Evidence: `test_challenge_issuance_has_capacity_cap_but_no_per_subject_rate_limit`.
- Proposal: add an adapter-level call to the existing trusted challenge limiter; do not implement a second policy engine.

### Medium — contact approval trusts a bearer header but does not validate Origin or use a CSRF token

- Attack: send no-token, cross-site form, and cross-origin JSON requests.
- Expected: unauthenticated requests fail; a request asserting an unrelated Origin is rejected even if a browser or extension can attach the bearer token.
- Actual: no-token and ordinary cross-site form requests return 403 because they cannot set the custom header. A request with the valid bearer header is accepted regardless of Origin.
- Evidence: `test_csrf_requests_without_contact_token_are_rejected_but_origin_is_not_checked`.
- Boundary: this is a local simulated credential, not production authentication.

### Medium — credential-origin self-approval check is configuration, not proof of separate human control

- Attack: one operator runs both devices and knows the CLI-provided contact token while configuring different origin labels.
- Expected: production enrollment proves independent control.
- Actual: the prototype only rejects identical configured origin strings. A single operator can control both ends when they possess the contact token.
- Evidence: source inspection of `phase2.build_app`; existing `test_expired_cross_contact_and_self_approval_are_rejected` covers only equal origin labels.
- Unable to test real independence: the prototype has no human identity provider or device attestation.

### Low — approval response lacks `Referrer-Policy`

- Attack: cause the review page to load or navigate to a third-party resource and inspect the Referer header.
- Expected: the opaque request URL is protected by a restrictive referrer policy.
- Actual: the response has no `Referrer-Policy` header. The current page contains no third-party links or resources, which limits immediate exposure.
- Evidence: `test_elicitation_url_is_opaque_one_time_and_page_lacks_referrer_policy`.

## Passed attack checks

1. **Cross-tool replay:** a `send_money` proof used for `place_order` is rejected with scope mismatch. Evidence: `test_cross_tool_replay_and_parameter_mutation_are_rejected`.
2. **Check/use mutation:** changing amount or destination after proof issuance is rejected; the existing phase-2 parametrized test also covers amount, destination, identity, and session. Cart mutation is not testable end-to-end because phase 2 elicits only `send_money`; direct `place_order` resource hashing includes the cart.
3. **Concurrent double spend:** two threads use one proof against one SQLite ledger; exactly one succeeds. Evidence: `test_concurrent_double_spend_allows_exactly_one_use`.
4. **CSRF basics:** POST without the contact token and a normal cross-site form are rejected. The Origin gap is reported above.
5. **Review data source:** query parameters cannot forge amount, destination, approval state, or displayed request identity; GET does not mutate state. Evidence: `test_approval_page_ignores_query_forgery_and_get_does_not_mutate`.
6. **Capability material in URLs:** the elicitation URL contains a random 128-bit hex identifier and no amount, destination, claimed identity, contact token, or capability proof. The URL becomes unavailable after decision. Evidence: `test_elicitation_url_is_opaque_one_time_and_page_lacks_referrer_policy`.
7. **Elicitation URL behavior:** fixed HTTPS origin, no redirect parameter, opaque identifier, one-time state, and coordinator expiry are present. Enumeration resistance is inferred from random identifier size, not empirically proven.
8. **Self-approval:** equal configured credential origins are rejected by the existing phase-2 test. The stronger single-operator boundary is reported above.
9. **Logs and Sentry:** the gateway emits no Python log containing the tested amount or destination. Evidence: `test_gateway_emits_no_sensitive_python_log_text`. Sentry event redaction is **not testable** on this path because the MCP adapter emits no Sentry event; production telemetry remains unassessed.
10. **Denial-of-service boundary:** a global one-thousand-pending capacity cap works, but the required per-subject issuance rate limit does not reach the MCP adapter; reported above.

## Limits

- This tests the current v1 proof path. Commitment v2 remains reverted and is not credited.
- No real browser CORS policy, reverse proxy, identity provider, contact enrollment, or public network was tested.
- No core fix was made. The two medium proposals require owner approval and design review.
