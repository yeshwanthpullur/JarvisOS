"""Conversation manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from commands import CommandManager
from conversation.conversation_context import ConversationContext
from conversation.conversation_engine import ConversationEngine
from conversation.conversation_history import ConversationHistory
from conversation.conversation_memory import ConversationMemory
from conversation.conversation_metrics import ConversationMetrics
from conversation.conversation_request import ConversationRequest
from conversation.conversation_response import ConversationResponse
from conversation.conversation_session import ConversationSession
from conversation.conversation_summary import ConversationSummary
from conversation.conversation_intelligence import ConversationIntelligenceManager
from context_intelligence import ContextIntelligenceManager
from goal_intelligence import GoalIntelligenceManager
from personal_intelligence import PersonalIntelligenceManager


@dataclass(frozen=True, slots=True)
class ConversationStatistics:
    """Startup/runtime statistics for conversation and command layers."""

    conversation_status: str
    command_engine_status: str
    cli_status: str
    request_pipeline_status: str
    response_pipeline_status: str
    active_conversations: int
    registered_commands: int
    session_status: str
    health_status: str


class ConversationManager:
    """Single operating interface coordinating conversation and commands."""

    def __init__(
        self,
        jarvis_core: object | None = None,
        memory_manager: object | None = None,
        memory_intelligence_manager: object | None = None,
        knowledge_manager: object | None = None,
        task_manager: object | None = None,
        task_intelligence_manager: object | None = None,
        workflow_manager: object | None = None,
        retrieval_manager: object | None = None,
        research_manager: object | None = None,
        goal_intelligence_manager: GoalIntelligenceManager | None = None,
        plugin_manager: object | None = None,
        provider_manager: object | None = None,
        provider_router: object | None = None,
        agent_manager: object | None = None,
        agent_creator: object | None = None,
        tool_manager: object | None = None,
        autonomous_planning: object | None = None,
        voice_intelligence: object | None = None,
        vision_intelligence: object | None = None,
        image_generation: object | None = None,
        sync_intelligence: object | None = None,
        web_automation: object | None = None,
        research_agent: object | None = None,
        coding_agent: object | None = None,
        document_agent: object | None = None,
        browser_agent: object | None = None,
        scheduler_agent: object | None = None,
        communication_agent: object | None = None,
        adapter_agent: object | None = None,
        advanced_model_planner: object | None = None,
        advanced_model_runtime: object | None = None,
        evaluation_runner: object | None = None,
        release_readiness_evaluator: object | None = None,
        phase4_runtime: object | None = None,
        mobile_automation: object | None = None,
        personal_intelligence_manager: PersonalIntelligenceManager | None = None,
        context_intelligence_manager: ContextIntelligenceManager | None = None,
        conversation_config: object | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.jarvis_core = jarvis_core
        self.command_manager = CommandManager()
        self.engine = ConversationEngine()
        self.history = ConversationHistory()
        self.memory = ConversationMemory(memory_manager)
        self.memory_intelligence = memory_intelligence_manager
        self.metrics = ConversationMetrics()
        self.active_session = ConversationSession()
        self.knowledge_manager = knowledge_manager
        self.task_manager = task_manager
        self.task_intelligence_manager = task_intelligence_manager
        self.workflow_manager = workflow_manager
        self.retrieval_manager = retrieval_manager
        self.research_manager = research_manager
        self.goal_intelligence = goal_intelligence_manager
        self.plugin_manager = plugin_manager
        self.provider_manager = provider_manager
        self.provider_router = provider_router
        self.agent_manager = agent_manager
        self.agent_creator = agent_creator
        self.tool_manager = tool_manager
        self.autonomous_planning = autonomous_planning
        self.voice_intelligence = voice_intelligence
        self.vision_intelligence = vision_intelligence
        self.image_generation = image_generation
        self.sync_intelligence = sync_intelligence
        self.web_automation = web_automation
        self.research_agent = research_agent
        self.coding_agent = coding_agent
        self.document_agent = document_agent
        self.browser_agent = browser_agent
        self.scheduler_agent = scheduler_agent
        self.communication_agent = communication_agent
        self.adapter_agent = adapter_agent
        self.advanced_model_planner = advanced_model_planner
        self.advanced_model_runtime = advanced_model_runtime
        self.evaluation_runner = evaluation_runner
        self.release_readiness_evaluator = release_readiness_evaluator
        self.phase4_runtime = phase4_runtime
        self.mobile_automation = mobile_automation
        self.personal_intelligence = personal_intelligence_manager
        self.context_intelligence = context_intelligence_manager
        self.conversation_intelligence = ConversationIntelligenceManager(conversation_config)
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False
        self._conversations: dict[str, tuple[ConversationSession, ConversationHistory]] = {
            self.active_session.conversation_id: (self.active_session, self.history)
        }

    def initialize(self) -> ConversationStatistics:
        """Initialize conversation and command engines."""
        self.command_manager.initialize()
        self.metrics.sessions = 1
        self.metrics.active_sessions = 1
        self.metrics.conversations = 1
        self.initialized = True
        self.logger.info("conversation_manager_initialized commands=%s", len(self.command_manager.registry.list_commands()))
        return self.statistics()

    def handle_input(self, user_input: str, request_id: str | None = None) -> ConversationResponse:
        """Handle user input through conversation, command, and executive layers."""
        self.active_session.request_id = request_id
        stripped_input = user_input.strip()
        is_command = self.command_manager.is_command_candidate(stripped_input)
        plan = None if is_command else self.conversation_intelligence.prepare(
            stripped_input,
            {
                "vision_context": self.active_session.metadata.get("vision_context"),
                "web_context": self.active_session.metadata.get("web_context"),
            },
        )
        routed_input = plan.provider_input if plan is not None and not plan.clarification else stripped_input
        request = ConversationRequest(
            user_input=routed_input,
            normalized_input=routed_input.lower(),
            goal=stripped_input,
            metadata={"request_id": request_id} if request_id else {},
        )
        personal_context = (
            self.personal_intelligence.apply_context(user_input, conversation_id=self.active_session.conversation_id)
            if self.personal_intelligence is not None
            else {}
        )
        context = ConversationContext(
            session=self.active_session,
            jarvis_core=self.jarvis_core,
            command_manager=self.command_manager,
            memory_manager=self.memory.memory_manager,
            memory_intelligence_manager=self.memory_intelligence,
            knowledge_manager=self.knowledge_manager,
            task_manager=self.task_manager,
            task_intelligence_manager=self.task_intelligence_manager,
            workflow_manager=self.workflow_manager,
            retrieval_manager=self.retrieval_manager,
            research_manager=self.research_manager,
            goal_intelligence_manager=self.goal_intelligence,
            plugin_manager=self.plugin_manager,
            provider_manager=self.provider_manager,
            provider_router=self.provider_router,
            agent_manager=self.agent_manager,
            agent_creator=self.agent_creator,
            tool_manager=self.tool_manager,
            autonomous_planning=self.autonomous_planning,
            voice_intelligence=self.voice_intelligence,
            vision_intelligence=self.vision_intelligence,
            image_generation=self.image_generation,
            sync_intelligence=self.sync_intelligence,
            web_automation=self.web_automation,
            research_agent=self.research_agent,
            coding_agent=self.coding_agent,
            document_agent=self.document_agent,
            browser_agent=self.browser_agent,
            scheduler_agent=self.scheduler_agent,
            communication_agent=self.communication_agent,
            adapter_agent=self.adapter_agent,
            advanced_model_planner=self.advanced_model_planner,
            advanced_model_runtime=self.advanced_model_runtime,
            evaluation_runner=self.evaluation_runner,
            release_readiness_evaluator=self.release_readiness_evaluator,
            phase4_runtime=self.phase4_runtime,
            mobile_automation=self.mobile_automation,
            metadata={
                "session_metadata": dict(self.active_session.metadata),
                "personal_intelligence_manager": self.personal_intelligence,
                "personal_context": personal_context,
                "context_intelligence_manager": self.context_intelligence,
                "goal_intelligence_manager": self.goal_intelligence,
                "memory_intelligence_manager": self.memory_intelligence,
                "conversation_intelligence_manager": self.conversation_intelligence,
                "conversation_original_input": stripped_input,
                "conversation_plan": plan,
                "document_agent": self.document_agent,
                "browser_agent": self.browser_agent,
                "scheduler_agent": self.scheduler_agent,
                "communication_agent": self.communication_agent,
                "adapter_agent": self.adapter_agent,
                "advanced_model_planner": self.advanced_model_planner,
                "advanced_model_runtime": self.advanced_model_runtime,
                "evaluation_runner": self.evaluation_runner,
                "release_readiness_evaluator": self.release_readiness_evaluator,
                "phase4_runtime": self.phase4_runtime,
            },
        )
        response = (
            ConversationResponse(
                response=plan.clarification,
                metadata={"conversation_confidence": plan.confidence, "clarification": True},
            )
            if plan is not None and plan.clarification
            else self.engine.handle(request, context)
        )
        if plan is not None and not plan.clarification:
            self.conversation_intelligence.record_response(response.response)
        elif stripped_input.lower().startswith(("vision analyze ", "vision describe ", "vision ask ")) and response.execution_state != "failed":
            self.active_session.metadata["vision_context"] = response.response[:500]
        elif stripped_input.lower().startswith(("web open ", "web snapshot")) and response.execution_state != "failed":
            self.active_session.metadata["web_context"] = response.response[:500]
        if self.context_intelligence is not None:
            self.context_intelligence.record_interaction(self.active_session, user_input, response)
        if not is_command and self.memory_intelligence is not None and hasattr(self.memory_intelligence, "note_response"):
            try:
                self.memory_intelligence.note_response(
                    user_input,
                    response.response,
                    context.session.conversation_id,
                    session_id=getattr(context.session, "request_id", None),
                )
            except Exception:
                pass
        history_request = ConversationRequest(
            user_input=stripped_input,
            normalized_input=stripped_input.lower(),
            goal=stripped_input,
            metadata=dict(request.metadata),
        )
        self.history.append(history_request, response)
        self.active_session.current_topic = self.conversation_intelligence.state.active_topic
        self.active_session.record(stripped_input, response.response)
        self.metrics.requests += 1
        self.metrics.responses += 1
        self.metrics.history_size = self.history.statistics()["turns"]
        if response.warnings:
            self.metrics.failures += 1
        return response

    def create_conversation(self) -> ConversationSession:
        """Create and activate a new conversation using existing session/history models."""
        self._conversations[self.active_session.conversation_id] = (self.active_session, self.history)
        self.active_session = ConversationSession()
        self.history = ConversationHistory()
        self._conversations[self.active_session.conversation_id] = (self.active_session, self.history)
        self.metrics.sessions += 1
        self.metrics.conversations += 1
        return self.active_session

    def activate_conversation(self, conversation_id: str) -> bool:
        """Activate a known in-memory conversation without duplicating its history."""
        record = self._conversations.get(conversation_id)
        if record is None:
            return False
        self.active_session, self.history = record
        return True

    def list_conversations(self) -> tuple[dict[str, object], ...]:
        """Return bounded safe summaries of existing conversation sessions."""
        self._conversations[self.active_session.conversation_id] = (self.active_session, self.history)
        records = sorted(
            self._conversations.values(),
            key=lambda item: str(item[0].updated_at),
            reverse=True,
        )
        return tuple(
            {
                "conversation_id": session.conversation_id,
                "title": session.current_topic or (session.previous_requests[0][:64] if session.previous_requests else "New conversation"),
                "turns": history.statistics()["turns"],
                "updated_at": str(session.updated_at),
                "active": session.conversation_id == self.active_session.conversation_id,
            }
            for session, history in records
        )

    def conversation_messages(self, conversation_id: str, limit: int = 200) -> tuple[dict[str, object], ...] | None:
        """Return safe visible messages for a known conversation."""
        self._conversations[self.active_session.conversation_id] = (self.active_session, self.history)
        record = self._conversations.get(conversation_id)
        if record is None:
            return None
        _, history = record
        messages: list[dict[str, object]] = []
        for request, response in history.export()[-max(1, limit):]:
            messages.extend((
                {"role": "user", "content": request.user_input, "timestamp": str(request.timestamp)},
                {"role": "assistant", "content": response.response, "timestamp": str(request.timestamp), "status": response.execution_state, "metadata": dict(response.metadata)},
            ))
        return tuple(messages)

    def summary(self) -> ConversationSummary:
        """Return active conversation summary."""
        return ConversationSummary(
            conversation_id=self.active_session.conversation_id,
            turns=self.history.statistics()["turns"],
            active_topic=self.active_session.current_topic,
            active_goal=self.active_session.current_goal,
        )

    def statistics(self) -> ConversationStatistics:
        """Return conversation statistics."""
        return ConversationStatistics(
            conversation_status="ready" if self.initialized else "unavailable",
            command_engine_status="ready" if self.command_manager.initialized else "unavailable",
            cli_status="ready",
            request_pipeline_status="ready" if self.engine.initialized else "unavailable",
            response_pipeline_status="ready",
            active_conversations=self.metrics.active_sessions,
            registered_commands=len(self.command_manager.registry.list_commands()),
            session_status="active",
            health_status="healthy",
        )
