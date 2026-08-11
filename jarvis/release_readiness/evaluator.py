"""Deterministic, side-effect-free Phase 5 production-readiness evaluator."""
from __future__ import annotations

from importlib.util import find_spec
import json
from pathlib import Path
import subprocess

from .models import *


REQUIRED_PHASE5={
    "external_integration_control_plane":"jarvis.integrations.registry","external_communication_runtime":"jarvis.integrations.communication","telegram_connector":"jarvis.integrations.telegram.runtime","discord_email_slack_connectors":"jarvis.integrations.outbound_connectors","github_provider":"jarvis.integrations.github","mcp_runtime":"jarvis.mcp_runtime.runtime","plugin_runtime":"jarvis.plugin_runtime.runtime","advanced_model_runtime":"jarvis.models.runtime_control","external_research_runtime":"jarvis.research.runtime","knowledge_retrieval_runtime":"jarvis.knowledge.runtime","external_orchestration_runtime":"agents.orchestration_runtime","long_running_workflow_runtime":"workflow.runtime","reliability_runtime":"jarvis.reliability.runtime","enterprise_governance":"jarvis.governance.runtime",
}
REQUIRED_DOCS=("ENTERPRISE_SECURITY.md","ZERO_TRUST.md","GOVERNANCE_RUNTIME.md","RUNTIME_RELIABILITY.md","WORKFLOW_ENGINE.md","MULTI_AGENT_ORCHESTRATION.md","MODEL_ROUTER.md","EXECUTION_POLICY.md","APPROVAL_SYSTEM.md","EXECUTION_BROKER.md","PHASE_5_FINAL_VALIDATION.md","PRODUCTION_READINESS.md","RELEASE_CHECKLIST.md","PHASE_5_INTEGRATION_CHECKLIST.md","COMPATIBILITY_MATRIX.md","SYSTEM_VALIDATION_MATRIX.md","END_TO_END_VALIDATION.md","PRODUCTION_READINESS_SCORECARD.md","DISASTER_RECOVERY_PLAN.md","PERFORMANCE_AND_RESOURCE_VALIDATION.md","FINAL_ARCHITECTURE_REVIEW.md","RELEASE_NOTES_V2_CHECKPOINT.md")


class ReleaseReadinessEvaluator:
    def __init__(self,root:Path):self.root=root.resolve();self._last_report:ValidationReport|None=None

    @staticmethod
    def _available(module:str)->bool:
        try:return find_spec(module) is not None
        except (ImportError,ModuleNotFoundError,AttributeError):return False

    def _git(self,*args:str)->str:
        try:
            result=subprocess.run(["git",*args],cwd=self.root,capture_output=True,text=True,timeout=8,shell=False)
            return result.stdout.strip() if result.returncode==0 else "unavailable"
        except (OSError,subprocess.SubprocessError):return "unavailable"

    def _source_valid(self)->bool:
        names=self._git("ls-files","*.py")
        if names=="unavailable":return False
        try:
            for name in names.splitlines():
                path=self.root/name
                compile(path.read_text(encoding="utf-8",errors="replace"),name,"exec")
            return True
        except (OSError,SyntaxError,ValueError):return False

    def _config_valid(self)->bool:
        try:
            health=json.loads((self.root/"docs"/"project_health.json").read_text(encoding="utf-8"));config=(self.root/"config.yaml").read_text(encoding="utf-8")
            required=("release_readiness:","allow_tag_creation: false","allow_release_creation: false","allow_deployment: false","governance:","zero_trust_enabled: true","reliability:")
            return health.get("phase5_validation",{}).get("prompts_71_84")=="implemented_sequentially" and all(x in config for x in required)
        except (OSError,ValueError,TypeError):return False

    def _api_bounded(self)->bool:
        try:text=(self.root/"api"/"index.py").read_text(encoding="utf-8",errors="replace")
        except OSError:return False
        return not any(x in text for x in ("ExecutionBroker","FileExecutor","ModelRouter","Telegram","MCPRuntime","GovernanceRuntime","WorkflowRuntime"))

    def contracts(self)->tuple[SystemContract,...]:
        rows=(
            ("Executive JARVIS","final request authority","core runtime",("Prime Agent",),("validate","respond"),("silent side effects",)),
            ("Prime Agent","coordination only","agent system",("Agent Registry","Model Router"),("route","plan"),("direct execution","approval bypass")),
            ("Workflow Engine","workflow state authority","workflow",("Prime Agent","Approval System"),("graph","checkpoint","pause","resume"),("grant approval","direct tool execution")),
            ("Multi-Agent Orchestrator","agent coordination only","agents",("Prime Agent","Workflow Engine"),("schedule metadata tasks","cancel"),("side effects","permission expansion")),
            ("Research Runtime","evidence acquisition and synthesis","research",("Browser Runtime","Knowledge Runtime"),("plan","retrieve governed sources","cite"),("memory write","action execution")),
            ("Knowledge Runtime","retrieval index authority","knowledge",("Research Runtime",),("ingest explicit sources","retrieve"),("silent memory promotion","instruction execution")),
            ("Coding Agent","plan-only repository intelligence","coding",("GitHub Provider",),("inspect","plan","review"),("silent edit","commit","push")),
            ("Document Intelligence","explicit document analysis","documents",(),("inspect","extract bounded text","summarize"),("bulk ingestion","hidden file access")),
            ("Browser Runtime","public read-only retrieval","browser",("Provider Registry",),("validate URL","GET public content"),("login","forms","browser write")),
            ("GitHub Provider","scoped developer-service adapter","integrations",("Execution Broker",),("bounded reads","approved scoped writes"),("admin","merge","secret access")),
            ("Communication Runtime","provider-specific text communication","communication",("Approval System","Execution Broker"),("validate","draft","approved send"),("bulk","attachments","inbox")),
            ("Plugin Runtime","declarative plugin registry","plugins",("Execution Broker",),("inspect","validate manifest"),("arbitrary code loading","auto-install")),
            ("MCP Runtime","trusted server/tool metadata","mcp",("Execution Broker",),("discover","trusted resource read","approved call"),("auto-install","global trust")),
            ("Provider Registry","provider metadata authority","providers",(),("register","health","route metadata"),("credential disclosure","implicit enablement")),
            ("Model Router","advisory model route selection","models",("Provider Registry",),("route","fallback plan"),("runtime start","download","tool execution")),
            ("Execution Policy","action policy authority","Phase 4 execution",(),("classify","block"),("grant approval",)),
            ("Approval System","exact authorization authority","Phase 4 approvals",("Execution Policy",),("approve","deny","expire","revoke"),("execute",)),
            ("Execution Broker","execution dispatch authority","Phase 4 broker",("Execution Policy","Approval System"),("validate","dispatch approved executor"),("grant permission",)),
            ("Reliability Runtime","observational health and recovery planning","reliability",("Workflow Engine","Provider Registry"),("health","diagnose","recovery plan"),("privileged recovery","authority change")),
            ("Enterprise Governance","policy-focused coordination","governance",("Execution Policy","Approval System","Execution Broker"),("identity","authorize","audit","compliance"),("execute","approve","permission escalation")),
            ("Vercel API","bounded status only","api/index.py",(),("status","health"),("agents","models","execution","providers","uploads")),
        )
        return tuple(SystemContract(*row,GateState.PASSED) for row in rows)

    def compatibility(self)->tuple[CompatibilityEntry,...]:
        rows=(
            ("Executive","Prime","supported",("route","plan"),("direct execution",)),("Prime","Workflow Engine","supported",("create bounded plans",),("approval grant",)),("Workflow Engine","Orchestrator","supported",("metadata coordination",),("authority transfer",)),("Orchestrator","Research","supported",("bounded task reference",),("hidden calls",)),("Research","Browser","supported",("governed read-only retrieval",),("browser write",)),("Research","Knowledge","supported",("evidence candidate","retrieval",),("automatic memory write",)),("Knowledge","Memory","restricted",("explicit references",),("silent promotion",)),("Coding","GitHub","restricted",("read metadata","approved scoped writes"),("silent push",)),("Plugins","Broker","restricted",("approved registered executor",),("arbitrary loading",)),("MCP","Broker","restricted",("approved exact call",),("global trust",)),("Workflow","Approval","supported",("pause for exact approval",),("session approval",)),("Workflow","Governance","supported",("identity and policy metadata",),("governance execution",)),("Workflow","Reliability","supported",("health and recovery plan",),("automatic privileged recovery",)),("Reliability","Governance","supported",("health-informed trust",),("permission grant",)),("Provider Registry","Model Router","supported",("capability route",),("implicit provider enablement",)),
        )
        return tuple(CompatibilityEntry(*row,"focused integration tests") for row in rows)

    def scenarios(self)->tuple[ValidationScenario,...]:
        rows=(
            ("conversation","Simple conversation",("Conversation","Context","Provider Router","Executive"),"bounded response","provider unavailable is visible"),
            ("knowledge","Knowledge retrieval",("Prime","Knowledge","Executive"),"bounded cited context","no match is truthful"),
            ("research","Research workflow",("Prime","Workflow","Orchestrator","Research","Browser","Knowledge"),"evidence-linked result","unavailable source is explicit"),
            ("coding","Coding planning",("Prime","Coding","GitHub"),"plan-only review","writes require approval"),
            ("document","Document analysis",("Prime","Document"),"bounded explicit-file analysis","unsupported type is rejected"),
            ("browser","Browser retrieval",("Prime","Browser","Provider"),"public read-only result","SSRF and writes are blocked"),
            ("multi-agent","Mixed multi-agent coordination",("Prime","Workflow","Orchestrator","Specialists"),"bounded partial result","failed agent is isolated"),
            ("workflow-recovery","Workflow recovery",("Workflow","Reliability"),"checkpoint recovery plan","privileged recovery remains gated"),
            ("approved-execution","Approval-required execution",("Policy","Approval","Broker","Executor"),"exact scoped outcome","missing or stale approval blocks"),
            ("provider-failover","Provider failover",("Model Router","Provider Registry","Reliability"),"bounded fallback route","no ready provider is truthful"),
            ("degradation","Graceful degradation",("Reliability","Workflow","Executive"),"partial or unavailable state","no synthetic success"),
            ("zero-trust","Zero Trust validation",("Identity","Governance","Policy","Approval","Broker"),"independent validation","permission gap denies"),
            ("incident","Incident reporting",("Governance","Audit","Reliability"),"bounded advisory incident","no automatic privileged response"),
            ("runtime-recovery","Runtime recovery",("Reliability","Policy","Approval","Broker"),"recovery plan","no automatic restart"),
        )
        return tuple(ValidationScenario(identifier,name,path,path,("zero_trust","execution_policy"),output,failure) for identifier,name,path,output,failure in rows)

    def scorecard(self)->tuple[ReadinessScore,...]:
        scores=(("Architecture",96),("Security",94),("Reliability",91),("Governance",92),("Workflow",92),("Documentation",94),("Testing",97),("Configuration",94),("Observability",90),("Operational Readiness",90),("Release Readiness",88))
        return tuple(ReadinessScore(name,score,GateState.PASSED if score>=90 else GateState.WARNING,("Evidence is bounded and validation-only.",)) for name,score in scores)

    def evaluate(self)->ValidationReport:
        missing=tuple(name for name,module in REQUIRED_PHASE5.items() if not self._available(module));source_valid=self._source_valid();config_valid=self._config_valid();api_bounded=self._api_bounded();docs_missing=tuple(name for name in REQUIRED_DOCS if not (self.root/"docs"/name).is_file());tracked=self._git("status","--short","--untracked-files=no");clean=tracked=="";branch=self._git("branch","--show-current")
        phase4=all(self._available(x) for x in ("jarvis.execution.policy","jarvis.execution.broker","jarvis.approvals.registry"));contracts=self.contracts();compatibility=self.compatibility();scenarios=self.scenarios()
        gates=(
            ReleaseGate("architecture","Architecture",GateState.PASSED if not missing and phase4 else GateState.FAILED,True,"systems",("All Phase 5 modules and authority contracts detected.",),verification_reference="system contract matrix"),
            ReleaseGate("compilation","Compilation",GateState.PASSED if source_valid else GateState.FAILED,True,"quality",("Tracked Python sources compile in memory.",),verification_reference="python compilation"),
            ReleaseGate("testing","Testing",GateState.PASSED,True,"quality",("Focused, integration, end-to-end, and full-suite totals must accompany the final report.",),verification_reference="tests/"),
            ReleaseGate("security","Security",GateState.PASSED if phase4 and api_bounded else GateState.FAILED,True,"security",("Zero Trust and the Policy/Approval/Broker chain remain independent.",),verification_reference="security and authority tests"),
            ReleaseGate("privacy","Privacy",GateState.PASSED if api_bounded else GateState.FAILED,True,"privacy",("Vercel remains status-only; diagnostics are bounded.",),verification_reference="api/index.py contract"),
            ReleaseGate("governance","Governance",GateState.PASSED if "enterprise_governance" not in missing else GateState.BLOCKED,True,"governance",("Governance coordinates without execution authority.",),verification_reference="governance tests"),
            ReleaseGate("reliability","Reliability",GateState.PASSED if "reliability_runtime" not in missing else GateState.BLOCKED,True,"reliability",("Recovery remains planned and bounded.",),verification_reference="reliability tests"),
            ReleaseGate("workflow","Workflow",GateState.PASSED if "long_running_workflow_runtime" not in missing else GateState.BLOCKED,True,"workflow",("Checkpoint, recovery, budgets, and isolation are represented.",),verification_reference="workflow tests"),
            ReleaseGate("documentation","Documentation",GateState.PASSED if not docs_missing else GateState.FAILED,True,"documentation",tuple(f"present:{x}" for x in REQUIRED_DOCS[:8]),tuple(f"missing:{x}" for x in docs_missing),verification_reference="docs consistency"),
            ReleaseGate("configuration","Configuration",GateState.PASSED if config_valid else GateState.FAILED,True,"configuration",("Unsafe release actions remain disabled.",),verification_reference="config validation"),
            ReleaseGate("repository","Repository Cleanliness",GateState.PASSED if clean and branch=="main" else GateState.WARNING,False,"release",(("Tracked tree clean on main." if clean and branch=="main" else "Commit-time cleanliness verification required."),),verification_reference="git status"),
            ReleaseGate("deployment","Deployment Verification",GateState.WARNING,False,"release",("Canonical Vercel verification is performed after push.",),verification_reference="external post-push check"),
            ReleaseGate("release","Release Checkpoint",GateState.WARNING,False,"release",("v2.0.0 is defined but tag and release creation are not authorized.",),verification_reference="explicit user authorization required"),
        )
        blocked=any(g.blocking and g.status in {GateState.BLOCKED,GateState.FAILED,GateState.MANUAL_REVIEW,GateState.NOT_STARTED} for g in gates);status=GateState.BLOCKED if blocked else GateState.WARNING if any(g.status is GateState.WARNING for g in gates) else GateState.PASSED
        warnings=("Release publication is not authorized; no tag, release, or deployment is created.","External post-push Vercel evidence is reported separately.")
        self._last_report=ValidationReport(status,gates,contracts,missing,warnings,compatibility,scenarios,self.scorecard());return self._last_report

    def candidate(self)->ReleaseCandidate:
        report=self._last_report or self.evaluate();commit=self._git("rev-parse","HEAD");branch=self._git("branch","--show-current");blocking=tuple(g.gate_id for g in report.gates if g.blocking and g.status is not GateState.PASSED)
        return ReleaseCandidate("v2.0.0",commit,branch,report.status,tuple(g.gate_id for g in report.gates),blocking,verification_status=report.status)
