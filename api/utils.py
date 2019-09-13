import datetime


def get_month_parameter(request):
    """helper function for klubi_demoshow and scenesat_monthly:
    extract a 'month' param from the request and return start_date/end date"""
    try:
        start_date = datetime.datetime.strptime(request.GET['month'], '%Y-%m').date()
    except (KeyError, ValueError):
        this_month = datetime.date.today().replace(day=1)
        # find last month by subtracting 7 days from start of this month, and taking
        # first day of the resulting month. ugh.
        start_date = (this_month - datetime.timedelta(days=7)).replace(day=1)

    # there must be a less horrible way to add one month, surely...?
    end_date = (start_date + datetime.timedelta(days=40)).replace(day=1)

    return (start_date, end_date)
