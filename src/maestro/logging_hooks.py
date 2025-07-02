import time
from datetime import datetime, UTC
from maestro.file_logger import FileLogger

logger = FileLogger()


def log_agent_run(workflow_id, agent_name, agent_model):
    def decorator(run_func):
        async def wrapper(*args, **kwargs):
            step_index = kwargs.pop("step_index", None)
            if step_index is None:
                raise ValueError("Missing step_index for logging.")

            perf_start = time.perf_counter()
            start_time = datetime.now(UTC)

            result = await run_func(*args, **kwargs)

            end_time = datetime.now(UTC)
            perf_end = time.perf_counter()

            input_text = ""
            if len(args) > 0:
                input_text = args[0]

            logger.log_agent_response(
                workflow_id=workflow_id,
                step_index=step_index,
                agent_name=agent_name,
                model=agent_model,
                input_text=input_text,
                response_text=result,
                tool_used=None,
                start_time=start_time,
                end_time=end_time,
                duration_ms=int((perf_end - perf_start) * 1000),
            )

            return result

        return wrapper

    return decorator
