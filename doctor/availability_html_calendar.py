# Month grid via calendar.HTMLCalendar (Python stdlib), following the pattern discussed at:
# https://stackoverflow.com/q/74084453 (CC BY-SA 4.0) — ListView + HTMLCalendar().formatmonth.
import calendar
import datetime


class AvailabilityHTMLCalendar(calendar.HTMLCalendar):
    """Renders one month as an HTML <table> with selectable in-range day cells."""

    cssclass_month = 'availability-htmlcal-table month'

    def __init__(self, range_start, range_end, today, firstweekday=calendar.MONDAY):
        super().__init__(firstweekday)
        self.range_start = range_start
        self.range_end = range_end
        self.today = today

    def formatmonthname(self, theyear, themonth, withyear=True):
        # Month/year is shown by the separate <input type="month"> control.
        return ''

    def formatmonth(self, theyear, themonth, withyear=True):
        self._display_year = theyear
        self._display_month = themonth
        lines = [
            f'<table class="{self.cssclass_month}" role="grid" aria-label="Availability calendar">',
        ]
        head = self.formatmonthname(theyear, themonth, withyear=withyear)
        if head.strip():
            lines.append(head)
        lines.append(self.formatweekheader())
        for week in self.monthdays2calendar(theyear, themonth):
            lines.append(self.formatweek(week))
        lines.append('</table>')
        return '\n'.join(lines)

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday availability-cal-noday">&nbsp;</td>'

        y, m = self._display_year, self._display_month
        dt = datetime.date(y, m, day)
        iso = dt.isoformat()
        in_range = self.range_start <= dt <= self.range_end
        dow = dt.strftime('%a')

        if not in_range:
            return (
                '<td class="noday availability-cal-out" data-iso="'
                f'{iso}"><span class="availability-cal-out-inner">'
                f'<span class="availability-cal-dow">{dow}</span>'
                f'<span class="availability-cal-dom">{day}</span>'
                '</span></td>'
            )

        is_today = ' availability-cal-is-today' if dt == self.today else ''
        return (
            '<td class="availability-cal-selectable'
            f'{is_today}"><button type="button" class="availability-cal-day" '
            f'data-iso="{iso}" aria-label="{dow} {iso}">'
            '<span class="availability-cal-cell-inner">'
            f'<span class="availability-cal-dow">{dow}</span>'
            f'<span class="availability-cal-dom">{day}</span>'
            '</span></button></td>'
        )
