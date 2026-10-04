"""Progress statistics, session summaries, and question selection (including adaptive practice)."""
from __future__ import annotations

import math
import random
from collections import defaultdict

import db
from engine.catalog import TOPICS, TYPES, SESSION_TOPICS, TN_TOPICS
from engine import generator

PRIOR_N, PRIOR_ACC = 2.0, 0.7


# ============================================================================ statistics
def _agg(qs):
    n = len(qs)
    correct = sum(1 for q in qs if q["correct"])
    first = sum(1 for q in qs if q["first_try_correct"])
    hinted = sum(1 for q in qs if q["hints_used"] > 0)
    attempts = [q["attempts"] for q in qs if q["attempts"] > 0]
    return {
        "answered": n, "correct": correct, "incorrect": n - correct,
        "accuracy": round(100 * first / n) if n else None,
        "eventual": round(100 * correct / n) if n else None,
        "first_try": first, "hinted": hinted,
        "avg_attempts": round(sum(attempts) / len(attempts), 2) if attempts else None,
    }


def track_stats():
    out = {}
    for track in ("complexity", "pseudocode", "tn"):
        qs = db.answered_questions(track)
        total = len(db.list_exercises(track=track))
        seen = len({q["exercise_id"] for q in qs})
        solved = len({q["exercise_id"] for q in qs if q["correct"]})
        a = _agg(qs)
        a.update(total_exercises=total, seen=seen, solved=solved,
                 coverage=round(100 * solved / total) if total else 0)
        out[track] = a
    return out


def topic_stats(track=None):
    groups = defaultdict(list)
    for q in db.answered_questions(track):
        groups[q["topic"]].append(q)
    rows = []
    for topic, qs in groups.items():
        a = _agg(qs)
        a.update(topic=topic, label=TOPICS.get(topic, topic), track=qs[0]["track"])
        rows.append(a)
    rows.sort(key=lambda r: (r["accuracy"] if r["accuracy"] is not None else 101))
    return rows


def type_stats():
    groups = defaultdict(list)
    for q in db.answered_questions():
        groups[q["type"]].append(q)
    rows = []
    for t, qs in groups.items():
        a = _agg(qs)
        a.update(type=t, label=TYPES.get(t, t), track=qs[0]["track"])
        rows.append(a)
    rows.sort(key=lambda r: r["label"])
    return rows


def _pct(num, den):
    return round(100 * num / den) if den else None


def tn_stats():
    """T(n) Analysis statistics, kept separate from Big-O accuracy. Part accuracies use first attempts."""
    qs = [q for q in db.answered_questions("tn")]
    graded = [q for q in qs if q["t_first"] is not None]

    def block(items):
        g = [q for q in items if q["t_first"] is not None]
        return {
            "answered": len(items),
            "t_first": _pct(sum(q["t_first"] for q in g), len(g)),
            "theta_first": _pct(sum(q["theta_first"] for q in g), len(g)),
            "t_eventual": _pct(sum(q["t_correct"] or 0 for q in g), len(g)),
            "first_try": _pct(sum(q["first_try_correct"] for q in items), len(items)),
            "hinted": sum(1 for q in items if q["hints_used"] > 0),
            "avg_attempts": round(sum(q["attempts"] for q in items if q["attempts"]) / max(1, sum(1 for q in items if q["attempts"])), 2)
            if any(q["attempts"] for q in items) else None,
        }

    by_topic = []
    for t, label in TN_TOPICS.items():
        items = [q for q in qs if q["topic"] == t]
        row = block(items)
        row.update(topic=t, label=label)
        by_topic.append(row)
    by_diff = []
    for d in ("beginner", "intermediate", "advanced"):
        row = block([q for q in qs if q["difficulty"] == d])
        row.update(difficulty=d)
        by_diff.append(row)
    overall = block(qs)
    overall.update(correct_T=sum(1 for q in graded if q["t_correct"]), correct_theta=sum(1 for q in graded if q["theta_correct"]),
                   exercises_attempted=len({q["exercise_id"] for q in qs}),
                   open_mistakes=sum(1 for m in db.list_mistakes(track="tn") if m["status"] == "open"))
    return {"overall": overall, "by_topic": by_topic, "by_difficulty": by_diff}


def topic_accuracy_map():
    """Smoothed first-try accuracy per topic, used by adaptive practice."""
    groups = defaultdict(lambda: [0, 0])
    for q in db.answered_questions():
        groups[q["topic"]][0] += q["first_try_correct"]
        groups[q["topic"]][1] += 1
    return {t: (c + PRIOR_ACC * PRIOR_N) / (n + PRIOR_N) for t, (c, n) in groups.items()}, {t: n for t, (c, n) in groups.items()}


def session_summary(sid):
    s = db.get_session(sid)
    qs = [q for q in db.session_questions(sid) if q["attempts"] or q["revealed"]]
    a = _agg(qs)
    by_topic = defaultdict(list)
    for q in qs:
        by_topic[q["topic"]].append(q)
    difficult = []
    for t, lst in by_topic.items():
        missed = sum(1 for q in lst if not q["first_try_correct"])
        if missed:
            difficult.append({"topic": t, "label": TOPICS.get(t, t), "missed": missed, "total": len(lst),
                              "accuracy": round(100 * (len(lst) - missed) / len(lst))})
    difficult.sort(key=lambda d: (d["accuracy"], -d["missed"]))
    per_topic = [{"topic": t, "label": TOPICS.get(t, t), "total": len(l),
                  "accuracy": round(100 * sum(q["first_try_correct"] for q in l) / len(l))} for t, l in by_topic.items()]
    per_topic.sort(key=lambda d: d["accuracy"])
    return {
        "session": {"id": sid, "mode": s["mode"], "config": s["config"], "created_at": s["created_at"], "ended_at": s["ended_at"]},
        "answered": a["answered"],
        "correct": a["correct"], "incorrect": a["incorrect"],
        "first_try": a["first_try"],
        "accuracy": a["accuracy"], "eventual": a["eventual"],
        "no_hints": sum(1 for q in qs if q["correct"] and q["hints_used"] == 0),
        "after_hints": sum(1 for q in qs if q["correct"] and q["hints_used"] > 0),
        "revealed": sum(1 for q in qs if q["revealed"] and not q["correct"]),
        "avg_attempts": a["avg_attempts"],
        "difficult_topics": difficult,
        "per_topic": per_topic,
    }


# ============================================================================ selection
DIFF_LEVELS = {"beginner": (1, 2), "intermediate": (3, 4), "advanced": (5, 6)}
GEN_FAMILY = {"loops": ["single", "sequential", "conditional"], "nested": ["nested", "multivar", "dependent"],
              "mixed_complexity": ["mixed"], "big_o": ["mixed"], "mixed": ["mixed"]}


def matches_topic(ex_row, topic):
    if topic in (None, "", "mixed"):
        return True
    if topic == "mixed_complexity":
        return ex_row["track"] == "complexity"
    if topic == "pseudocode":
        return ex_row["track"] == "pseudocode"
    if topic == "tn":
        return ex_row["track"] == "tn"
    return topic in ex_row["tags"]


def matches_filters(ex_row, config):
    """Optional narrowing used when a session is started from a track page."""
    style = config.get("style")
    if style and ("course_style" in ex_row["tags"]) != (style == "course"):
        return False
    return all(config.get(key) in (None, "") or ex_row[col] == config[key]
               for key, col in (("track", "track"), ("subtopic", "topic"), ("type", "type"), ("level", "level")))


def build_pool(config):
    rows = db.list_exercises()
    diff = config.get("difficulty")
    pool = [r for r in rows if (diff in (None, "", "mixed") or r["difficulty"] == diff) and matches_topic(r, config.get("topic"))
            and matches_filters(r, config)]
    if config.get("review"):
        wanted = {m["exercise_id"] for m in db.list_mistakes() if m["status"] != "mastered"}
        allrows = db.list_exercises(source=None)
        pool = [r for r in allrows if r["id"] in wanted]
    return pool


def _generated_question(config, rng):
    if config.get("track"):
        return None  # a narrowed session only serves bank exercises that match its filters
    fams = GEN_FAMILY.get(config.get("topic") or "mixed")
    if not fams:
        return None
    lo, hi = DIFF_LEVELS.get(config.get("difficulty"), (1, 6))
    for _ in range(12):
        ex = generator.generate(rng.choice(fams), rng.randrange(10 ** 8))
        if lo <= ex["level"] <= hi:
            store_generated(ex)
            return ex["id"]
    return None


def store_generated(ex):
    from engine.catalog import difficulty_of
    ex = {k: v for k, v in ex.items() if not k.startswith("_")}
    ex["difficulty"] = difficulty_of(ex["level"])
    db.upsert_exercise(ex, "generated")
    return ex


def pick_next(session):
    cfg = session["config"]
    served = session["served"]
    rng = random.Random()
    pool = build_pool(cfg)
    if not pool and not cfg.get("review"):
        gid = _generated_question(cfg, rng)
        return gid
    fresh = [r for r in pool if r["id"] not in served]
    if not fresh:
        if cfg.get("review"):
            return None
        fresh = pool  # everything has been seen this session: allow repeats
    if not cfg.get("review") and cfg.get("topic") in GEN_FAMILY and rng.random() < 0.15:
        gid = _generated_question(cfg, rng)
        if gid:
            return gid
    if cfg.get("adaptive"):
        return adaptive_pick(fresh, rng)
    return rng.choice(fresh)["id"]


def adaptive_weights():
    acc, counts = topic_accuracy_map()
    return acc, counts


def adaptive_pick(candidates, rng):
    acc, _ = topic_accuracy_map()
    status = db.exercise_status_map()
    by_topic = defaultdict(list)
    for r in candidates:
        by_topic[r["topic"]].append(r)
    topics = list(by_topic)
    # weak topics get more weight, strong topics never drop to zero
    tw = [0.15 + (1 - acc.get(t, PRIOR_ACC)) ** 1.2 for t in topics]
    topic = rng.choices(topics, weights=tw)[0]
    a = acc.get(topic, PRIOR_ACC)
    top_level = max(r["level"] for r in by_topic[topic]) if by_topic[topic] else 6
    low_level = min(r["level"] for r in by_topic[topic]) if by_topic[topic] else 1
    target = low_level + a * (top_level - low_level)  # stronger topic -> harder levels
    ews = []
    for r in by_topic[topic]:
        w = math.exp(-abs(r["level"] - target) / 1.5)
        st = status.get(r["id"])
        if st == "missed":
            w *= 2.5
        elif st is None:
            w *= 1.5
        elif st == "solved" or st == "mastered":
            w *= 0.5
        ews.append(w)
    return rng.choices(by_topic[topic], weights=ews)[0]["id"]


def weak_topic_table():
    acc, counts = topic_accuracy_map()
    rows = []
    for t, label in TOPICS.items():
        a = acc.get(t)
        rows.append({"topic": t, "label": label, "accuracy": round(100 * a) if a is not None else None,
                     "answered": counts.get(t, 0), "weight": round(0.15 + (1 - (a if a is not None else PRIOR_ACC)) ** 1.2, 2)})
    total = sum(r["weight"] for r in rows)
    for r in rows:
        r["share"] = round(100 * r["weight"] / total)
    rows.sort(key=lambda r: (r["accuracy"] if r["accuracy"] is not None else 70))
    return rows


__all__ = ["track_stats", "topic_stats", "type_stats", "session_summary", "pick_next", "weak_topic_table",
           "store_generated", "SESSION_TOPICS"]
