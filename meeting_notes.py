from llm import ask_llm


def generate_meeting_notes(transcript: str) -> str:
    question = """
Convert this meeting transcript into structured corporate meeting notes.

Include:
- Meeting Summary
- Key Decisions
- Risks
- Action Items
- Open Questions

Keep the output clear and professional.
"""

    result = ask_llm(
        context=transcript,
        question=question,
    )

    return result["answer"]