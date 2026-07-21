from app.job_executor import JobExecutor
from app.job_service import JobService


class JobWorker:
    def __init__(
        self,
        *,
        job_service: JobService,
        executor: JobExecutor,
    ) -> None:
        self._job_service = job_service
        self._executor = executor
        self.current_job_id: str | None = None
        self.current_job_type: str | None = None
        self.jobs_processed = 0
        self.last_error: str | None = None

    def run_once(self) -> bool:
        job = self._job_service.claim_next()

        if job is None:
            return False

        self.current_job_id = job.job_id
        self.current_job_type = job.job_type.value
        self.last_error = None

        try:
            result, with_warnings = (
                self._executor.execute(job=job)
            )
        except Exception as error:
            self.last_error = (
                f"{type(error).__name__}: {error}"
            )
            self._job_service.fail(
                job_id=job.job_id,
                error=error,
            )
            self.jobs_processed += 1
            return True
        finally:
            self.current_job_id = None
            self.current_job_type = None

        self._job_service.complete(
            job_id=job.job_id,
            result=result,
            with_warnings=with_warnings,
        )
        self.jobs_processed += 1
        return True
