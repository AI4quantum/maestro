import time
from maestro.file_logger import FileLogger

logger = FileLogger()

def log_agent_run(workflow_id):
    def decorator(run_func):
        async def wrapper(self, *args, **kwargs):
            step_index = kwargs.pop("step_index", None)
            if step_index is None:
                raise ValueError("Missing step_index for logging.")

            start = time.perf_counter()
            result = await run_func(self, *args, **kwargs)
            end = time.perf_counter()

            logger.log_agent_response(
                workflow_id=workflow_id,
                step_index=step_index,
                agent_name=getattr(self, "agent_name", "unknown"),
                model=getattr(self, "agent_model", "unknown"),
                input_text=args[0] if args else "",
                response_text=result,
                tool_used=None,
                duration_ms=int((end - start) * 1000)
            )

            return result
        return wrapper
    return decorator
