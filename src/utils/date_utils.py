from datetime import datetime

def to_iso_date(date_str):
    """Convert a date string to ISO format (YYYY-MM-DD) if possible."""
    date_formats = [
        "%Y%m%d",       # 20240214
        "%d-%m-%Y",     # 14-02-2024
        "%d.%m.%Y",     # 14.02.2024
        "%m/%d/%Y",     # 02/14/2024 (US format)
        "%Y/%m/%d",     # 2024/02/14
        "%B %d, %Y",    # February 14, 2024
        "%d %B %Y",     # 14 February 2024
        "%Y-%m-%d",     # 2024-02-14 (already ISO)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass  # Try the next format

    raise ValueError(f"Could not parse date: {date_str}")