"""
State machine state emoji definitions.

Covers all StateMachine states and transitions.

Usage:
    >>> from shared.reporter.emojis.states import StateEmoji
    >>> print(f"{StateEmoji.INIT} Initializing state machine")
    🆕 Initializing state machine
"""

from shared.reporter.emojis.base_emojis import ComponentEmoji


class StateEmoji(ComponentEmoji):
    """
    State machine states and transitions.

    Categories:
        - States: START, INIT, UPDATE, etc.
        - Movements: Left, right, tick
        - Control: Stop, pause, resume
    """

    # ============================================================
    # Core States
    # ============================================================

    START = "🟢"  # START state
    INIT = "🆕"  # INIT state
    UPDATE = "🔄"  # UPDATE state
    TICK = "⏱️"  # TICK state
    HEARTBEAT = "❤️"  # HEARTBEAT state
    RESET = "♻️"  # RESET state
    DONE = "✅"  # DONE state

    # ============================================================
    # Movement States
    # ============================================================

    MOVED_LEFT = "⬅️"  # MOVED_LEFT state
    MOVED_RIGHT = "➡️"  # MOVED_RIGHT state
    NO_MOVEMENT = "⏸️"  # No bin change

    # ============================================================
    # Control States
    # ============================================================

    STOP = "⏹️"  # STOP state
    PAUSE = "⏸️"  # PAUSE state
    RESUME = "▶️"  # RESUME state

    # ============================================================
    # Transitions
    # ============================================================

    TRANSITION = "🔀"  # State transition
    REQUESTED = "📝"  # State change requested
    APPLIED = "✔️"  # State change applied
