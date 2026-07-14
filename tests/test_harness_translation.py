from __future__ import annotations

from types import SimpleNamespace

from autocedar.harness import eval_harness


class _RecordingBackend:
    provider_id = "local"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_text(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text="- Only owners may read the document.")


def test_reference_review_uses_selected_provider_backend_without_anthropic_key(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    references = tmp_path / "references"
    references.mkdir()
    (references / "ceiling_owner_read.cedar").write_text(
        'permit(principal, action == Action::"read", resource) '
        "when { principal == resource.owner };\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        eval_harness,
        "load_checks",
        lambda _workspace: [
            {
                "name": "owner_only",
                "type": "implies",
                "description": "Only the owner may read.",
                "reference_path": str(references / "ceiling_owner_read.cedar"),
            },
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    backend = _RecordingBackend()

    approved, feedback = eval_harness.review_references(
        str(tmp_path),
        "entity User; entity Document { owner: User };",
        backend=backend,  # type: ignore[arg-type]
        model="served-local-model",
    )

    assert approved is True
    assert feedback == ""
    assert len(backend.calls) == 1
    assert backend.calls[0]["model"] == "served-local-model"
    output = capsys.readouterr().out
    assert "Only owners may read" in output
    assert "set ANTHROPIC_API_KEY" not in output
