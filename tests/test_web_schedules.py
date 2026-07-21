from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.application_errors import AuthenticationError, AuthorizationError
from app.authentication import AuthenticatedUser
from app.job import JobRecord, JobStatus, JobType
from app.scheduled_task import CatchUpPolicy, ScheduledTask, ScheduleKind
from web.app import create_app

class Auth:
    user=AuthenticatedUser(user_id="u", username="admin", role="ADMIN")
    def authenticate(self, *, session_token):
        if session_token != "s": raise AuthenticationError("Authentication is required.", code="AUTH_REQUIRED")
        return self.user
    def verify_csrf(self, *, session_token, csrf_token):
        user=self.authenticate(session_token=session_token)
        if csrf_token != "c": raise AuthorizationError("Invalid CSRF.", code="CSRF_INVALID")
        return user
    def login(self, **kwargs): raise NotImplementedError
    def logout(self, **kwargs): pass
class Audit:
    def __init__(self): self.events=[]
    def record(self, **kwargs): self.events.append(kwargs)
    def list_recent(self, *, limit=100): return tuple(self.events)
class Schedules:
    def __init__(self): self.item=None
    def list(self): return () if self.item is None else (self.item,)
    def get(self, *, schedule_id): return self.item if self.item and self.item.schedule_id==schedule_id else None
    def create(self, **kwargs):
        now=datetime(2026,7,21,12,0,tzinfo=timezone.utc)
        self.item=ScheduledTask(schedule_id=kwargs.get("schedule_id") or "s1", task_type=kwargs["task_type"], enabled=kwargs["enabled"], schedule_kind=kwargs["schedule_kind"], timezone_name=kwargs["timezone_name"], interval_seconds=kwargs.get("interval_seconds"), local_hour=kwargs.get("local_hour"), local_minute=kwargs.get("local_minute"), weekday=kwargs.get("weekday"), next_run_at=now, payload=kwargs["payload"], catch_up_policy=kwargs["catch_up_policy"], catch_up_window_seconds=kwargs.get("catch_up_window_seconds"), created_at=now, updated_at=now)
        return self.item
    def update(self, *, schedule_id, **kwargs): return self.create(schedule_id=schedule_id, **kwargs) if self.get(schedule_id=schedule_id) else None
    def set_enabled(self, *, schedule_id, enabled):
        if not self.get(schedule_id=schedule_id): return None
        self.item=ScheduledTask(**{**self.item.__dict__, "enabled": enabled})
        return self.item
    def delete(self, *, schedule_id):
        if not self.get(schedule_id=schedule_id): return False
        self.item=None; return True
    def run_now(self, *, schedule_id):
        if not self.get(schedule_id=schedule_id): return None
        return JobRecord(job_id="j1", job_type=self.item.task_type, status=JobStatus.QUEUED, created_at=datetime.now(timezone.utc), payload=dict(self.item.payload))
class Infra:
    class R:
        def to_dictionary(self): return {"name":"scheduler","status":"IDLE","online":True}
    def get_scheduler_status(self): return self.R()
    def get_status(self): return self.R()
class Status:
    def get_status(self, *, request):
        class R:
            def to_dictionary(self): return {}
        return R()
class History:
    def initialize(self): pass
    def list_recent(self, **kwargs): return ()

def client(service):
    app=create_app(authentication_service_factory=lambda:Auth(), audit_service_factory=lambda:Audit(), schedule_management_service_factory=lambda:service, infrastructure_status_service_factory=lambda:Infra(), system_status_service_factory=lambda:Status(), run_history_service_factory=lambda:History())
    c=TestClient(app); c.cookies.set("trading_session","s"); c.headers.update({"X-CSRF-Token":"c"}); return c

def payload(): return {"schedule_id":"hourly","task_type":"INTELLIGENCE_CYCLE","enabled":True,"schedule_kind":"INTERVAL","timezone_name":"UTC","interval_seconds":3600,"payload":{"symbols":["AAPL"]}}

def test_schedule_crud_and_run_now():
    service=Schedules(); c=client(service)
    assert c.post("/api/schedules",json=payload()).status_code==201
    assert c.get("/api/schedules").json()["count"]==1
    assert c.post("/api/schedules/hourly/disable").json()["enabled"] is False
    assert c.post("/api/schedules/hourly/run-now").status_code==202
    assert c.delete("/api/schedules/hourly").status_code==204

def test_rejects_paper_trading_schedule():
    data=payload(); data["task_type"]="PAPER_TRADING_START"
    assert client(Schedules()).post("/api/schedules",json=data).status_code==422

def test_scheduler_status_requires_authentication():
    app=create_app(authentication_service_factory=lambda:Auth(), schedule_management_service_factory=lambda:Schedules(), infrastructure_status_service_factory=lambda:Infra(), system_status_service_factory=lambda:Status(), run_history_service_factory=lambda:History())
    assert TestClient(app).get("/api/scheduler/status").status_code==401