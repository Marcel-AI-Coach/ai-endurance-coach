# planner.py
from datetime import datetime, timedelta
from sqlalchemy import text


def get_week_dates(week_start: str):
    start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
    return [start_date + timedelta(days=i) for i in range(7)]


def load_weekly_planning_data(db, athlete_id: int, week_start: str):
    week_dates = get_week_dates(week_start)
    week_start_date = week_dates[0]
    week_end_date = week_dates[-1]

    athlete_query = text("""
        SELECT *
        FROM athletes
        WHERE id = :athlete_id
          AND active = true
    """)

    athlete_sports_query = text("""
        SELECT *
        FROM athlete_sports
        WHERE athlete_id = :athlete_id
          AND active = true
    """)

    sports_query = text("""
        SELECT *
        FROM sports
    """)

    preferences_query = text("""
        SELECT *
        FROM athlete_training_preferences
        WHERE athlete_id = :athlete_id
    """)

    availability_query = text("""
        SELECT *
        FROM athlete_availability
        WHERE athlete_id = :athlete_id
          AND (
                date BETWEEN :week_start AND :week_end
                OR (
                    date_from IS NOT NULL
                    AND date_to IS NOT NULL
                    AND date_from <= :week_end
                    AND date_to >= :week_start
                )
              )
    """)

    competitions_query = text("""
        SELECT *
        FROM competitions
        WHERE athlete_id = :athlete_id
          AND date BETWEEN :week_start AND :week_end
    """)

    training_sessions_query = text("""
        SELECT *
        FROM training_sessions
        WHERE athlete_id = :athlete_id
          AND date BETWEEN :week_start AND :week_end
    """)

    athlete = db.execute(
        athlete_query,
        {"athlete_id": athlete_id}
    ).mappings().first()

    athlete_sports = db.execute(
        athlete_sports_query,
        {"athlete_id": athlete_id}
    ).mappings().all()

    sports = db.execute(
        sports_query
    ).mappings().all()

    preferences = db.execute(
        preferences_query,
        {"athlete_id": athlete_id}
    ).mappings().all()

    availability = db.execute(
        availability_query,
        {
            "athlete_id": athlete_id,
            "week_start": str(week_start_date),
            "week_end": str(week_end_date)
        }
    ).mappings().all()

    competitions = db.execute(
        competitions_query,
        {
            "athlete_id": athlete_id,
            "week_start": str(week_start_date),
            "week_end": str(week_end_date)
        }
    ).mappings().all()

    training_sessions = db.execute(
        training_sessions_query,
        {
            "athlete_id": athlete_id,
            "week_start": str(week_start_date),
            "week_end": str(week_end_date)
        }
    ).mappings().all()

    return {
        "athlete": dict(athlete) if athlete else None,
        "athlete_sports": [dict(row) for row in athlete_sports],
        "sports": [dict(row) for row in sports],
        "athlete_training_preferences": [dict(row) for row in preferences],
        "athlete_availability": [dict(row) for row in availability],
        "competitions": [dict(row) for row in competitions],
        "training_sessions": [dict(row) for row in training_sessions],
        "week_dates": [str(day) for day in week_dates]
    }
