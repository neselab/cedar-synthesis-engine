"""
NL Translation Layer for the Cedar Synthesis Engine.

Provides LLM-powered translation between Cedar policies and natural language,
enabling security administrators to review and modify reference policies
without reading Cedar syntax.
"""
import os
from autocedar.llm import create_runtime_backend, default_model_for_provider
from autocedar.providers import ChatMessage, ModelBackend


def _get_client() -> ModelBackend:
    """Return the configured provider-neutral translation backend."""

    return create_runtime_backend()


def _model() -> str:
    return os.environ.get("CEDAR_TRANSLATE_MODEL") or default_model_for_provider()


def policy_to_nl(
    policy_text: str,
    schema_text: str,
    *,
    backend: ModelBackend | None = None,
    model: str | None = None,
) -> str:
    """Translate a Cedar policy into plain-language summary."""
    response = (backend or _get_client()).generate_text(
        model=model or _model(),
        max_tokens=1024,
        messages=(ChatMessage(
            role="user",
            content=f"""Translate this Cedar access control policy into clear, non-technical natural language that a security administrator could understand and approve.

Cedar Schema:
```
{schema_text}
```

Policy:
```
{policy_text}
```

Rules:
- Explain what the policy ALLOWS and what it DENIES
- Use plain business language (e.g., "Clinical Researchers" not "principal in Role::ClinicalResearcher")
- Mention specific numeric thresholds and exact conditions
- Call out any exceptions (e.g., "unless" clauses)
- Format as a bulleted list of rules
- Be precise but concise — aim for 3-6 bullet points""",
        ),),
    )
    return response.text


def counterexample_to_nl(
    counterexample: str,
    check_name: str,
    check_description: str,
    *,
    backend: ModelBackend | None = None,
    model: str | None = None,
) -> str:
    """Translate a solver counterexample into plain-language explanation."""
    response = (backend or _get_client()).generate_text(
        model=model or _model(),
        max_tokens=512,
        messages=(ChatMessage(
            role="user",
            content=f"""A formal verification check on a Cedar access control policy FAILED. Translate this counterexample into plain language explaining what went wrong.

Check name: {check_name}
Check description: {check_description}

Raw counterexample from SMT solver:
```
{counterexample}
```

Rules:
- Explain in plain business language what scenario the solver found
- State what was allowed/denied that shouldn't have been
- Mention the specific attribute values that caused the violation
- Keep to 2-3 sentences
- Start with "VIOLATION:" """,
        ),),
    )
    return response.text


def feedback_to_policy(
    feedback: str,
    current_policy: str,
    schema_text: str,
    *,
    backend: ModelBackend | None = None,
    model: str | None = None,
) -> str:
    """Update a Cedar policy based on administrator NL feedback."""
    response = (backend or _get_client()).generate_text(
        model=model or _model(),
        max_tokens=2048,
        messages=(ChatMessage(
            role="user",
            content=f"""An administrator wants to modify this Cedar access control policy based on their feedback.

Cedar Schema:
```
{schema_text}
```

Current policy:
```
{current_policy}
```

Administrator's feedback:
{feedback}

Output ONLY the updated Cedar policy code. No explanations, no markdown fencing.
Maintain the same comment style. Ensure the output is valid Cedar syntax.""",
        ),),
    )
    return response.text
