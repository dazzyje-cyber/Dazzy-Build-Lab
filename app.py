"""
Dazzy's Build Lab — interactive attachment simulator
Run with:  streamlit run app.py
(install once with:  pip install streamlit)
"""

import streamlit as st

# ---------------------------------------------------------------------------
# GUN DATA
# Add a new gun each week by adding one entry here.
# base stats are 0-100 scale except mag (round count) and ttk (seconds, lower=better)
# ---------------------------------------------------------------------------
GUNS = {
    "INP9": {
        "type": "SMG",
        "base": {"range": 25, "recoil_control": 80, "mobility": 78, "mag": 26, "ttk": 0.42},
        "note": "Highest recoil-control stat of any SMG in the game. Natural close-range weapon. "
                "Small base magazine is its real weakness. Barrels generally work against it — "
                "the Skeleton Barrel is the one mild exception.",
    },
    "Bizon": {
        "type": "SMG",
        "base": {"range": 30, "recoil_control": 70, "mobility": 70, "mag": 32, "ttk": 0.40},
        "note": "Current meta close-quarters pick. Strong accuracy retention at range for an SMG.",
    },
    "HK416": {
        "type": "AR",
        "base": {"range": 55, "recoil_control": 65, "mobility": 55, "mag": 30, "ttk": 0.38},
        "note": "All-round rifle. Controllable recoil, forgiving at mid-range.",
    },
    "AK47": {
        "type": "AR",
        "base": {"range": 55, "recoil_control": 40, "mobility": 50, "mag": 30, "ttk": 0.34},
        "note": "High-skill, high-reward. Harder to control but strong first-shot damage.",
    },
}

# ---------------------------------------------------------------------------
# ATTACHMENT DATA
# Each value is a delta applied to the gun's base stats.
# ---------------------------------------------------------------------------
ATTACHMENTS = {
    "Muzzle": {
        "None": {},
        "Suppressor": {"range": -5, "recoil_control": 5, "mobility": 0},
        "Compensator": {"range": 0, "recoil_control": 15, "mobility": -2},
        "CQB Muzzle Device": {"recoil_control": 10, "mobility": 5},
    },
    "Barrel": {
        "None": {},
        "Range Extension Barrel": {"range": 20, "mobility": -10},
        "Skeleton Barrel": {"range": 8, "mobility": -3},
    },
    "Underbarrel": {
        "None": {},
        "Extended Vertical Grip": {"recoil_control": 12, "mobility": -3},
        "Angled Grip": {"mobility": 8, "recoil_control": 3},
    },
    "Optic": {
        "None / Iron Sights": {},
        "Red Dot": {"range": 2},
        "Reflex Optic": {"range": 5},
        "2x-3x Scope": {"range": 15, "mobility": -5},
    },
    "Stock": {
        "None": {},
        "Balanced Stock": {"recoil_control": 8, "mobility": 2},
        "Heavy Stock": {"recoil_control": 15, "mobility": -8},
    },
    "Magazine": {
        "Standard Mag": {},
        "Extended Mag": {"mag": 14, "mobility": -3},
        "Quickdraw Mag": {"mobility": 5, "mag": -4},
    },
}

# Attachments that fight a gun's natural role — shown as a heads-up, not a block.
CAUTION_RULES = {
    "INP9": {"Barrel": ["Range Extension Barrel"]},  # only Skeleton Barrel is fine
}


def classify_build(stats):
    """Very simple rule of thumb, not exact game math — just a directional read."""
    range_score = stats["range"]
    recoil_score = stats["recoil_control"]
    mobility_score = stats["mobility"]

    if range_score >= recoil_score and range_score >= mobility_score:
        return "Long Range build", "Best for engaging targets past mid-range. You'll trade some mobility for reach."
    if mobility_score >= recoil_score and mobility_score >= range_score:
        return "Close Range / Rush build", "Fast time-to-first-shot, built for aggressive close-quarters play."
    return "Stable Recoil build", "Steadiest spray pattern — best if you want consistency over speed or range."


def show_welcome_page():
    """Animated landing page — shown once per session until a name is entered."""
    st.markdown(
        """
        <style>
        @keyframes fadeSlideIn {
            0%   { opacity: 0; transform: translateY(25px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes glow {
            0%, 100% { text-shadow: 0 0 10px #ff4b4b, 0 0 20px #ff4b4b; }
            50%      { text-shadow: 0 0 20px #ff914d, 0 0 35px #ff914d; }
        }
        .welcome-title {
            font-size: 3em;
            font-weight: 800;
            text-align: center;
            animation: fadeSlideIn 1s ease-out, glow 2.5s ease-in-out infinite;
            margin-bottom: 0;
        }
        .welcome-subtitle {
            font-size: 1.3em;
            text-align: center;
            color: #cccccc;
            animation: fadeSlideIn 1.2s ease-out;
            margin-top: 0;
            margin-bottom: 2em;
        }
        .name-prompt {
            text-align: center;
            font-size: 1.1em;
            animation: fadeSlideIn 1.6s ease-out;
        }
        </style>
        <div class="welcome-title">🔫 Welcome to Dazzy's Build Lab</div>
        <div class="welcome-subtitle">Bloodstrike Gun Modification</div>
        <div class="name-prompt">Enter your name to get started</div>
        """,
        unsafe_allow_html=True,
    )

    name = st.text_input("Your name", key="name_input", label_visibility="collapsed", placeholder="Type your name here...")

    if st.button("Enter the Lab", use_container_width=True):
        if name.strip():
            st.session_state["player_name"] = name.strip()
            st.rerun()
        else:
            st.warning("Type your name first so I know who's building.")


def main():
    st.set_page_config(page_title="Dazzy's Build Lab", page_icon="🔫", layout="centered")

    # Gate the whole app behind the animated welcome page until a name is set
    if "player_name" not in st.session_state:
        show_welcome_page()
        return

    st.markdown(
        f"""
        <style>
        @keyframes fadeIn {{ 0% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
        .greet {{ animation: fadeIn 1s ease-in; font-size: 1.2em; margin-bottom: 0.5em; }}
        </style>
        <div class="greet">👋 Welcome back, <b>{st.session_state['player_name']}</b> — let's build something.</div>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔫 Dazzy's Build Lab")
    st.caption(
        "Pick a gun and attachments, see what build you've made. "
        "Stat model is simplified for teaching purposes, not exact in-game math."
    )

    gun_name = st.selectbox("Gun", list(GUNS.keys()))
    gun = GUNS[gun_name]
    st.info(gun["note"])

    st.subheader("Attachments")
    chosen = {}
    cols = st.columns(2)
    slots = list(ATTACHMENTS.keys())
    for i, slot in enumerate(slots):
        with cols[i % 2]:
            chosen[slot] = st.selectbox(slot, list(ATTACHMENTS[slot].keys()), key=slot)

    # caution flags
    rules = CAUTION_RULES.get(gun_name, {})
    for slot, bad_choices in rules.items():
        if chosen.get(slot) in bad_choices:
            st.warning(
                f"Heads up: {chosen[slot]} doesn't play to {gun_name}'s strengths based on current "
                f"weapon data — you'll still see the stat effect below, but it's fighting the gun's natural role."
            )

    # compute stats
    stats = dict(gun["base"])
    for slot, choice in chosen.items():
        deltas = ATTACHMENTS[slot][choice]
        for stat, delta in deltas.items():
            stats[stat] = stats.get(stat, 0) + delta

    st.subheader("Resulting stats")
    display_stats = {k: v for k, v in stats.items() if k != "ttk"}
    st.bar_chart(display_stats)
    st.metric("Estimated TTK (lower is faster)", f'{stats["ttk"]:.2f}s')
    st.metric("Magazine size", int(stats["mag"]))

    build_type, build_desc = classify_build(stats)
    st.subheader(f"📋 Build type: {build_type}")
    st.write(build_desc)


if __name__ == "__main__":
    main()
            
