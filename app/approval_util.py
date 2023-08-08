from datetime import datetime

# class OutputApprovalDataConversion():

"""
    0000-00-00を空に置き換える
    Param:
        arg: datetime
    Return:
        : datetime
    """    
def convert_str_to_date(arg: datetime) -> datetime:
    if arg != '':
        return arg
    else:
        conv_date_empty = arg.replace('%Y-%m-%d', '')
        return conv_date_empty
    
"""
    00:00を空に置き換える
    上と同じ
    """
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
    # 内容名を数値に置き換える
    elif type(arg) is str:
        content_value = table.query.filter(table.NAME==arg).first()
        return content_value.CODE
    else:
        TypeError("intかstrのどちらかです")
