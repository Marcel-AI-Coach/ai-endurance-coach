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


def build_sport_lookup(sports):
    sport_lookup = {}
    for sport in sports:
        sport_lookup[sport["id"]] = sport
    return sport_lookup


def build_primary_sport_lookup(athlete_sports):
    primary_lookup = {}
    for athlete_sport in athlete_sports:
        sport_id = athlete_sport["sport_id"]
        primary_lookup[sport_id] = bool(athlete_sport.get("primary_sport", False))
    return primary_lookup


def get_day_name(date_string: str):
    date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()
    return date_obj.strftime("%A").lower()


def get_competition_for_day(competitions, date_string: str):
    for competition in competitions:
        if str(competition["date"]) == date_string:
            return competition
    return None


def get_existing_training_session_for_day(training_sessions, date_string: str):
    for session in training_sessions:
        if str(session["date"]) == date_string:
            return session
    return None


def get_availability_for_day(availability_entries, date_string: str):
    matching_entries = []

    for entry in availability_entries:
        entry_date = entry.get("date")
        entry_date_from = entry.get("date_from")
        entry_date_to = entry.get("date_to")

        if entry_date is not None and str(entry_date) == date_string:
            matching_entries.append(("date", entry))

        elif entry_date_from is not None and entry_date_to is not None:
            if str(entry_date_from) <= date_string <= str(entry_date_to):
                matching_entries.append(("range", entry))

    date_entries = [entry for entry_type, entry in matching_entries if entry_type == "date"]
    range_entries = [entry for entry_type, entry in matching_entries if entry_type == "range"]

    if date_entries:
        return date_entries[0]

    if range_entries:
        return range_entries[0]

    return None


def get_preferences_for_weekday(preferences, weekday_name: str):
    matching_preferences = []

    for preference in preferences:
        if preference.get("weekday") == weekday_name and preference.get("preferred") is True:
            matching_preferences.append(preference)

    return matching_preferences


def choose_best_preference(preferences_for_day, primary_sport_lookup):
    if not preferences_for_day:
        return None

    def sort_key(preference):
        priority = preference.get("priority")
        if priority is None:
            priority = 9999

        sport_id = preference.get("sport_id")
        is_primary = primary_sport_lookup.get(sport_id, False)

        return (priority, -int(is_primary))

    sorted_preferences = sorted(preferences_for_day, key=sort_key)
    return sorted_preferences[0]


def build_preview_item_for_rest_day(date_string: str, weekday_name: str, reason: str):
    return {
        "date": date_string,
        "weekday": weekday_name,
        "planned": False,
        "reason": reason,
        "sport_id": None,
        "sport_name": None,
        "session_type": None,
        "duration_minutes": None,
        "title": None,
        "description": None
    }


def build_preview_item_for_existing_session(date_string: str, weekday_name: str, session, sport_lookup):
    sport = sport_lookup.get(session.get("sport_id"))

    return {
        "date": date_string,
        "weekday": weekday_name,
        "planned": bool(session.get("planned")),
        "reason": "existing_training_session",
        "sport_id": session.get("sport_id"),
        "sport_name": sport.get("name") if sport else None,
        "session_type": session.get("session_type"),
        "duration_minutes": session.get("duration_minutes"),
        "title": session.get("title"),
        "description": session.get("description")
    }


def build_preview_item_for_competition(date_string: str, weekday_name: str, competition, sport_lookup):
    sport = sport_lookup.get(competition.get("sport_id"))

    return {
        "date": date_string,
        "weekday": weekday_name,
        "planned": True,
        "reason": "competition",
        "sport_id": competition.get("sport_id"),
        "sport_name": sport.get("name") if sport else None,
        "session_type": "race",
        "duration_minutes": None,
        "title": f"Wettkampf: {competition.get('name')}",
        "description": "Automatisch aus competitions übernommen"
    }


def build_preview_item_for_preference(date_string: str, weekday_name: str, preference, sport_lookup, availability_entry):
    sport = sport_lookup.get(preference.get("sport_id"))

    preferred_max_duration = preference.get("max_duration_minutes")
    availability_max_duration = None

    if availability_entry is not None:
        availability_max_duration = availability_entry.get("max_duration_minutes")

    final_duration = preferred_max_duration

    if final_duration is None:
        final_duration = preference.get("min_duration_minutes")

    if availability_max_duration is not None:
        if final_duration is None:
            final_duration = availability_max_duration
        else:
            final_duration = min(final_duration, availability_max_duration)

    return {
        "date": date_string,
        "weekday": weekday_name,
        "planned": True,
        "reason": "training_preference",
        "sport_id": preference.get("sport_id"),
        "sport_name": sport.get("name") if sport else None,
        "session_type": preference.get("preferred_session_type"),
        "duration_minutes": final_duration,
        "title": f"{sport.get('name') if sport else 'Training'} - {preference.get('preferred_session_type')}",
        "description": "Automatisch aus athlete_training_preferences erzeugt"
    }


def generate_week_preview(db, athlete_id: int, week_start: str):
    data = load_weekly_planning_data(db, athlete_id, week_start)

    if not data["athlete"]:
        return {
            "status": "error",
            "error_message": "Athlet nicht gefunden oder nicht aktiv."
        }

    sport_lookup = build_sport_lookup(data["sports"])
    primary_sport_lookup = build_primary_sport_lookup(data["athlete_sports"])

    preview_days = []

    for date_string in data["week_dates"]:
        weekday_name = get_day_name(date_string)

        existing_session = get_existing_training_session_for_day(
            data["training_sessions"],
            date_string
        )
        if existing_session:
            preview_days.append(
                build_preview_item_for_existing_session(
                    date_string,
                    weekday_name,
                    existing_session,
                    sport_lookup
                )
            )
            continue

        competition = get_competition_for_day(
            data["competitions"],
            date_string
        )
        if competition:
            preview_days.append(
                build_preview_item_for_competition(
                    date_string,
                    weekday_name,
                    competition,
                    sport_lookup
                )
            )
            continue

        availability_entry = get_availability_for_day(
            data["athlete_availability"],
            date_string
        )
        if availability_entry is not None and availability_entry.get("available") is False:
            preview_days.append(
                build_preview_item_for_rest_day(
                    date_string,
                    weekday_name,
                    "blocked_by_athlete_availability"
                )
            )
            continue

        preferences_for_day = get_preferences_for_weekday(
            data["athlete_training_preferences"],
            weekday_name
        )
        if not preferences_for_day:
            preview_days.append(
                build_preview_item_for_rest_day(
                    date_string,
                    weekday_name,
                    "no_training_preference"
                )
            )
            continue

        best_preference = choose_best_preference(
            preferences_for_day,
            primary_sport_lookup
        )
        if not best_preference:
            preview_days.append(
                build_preview_item_for_rest_day(
                    date_string,
                    weekday_name,
                    "no_valid_preference"
                )
            )
            continue

        preview_days.append(
            build_preview_item_for_preference(
                date_string,
                weekday_name,
                best_preference,
                sport_lookup,
                availability_entry
            )
        )

    return {
        "status": "ok",
        "athlete_id": athlete_id,
        "week_start": week_start,
        "athlete": data["athlete"],
        "preview_days": preview_days
    }
