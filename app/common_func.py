

from app import app, db

#***** DBのリスト作成*******#
"""
    申請理由プルダウンリスト
    @Param
    Table class
    Table code
    Table name
    sort基準
    """
def GetPullDownList(TABLE, colCODE, colNAME, OrderCol):
    
    GetList = []
    dblist = db.session.query(TABLE, colCODE.label("CODE"), colNAME.label("NAME") ).order_by(OrderCol)
    # GetList.append(["", ""])
    GetList.append(("", ""))
    for row in dblist:
        # GetList.append([row.CODE, row.NAME])
        GetList.append((row.CODE, row.NAME))

    return GetList

#DB登録用　int型が空白だったらNoneを代入
def intCheck(intValue):
    
    if str.isnumeric(intValue):
        return intValue
    else:
        intValue = None
        return intValue

def blankCheck(strValue):

    if strValue != '':
        return strValue
    else:
        strValue = None
        return strValue