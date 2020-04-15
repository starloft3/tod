#new import
import random

#globals
basenames=[]

#functions

#this should be run by the server every resolution, populates basenames
def loadbasenames():
    db = load_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM basenames")
    data = cur.fetchall()
    for x in data:
        basenames.append([x[0], int(x[1]), int(x[2])])
    cur.close()
    db.close()

#this should be run during Set Start Positions, put it with the other resets
def resetbasenames():
    db = load_db()
    cur = db.cursor()
    cur.execute("UPDATE basenames SET used=0")
    cur.close()

    db.commit()
    db.close()

#main function.  takes faction # as input, outputs basename string.
#also marks that base as USED
def nameBase(faction):
    candidates = []
    for x in range(len(basenames)):
        if basenames[x][1] == faction and basenames[x][2] == 0:
            candidates.append(basenames[x][0])
    if len(candidates) > 0:
        winner = random.choice(candidates)
        db = load_db()
        cur = db.cursor()
        cur.execute("UPDATE basenames SET used=1 WHERE basename=%s", [winner])
        cur.close()
        db.commit()
        db.close()
        return winner
    else:
        return 'Error'
