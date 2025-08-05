"""Utility functions for Semantic Scholar MCP Server."""

from typing import Any

from .models import PublicationType, SearchFilters


def parse_year_range(year_range: str) -> tuple[int, int] | None:
    """Parse year range string like '2020-2023' into tuple."""
    if not year_range:
        return None

    if "-" in year_range:
        parts = year_range.split("-")
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return (start, end)
            except ValueError:
                pass

    return None


def create_search_filters(
    publication_types: list[str] | None = None,
    fields_of_study: list[str] | None = None,
    year_range: str | None = None,
    min_citation_count: int | None = None,
    min_influential_citation_count: int | None = None,
    venue_id: str | None = None,
    open_access_only: bool = False,
) -> SearchFilters | None:
    """Create SearchFilters object from parameters."""
    if not any(
        [
            publication_types,
            fields_of_study,
            year_range,
            min_citation_count,
            min_influential_citation_count,
            venue_id,
            open_access_only,
        ]
    ):
        return None

    return SearchFilters(
        publication_types=[PublicationType(pt) for pt in (publication_types or [])],
        fields_of_study=fields_of_study,
        year_range=parse_year_range(year_range) if year_range else None,
        min_citation_count=min_citation_count,
        min_influential_citation_count=min_influential_citation_count,
        venue_id=venue_id,
        open_access_only=open_access_only,
    )


def format_success_response(data: Any) -> dict[str, Any]:
    """Format successful MCP response."""
    return {
        "success": True,
        "data": data,
    }


def format_error_response(
    error: Exception, error_type: str = "error"
) -> dict[str, Any]:
    """Format error MCP response."""
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": str(error),
        },
    }


def format_paginated_response(
    items: list[Any],
    total: int,
    offset: int,
    limit: int,
    has_more: bool | None = None,
) -> dict[str, Any]:
    """Format paginated response."""
    if has_more is None:
        has_more = (offset + limit) < total

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
    }


def extract_field_value(field_obj: Any) -> Any:
    """Extract actual value from Pydantic Field object or return the value itself."""
    # If it's already a simple value, return it
    if isinstance(field_obj, str | int | float | bool | list | dict | type(None)):
        return field_obj

    # Check for various Field object attributes
    if hasattr(field_obj, "default"):
        return field_obj.default
    if hasattr(field_obj, "value"):
        return field_obj.value
    if hasattr(field_obj, "__value__"):
        return field_obj.__value__

    # If it's a FieldInfo object from Pydantic
    if hasattr(field_obj, "__class__") and field_obj.__class__.__name__ == "FieldInfo":
        if hasattr(field_obj, "default"):
            return field_obj.default

    # Fallback - return the object itself
    return field_obj


def validate_batch_size(ids: list[str], max_size: int = 500) -> None:
    """Validate batch size limits."""
    if len(ids) > max_size:
        raise ValueError(f"Too many IDs: {len(ids)}, maximum allowed: {max_size}")


def validate_publication_types(publication_types: list[str]) -> list[PublicationType]:
    """Validate and convert publication types."""
    if not publication_types:
        return []

    valid_types = []
    for pt in publication_types:
        try:
            valid_types.append(PublicationType(pt))
        except ValueError:
            # Skip invalid publication types
            continue

    return valid_types


def extract_nested_field(data: dict[str, Any], field_path: str) -> Any:
    """
    Extract nested field value using dot notation.

    Examples:
        - "title" -> data["title"]
        - "authors.name" -> [author["name"] for author in data["authors"]]
        - "publicationVenue.name" -> data["publicationVenue"]["name"]

    Args:
        data: The data dictionary to extract from
        field_path: The dot-notation field path

    Returns:
        The extracted value or None if not found
    """
    if not field_path or not data:
        return None

    parts = field_path.split(".")
    current = data

    for i, part in enumerate(parts):
        if current is None:
            return None

        # Handle list case - extract field from all items
        if isinstance(current, list):
            # If we're at a list and have more parts, extract from each item
            remaining_path = ".".join(parts[i:])
            return [
                extract_nested_field(item, remaining_path)
                for item in current
                if item is not None
            ]

        # Handle dict case
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)

    return current


def apply_field_selection(
    data: dict[str, Any], fields: list[str] | None
) -> dict[str, Any]:
    """
    Apply field selection to data using dot notation.

    Args:
        data: The complete data dictionary
        fields: List of fields to include (None means all fields)

    Returns:
        Filtered data dictionary with only requested fields
    """
    if not fields:
        return data

    result = {}

    for field in fields:
        # Handle nested fields
        if "." in field:
            # For nested fields, we need to maintain the structure
            parts = field.split(".")
            value = extract_nested_field(data, field)

            if value is not None:
                # Reconstruct the nested structure
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
        else:
            # Simple field
            if field in data:
                result[field] = data[field]

    return result
