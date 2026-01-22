class IssueCollector:
    """In-memory accumulator for parser issues."""

    def __init__(self):
        self.items: list[dict] = []

    def add(
        self,
        category: str,
        message: str,
        level: str = "warning",
        row_index: int | None = None,
        row_repr: str | None = None,
        row_data: dict | None = None,
        extra: dict | None = None,
    ):
        self.items.append(
            {
                "category": category,
                "message": message,
                "level": level,
                "row_index": row_index,
                "row_repr": row_repr,
                "row_data": row_data,
                "extra": extra or {},
            }
        )

    def by_category(self) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for item in self.items:
            grouped.setdefault(item["category"], []).append(item)
        return grouped

    def has_items(self) -> bool:
        return bool(self.items)
