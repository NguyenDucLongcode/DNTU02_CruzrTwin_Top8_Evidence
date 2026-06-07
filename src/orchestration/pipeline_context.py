from src.common.time_utils import now_iso

class PipelineContext:
    def __init__(self, demo_run_id: str, scenario_id: str, scenario_source: str, zone_id: str, timestamp: str = None):
        self.demo_run_id = demo_run_id
        self.scenario_id = scenario_id
        self.scenario_source = scenario_source
        self.zone_id = zone_id
        self.timestamp = timestamp or now_iso()
        self.trace_refs = {}
        self.errors = []
