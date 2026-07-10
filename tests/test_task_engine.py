"""Tests for the JARVIS OS Task Engine."""

from __future__ import annotations

import unittest

from tasks import TaskManager, TaskPriority, TaskQueue, TaskStatus


class TaskEngineTests(unittest.TestCase):
    """Task Engine lifecycle and queue tests."""

    def test_create_task_queues_task_and_tracks_statistics(self) -> None:
        manager = TaskManager()
        manager.initialize()

        task = manager.create_task(
            name="Read PDF",
            description="Create a task for future PDF reading.",
            priority=TaskPriority.HIGH,
            assigned_agent="document-agent",
            related_memories=("memory-1",),
            metadata={"source": "unit-test"},
        )

        self.assertEqual(task.status, TaskStatus.QUEUED)
        self.assertEqual(task.assigned_agent, "document-agent")
        self.assertEqual(task.related_memories, ("memory-1",))
        self.assertEqual(manager.statistics().total_tasks, 1)
        self.assertEqual(manager.statistics().queued_tasks, 1)

    def test_pause_resume_cancel_and_search_task(self) -> None:
        manager = TaskManager()
        manager.initialize()
        task = manager.create_task(
            name="Search Memory",
            description="Future agent searches memory through a task.",
        )

        paused = manager.pause_task(task.task_id)
        self.assertIsNotNone(paused)
        self.assertEqual(paused.status, TaskStatus.PAUSED)

        resumed = manager.resume_task(task.task_id)
        self.assertIsNotNone(resumed)
        self.assertEqual(resumed.status, TaskStatus.QUEUED)

        results = manager.search_tasks("memory")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, task.task_id)

        cancelled = manager.cancel_task(task.task_id)
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled.status, TaskStatus.CANCELLED)
        self.assertEqual(manager.history.count(), 1)

    def test_fail_retry_and_complete_task_history(self) -> None:
        manager = TaskManager()
        manager.initialize()
        task = manager.create_task(
            name="Install Software",
            description="Architecture-only task, no installer execution.",
        )

        failed = manager.fail_task(task.task_id)
        self.assertIsNotNone(failed)
        self.assertEqual(failed.status, TaskStatus.FAILED)

        retried = manager.retry_task(task.task_id)
        self.assertIsNotNone(retried)
        self.assertEqual(retried.retry_count, 1)
        self.assertEqual(retried.status, TaskStatus.QUEUED)

        completed = manager.complete_task(task.task_id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertEqual(manager.history.count(), 1)

    def test_fifo_and_priority_queue_ordering(self) -> None:
        manager = TaskManager()
        manager.initialize()
        low = manager.create_task("Low", "Low priority", priority=TaskPriority.LOW)
        high = manager.create_task("High", "High priority", priority=TaskPriority.HIGH)

        self.assertEqual(manager.queue.dequeue_priority(), high.task_id)
        self.assertEqual(manager.queue.dequeue_priority(), low.task_id)

        queue = TaskQueue()
        queue.enqueue_fifo(low)
        queue.enqueue_fifo(high)

        self.assertEqual(queue.dequeue_fifo(), low.task_id)
        self.assertEqual(queue.dequeue_fifo(), high.task_id)


if __name__ == "__main__":
    unittest.main()
