"""Media preprocessing package.

Purpose:
- Define provider-neutral hooks for privacy transforms before social sharing.

Input/Output:
- Input: image path references + optional transform prompt.
- Output: transformed image references (future implementation).

Invariants:
- No image data is sent externally unless user enabled this explicitly.

Debugging:
- Inspect configuration flags and preprocessing prompt in options.
"""
