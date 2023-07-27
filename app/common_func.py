

from app import app, db

#***** DBのリスト作成*******#
def GetPullDownList(TABLE, colCODE, colNAME, OrderCol):
    
    GetList = []
    dblist = db.session.query(TABLE, colCODE.label("CODE"), colNAME.label("NAME") ).order_by(OrderCol)
    GetList.append(["", ""])
    for row in dblist:
        GetList.append([row.CODE, row.NAME])

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