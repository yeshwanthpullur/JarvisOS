# Executive Provider Integration

JARVIS never communicates directly with provider SDKs or provider implementations. Future provider use must follow:

`JARVIS -> Decision Engine -> Provider Selection Metadata -> Provider Router -> Provider -> Provider Router -> JARVIS`

The current implementation stores provider routing metadata only and performs no network calls.

