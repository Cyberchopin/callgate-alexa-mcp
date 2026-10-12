# UI verification record

## Implemented and checked

- Keyboard-visible focus rings using `:focus-visible`.
- Minimum 44-pixel button/input height.
- Semantic headings, buttons, labels, details/summary, and status regions.
- `aria-live="polite"` status updates and `role="alert"` error output.
- Responsive single-column layout at widths up to 680 pixels.
- Loading, success, denial, and error copy in the local JavaScript.
- Calm assistant copy states why the action paused, what was protected, and the next step.
- Contact data is rendered from server-held pending state; query-string forgery is tested and ignored.
- Collapsible proof panel omits transcript text and contact credential.
- `no-store`, `no-referrer`, content-type, and same-origin content-security headers on HTML responses.
- High-contrast foreground/background pairs chosen in source. Automated WCAG contrast measurement was not available in this environment.

## Screenshot status

Requested wide and narrow screenshots were not produced. The available browser could not connect to the loopback preview (`net::ERR_CONNECTION_TIMED_OUT`). This is a tooling limitation, not a visual verification result. Capture three screenshots outside this environment before submission:

1. wide simulated assistant page at `/demo`;
2. narrow simulated assistant page at `/demo`;
3. narrow contact review page for a live pending request.

