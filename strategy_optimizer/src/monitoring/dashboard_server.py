from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import logging
from typing import List

# from storage.state_manager import StateManager
# from storage.artifact_manager import ArtifactManager
# from governance.incident_tracker import IncidentTracker
# from data_bus.schemas import AuditVerdict, OptimizerProposal

class DashboardServer:
    """
    FastAPI web dashboard to display system status, metrics, incidents, and audit artifacts.
    """
    def __init__(self, config, state_manager, artifact_manager, incident_tracker):
        self.config = config
        self.state_manager = state_manager
        self.artifact_manager = artifact_manager
        self.incident_tracker = incident_tracker
        self.app = FastAPI(title="Strategy Optimizer Dashboard")
        self.port = self.config['system_config']['monitoring']['dashboard_port']

        self._setup_routes()
        logging.info(f"Initialized DashboardServer on port {self.port}.")

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            return """
            <html>
                <head>
                    <title>Strategy Optimizer Dashboard</title>
                </head>
                <body>
                    <h1>Welcome to the Strategy Optimizer Dashboard!</h1>
                    <p>Visit /docs for API documentation.</p>
                    <ul>
                        <li><a href="/metrics">Metrics</a></li>
                        <li><a href="/incidents">Incidents</a></li>
                        <li><a href="/audit-artifacts">Audit Artifacts</a></li>
                    </ul>
                </body>
            </html>
            """
        
        @self.app.get("/metrics")
        async def get_metrics():
            # Placeholder for actual metrics from metrics_collector
            return {"status": "ok", "equity": 100000, "drawdown": 5.2, "t1_flags": 0}

        @self.app.get("/incidents")
        async def get_incidents():
            incidents = self.incident_tracker.get_active_incidents()
            # Convert to a more friendly format if needed
            return {"active_incidents": incidents}

        @self.app.get("/audit-artifacts/{audit_id}")
        async def get_audit_artifact(audit_id: str):
            artifact = self.artifact_manager.download_artifact(f"audit_{audit_id}.json")
            if not artifact:
                raise HTTPException(status_code=404, detail="Artifact not found")
            # return AuditVerdict.model_validate_json(artifact)
            return {"artifact_content": artifact} # For now, return raw content

        @self.app.get("/audit-artifacts")
        async def list_audit_artifacts():
            # This would ideally list available artifact IDs or a summary
            return {"message": "Provide an audit_id to retrieve a specific artifact, e.g., /audit-artifacts/some-uuid"}

    def start(self):
        """
        Starts the FastAPI server. This is a blocking call.
        """
        logging.info(f"Starting dashboard server on http://0.0.0.0:{self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
