import threading


class TelemetryTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self.total_input_words: int = 0
        self.total_output_words: int = 0
        self.discards_count: int = 0
        self.adds_count: int = 0
        self.conflicts_count: int = 0

    def record_input_words(self, count: int):
        with self._lock:
            self.total_input_words += count

    def record_output_words(self, count: int):
        with self._lock:
            self.total_output_words += count

    def record_discard(self):
        with self._lock:
            self.discards_count += 1

    def record_add(self):
        with self._lock:
            self.adds_count += 1

    def record_conflict(self):
        with self._lock:
            self.conflicts_count += 1

    def get_token_savings_percentage(self) -> float:
        with self._lock:
            if self.total_input_words == 0:
                return 0.0
            saved = self.total_input_words - self.total_output_words
            return round(max(0.0, (saved / self.total_input_words) * 100.0), 2)

    def get_summary(self) -> dict:
        with self._lock:
            savings = self.get_token_savings_percentage()
            return {
                "total_input_words": self.total_input_words,
                "total_output_words": self.total_output_words,
                "facts_added": self.adds_count,
                "facts_discarded_duplicate": self.discards_count,
                "facts_conflicted": self.conflicts_count,
                "token_savings_pct": savings,
                "token_reduction_pct": savings,
                "total_facts_extracted": self.adds_count + self.discards_count + self.conflicts_count
            }


    def print_summary(self):
        saved_pct = self.get_token_savings_percentage()
        print("\n" + "="*60)
        print("OPEN-RESEARCH-LITE TELEMETRY SUMMARY")
        print("="*60)
        print(f"  • Raw Input Words Intercepted : {self.total_input_words:,}")
        print(f"  • Output Diff Words Sent      : {self.total_output_words:,}")
        print(f"  • Token Reduction Percentage  : {saved_pct}% Saved")
        print(f"  • Facts Added (DIFF_ADD)      : {self.adds_count}")
        print(f"  • Facts Discarded (DISCARD)   : {self.discards_count}")
        print(f"  • Conflicts Flagged (CONFLICT): {self.conflicts_count}")
        print("="*60 + "\n")
