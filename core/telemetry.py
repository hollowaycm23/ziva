
import logging
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure specialized logger
telemetry_logger = logging.getLogger("ZivaTelemetry")
telemetry_logger.setLevel(logging.INFO)

# File handler for telemetry (structured jsonl)
file_handler = logging.FileHandler("/home/holloway/ziva/logs/telemetry.jsonl")
file_handler.setFormatter(logging.Formatter('%(message)s'))
telemetry_logger.addHandler(file_handler)

@dataclass
class ToolExecutionEvent:
    tool_name: str
    status: str # "success", "error"
    duration_ms: float
    input_summary: str
    error_message: Optional[str] = None
    timestamp: float = 0.0

@dataclass
class CognitiveLoopEvent:
    loop_count: int
    trigger_node: str
    resolution: str # "retry", "abort", "generated"
    timestamp: float = 0.0

class TelemetryManager:
    """
    Centralized observability for Ziva (Phase A).
    Tracks tool usage, cognitive loops, and latency.
    """
    
    @staticmethod
    def log_tool_execution(tool: str, start_time: float, status: str, input_val: str, error: str = None):
        duration = (time.time() - start_time) * 1000
        event = ToolExecutionEvent(
            tool_name=tool,
            status=status,
            duration_ms=round(duration, 2),
            input_summary=input_val[:100], # Truncate for log size
            error_message=error,
            timestamp=time.time()
        )
        telemetry_logger.info(json.dumps(asdict(event)))

    @staticmethod
    def log_cognitive_loop(count: int, node: str, resolution: str):
        event = CognitiveLoopEvent(
            loop_count=count,
            trigger_node=node,
            resolution=resolution,
            timestamp=time.time()
        )
        telemetry_logger.info(json.dumps(asdict(event)))
