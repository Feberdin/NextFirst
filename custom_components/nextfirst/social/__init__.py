"""Social integration package.

Purpose:
- Hold provider-neutral social posting interfaces and orchestration.

Input/Output:
- Input: called by services when sharing is requested.
- Output: structured posting result or actionable error.

Invariants:
- No implicit external posting without explicit opt-in configuration.

Debugging:
- Service responses expose provider/config errors early and clearly.
"""
