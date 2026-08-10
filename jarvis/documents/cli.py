"""Document Intelligence CLI renderer."""

from .agent import DocumentAgent, SAFE_TEXT_TYPES, PLANNED_TYPES, document_safety


def render_document_command(agent: DocumentAgent, command: str, arguments: tuple[str, ...]) -> str:
    text = " ".join(arguments).strip()
    if command == "document status": return "Document status: " + " ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in agent.status().items())
    if command == "document help": return "Document commands: status, help, plan, safety, types, inspect, extract, summarize, ask, show, history. Reads only explicit bounded local text files."
    if command == "document types": return "Document types: readable=" + ",".join(SAFE_TEXT_TYPES) + " planned_unavailable=" + ",".join(PLANNED_TYPES) + " OCR=disabled cloud=disabled."
    if command == "document plan":
        result=agent.plan(text); return f"Document plan: status={result.status.value} intent={result.plan.intent.value if result.plan else 'unknown'} steps=" + " | ".join(result.plan.proposed_steps if result.plan else ())
    if command == "document safety":
        risk,allowed,reason=document_safety(text); return f"Document safety: risk={risk.value} allowed={'yes' if allowed else 'no'} reason={reason}"
    if command == "document inspect":
        result=agent.inspect(text); ref=result.references[0] if result.references else None; return f"Document inspect: status={result.status.value} name={ref.display_name if ref else 'unavailable'} type={ref.file_type if ref else 'unknown'} content_available={'yes' if ref and ref.content_available else 'no'} error={result.error or 'none'}."
    if command == "document extract":
        result=agent.extract(text); return f"Document extract: status={result.status.value} parser={result.extraction.parser_used if result.extraction else 'none'} preview={result.extraction.extracted_text_preview if result.extraction else 'unavailable'} error={result.error or 'none'}."
    if command == "document summarize":
        if not arguments: return "Usage: document summarize <path_or_ref> [instruction]"
        result=agent.summarize(arguments[0], " ".join(arguments[1:])); return f"Document summary: status={result.status.value} summary={result.summary.summary if result.summary else 'unavailable'} error={result.error or 'none'}."
    if command == "document ask":
        if len(arguments)<2: return "Usage: document ask <path_or_ref> <question>"
        result=agent.ask(arguments[0], " ".join(arguments[1:])); return f"Document answer: status={result.status.value} answer={result.answer.answer if result.answer else 'unavailable'} error={result.error or 'none'}."
    if command == "document show":
        result=agent.show(text); return "Document job unavailable." if result is None else f"Document job: id={result.request_id} status={result.status.value} error={result.error or 'none'}."
    if command == "document history": return "Document history: " + (", ".join(f"{x.request_id}:{x.status.value}" for x in agent.history[-10:]) or "empty")
    return "Document command unavailable."
