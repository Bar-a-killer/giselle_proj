from app.services import jobs


def _reset():
    jobs._jobs.clear()


def test_try_create_job_allows_up_to_max():
    _reset()
    j1 = jobs.try_create_job(3)
    j2 = jobs.try_create_job(3)
    j3 = jobs.try_create_job(3)
    assert j1 is not None
    assert j2 is not None
    assert j3 is not None
    assert len({j1.id, j2.id, j3.id}) == 3


def test_try_create_job_rejects_beyond_max():
    _reset()
    for _ in range(3):
        assert jobs.try_create_job(3) is not None

    assert jobs.try_create_job(3) is None


def test_try_create_job_allows_more_once_a_job_finishes():
    _reset()
    active = [jobs.try_create_job(3) for _ in range(3)]
    assert jobs.try_create_job(3) is None

    jobs.set_done(active[0].id, {"venues_created": 1})
    assert jobs.try_create_job(3) is not None


def test_done_and_error_jobs_dont_count_toward_the_cap():
    _reset()
    j1 = jobs.try_create_job(3)
    j2 = jobs.try_create_job(3)
    jobs.set_done(j1.id, {})
    jobs.set_error(j2.id, "boom")

    for _ in range(3):
        assert jobs.try_create_job(3) is not None
    assert jobs.try_create_job(3) is None
