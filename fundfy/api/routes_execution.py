"""Execution API routes."""

import json
import uuid

from fastapi import APIRouter

from fundfy.api.schemas import ExecutionRequest, ExecutionResponse, WorkstreamResponse

router = APIRouter(prefix="/api", tags=["execution"])

# In-memory store for workstreams
_workstreams: dict[str, list[dict]] = {}


@router.post("/execute", response_model=ExecutionResponse)
async def execute_plan(request: ExecutionRequest):
    """Trigger execution orchestrator for an objective."""
    from fundfy.dependencies import get_orchestrator

    planner, dispatcher = get_orchestrator()
    tasks = await planner.plan(request.objective, request.context or "")

    # Store tasks
    stored_tasks = []
    for task in tasks:
        task_record = {
            "id": str(uuid.uuid4()),
            "business_id": request.business_id,
            "type": task.get("type", "unknown"),
            "status": "pending",
            "params_json": json.dumps(task.get("params", {})),
            "result_json": None,
        }
        stored_tasks.append(task_record)

    _workstreams[request.business_id] = stored_tasks

    # Execute tasks
    results = await dispatcher.execute(tasks)

    # Update statuses
    for i, result in enumerate(results):
        if i < len(stored_tasks):
            stored_tasks[i]["status"] = result.status
            if result.result:
                stored_tasks[i]["result_json"] = json.dumps(result.result)

    return ExecutionResponse(
        business_id=request.business_id,
        tasks=stored_tasks,
        status="completed",
    )


@router.get("/workstreams/{business_id}", response_model=list[WorkstreamResponse])
async def get_workstreams(business_id: str):
    """Get workstream tasks for a business."""
    tasks = _workstreams.get(business_id, [])
    return [WorkstreamResponse(**t) for t in tasks]
