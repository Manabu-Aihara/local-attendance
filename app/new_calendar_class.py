import calendar

def print_monthrange():
  for w, l in calendar.monthrange(2023, 9):
    print(f"曜日：{w}-日：{l}")
  # return calendar.monthrange(2023, 9)[1]
