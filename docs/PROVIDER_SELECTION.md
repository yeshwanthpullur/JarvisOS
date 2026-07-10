# Provider Selection

The Provider Selector ranks enabled providers without calling provider APIs.

Selection inputs include:
- request intent
- required capabilities
- provider health
- provider priority
- locality preferences
- fallback metadata
- historical reliability

The selector returns the best execution-time provider record or `None` when no provider matches.
