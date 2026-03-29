import streamlit as st
from datetime import date, time

from pawpal_system import Frequency, Owner, Pet, Scheduler, Status, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# ---------------------------------------------------------------------------

def _init_state() -> None:
    if "owner"     not in st.session_state: st.session_state.owner     = None
    if "scheduler" not in st.session_state: st.session_state.scheduler = None
    if "raw_tasks" not in st.session_state: st.session_state.raw_tasks = []

_init_state()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIORITY_MAP   = {"Low": 1, "Medium": 3, "High": 5}
PRIORITY_LABEL = {1: "🟢 Low", 3: "🟡 Medium", 5: "🔴 High"}
FREQUENCY_OPTS = {f.value.replace("_", " ").title(): f for f in Frequency}

STATUS_ICON = {
    Status.PENDING:     "🟡 Pending",
    Status.IN_PROGRESS: "🔵 In Progress",
    Status.DONE:        "✅ Done",
    Status.SKIPPED:     "⏭️ Skipped",
}

STATUS_FILTER_MAP = {
    "All":         None,
    "Pending":     Status.PENDING,
    "In Progress": Status.IN_PROGRESS,
    "Done":        Status.DONE,
    "Skipped":     Status.SKIPPED,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_owner_and_scheduler(owner_name, pet_name, species, breed, age, raw_tasks):
    owner = Owner(name=owner_name)
    pet   = Pet(name=pet_name, species=species, breed=breed, age=age)
    for rt in raw_tasks:
        pet.add_task(Task(
            name           = rt["title"],
            description    = rt.get("description", ""),
            duration       = rt["duration"],
            priority       = PRIORITY_MAP[rt["priority"]],
            frequency      = FREQUENCY_OPTS[rt["frequency"]],
            scheduled_time = rt.get("scheduled_time"),
            due_date       = date.today(),
        ))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    sched.generate_schedule()
    return owner, sched


def _tasks_to_table_rows(tasks: list) -> list[dict]:
    """Convert Task objects into display-friendly dicts for st.table."""
    rows = []
    for t in tasks:
        rows.append({
            "Status":    STATUS_ICON[t.status],
            "Task":      t.name,
            "Priority":  PRIORITY_LABEL[t.priority],
            "Duration":  f"{t.duration} min",
            "Frequency": t.frequency.value.replace("_", " ").title(),
            "Time":      t.time_label,
        })
    return rows

# ---------------------------------------------------------------------------
# Sidebar — owner / pet / task input
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("👤 Owner & Pet")
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name   = st.text_input("Pet name",   value="Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    breed      = st.text_input("Breed (optional)")
    age        = st.number_input("Age (years)", min_value=0.0, max_value=30.0,
                                  value=3.0, step=0.5)

    st.divider()
    st.header("➕ New Task")
    task_title  = st.text_input("Title",       value="Morning walk")
    description = st.text_input("Description", value="")
    duration    = st.number_input("Duration (min)", min_value=1, max_value=300, value=20)
    priority    = st.selectbox("Priority",  list(PRIORITY_MAP.keys()), index=2)
    frequency   = st.selectbox("Frequency", list(FREQUENCY_OPTS.keys()), index=1)
    use_time    = st.checkbox("Set a scheduled time")
    sched_time  = st.time_input("Scheduled time", value=time(8, 0)) if use_time else None

    if st.button("Add Task ➕", use_container_width=True, type="primary"):
        st.session_state.raw_tasks.append({
            "title": task_title, "description": description,
            "duration": int(duration), "priority": priority,
            "frequency": frequency, "scheduled_time": sched_time,
        })
        st.success(f"Added "{task_title}"")

    if st.button("Clear all tasks 🗑️", use_container_width=True):
        st.session_state.raw_tasks = []
        st.session_state.owner     = None
        st.session_state.scheduler = None
        st.rerun()

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+")
st.caption("Pet care scheduling, powered by your Scheduler backend.")
st.divider()

# ---------------------------------------------------------------------------
# Staged tasks preview
# ---------------------------------------------------------------------------

st.subheader("📋 Staged Tasks")

if not st.session_state.raw_tasks:
    st.info("No tasks yet — add some in the sidebar, then generate a schedule.")
else:
    preview_rows = [
        {
            "Title":    rt["title"],
            "Duration": f"{rt['duration']} min",
            "Priority": rt["priority"],
            "Freq":     rt["frequency"],
            "Time":     rt["scheduled_time"].strftime("%H:%M") if rt["scheduled_time"] else "—",
        }
        for rt in st.session_state.raw_tasks
    ]
    st.table(preview_rows)                          # clean, bordered read-only table

    if st.button("🗓️ Generate Schedule", type="primary", use_container_width=True):
        try:
            owner, scheduler = _build_owner_and_scheduler(
                owner_name, pet_name, species, breed, age,
                st.session_state.raw_tasks,
            )
            st.session_state.owner     = owner
            st.session_state.scheduler = scheduler
            st.success("Schedule generated successfully!")
        except Exception as exc:
            st.error(f"Could not build schedule: {exc}")

# ---------------------------------------------------------------------------
# Everything below only renders once a schedule exists
# ---------------------------------------------------------------------------

scheduler: Scheduler | None = st.session_state.scheduler
owner:     Owner     | None = st.session_state.owner

if scheduler is None:
    st.stop()

pet = owner.all_pets()[0]

st.divider()

# ── Pet profile ─────────────────────────────────────────────────────────────
st.subheader(f"🐾 {pet.name}")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Species", pet.species.title())
p2.metric("Breed",   pet.breed or "—")
p3.metric("Age",     f"{pet.age}y")
p4.metric("Tasks",   len(pet.all_tasks()))

st.divider()

# ── Conflict warnings ────────────────────────────────────────────────────────
st.subheader("⚠️ Conflict Check")
warnings = scheduler.warn_conflicts()
if warnings:
    for w in warnings:
        st.warning(w)
else:
    st.success("✓ No scheduling conflicts detected.")

st.divider()

# ── View controls ─────────────────────────────────────────────────────────────
st.subheader("📅 Schedule")

vc1, vc2 = st.columns(2)
with vc1:
    sort_mode = st.radio("Sort by", ["Priority", "Scheduled time"], horizontal=True)
with vc2:
    show_filter = st.selectbox("Filter by status", list(STATUS_FILTER_MAP.keys()))

status_filter = STATUS_FILTER_MAP[show_filter]

# Resolve display list using Scheduler methods
if sort_mode == "Scheduled time":
    display_tasks = scheduler.sort_by_time()          # Scheduler.sort_by_time()
else:
    display_tasks = list(scheduler)                   # __iter__ — priority order

if status_filter is not None:
    keyset = {t.task_id for t in scheduler.filter_tasks(status=status_filter)}
    display_tasks = [t for t in display_tasks if t.task_id in keyset]

# ── Schedule table ────────────────────────────────────────────────────────────
if not display_tasks:
    st.warning("No tasks match the current filter.")
else:
    st.table(_tasks_to_table_rows(display_tasks))     # st.table for clean grid

# ── Per-task action buttons (only actionable tasks) ──────────────────────────
actionable = [t for t in display_tasks
              if t.status in (Status.PENDING, Status.IN_PROGRESS)]
if actionable:
    st.markdown("**Advance a task:**")
    for task in actionable:
        btn_label = (
            f"▶ Start — {task.name}"        if task.status == Status.PENDING else
            f"✔ Complete — {task.name}"
        )
        col_btn, col_skip = st.columns([3, 1])
        with col_btn:
            if st.button(btn_label, key=f"adv_{task.task_id}", use_container_width=True):
                try:
                    scheduler.advance(task.task_id)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with col_skip:
            if task.status == Status.PENDING:
                if st.button("⏭ Skip", key=f"skip_{task.task_id}", use_container_width=True):
                    scheduler.skip(task.task_id)
                    st.rerun()

st.divider()

# ── Completion summary ────────────────────────────────────────────────────────
st.subheader("📊 Summary")

summary = scheduler.completion_summary()
m1, m2, m3, m4 = st.columns(4)
m1.metric("🟡 Pending",     summary["pending"])
m2.metric("🔵 In Progress", summary["in_progress"])
m3.metric("✅ Done",        summary["done"])
m4.metric("⏭️ Skipped",     summary["skipped"])

remaining = scheduler.total_duration(status=Status.PENDING)
total     = scheduler.total_duration()
if total:
    pct_done = int((1 - remaining / total) * 100)
    st.progress(pct_done, text=f"{pct_done}% of scheduled time completed")

st.caption(f"⏱️ Time remaining (pending tasks): **{remaining} min**")

# ── Overdue tasks ─────────────────────────────────────────────────────────────
overdue = scheduler.overdue()
if overdue:
    st.warning(f"⚠️ {len(overdue)} overdue task(s):")
    st.table(_tasks_to_table_rows(overdue))
else:
    st.success("✓ No overdue tasks.")

# ── Schedule history ──────────────────────────────────────────────────────────
history = scheduler.get_history()
if history:
    with st.expander(f"🕑 Schedule history ({len(history)} snapshot(s))"):
        for snap in reversed(history):
            st.caption(f"Snapshot at {snap['timestamp'].strftime('%H:%M:%S')}")
            if snap["schedule"]:
                st.table(_tasks_to_table_rows(snap["schedule"]))
            else:
                st.info("Empty snapshot.")