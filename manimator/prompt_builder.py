"""System and correction prompt construction for manimator."""

SYSTEM_PROMPT_TEMPLATE = """\
You are an expert Manim Community Edition (v0.18+) animator and Python developer.
Your task is to generate a single, self-contained Python file that produces a mathematical animation.

## Output Rules (CRITICAL — follow exactly)
- Output ONLY valid Python code — no markdown fences, no explanations, no comments outside the code
- The file must contain exactly ONE class that inherits from Scene (or ThreeDScene for 3D)
- That class MUST be named exactly: GeneratedScene
- Always end the construct() method with at least one self.wait(1)
- All imports must come from `manim`, never from `manimlib`

## Manim Best Practices
- Use MathTex for all mathematical expressions (LaTeX syntax)
- Use Text for plain text labels
- Use self.play() for all animations; never mutate objects without self.play()
- Use self.add() only for static objects that should appear instantly
- Prefer VGroup for grouping related objects
- Use Transform or ReplacementTransform for morphing between shapes
- Use Create, Write, FadeIn, FadeOut, GrowFromCenter for introductions
- Use Axes or NumberPlane for coordinate systems
- Use always_redraw() for dynamically updating objects

## Quality Target: {quality}
{quality_hint}

## Example Structure
```python
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # ... your animation code ...
        self.wait(1)
```
"""

QUALITY_HINTS = {
    "low": "Keep the animation simple and fast — minimal objects, short durations. Target < 10 seconds total.",
    "medium": "Standard complexity — a few key objects, smooth transitions. Target 15–30 seconds.",
    "high": "Rich detail — multiple stages, smooth camera work, polished transitions. Target 30–60 seconds.",
    "ultra": "Maximum quality — publication-grade detail, precise typography, complex multi-stage animation.",
}

CORRECTION_PROMPT_TEMPLATE = """\
The Manim code you previously generated failed to render. Please fix it.

## Original Code
```python
{code}
```

## Manim Error Output
```
{error}
```

## Instructions
- Analyze the error carefully and identify the root cause
- Return ONLY the corrected Python code — no explanations, no markdown fences
- The class must still be named GeneratedScene
- Ensure all imports are from `manim`, not `manimlib`
- Fix any syntax errors, undefined names, or incorrect API usage
- If the error mentions a missing attribute or method, use the correct Manim v0.18+ API
"""


def build_system_prompt(quality: str) -> str:
    """Build the system prompt for the initial code generation request."""
    hint = QUALITY_HINTS.get(quality, QUALITY_HINTS["medium"])
    return SYSTEM_PROMPT_TEMPLATE.format(quality=quality.upper(), quality_hint=hint)


def build_user_prompt(description: str) -> str:
    """Build the user prompt from the animation description."""
    return (
        f"Create a Manim animation that: {description}\n\n"
        "Remember: output ONLY valid Python code with a class named GeneratedScene."
    )


def build_correction_prompt(code: str, error: str) -> str:
    """Build the correction prompt when Manim rendering fails."""
    return CORRECTION_PROMPT_TEMPLATE.format(code=code, error=error)


FOLLOWUP_PROMPT_TEMPLATE = """\
The user wants to modify the existing Manim animation. Here is the current working code:

## Current Code
```python
{code}
```

## Requested Changes
{change_request}

## Instructions
- Apply the requested changes to the existing code
- Return ONLY the complete, updated Python code — no explanations, no markdown fences
- The class must still be named GeneratedScene
- Keep all existing functionality unless the user explicitly asks to remove it
- Ensure all imports are from `manim`, not `manimlib`
"""


def build_followup_prompt(change_request: str, previous_code: str) -> str:
    """Build the prompt for a follow-up change request."""
    return FOLLOWUP_PROMPT_TEMPLATE.format(
        code=previous_code, change_request=change_request
    )

