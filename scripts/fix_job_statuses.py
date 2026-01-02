
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from shared.models import Job, JobStatus, WorkflowState
from shared.database import DatabaseManager

async def fix_job_statuses():
    print("Starting Job Status Cleanup...")
    db = DatabaseManager()
    
    with db.get_session() as session:
        # 1. Fix Completed Jobs
        completed_jobs = session.query(Job).filter(
            Job.current_state == WorkflowState.COMPLETED,
            Job.status != JobStatus.COMPLETED
        ).all()
        
        for job in completed_jobs:
            print(f"Fixing Job {job.id}: Status {job.status} -> COMPLETED")
            job.status = JobStatus.COMPLETED
            
        # 2. Fix Failed Jobs
        failed_jobs = session.query(Job).filter(
            Job.current_state == WorkflowState.FAILED,
            Job.status != JobStatus.FAILED
        ).all()
        
        for job in failed_jobs:
            print(f"Fixing Job {job.id}: Status {job.status} -> FAILED")
            job.status = JobStatus.FAILED

        if not completed_jobs and not failed_jobs:
            print("No inconsistent jobs found.")
        else:
            session.commit()
            print(f"Fixed {len(completed_jobs)} completed jobs and {len(failed_jobs)} failed jobs.")

if __name__ == "__main__":
    asyncio.run(fix_job_statuses())
