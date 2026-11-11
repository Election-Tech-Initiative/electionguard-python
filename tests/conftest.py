from hypothesis import settings

# Property tests check results, not timing. Hypothesis's default 200 ms deadline per
# example makes them fail with DeadlineExceeded on a slow or busy machine, so the
# test session runs without one. CI keeps its overall timeout.
settings.register_profile("electionguard", deadline=None)
settings.load_profile("electionguard")
