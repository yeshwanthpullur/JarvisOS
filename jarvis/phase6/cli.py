"""Bounded CLI rendering for Phase 6 environment and local-model metadata."""

from __future__ import annotations

from .models import MODEL_ROLES
from .runtime import Phase6Runtime


def _yes(value: object) -> str:
    return "yes" if value else "no"


def render_phase6_command(runtime: Phase6Runtime, command: str, args: tuple[str, ...]) -> str:
    if command in {"environment status", "tool status"}:
        summary = runtime.environments.summary()
        return "Tool environments: " + " ".join(f"{key}={value}" for key, value in summary.items()) + " installed_is_authorized=no"
    if command in {"environment audit", "tool audit"}:
        audit = runtime.environments.audit(run_pip_check="--pip-check" in args)
        warnings = "; ".join(audit.warnings) or "none"
        return f"Environment audit: python={audit.python_version} environment={audit.environment} isolated={_yes(audit.isolated)} pip={_yes(audit.pip_available)} pip_check={audit.pip_check_status} packages={audit.installed_packages_checked} tools={audit.detected_tools} incompatible={len(audit.incompatible_tools)} warnings={warnings}"[:4000]
    if command == "tool environments":
        records = runtime.environments.refresh()
        return "Tool environments: " + "; ".join(f"{item.tool_id}:{item.install_status}:{item.health_status.value}:enabled={_yes(item.enabled)}:env={item.environment_name}" for item in records)[:6000]
    if command in {"tool inspect", "tool environment-show"}:
        record = runtime.environments.inspect(args[0] if args else "")
        if record is None:
            return "Tool environment not found."
        return f"Tool {record.tool_id}: category={record.category} role={record.primary_or_backup} install={record.install_status} health={record.health_status.value} enabled={_yes(record.enabled)} adapter={record.adapter_type} environment={record.environment_name} python={record.recommended_python} approval={_yes(record.approval_required)} permissions={','.join(record.permission_profile)} fallback={record.fallback} error={record.last_error or 'none'}"[:3000]
    if command in {"provider inspect", "provider test"}:
        provider_id = args[0] if args else "ollama"
        if command == "provider test" and provider_id == "ollama":
            runtime.models.refresh(probe=True)
        provider = runtime.models.provider(provider_id)
        if provider is None:
            return "Provider not found."
        return f"Provider {provider.provider_id}: runtime={provider.runtime} locality={provider.local_or_cloud} configured={_yes(provider.configured)} detected={_yes(provider.detected)} enabled={_yes(provider.enabled)} policy_allowed={_yes(provider.policy_allowed)} approval={_yes(provider.approval_required)} healthy={_yes(provider.healthy)} current_model={provider.current_model or 'none'} models={len(provider.available_models)} error={provider.last_error or 'none'}"[:3000]
    if command in {"model list", "model health"}:
        if command == "model health":
            runtime.models.refresh(probe=True)
        records = runtime.models.models()
        return "Models: " + ("; ".join(f"{item.model_id}:provider={item.provider_id}:healthy={_yes(item.healthy)}:roles={','.join(item.roles)}" for item in records) or "none detected")[:5000]
    if command == "model inspect":
        item = runtime.models.model(args[0] if args else "")
        if item is None:
            return "Model not found; no download was attempted."
        return f"Model {item.model_id}: provider={item.provider_id} runtime={item.runtime} roles={','.join(item.roles)} available={_yes(item.available)} healthy={_yes(item.healthy)} vision={_yes(item.supports_vision)} embeddings={_yes(item.supports_embeddings)} streaming={_yes(item.supports_streaming)} json={_yes(item.supports_json)}"[:3000]
    if command == "model roles":
        return "Model roles: " + "; ".join(f"{role}={getattr(runtime.models.route(role), 'model_id', 'unavailable')}" for role in MODEL_ROLES)
    if command == "model select":
        if len(args) < 2:
            return "Usage: model select <role> <installed_model>. Selection is metadata-only."
        try:
            selected = runtime.models.select(args[0], args[1])
        except ValueError:
            return "Unknown model role."
        return "Model selection updated for this process." if selected else "Model selection unavailable: model is missing, unhealthy, disallowed, or does not support that role."
    if command == "model test":
        runtime.models.refresh(probe=True)
        item = runtime.models.model(args[0] if args else "")
        if item is None:
            return "Model test unavailable: model is not installed. No model was downloaded."
        return f"Model test metadata: model={item.model_id} provider_reachable={_yes(item.healthy)} inference_executed=no. Use normal chat for an authorized local inference test."
    if command in {"browser health", "browser permissions", "browser test"}:
        status = runtime.web.status()
        if command == "browser permissions":
            return "Browser permissions: public_read=policy_gated browser_open=approval_required screenshot=blocked download=blocked upload=blocked click=approval_required login=blocked form_submit=blocked purchase=blocked remote_modify=blocked."
        return "Browser runtime: " + " ".join(f"{key}={value}" for key, value in status.items()) + " launch_performed=no"
    if command == "browser session-list":
        values = tuple(runtime.web.sessions.values())[-20:]
        return "Browser sessions: " + (", ".join(f"{item.session_id}:{item.status}:{item.tool}" for item in values) or "none")
    if command == "browser session-inspect":
        item = runtime.web.sessions.get(args[0] if args else "")
        return "Browser session not found." if item is None else f"Browser session {item.session_id}: status={item.status} tool={item.tool} actions={item.actions_taken} approvals={item.approval_events} downloads={item.downloads} uploads={item.uploads} screenshots={item.screenshots} errors={item.errors}"
    if command == "browser session-close":
        return "Browser session closed." if runtime.web.close(args[0] if args else "") else "Browser session not found."
    if command in {"crawl status", "crawl health"}:
        status = runtime.web.status()
        return f"Crawler: enabled={_yes(status['crawler_enabled'])} network_allowed={_yes(status['network_allowed'])} primary=crawl4ai backup=firecrawl max_pages={runtime.web.limits.max_pages} max_depth={runtime.web.limits.max_depth} execution_authority=no"
    if command in {"crawl plan", "crawl run"}:
        if not args:
            return f"Usage: {command} <public_https_url>"
        plan = runtime.web.run_crawl(args[0]) if command == "crawl run" else runtime.web.plan_crawl(args[0])
        return f"Crawl {plan.crawl_id}: status={plan.status} domain={plan.safe_domain or 'blocked'} tool={plan.tool} pages={plan.limits.max_pages} depth={plan.limits.max_depth} timeout={plan.limits.max_runtime_seconds}s reason={plan.reason}"[:3000]
    if command == "crawl inspect":
        item = runtime.web.crawls.get(args[0] if args else "")
        return "Crawl not found." if item is None else f"Crawl {item.crawl_id}: status={item.status} domain={item.safe_domain} tool={item.tool} pages={item.limits.max_pages} depth={item.limits.max_depth}"
    if command in {"research health", "research audit", "research clear-session", "research source-list", "research source-inspect"}:
        if command == "research audit":
            return "Research web audit: " + (", ".join(f"{item['action']}:{item['status']}:{item['domain'] or 'none'}" for item in runtime.web.audit[-20:]) or "none")
        if command == "research clear-session":
            runtime.web.audit.clear(); runtime.web.crawls.clear(); return "Research session metadata cleared; no memory or knowledge records were changed."
        return "Research sources: no Phase 6 web sources retrieved; citations are required and fabrication is blocked."
    if command in {"document health", "document audit", "document sources", "document clear-session"}:
        if command == "document audit":
            return "Document audit: " + (", ".join(f"{item['document_id']}:{item['status']}:{item['parser']}:{item['chunks']}" for item in runtime.documents.audit[-20:]) or "none")
        if command == "document clear-session":
            runtime.documents.records.clear(); runtime.documents.audit.clear(); return "Document session metadata cleared; memory and knowledge were not changed."
        if command == "document sources":
            return "Document sources: " + (", ".join(f"{item.document_id}:{item.display_name}:{item.status}" for item in tuple(runtime.documents.records.values())[-20:]) or "none")
        status = runtime.documents.status(); return "Document health: " + " ".join(f"{key}={value}" for key, value in status.items())
    if command == "document parse":
        if not args: return "Usage: document parse <explicit_file_path>"
        item = runtime.documents.parse(args[0]); return f"Document {item.document_id}: status={item.status} file={item.display_name} parser={item.parser_used} sensitivity={item.sensitivity_class} chunks={len(item.chunks)} warnings={','.join(item.warnings) or 'none'}"
    if command in {"document inspect-id", "document chunks", "document summarize-id"}:
        item = runtime.documents.records.get(args[0] if args else "")
        if item is None: return "Document not found."
        if command == "document chunks": return "Document chunks: " + (", ".join(f"{chunk.chunk_id}:{chunk.source_ref}:injection={_yes(chunk.prompt_injection_detected)}" for chunk in item.chunks[:30]) or "none")
        if command == "document summarize-id": return runtime.documents.summarize(item.document_id)
        return f"Document {item.document_id}: file={item.display_name} type={item.source_type} parser={item.parser_used} trust={item.trusted_status} sensitivity={item.sensitivity_class} status={item.status} chunks={len(item.chunks)}"
    if command in {"ocr status", "ocr health"}:
        return f"OCR: enabled={_yes(runtime.documents.ocr_enabled)} providers=paddleocr,easyocr,tesseract status={'unconfigured' if not runtime.documents.ocr_enabled else 'policy_gated'} automatic_execution=no"
    if command == "ocr parse":
        return "OCR parsing unavailable: OCR is disabled and no optional OCR adapter was executed."
    if command == "knowledge ingest-document":
        return "Knowledge ingestion requires an existing document ID plus Knowledge authority and policy approval; no ingestion occurred."
    if command == "knowledge source-inspect":
        return "Knowledge source inspection is available through the authoritative Knowledge Runtime; Phase 6 document adapters do not duplicate it."
    if command in {"memory health", "memory conflicts"}:
        status = runtime.memory.status(); return "Memory adapters: " + " ".join(f"{key}={value}" for key, value in status.items()) + " conflicts=authoritative_memory_owned"
    if command in {"vector status", "vector health", "vector collections", "vector inspect", "graph status", "graph health", "graph inspect", "embedding status", "embedding health", "embedding models"}:
        root = command.split()[0]
        if root == "vector": return "Vector runtime: primary=qdrant backup=chromadb temporary=faiss status=unconfigured fallback=bounded_lexical automatic_indexing=no"
        if root == "graph": return "Graph runtime: provider=graphiti status=unconfigured authority=memory_intelligence temporal_updates=disabled"
        return "Embedding runtime: provider=local model=unconfigured status=degraded downloads_automatic=no incompatible_dimensions=rejected"
    return "Phase 6 command unavailable. No external action was performed."
