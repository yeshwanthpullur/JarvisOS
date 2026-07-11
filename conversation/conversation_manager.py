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
        personal_intelligence_manager: PersonalIntelligenceManager | None = None,
        context_intelligence_manager: ContextIntelligenceManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.jarvis_core = jarvis_core
        self.command_manager = CommandManager()
        self.engine = ConversationEngine()
        self.history = ConversationHistory()
        self.memory = ConversationMemory(memory_manager)
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
        self.personal_intelligence = personal_intelligence_manager
        self.context_intelligence = context_intelligence_manager
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> ConversationStatistics:
        """Initialize conversation and command engines."""
        self.command_manager.initialize()
        self.metrics.sessions = 1
        self.metrics.active_sessions = 1
        self.metrics.conversations = 1
        self.initialized = True
        self.logger.info("conversation_manager_initialized commands=%s", len(self.command_manager.registry.list_commands()))
        return self.statistics()

    def handle_input(self, user_input: str) -> ConversationResponse:
        """Handle user input through conversation, command, and executive layers."""
        request = ConversationRequest(user_input=user_input, normalized_input=user_input.strip().lower(), goal=user_input.strip())
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
            metadata={
                "personal_intelligence_manager": self.personal_intelligence,
                "personal_context": personal_context,
                "context_intelligence_manager": self.context_intelligence,
                "goal_intelligence_manager": self.goal_intelligence,
            },
        )
        response = self.engine.handle(request, context)
        if self.context_intelligence is not None:
            self.context_intelligence.record_interaction(self.active_session, user_input, response)
        self.history.append(request, response)
        self.active_session.record(user_input, response.response)
        self.metrics.requests += 1
        self.metrics.responses += 1
        self.metrics.history_size = self.history.statistics()["turns"]
        if response.warnings:
            self.metrics.failures += 1
        return response

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
