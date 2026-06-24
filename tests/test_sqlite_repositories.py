from quotalane.models.job import Job
from quotalane.models.work import WorkItem
from quotalane.storage.repositories import SQLiteRepository


def test_sqlite_repositories(db_path):
    repo = SQLiteRepository(db_path)
    job = Job(job_id="job", job_type="paragraph_summary")
    item = WorkItem(work_item_id="w1", external_id="e1", input_text_hash="h1", estimated_input_tokens=100)
    repo.upsert_job(job)
    repo.upsert_work_items("job", [item])
    assert repo.get_job("job").job_id == "job"
    assert repo.list_work_items("job")[0].work_item_id == "w1"
