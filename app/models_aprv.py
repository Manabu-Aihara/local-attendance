from app import db

class Approval(db.Model):
    __tablename__ = "M_APPROVAL"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(db.Integer, db.ForeignKey('M_STAFFINFO.STAFFID'), index=True, nullable=False)
    TYPE = db.Column(db.String(10), index=True, nullable=False)
    GROUPNAME = db.Column(db.String(50), nullable=False)

    def __init__(self, STAFFID, TYPE, GROUPNAME):
        self.STAFFID = STAFFID
        # self.TYPE = TYPE
        # self.GROUPNAME = GROUPNAME

class NotificationList(db.Model):
    __tablename__ = "D_NOTIFICATION_LIST"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(db.Integer, db.ForeignKey('M_STAFFINFO.STAFFID'), index=True, nullable=False)
    N_CODE = db.Column(db.Integer, db.ForeignKey('M_NOTIFICATION.CODE'), index=True, nullable=False)
    STATUS = db.Column(db.Integer, index=True, nullable=False)
    START_DAY = db.Column(db.Date)
    START_TIME = db.Column(db.Time, nullable=True)
    END_DAY = db.Column(db.Date)
    END_TIME = db.Column(db.Time, nullable=True)
    REMARK = db.Column(db.String(255))

    def __init__(self, STAFFID, N_CODE, STATUS, START_DAY, START_TIME, END_DAY, END_TIME, REMARK):
        self.STAFFID = STAFFID
        self.N_CODE = N_CODE
        self.STATUS = STATUS
        self.START_DAY = START_DAY
        self.START_TIME = START_TIME
        self.END_DAY = END_DAY
        self.END_TIME = END_TIME
        self.REMARK = REMARK

