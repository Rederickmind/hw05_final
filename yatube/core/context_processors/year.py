from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    current_dateTime = datetime.now()
    year = int(current_dateTime.year)
    return {
        'year': year,
    }
