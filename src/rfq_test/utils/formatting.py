"""Utilities for formatting transaction events and other data structures."""

from typing import Any, Dict, List


def format_event(event: Dict[str, Any], index: int = None) -> str:
    """Format a transaction event for pretty printing.
    
    Args:
        event: Event dictionary with 'type' and 'attributes'
        index: Optional event index number
        
    Returns:
        Formatted string representation
    """
    event_type = event.get('type', 'unknown')
    attrs = event.get('attributes', [])
    
    lines = []
    prefix = f"  {index}. " if index is not None else "  "
    lines.append(f"{prefix}📌 {event_type}")
    
    if attrs:
        # Group attributes by key for better readability
        attr_dict = {}
        for attr in attrs:
            if isinstance(attr, dict):
                key = attr.get('key', '')
                value = attr.get('value', '')
                # Decode base64 strings if needed
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                attr_dict[key] = value
        
        # Show most important attributes first
        priority_keys = ['sender', 'recipient', 'receiver', 'spender', 'maker', 'taker', 
                        'granter', 'grantee', 'amount', 'action', 'module']
        
        shown = set()
        for key in priority_keys:
            if key in attr_dict:
                value = str(attr_dict[key])
                if len(value) > 80:
                    value = value[:80] + "..."
                lines.append(f"     └─ {key}: {value}")
                shown.add(key)
        
        # Show remaining attributes (limit to 3 more)
        remaining = [(k, v) for k, v in attr_dict.items() if k not in shown]
        for key, value in remaining[:3]:
            value = str(value)
            if len(value) > 80:
                value = value[:80] + "..."
            lines.append(f"     └─ {key}: {value}")
        
        if len(remaining) > 3:
            lines.append(f"     └─ ... ({len(remaining) - 3} more attributes)")
    
    return "\n".join(lines)


def format_events_summary(events: List[Dict[str, Any]], max_events: int = 10) -> str:
    """Format a list of events for pretty printing.
    
    Args:
        events: List of event dictionaries
        max_events: Maximum number of events to show
        
    Returns:
        Formatted string representation
    """
    if not events:
        return "  ⚠️  No events found in transaction"
    
    lines = [f"  📦 Transaction Events ({len(events)} total):"]
    
    for i, event in enumerate(events[:max_events], 1):
        lines.append(format_event(event, index=i))
    
    if len(events) > max_events:
        lines.append(f"  ... ({len(events) - max_events} more events)")
    
    return "\n".join(lines)
