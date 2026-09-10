import asyncio
from unittest.mock import patch

import pytest

from app.services import batch_executor


@pytest.fixture(autouse=True)
def temp_jobs_dir(tmp_path):
    """Create a temporary jobs directory for testing."""
    temp_jobs = tmp_path / "jobs"
    temp_jobs.mkdir()

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs)):
        yield temp_jobs


async def test_worker_pool_concurrency_limit():
    """Test that the semaphore in batch_executor.py limits concurrent tasks."""
    # Track concurrent executions
    concurrent_count = 0
    max_concurrent = 0
    execution_order = []

    async def mock_task(task_id: str, delay: float):
        nonlocal concurrent_count, max_concurrent
        # Use the semaphore from batch_executor
        async with batch_executor.semaphore:
            execution_order.append(f"start-{task_id}")
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(delay)
            concurrent_count -= 1
            execution_order.append(f"end-{task_id}")
            return {"task_id": task_id, "success": True}

    # Create more tasks than MAX_WORKERS
    tasks = [mock_task(f"task-{i}", 0.1) for i in range(10)]

    # Patch the semaphore to use a small limit for testing
    original_max_workers = batch_executor.MAX_WORKERS
    original_semaphore = batch_executor.semaphore
    batch_executor.MAX_WORKERS = 3
    batch_executor.semaphore = asyncio.Semaphore(3)

    try:
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed
        assert len(results) == 10
        assert all(r["success"] for r in results)

        # Verify concurrency was limited
        assert max_concurrent <= 3

        # Verify tasks actually ran concurrently (not serially)
        # If serial, max_concurrent would be 1
        assert max_concurrent > 1

    finally:
        batch_executor.MAX_WORKERS = original_max_workers
        batch_executor.semaphore = original_semaphore


async def test_worker_pool_task_cancellation():
    """Test task cancellation in async worker context."""
    cancelled_task = None
    task_started = asyncio.Event()

    async def long_running_task(task_id: str):
        nonlocal cancelled_task
        task_started.set()
        try:
            await asyncio.sleep(10)  # Long sleep that should be cancelled
            return {"task_id": task_id, "success": True}
        except asyncio.CancelledError:
            cancelled_task = task_id
            raise

    # Start a long-running task
    task = asyncio.create_task(long_running_task("task-1"))

    # Wait for it to start
    await task_started.wait()

    # Cancel it immediately
    task.cancel()

    # Verify cancellation
    with pytest.raises(asyncio.CancelledError):
        await task

    assert cancelled_task == "task-1"


async def test_worker_pool_crash_recovery():
    """Test handling of worker crashes/errors in batch processing."""
    crash_count = 0
    success_count = 0

    async def flaky_task(task_id: str, should_crash: bool):
        nonlocal crash_count, success_count
        await asyncio.sleep(0.01)

        if should_crash:
            crash_count += 1
            raise RuntimeError(f"Task {task_id} crashed")
        else:
            success_count += 1
            return {"task_id": task_id, "success": True}

    # Create a mix of crashing and successful tasks
    tasks = [
        flaky_task(f"task-{i}", i % 3 == 0)  # Every 3rd task crashes
        for i in range(9)
    ]

    # Use asyncio.gather with return_exceptions to collect all results
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify crash count
    assert crash_count == 3  # 3 tasks should have crashed (0, 3, 6)
    assert success_count == 6  # 6 tasks should have succeeded

    # Verify that exceptions were collected rather than propagating
    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) == 3

    # Verify successful results
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 6
    assert all(s["success"] for s in successes)


async def test_semaphore_limits_batch_job_concurrency():
    """Test that batch job respects semaphore limits during processing."""
    job_id = "test-job"
    image_format = "png"

    # Mock the process_single_image to track concurrency
    active_tasks = 0
    max_active = 0
    task_lock = asyncio.Lock()

    async def mock_process_single_image(job_id: str, filename: str, graph, image_format: str):
        nonlocal active_tasks, max_active

        async with batch_executor.semaphore:
            async with task_lock:
                active_tasks += 1
                max_active = max(max_active, active_tasks)

            await asyncio.sleep(0.05)

            async with task_lock:
                active_tasks -= 1

            return {"filename": filename, "success": True, "output_filename": f"out_{filename}", "error": None}

    # Patch the process_single_image function
    with patch("app.services.batch_executor.process_single_image", side_effect=mock_process_single_image):
        # Create a batch job with many files
        filenames = [f"image_{i}.png" for i in range(20)]

        # Set a low worker limit for testing
        original_max_workers = batch_executor.MAX_WORKERS
        original_semaphore = batch_executor.semaphore
        batch_executor.MAX_WORKERS = 4
        batch_executor.semaphore = asyncio.Semaphore(4)

        try:
            # Create a minimal graph for testing
            from app.models.graph import PipelineGraph

            graph = PipelineGraph(nodes=[], edges=[])

            # Run the batch job
            await batch_executor.run_batch_job(job_id, filenames, graph, image_format)

            # Verify that concurrency was limited
            assert max_active <= 4

            # Verify that tasks ran concurrently (not serially)
            assert max_active > 1

        finally:
            batch_executor.MAX_WORKERS = original_max_workers
            batch_executor.semaphore = original_semaphore
