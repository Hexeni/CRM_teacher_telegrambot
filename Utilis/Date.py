import datetime


class Date:
    @staticmethod
    def find_next_weekday(target_weekday: int):
        today = datetime.date.today()
        today_weekday = today.weekday()

        days_ahead = (target_weekday-today_weekday) % 7

        if days_ahead % 7 == 0:
            days_ahead = 7

        return today + datetime.timedelta(days_ahead)

    @staticmethod
    def parse_user_datetime(text: str):
        try:
            dt = datetime.datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
            return dt
        except ValueError:
            return None


