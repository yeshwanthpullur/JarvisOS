"""Bounded CLI rendering for Phase 6 environment and local-model metadata."""

from __future__ import annotations

from .models import MODEL_ROLES
from .runtime import Phase6Runtime
from .automation import LocalAction


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
        return "Tool environments: " + "; ".join(f"{item.tool_id}:{item.install_status}:{item.health_status.value}:configured={_yes(item.configured)}:integrated={_yes(item.integrated)}:enabled={_yes(item.enabled)}:authorized={_yes(item.execution_authorized)}:env={item.environment_name}" for item in records)[:6000]
    if command in {"tool inspect", "tool environment-show"}:
        record = runtime.environments.inspect(args[0] if args else "")
        if record is None:
            return "Tool environment not found."
        return f"Tool {record.tool_id}: category={record.category} role={record.primary_or_backup} installed={_yes(record.install_status == 'installed')} detected={_yes(record.detected)} configured={_yes(record.configured)} integrated={_yes(record.integrated)} enabled={_yes(record.enabled)} authorized={_yes(record.execution_authorized)} health={record.health_status.value} source={record.discovery_source or 'none'} adapter={record.adapter_type} environment={record.environment_name} python={record.recommended_python} approval={_yes(record.approval_required)} permissions={','.join(record.permission_profile)} fallback={record.fallback} error={record.last_error or 'none'}"[:3000]
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
    if command in {"voice stt", "voice tts"}:
        route = runtime.voice.stt() if command == "voice stt" else runtime.voice.tts()
        return f"Voice {route.capability}: primary={route.primary} backup={route.backup} selected={route.selected or 'none'} status={route.status} local_only=yes hidden_capture=no retention=no reason={route.reason}"
    if command in {"voice test-input", "voice test-output"}:
        return "Voice adapter test is metadata-only here. Use explicit voice listen or voice say for a user-controlled real test; no microphone or playback was started."
    if command in {"voice sessions", "voice session-inspect"}:
        return "Voice sessions are owned by Voice Intelligence; Phase 6 adapter diagnostics retain no transcript or raw-audio session data."
    if command in {"vision health", "vision inspect-media"}:
        if command == "vision health":
            return "Vision health: " + " ".join(f"{key}={value}" for key, value in runtime.vision.status().items())
        if not args: return "Usage: vision inspect <explicit_image>"
        item = runtime.vision.inspect(args[0]); return f"Visual evidence: file={item.display_name} type={item.media_type} size={item.size_bytes} status={item.status} route={item.provider_route} retained={_yes(item.retained)} trusted={_yes(item.trusted)} warning={item.warning or 'none'}"
    if command == "ocr extract": return "OCR extraction unavailable: optional OCR adapters are disabled; no text was fabricated."
    if command in {"camera status", "camera devices"}:
        return "Camera: enabled=no devices=not_enumerated hidden_capture=no retained_frames=no sessions=0"
    if command == "camera start": return runtime.vision.camera_start()
    if command == "camera stop": return "Camera is not active."
    if command == "camera session-inspect": return "Camera session not found; no camera was activated."
    if command in {"coding health", "coding tools"}:
        status = runtime.coding.status(); return "External coding tools: " + " ".join(f"{key}={value}" for key, value in status.items())
    if command == "coding tool-inspect":
        item = runtime.environments.inspect(args[0] if args else "")
        if item is None or item.category != "coding": return "Coding tool not found."
        return f"Coding tool {item.tool_id}: install={item.install_status} health={item.health_status.value} enabled={_yes(item.enabled)} write=no shell=no network=no approval=yes environment={item.environment_name}"
    if command == "coding external-plan":
        if not args: return "Usage: coding plan <request>"
        item = runtime.coding.plan(" ".join(args)); return f"Coding task {item.task_id}: tool={item.selected_tool} mode={item.mode} status={item.status} approval=yes files={len(item.likely_files)} tests={','.join(item.required_tests)}"
    if command in {"coding apply", "coding test-task", "coding cancel", "coding audit"}:
        if command == "coding audit": return "Coding audit: " + (", ".join(f"{item['task_id']}:{item['operation']}:{item['status']}" for item in runtime.coding.audit[-20:]) or "none")
        task_id = args[0] if args else ""
        if command == "coding apply": return f"Coding apply: {runtime.coding.apply(task_id)}. No file was modified."
        if command == "coding cancel":
            task = runtime.coding.tasks.get(task_id)
            if task is None: return "Coding task not found."
            task.status = "cancelled"; return "Coding task cancelled; no file was modified."
        return "Coding test execution requires a bounded command plan and exact approval; no command was run."
    if command.startswith("git "):
        operation = command.split()[1]; return f"Git {operation}: {runtime.coding.repo_metadata(operation)}"[:4000]
    if command in {"github branch", "github commits"}:
        operation = "status" if command.endswith("branch") else "history"
        return f"GitHub {command.split()[1]} (local metadata only): {runtime.coding.repo_metadata(operation)}"[:4000]
    if command in {"system status", "system health", "system processes", "system disks", "system memory", "system gpu"}:
        status = runtime.automation.system_status()
        if command == "system processes": return "System processes: count unavailable; process names and command lines are not exposed."
        return "System status: " + " ".join(f"{key}={value}" for key, value in status.items())
    if command in {"automation status", "automation permissions"}:
        status = runtime.automation.status(); return "Automation: " + " ".join(f"{key}={value}" for key, value in status.items())
    if command in {"scheduler list", "scheduler inspect"}:
        return "Scheduler metadata is owned by the existing manual runner. Use scheduler jobs or scheduler show <id>; scheduled actions never gain new permissions."
    if command in {"app status", "app list"}:
        return "Applications: enabled=no known=" + (",".join(runtime.automation.app_list()) or "none") + " approval_required=yes"
    if command in {"app open", "app close"}:
        preview = runtime.automation.preview(LocalAction.OPEN_APPLICATION if command.endswith("open") else LocalAction.CLOSE_APPLICATION, args[0] if args else "")
        return f"Action preview: action={preview.action.value} target={preview.target} effect={preview.expected_effect} risk={preview.risk} approval={_yes(preview.approval_required)} rollback={_yes(preview.rollback_available)} allowed={_yes(preview.allowed)} reason={preview.reason}"
    if command in {"file status", "file read", "file write", "file move", "file copy", "file delete"}:
        if command == "file status": return "File automation: read=explicit_allowed_root_only write=approval_and_broker delete=blocked secrets=blocked traversal=blocked. Use file-exec commands for governed execution."
        mapping = {"file read": LocalAction.READ_FILE, "file write": LocalAction.WRITE_FILE, "file move": LocalAction.MOVE_FILE, "file copy": LocalAction.COPY_FILE, "file delete": LocalAction.DELETE_FILE}
        preview = runtime.automation.preview(mapping[command], args[0] if args else "")
        return f"Action preview: action={preview.action.value} target={preview.target} effect={preview.expected_effect} risk={preview.risk} approval={_yes(preview.approval_required)} rollback={_yes(preview.rollback_available)} allowed={_yes(preview.allowed)} reason={preview.reason}"
    if command.startswith("connector "):
        operation = command.split()[1]
        if operation in {"status", "health"}: return "Connectors: " + " ".join(f"{key}={value}" for key, value in runtime.connectors.summary().items())
        if operation == "list": return "Connectors: " + "; ".join(f"{item.connector_id}:discovered={_yes(item.discovered)}:configured={_yes(item.configured)}:enabled={_yes(item.enabled)}:healthy={_yes(item.healthy)}" for item in runtime.connectors.list())
        if operation == "capabilities": return "Connector capabilities: " + "; ".join(f"{owner}:{capability}" for owner, capability in runtime.connectors.capabilities())
        item = runtime.connectors.get(args[0] if args else "")
        if item is None: return "Connector not found."
        if operation == "test": return f"Connector test: {runtime.connectors.test(item.connector_id)}; no remote mutation occurred."
        if operation == "permissions": return f"Connector {item.connector_id} permissions: {','.join(item.permissions) or 'none'} approval={_yes(item.approval_required)} policy_allowed={_yes(item.policy_allowed)}"
        if operation == "audit": return "Connector audit: metadata-only; credentials and payloads are excluded."
        return f"Connector {item.connector_id}: category={item.category} adapter={item.adapter_type} installed={_yes(item.installed)} discovered={_yes(item.discovered)} configured={_yes(item.configured)} credentials_present={_yes(item.credentials_present)} enabled={_yes(item.enabled)} policy_allowed={_yes(item.policy_allowed)} approval={_yes(item.approval_required)} authenticated={_yes(item.authenticated)} healthy={_yes(item.healthy)} connected={_yes(item.connected)} trust={item.trust_level} credential_reference={item.credential_reference or 'none'}"
    if command.startswith("performance "):
        runtime.observability.snapshot(); domain = command.split()[1]
        mapped = {"providers":"provider","models":"model","memory":"memory","voice":"voice"}.get(domain, "application")
        summary = runtime.observability.domain_summary(mapped)
        return f"Performance {domain}: points={summary['points']} measured={summary['measured']} estimated={summary['estimated']} latest={','.join(summary['latest']) or 'none'} profiling_enabled={_yes(runtime.observability.profiling_enabled)}"
    if command.startswith("operations "):
        operation = command.split()[1]
        if operation == "alerts": return "Operations alerts: advisory_only; use runtime alerts for bounded active records."
        if operation == "audit": return "Operations audit: payloads=no prompts=no audio=no document_text=no credentials=no telemetry_upload=no."
        return "Operations status: local_only=yes telemetry_upload=no privileged_recovery=no observability_authority=informational_only."
    if command in {"phase6 status", "phase6 candidate"}:
        report = runtime.candidate_report(probe_provider="--probe" in args)
        summary = report.summary()
        return "Phase 6 candidate: " + " ".join(f"{key}={value}" for key, value in summary.items()) + f" degradations={','.join(report.degradations) or 'none'}"[:5000]
    if command == "phase6 checklist":
        report = runtime.candidate_report()
        return "Phase 6 checklist: " + "; ".join(f"{item.component}:{item.state.value}:{item.evidence}" for item in report.checks)[:7000]
    return "Phase 6 command unavailable. No external action was performed."
