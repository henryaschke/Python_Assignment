from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string in YYYY-MM-DD format to a datetime object."""
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def format_datetime(dt: datetime) -> str:
    """Format a datetime object as an ISO string."""
    if not dt:
        return None
    return dt.isoformat()

def calculate_date_range(days: int) -> Dict[str, str]:
    """Calculate a date range from today going back a specified number of days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d')
    }

def paginate_results(results: List[Dict[str, Any]], page: int = 1, page_size: int = 50) -> Dict[str, Any]:
    """Paginate a list of results."""
    # Calculate total pages
    total_results = len(results)
    total_pages = (total_results + page_size - 1) // page_size  # Ceiling division
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # Calculate start and end indices
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_results)
    
    # Get subset of results for the current page
    page_results = results[start_idx:end_idx] if start_idx < total_results else []
    
    return {
        "total": total_results,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "results": page_results
    }

def format_market_period(hour: int) -> str:
    """Format a market period string from an hour (0-23)."""
    if not isinstance(hour, int) or hour < 0 or hour > 23:
        return None
    
    return f"{hour:02d}:00-{(hour+1)%24:02d}:00" 