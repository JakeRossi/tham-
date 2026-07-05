from app.drills.arithmetic import AdditionDrill, SubtractionDrill
from app.engine.warmup import INITIAL_ROUND_SIZE, WarmupSession


def test_warmup_gives_initial_round_across_all_drills():
    session = WarmupSession([AdditionDrill(), SubtractionDrill()], rng_seed=1)
    seen = 0
    while not session.state.complete and seen < INITIAL_ROUND_SIZE:
        problem = session.next_problem()
        assert problem is not None
        # simulate a perfect run so it terminates after the initial round
        session.record_attempt(
            problem.drill_id, correct=True, used_hint=False,
            time_taken_seconds=2, time_limit_seconds=20,
        )
        seen += 1
    assert seen == INITIAL_ROUND_SIZE


def test_warmup_extends_for_a_concept_the_user_fails_repeatedly():
    session = WarmupSession([AdditionDrill(), SubtractionDrill()], rng_seed=1)
    total_addition_problems = 0
    total_problems = 0
    safety_cap = 500

    while not session.state.complete and total_problems < safety_cap:
        problem = session.next_problem()
        if problem is None:
            break
        total_problems += 1
        if problem.drill_id == "addition":
            total_addition_problems += 1
            # simulate consistently failing addition
            session.record_attempt("addition", correct=False, used_hint=True,
                                    time_taken_seconds=20, time_limit_seconds=20)
        else:
            # ace everything else
            session.record_attempt(problem.drill_id, correct=True, used_hint=False,
                                    time_taken_seconds=2, time_limit_seconds=20)

    assert session.state.complete
    # addition should have been drilled well beyond its initial ~10-question share
    assert total_addition_problems > INITIAL_ROUND_SIZE // 2
    assert session.state.concept_mastery["addition"] < session.state.concept_mastery["subtraction"]
