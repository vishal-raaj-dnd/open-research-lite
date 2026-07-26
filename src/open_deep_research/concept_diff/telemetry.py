"""Telemetry Tracker for DeepResearch-Lite.

Tracks cumulative raw words intercepted, output words generated,
token savings percentages, and fact classification counts.
"""

from typing import Dict


class TelemetryTracker:
    """Tracks token reduction performance and statistics during research execution."""

    def __init__(self):
        self.total_input_words: int = 0
        self.total_output_words: int = 0
        self.discards_count: int = 0
        self.adds_count: int = 0
        self.conflicts_count: int = 0

    def record_input_words(self, count: int):
        self.total_input_words += count

    def record_output_words(self, count: int):
        self.total_output_words += count

    def record_discard(self):
        self.discards_count += 1

    def record_add(self):
        self.adds_count += 1

    def record_conflict(self):
        self.conflicts_count += 1

    def get_token_savings_percentage(self) -> float:
        if self.total_input_words == 0:
            return 0.0
        saved = self.total_input_words - self.total_output_words
        return round(max(0.0, (saved / self.total_input_words) * 100.0), 2)

    def print_summary(self):
        saved_pct = self.get_token_savings_percentage()
        print("\n" + "="*60)
        print("📊 DEEPRESEARCH-LITE TELEMETRY SUMMARY")
        print("="*60)
        print(f"  • Raw Input Words Intercepted : {self.total_input_words:,}")
        print(f"  • Output Diff Words Sent      : {self.total_output_words:,}")
        print(f"  • Token Reduction Percentage  : {saved_pct}% Saved ⚡")
        print(f"  • Facts Added (DIFF_ADD)      : {self.adds_count}")
        print(f"  • Facts Discarded (DISCARD)   : {self.discards_count}")
        print(f"  • Conflicts Flagged (CONFLICT): {self.conflicts_count}")
        print("="*60 + "\n")
