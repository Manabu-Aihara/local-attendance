from datetime import datetime

# class OutputApprovalDataConversion():
    
def convert_str_to_date(arg: datetime) -> datetime:
    if arg != '':
        return arg
    else:
        conv_date_empty = arg.replace('%Y-%m-%d', '')
        return conv_date_empty

def convert_str_to_time(arg: datetime) -> datetime:
    if arg != '':
        return arg
    else:
        conv_time_empty = arg.replace('%H:%M', '')      
        return conv_time_empty
    
def toggle_notification_type(table, arg: str | int) -> int | str:
    # 数値を内容名に置き換える
    if type(arg) is int:
        content_value = table.query.get(arg)
        return content_value.NAME
    elif type(arg) is str:
        content_value = table.query.filter(table.NAME==arg).first()
        return content_value.CODE
    else:
        TypeError("intかstrのどちらかです")

