from dateutil.relativedelta import relativedelta

# Existing function

def parse_date_from_duration(duration):
    # Assuming 'duration' is a timedelta or similar object
    start_date = datetime.utcnow()  # This would typically be your current date
    new_date = start_date + duration
    return new_date

# Updated function to include 2 days and 5 hours offset

def parse_date_from_duration_with_offset(duration):
    offset = relativedelta(days=2, hours=5)
    new_date_with_offset = parse_date_from_duration(duration) + offset
    return new_date_with_offset
