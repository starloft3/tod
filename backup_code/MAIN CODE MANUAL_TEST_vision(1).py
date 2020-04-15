from random import randint
import csv
import copy
import MySQLdb

#DATABASE VARIABLES
host_var="localhost"
user_var="root"
passwd_var="sniper67"
db_var="warcraft"

#CATEGORYLIST
CATEGORY_EXTERIOR_SIEGE=0
CATEGORY_RANGED=1
CATEGORY_EXPERT=2
CATEGORY_MELEE=3
CATEGORY_INTERIOR_SIEGE=4
CATEGORY_NO_FIRE=5
#ALLROADS
ROAD_HEX=0
ROAD_N=1
ROAD_NE=2
ROAD_SE=3
ROAD_S=4
ROAD_SW=5
ROAD_NW=6
#ALLUNITS
UNIT_NAME=0
UNIT_MAX_HIT_POINTS=1
UNIT_COMBAT=2
UNIT_CATEGORY=3
UNIT_TYPE=4
UNIT_LIGHT_MAX=5
UNIT_HEAVY=6
UNIT_NATURAL=7
UNIT_MOVEMENT_MAX=8
UNIT_VISION=9
UNIT_FACTION=10
UNIT_HIT_POINTS=11
UNIT_LOCATION=12
UNIT_TIER=13
UNIT_TIER_1=14
UNIT_TIER_2=15
UNIT_TIER_3=16
UNIT_TIER_4=17
UNIT_ALIVE=18
UNIT_HEX_DURATION=19
UNIT_FIRED=20
UNIT_LIGHT_CURRENT=21
UNIT_ARMORBROKEN=22
UNIT_TERRAIN=23
UNIT_FLANK=24
UNIT_MOVEMENT_REMAINING=25
UNIT_ROAD_MOVE_REMAINING=26
UNIT_ROAD_MOVE_ONLY=27
UNIT_PREVIOUS_LOCATION=28
UNIT_HOLD_BONUS=29
UNIT_COMBAT_START=30
UNIT_TIER_1_DATA=31
UNIT_TIER_2_DATA=32
UNIT_TIER_3_DATA=33
UNIT_TIER_4_DATA=34
UNIT_TRANSPORT_ONE=35
UNIT_TRANSPORT_TWO=36
UNIT_TRANSPORT_THREE=37
#FACTION DATA
FACTION_DATA_NAME=0
FACTION_DATA_GRUNT=1
FACTION_DATA_BERSERKER=2
FACTION_DATA_AXETHROWER=3
FACTION_DATA_OGRE=4
FACTION_DATA_CATAPULT=5
FACTION_DATA_DEATH_KNIGHT=6
FACTION_DATA_WAVE_RIDER=7
FACTION_DATA_TURTLE=8
FACTION_DATA_JUGGERNAUT=9
FACTION_DATA_HORDE_TRANSPORT=10
FACTION_DATA_DRAGON=11
FACTION_DATA_RAIDER=12
FACTION_DATA_SHAMAN=13
FACTION_DATA_WARLOCK=14
FACTION_DATA_FOOTMAN=15
FACTION_DATA_ARCHER=16
FACTION_DATA_KNIGHT=17
FACTION_DATA_BALLISTA=18
FACTION_DATA_MAGE=19
FACTION_DATA_DESTROYER=20
FACTION_DATA_SUBMARINE=21
FACTION_DATA_BATTLESHIP=22
FACTION_DATA_ALLIANCE_TRANSPORT=23
FACTION_DATA_GRYPHON=24
FACTION_DATA_DWARF=25
FACTION_DATA_SWORDSMAN=26
FACTION_DATA_WILDHAMMER_SHAMAN=27
FACTION_DATA_ROGUE=28
FACTION_DATA_SKELETON=29
FACTION_DATA_DEMON=30
FACTION_DATA_ELEMENTAL=31
#TYPES
TYPE_GROUND=0
TYPE_AIR=1
TYPE_SEA=2
#BASES
BASE_NAME=0
BASE_LOCATION=1
BASE_FACTION=2
BASE_TIER=3
BASE_GOLD=4
BASE_LUMBER=5
BASE_OIL=6
BASE_ACTIONS=7
#ALLHEXES FIX FIX FIX FIX FIX
HEX_TERRAIN=0
HEX_N_TERRAIN=1
HEX_NE_TERRAIN=2
HEX_SE_TERRAIN=3
HEX_S_TERRAIN=4
HEX_SW_TERRAIN=5
HEX_NW_TERRAIN=6
HEX_BUILDING=7# non-base building. #1 runestone #2 portal #3 dragon
HEX_OIL=8# OIL PRESENT
HEX_FARM=9# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_MILL=10# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_RIG=11# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_GOLD=12#TOTAL GOLD VALUE OF HEX
HEX_NEW_COMBAT=13
HEX_BATTLE_FOUGHT=14
HEX_N_CONTROL=15
HEX_NE_CONTROL=16
HEX_SE_CONTROL=17
HEX_S_CONTROL=18
HEX_SW_CONTROL=19
HEX_NW_CONTROL=20
HEX_ASSISTED=21
#ALLFACTIONS
FACTION_AMANI=0
FACTION_BLEEDING_HOLLOW=1
FACTION_BLACK_TOOTH_GRIN=2
FACTION_DRAGONMAW=3
FACTION_STORMREAVER=4
FACTION_TWILIGHTS_HAMMER=5
FACTION_BLACKROCK=6
FACTION_SILVERMOON=7
FACTION_AERIE_PEAK=8
FACTION_IRONFORGE=9
FACTION_DALARAN=10
FACTION_KUL_TIRAS=11
FACTION_STROMGARDE=12
FACTION_AZEROTH=13
FACTION_LORDAERON=14
FACTION_GILNEAS=15
FACTION_ALTERAC=16
FACTION_DARK_IRON=17
FACTION_BURNING_BLADE=18
FACTION_FROSTWOLF=19
FACTION_DALARAN_REBEL=20
FACTION_GILNEAS_REBEL=21
FACTION_FIRETREE=22
FACTION_SMOLDERTHORN=23
FACTION_SHADOWPINE=24
FACTION_SHADOWGLEN=25
FACTION_REVANTUSK=26
FACTION_MOSSFLAYER=27
FACTION_WITHERBARK=28
FACTION_VILEBRANCH=29
FACTION_DRAGON=30
FACTION_DEMON=31
#GLOBALS
factiondictionary={0:'Amani',1:'Bleeding Hollow',2:'Black Tooth Grin',3:'Dragonmaw',4:'Stormreaver',5:"Twilight's Hammer",6:'Blackrock',7:'Silvermoon',8:'Aerie Peak',9:'Ironforge',10:'Dalaran',11:'Kul Tiras',12:'Stromgarde',13:'Azeroth',14:'Lordaeron',15:'Gilneas',16:'Alterac',17:'Dark Iron',18:'Burning Blade',19:'Frostwolf',20:'Dalaran Rebel',21:'Gilnean Rebel',22:'Firetree',23:'Smolderthorn',24:'Shadowpine',25:'Shadowglen',26:'Revantusk',27:'Mossflayer',28:'Witherbark',29:'Vilebranch',30:'Dragon',31:'Demon'}
categorylist=[CATEGORY_EXTERIOR_SIEGE,CATEGORY_RANGED,CATEGORY_EXPERT,CATEGORY_MELEE,CATEGORY_INTERIOR_SIEGE]#this can be replaced by just a loop through the numbers, but change it elsewhere before deleting
# allfactions=[5,5,5,5,5,5,5,15,15,15,15,15,15,15,15,15,15,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]#each faction's initiative count (diplomatic standing)
allfactions = []
FOOD_SURPLUS=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
allunits=[]
allcurrentfaction=[]
allorders=[]
allspecialorders=[]
hexsidelimitchecks=[]
allhexes=[]
allroads=[]
allbases=[]
allexpandables=[]
allpotentialexpansionsreceived=[]
allbuildables=[]
basebuildorders=[]
expansionorders=[]
successfulexpansionorders=[]
alleconomicactions=[]
unitslegend=[]
baseslegend=[]
currentinitiative=[]
class caravan():
    path=[]
    originbase=-1
    destinationbase=-1
    faction=-1
    caravantype='none'
class constructionassist():
    path=[]
    originbase=-1
    destinationbase=-1
    faction=-1
    assisttype='none'
class unittype():
    maxhp=0
    combat=0
    category=0
    unittype=0
    light=0
    heavy=0
    natrual=0
    movement=0
    vision=0
    goldcost=0
    lumbercost=0
    oilcost=0
    mintier=0
allstats={'Grunt':unittype(),'Berserker':unittype(),'Axethrower':unittype(),'Ogre':unittype(),'Catapult':unittype(),'Death Knight':unittype(),'Wave Rider':unittype(),'Turtle':unittype(),'Juggernaut':unittype(),'Horde Transport':unittype(),'Dragon':unittype(),'Raider':unittype(),'Shaman':unittype(),'Warlock':unittype(),'Footman':unittype(),'Archer':unittype(),'Knight':unittype(),'Ballista':unittype(),'Mage':unittype(),'Destroyer':unittype(),'Submarine':unittype(),'Battleship':unittype(),'Alliance Transport':unittype(),'Gryphon':unittype(),'Dwarf':unittype(),'Swordsman':unittype(),'Wildhammer Shaman':unittype(),'Rogue':unittype(),'Skeleton':unittype(),'Demon':unittype(),'Elemental':unittype(),"Zul'jin":unittype(),'Kilrogg Deadeye':unittype(),'Rend Blackhand':unittype(),'Maim Blackhand':unittype(),'Zuluhed the Whacked':unittype(),"Gul'dan the Deceiver":unittype(),"Cho'gall":unittype(),'Orgrim Doomhammer':unittype(),'Varok Saurfang':unittype(),'Alleria Windrunner':unittype(),'Sylvanas Windrunner':unittype(),'Kurdran Wildhammer':unittype(),'Maz Drachrip':unittype(),'Magni Bronzebeard':unittype(),'Muradin Bronzebeard':unittype(),'Archmage Antonidas':unittype(),'Archmage Khadgar':unittype(),'Daelin Proudmoore':unittype(),'Derek Proudmoore':unittype(),'Thoras Trollbane':unittype(),'Danath Trollbane':unittype(),'Anduin Lothar':unittype(),'Turalyon':unittype(),'Uther the Lightbringer':unittype(),'Terenas Menethil':unittype(),'Genn Greymane':unittype(),'Darius Crowley':unittype(),'Aiden Perenolde':unittype(),'Lord Falconcrest':unittype(),'Dagran Thaurissan':unittype(),"Drek'thar":unittype(),'Nazgrel':unittype(),'Alexstrasza':unittype(),}
# method to load DB
def load_db():
    return MySQLdb.connect(host=host_var,
                           user=user_var,
                           passwd=passwd_var,
                           db=db_var)
def ordermenu(prompt,*options):
    print prompt
    active=1
    for x in range(len(options)):
        print x+1,'. ',options[x]
    while active==1:
        command=raw_input()
        if command.isdigit():
            command=int(command)-1
            if command<len(options):
                return command
                active=0
#LOAD GAME STATE
def loadcurrentfaction():
    db = load_db()

    cur = db.cursor()
    cur.execute("SELECT * FROM currentfaction")
    currentfactiondata = cur.fetchall()

    count = 0
    for x in currentfactiondata:
        if count==0:
            allcurrentfaction.append(x)
            count=count+1

    cur.close()
    db.close()
    
def loadcurrentinitiative():
    db = load_db()

    cur = db.cursor()
    cur.execute("SELECT * FROM currentinitiative")
    currentinitiativedata = cur.fetchall()
    templist=[]
    for x in currentinitiativedata:
        templist=list(x)
        # currentinitiative[0] = int(templist[0])
        currentinitiative.append(int(templist[0]))
    cur.close()
    db.close()
        
def loadunits():

    db = load_db()
    unitstats_cur = db.cursor()
    unitstats_cur.execute("SELECT * FROM unitstats")
    unitstats = unitstats_cur.fetchall()

    for x in unitstats:
        allstats[x[0]].maxhp=x[1]
        allstats[x[0]].combat=x[2]
        allstats[x[0]].category=x[3]
        allstats[x[0]].type=x[4]
        allstats[x[0]].light=x[5]
        allstats[x[0]].heavy=x[6]
        allstats[x[0]].natural=x[7]
        allstats[x[0]].movement=x[8]
        allstats[x[0]].vision=x[9]
        allstats[x[0]].goldcost=x[10]
        allstats[x[0]].lumbercost=x[11]
        allstats[x[0]].oilcost=x[12]
        allstats[x[0]].mintier=x[13]

    unitstats_cur.close()

    unitdata_cur = db.cursor()
    unitdata_cur.execute("SELECT * FROM unitdata")
    unitdata = unitdata_cur.fetchall()     
    count=0
    for x in unitdata:
        allunits.append([])
        allunits[count].append(x[0])
        allunits[count].append(int((allstats[x[0]].maxhp)))
        allunits[count].append(int((allstats[x[0]].combat)))
        allunits[count].append(int((allstats[x[0]].category)))
        allunits[count].append(int((allstats[x[0]].type)))
        allunits[count].append(int((allstats[x[0]].light)))
        allunits[count].append(int((allstats[x[0]].heavy)))
        allunits[count].append(int((allstats[x[0]].natural)))
        allunits[count].append(int((allstats[x[0]].movement)))
        allunits[count].append(int((allstats[x[0]].vision)))
        x = list(x)
        x.remove(x[0])
        for y in range(len(x)):
            if 0<=y<4 or y==8:
                allunits[count].append(int((x[y])))#upload
            else:
                allunits[count].append((x[y]))
        for y in range(0,19):
            allunits[count].append(0)
        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
        count=count+1

    unitdata_cur.close()
    db.close()
    
def loadsavedunits():
    db = load_db()
    
    unitstats_cur = db.cursor()
    unitstats_cur.execute("SELECT * FROM unitstats")
    unitstats = unitstats_cur.fetchall()

    for x in unitstats:
        allstats[x[0]].maxhp=x[1]
        allstats[x[0]].combat=x[2]
        allstats[x[0]].category=x[3]
        allstats[x[0]].type=x[4]
        allstats[x[0]].light=x[5]
        allstats[x[0]].heavy=x[6]
        allstats[x[0]].natural=x[7]
        allstats[x[0]].movement=x[8]
        allstats[x[0]].vision=x[9]
        allstats[x[0]].goldcost=x[10]
        allstats[x[0]].lumbercost=x[11]
        allstats[x[0]].oilcost=x[12]
        allstats[x[0]].mintier=x[13]

    unitstats_cur.close()

    unitdata_cur = db.cursor()
    unitdata_cur.execute("SELECT * FROM saveunits")
    unitdata = unitdata_cur.fetchall()
    count=0
    for x in unitdata:
        allunits.append([])
        allunits[count].append(x[0])
        allunits[count].append(int((allstats[x[0]].maxhp)))
        allunits[count].append(int((allstats[x[0]].combat)))
        allunits[count].append(int((allstats[x[0]].category)))
        allunits[count].append(int((allstats[x[0]].type)))
        allunits[count].append(int((allstats[x[0]].light)))
        allunits[count].append(int((allstats[x[0]].heavy)))
        allunits[count].append(int((allstats[x[0]].natural)))
        allunits[count].append(int((allstats[x[0]].movement)))
        allunits[count].append(int((allstats[x[0]].vision)))
        x = list(x)
        x.remove(x[0])
        for y in range(len(x)):
            #allunits[count].append((x[y]))
            if 0<=y<4 or y==8 or y>8:
                allunits[count].append(int((x[y])))#upload
            else:
                allunits[count].append((x[y]))
        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
        count=count+1
    unitdata_cur.close()
    db.close()
     
def loadorders():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM orders")
    orderdata = cur.fetchall()
    # print orderdata
    
    for x in orderdata:
        templist=[]
        for y in x:
            if y != None:
                templist.append(int(y))
        allorders.append(templist)
    cur.close()
    db.close()

def loadspecialorders():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM specialorders")
    orderdata = cur.fetchall()
    
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            if y==0:
                templist.append(x[y])
            elif x[y] != None:
                templist.append(int(x[y]))
        allspecialorders.append(templist)

    cur.close()
    db.close()

def loadeconomicactions():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM economicactions")
    orderdata = cur.fetchall()
    
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            templist.append(x[y])
        alleconomicactions.append(templist)

    cur.close()
    db.close()

def loadbuildables():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM buildables")
    orderdata = cur.fetchall()
    
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            templist.append(int(x[y]))
        allbuildables.append(templist)

    cur.close()
    db.close()

def loadsavedbuildables():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM savebuildables")
    orderdata = cur.fetchall()
    
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            templist.append(int(x[y]))
        allbuildables.append(templist)

    cur.close()
    db.close()

def loadcurrentbuildables():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currentbuildables")
    orderdata = cur.fetchall()
    count=0
    for x in orderdata:
        if count==0:
            allbuildables.append(x)
            count=count+1

    cur.close()
    db.close()

def loadmap():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM hexdata")
    mapdata = cur.fetchall()
    
    for x in mapdata:
        templist=[]
        for y in range(0,7):
            templist.append(x[y])
        for y in range(7,len(x)):
            templist.append(x[int(y)])
        allhexes.append(templist)

    cur.close()
    db.close()

def loadsavedmap():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM savehexes")
    mapdata = cur.fetchall()
    
    for x in mapdata:
        templist=[]
        for y in range(0,7):
            templist.append(x[y])
        for y in range(7,len(x)):
            templist.append(x[int(y)])
        allhexes.append(templist)

    cur.close()
    db.close()

def loadroads():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM roaddata")
    roaddata = cur.fetchall()
    
    for x in roaddata:
        templist=[]
        for y in x:
            templist.append(int(y))
        allroads.append(templist)

    cur.close()
    db.close()

def loadfactions():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM factiondata")
    allfactionsdata = cur.fetchall()
    templist = []
    for x in allfactionsdata:
        templist = list(x)
    for y in templist:
        allfactions.append(int(y))

    cur.close()
    db.close()

def loadsavedfactions():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM savefactions")
    allfactionsdata = cur.fetchall()
    templist = []
    for x in allfactionsdata:
        templist = list(x)
    for y in templist:
        allfactions.append(int(y))

    cur.close()
    db.close()

def loadbases():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM basedata")
    basedata = cur.fetchall()
    
    for x in basedata:
        templist=[]
        templist.append(x[0])
        for y in range(1,len(x)):
            templist.append(int(x[y]))
        allbases.append(templist)

    cur.close()
    db.close()

def loadsavedbases():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM savebases")
    basedata = cur.fetchall()
    
    for x in basedata:
        templist=[]
        templist.append(x[0])
        for y in range(1,len(x)):
            templist.append(int(x[y]))
        allbases.append(templist)

    cur.close()
    db.close()

def loadcurrentunitslegend():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currentunitslegend")
    data = cur.fetchall()
    
    for x in data:
        unitslegend.append(int(x[0]))

    cur.close()
    db.close()

def loadcurrentbaseslegend():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currentbaseslegend")
    data = cur.fetchall()
    
    for x in data:
        baseslegend.append(int(x[0]))

    cur.close()
    db.close()

def resetturns():
    db = load_db()
    cur = db.cursor()
    cur.execute("UPDATE turnstatus SET COL_0=0, COL_1=0, COL_2=0, COL_3=0, COL_4=0, COL_5=0, COL_6=0, COL_7=0, COL_8=0, COL_9=0, COL_10=0, COL_11=0, COL_12=0, COL_13=0, COL_14=0, COL_15=0, COL_16=0, COL_17=0, COL_18=0, COL_19=0, COL_20=0, COL_21=0, COL_22=0, COL_23=0, COL_24=0, COL_25=0, COL_26=0, COL_27=0, COL_28=0, COL_29=0, COL_30=0, COL_31=0")
    cur.close()

    db.commit()
    db.close()

def loadinitiative():
    db = load_db()
    cur = db.cursor()
    cur.execute("UPDATE currentinitiative SET CURRENT_INITIATIVE=-1")
    cur.close()

    db.commit()
    db.close()

def resetorders():
    db = load_db()
    
    o_cur = db.cursor()
    o_cur.execute("TRUNCATE orders")
    o_cur.close()

    e_cur = db.cursor()
    e_cur.execute("TRUNCATE economicactions")
    e_cur.close()

    s_cur = db.cursor()
    s_cur.execute("TRUNCATE specialorders")
    s_cur.close()

    db.commit()
    db.close()

def checkturns():
    templist=[]
    db = load_db()

    cur = db.cursor()
    cur.execute("SELECT * FROM turnstatus")
    data = cur.fetchall()
    for x in data:
        templist = list(x)

    cur.close()
    db.close()
    for y in templist:
        if y != 0:
            return 1
    return 0

def updateInitiative():
    db = load_db()

    initiative=-1
    i_cur = db.cursor()
    i_cur.execute("SELECT * FROM currentinitiative")
    i_data = i_cur.fetchall()
    for x in i_data:
        initiative=list(x)[0]
    i_cur.close()

    templist = []
    f_cur = db.cursor()
    f_cur.execute("SELECT * FROM savefactions")
    f_data = f_cur.fetchall()
    for y in f_data:
        templist = list(y)
    f_cur.close()

    u_cur = db.cursor()

    for i in range(len(templist)):
        templist[i] = int(templist[i])

    templist = sorted(set(templist))
    templist = [x for x in templist if x >= 0]
    for j in range(len(templist)):
        if templist[j] >= initiative + 1:
            u_cur.execute("UPDATE currentinitiative SET CURRENT_INITIATIVE=%s", templist[j])
            u_cur.close()
            db.commit()
            db.close()
            return

    u_cur.execute("UPDATE currentinitiative SET CURRENT_INITIATIVE=%s", templist[0])
    u_cur.close()
    db.commit()
    db.close()

def getCurrentFaction():
    db = load_db()
    
    initiative=-1
    i_cur = db.cursor()
    i_cur.execute("SELECT * FROM currentinitiative")
    i_data = i_cur.fetchall()
    for x in i_data:
        initiative=list(x)[0]
    i_cur.close()

    factionlist = []
    f_cur = db.cursor()
    f_cur.execute("SELECT * FROM savefactions")
    f_data = f_cur.fetchall()
    for y in f_data:
        factionlist = list(y)
    f_cur.close()

    for j in range(len(factionlist)):
        factionlist[j] = int(factionlist[j])

    turnlist = []
    t_cur = db.cursor()
    t_cur.execute("SELECT * FROM turnstatus")
    t_data = t_cur.fetchall()
    for z in t_data:
        turnlist = list(z)
    t_cur.close()

    for k in range(len(turnlist)):
        turnlist[k] = int(turnlist[k])

    
    for l in range(len(factionlist)):
        if factionlist[l] == initiative and turnlist[l] == 0:
            u_cur = db.cursor()
            u_cur.execute("UPDATE currentfaction SET CURRENT_FACTION=%s", l)
            u_cur.close()
            db.commit()
            db.close()
            print 'Current faction is now ' + factiondictionary[l]
            return l

    db.close()
    print 'All factions of this initiative have submitted turns.'
    return -1
    
#BASE ACTIONS

def generateExpandables():
    for x in range(len(allbases)):
        allexpandables.append([])
        allpotentialexpansionsreceived.append([])
        legalwaterhexes=[allbases[x][BASE_LOCATION]]
        legallandhexes=[allbases[x][BASE_LOCATION]]
        tempadditions=[]
        tempadditions=AddLegalExpandables(legalwaterhexes,'water',allbases[x][BASE_TIER])
        for y in range(len(tempadditions)):
            if IsItThere(tempadditions[y],legalwaterhexes)==0:
                legalwaterhexes.append(tempadditions[y])
        tempadditions=AddLegalExpandables(legallandhexes,'land',allbases[x][BASE_TIER])
        for y in range(len(tempadditions)):
            if IsItThere(tempadditions[y],legallandhexes)==0:
                legallandhexes.append(tempadditions[y])
        del legalwaterhexes[0]
        del legallandhexes[0]
        for y in range(len(legalwaterhexes)):
            allexpandables[x].append(legalwaterhexes[y])
        for y in range(len(legallandhexes)):
            allexpandables[x].append(legallandhexes[y])
        deletethese=[]
        for y in range(len(allexpandables[x])):
            for z in range(len(allbases)):
                if allbases[z][BASE_LOCATION]==allexpandables[x][y]:
                    deletethese.append(y)
            if int(allhexes[allexpandables[x][y]][HEX_FARM])!=-1 or int(allhexes[allexpandables[x][y]][HEX_MILL])!=-1 or int(allhexes[allexpandables[x][y]][HEX_RIG])!=-1:
                deletethese.append(y)
                allpotentialexpansionsreceived[x].append(allexpandables[x][y])
        deletethese.sort()
        deletethese.reverse()
        for y in deletethese:
            del allexpandables[x][y]
def AddLegalExpandables(legalhexes,tracetype,basetier):
    count=0
    generatedexpandables=[]
    while count<basetier:
        adjacents=GenerateLegalAdjacentHexes(legalhexes,tracetype)
        for x in adjacents:
            if IsItThere(x,legalhexes)==0:
                legalhexes.append(x)
        count=count+1
    return legalhexes
def GenerateLegalAdjacentHexes(legalhexes,tracetype):
    newhexes=[]
    adjacencies=[-1,38,39,1,-38,-39]
    if tracetype=='water':
        for x in legalhexes:
            for y in adjacencies:
                if (HexsideTerrain(x,x+y)=='O' or HexsideTerrain(x,x+y)=='K' or HexsideTerrain(x,x+y)=='Q') and IsItThere(x+y,legalhexes)==0:
                    newhexes.append(x+y)
    if tracetype=='land':
        for x in legalhexes:
            for y in adjacencies:
                if (HexsideTerrain(x,x+y)=='C' or HexsideTerrain(x,x+y)=='F' or HasRoad(x,x+y)==1) and IsItThere(x+y,legalhexes)==0:
                    newhexes.append(x+y)
    return newhexes
def receiveExpansions():
    for x in range(len(allhexes)):
        if allhexes[x][HEX_FARM]<-1:
            allhexes[x][HEX_FARM]=(allhexes[x][HEX_FARM]+2)*-1
        if allhexes[x][HEX_MILL]<-1:
            allhexes[x][HEX_MILL]=(allhexes[x][HEX_MILL]+2)*-1
        if allhexes[x][HEX_RIG]<-1:
            allhexes[x][HEX_RIG]=(allhexes[x][HEX_RIG]+2)*-1
def assistConstruction(actionhex,assist):
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION]==actionhex and allbases[x][BASE_GOLD]>1 and allbases[x][BASE_LUMBER]>1:
            valid=1    
            if assist.assisttype=='water':
                for x in range(1,len(assist.path)-1):
                    if Adjacent(assist.path[x-1],assist.path[x])==0 or allhexes[assist.path[x]][HEX_TERRAIN]!='O' or (HexsideTerrain(assist.path[x-1],assist.path[x])!='O' and HexsideTerrain(assist.path[x-1],assist.path[x])!='K') or EnemyUnitsPresent(assist.path,assist.faction)==0:
                        valid=0
                if Adjacent(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])==0 or HexsideTerrain(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])!='K' or allfactions[assist.faction]!=allfactions[allbases[assist.destinationbase][BASE_FACTION]]:
                    valid=0
            if assist.assisttype=='land':
                for x in range(1,len(assist.path)-1):
                    if Adjacent(assist.path[x-1],assist.path[x])==0 or (allhexes[assist.path[x]][HEX_TERRAIN]=='O' or allhexes[assist.path[x]][HEX_TERRAIN]=='I') or (HexsideTerrain(assist.path[x-1],assist.path[x])!='C' and HexsideTerrain(assist.path[x-1],assist.path[x])!='F' and HasRoad(assist.path[x-1],assist.path[x])!=1) or EnemyUnitsPresent(assist.path,assist.faction)==0:
                        valid=0
                if Adjacent(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])==0 or (HexsideTerrain(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])!='C' and HexsideTerrain(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])!='F' and HasRoad(assist.path[len(assist.path)-1],assist.path[len(assist.path)-2])) or allfactions[assist.faction]!=allfactions[allbases[assist.destinationbase][BASE_FACTION]]:
                    valid=0
            if valid==1:
                allbases[assist.originbase][BASE_ACTIONS]=allbases[assist.originbase][BASE_ACTIONS]-1
                if caravan.caravantype=='water':
                    allbases[caravan.originbase][BASE_GOLD]=allbases[caravan.originbase][BASE_GOLD]-2
                    allbases[caravan.originbase][BASE_LUMBER]=allbases[caravan.originbase][BASE_LUMBER]-2
                    allbases[caravan.originbase][BASE_OIL]=allbases[caravan.originbase][BASE_OIL]-1
                if caravan.caravantype=='land':
                    allbases[caravan.originbase][BASE_GOLD]=allbases[caravan.originbase][BASE_GOLD]-2
                    allbases[caravan.originbase][BASE_LUMBER]=allbases[caravan.originbase][BASE_LUMBER]-2
                allhexes[assist.destinationbase][HEX_ASSISTED]=1
def constructBase(actionhex,faction,name):
    for x in range(len(allbases)):
        if (allbases[x][BASE_LOCATION]==actionhex and allbases[x][BASE_TIER]==0) or allhexes[actionhex][HEX_ASSISTED]==1:
            allbases.append([])
            allbases[len(allbases)-1].append(name)
            allbases[len(allbases)-1].append(actionhex)
            allbases[len(allbases)-1].append(faction)
            allbases[len(allbases)-1].append(1)
            allbases[len(allbases)-1].append(0)
            allbases[len(allbases)-1].append(1)
            allbases[len(allbases)-1].append(0)
            allbases[len(allbases)-1].append(0)
            
def destroyBase(actionhex):

    #Iterate through allhexes to destroy all expansions.
    for x in range (len(allhexes)):
        if int(allhexes[x][HEX_FARM]) == actionhex:
            allhexes[x][HEX_FARM] = -1
        if int(allhexes[x][HEX_MILL]) == actionhex:
            allhexes[x][HEX_MILL] = -1
        if int(allhexes[x][HEX_RIG]) == actionhex:
            allhexes[x][HEX_RIG] = -1        
                

    #Update allbases to show 0 base tier (ruins), destroy all resources.
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex:
            allbases[x][BASE_TIER] = 0
            allbases[x][BASE_GOLD] = 0
            allbases[x][BASE_LUMBER] = 0
            allbases[x][BASE_OIL] = 0

def giveExpansion(basehex,actionhex,recipientbasehex):#set the expansions to a crazy negative then assign them to the new bases later after harvest happens
    print actionhex,basehex,recipientbasehex
    valid=1
    recipientbase=0
    base=0
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION]==recipientbasehex:
            recipientbase=x
        if allbases[x][BASE_LOCATION]==basehex:
            base=x
    print recipientbase
    print base
    if allfactions[allbases[recipientbase][BASE_FACTION]]!=allfactions[allbases[base][BASE_FACTION]]:
        valid=0
        print 'factions are not friendly'
    if int(allhexes[actionhex][HEX_FARM])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_RIG])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_MILL])!=allbases[base][BASE_LOCATION]:
        valid=0
        print 'expo does not belong to parent base'
    print 'allpotentialexpansionsreceived:',allpotentialexpansionsreceived
    if IsItThere(actionhex,allpotentialexpansionsreceived[recipientbase])==0:
        valid=0
        print 'not in allpotentialexpansionsreceived'
    if valid==1:
        if allhexes[actionhex][HEX_TERRAIN]=='C':
            allhexes[actionhex][HEX_FARM]=(allbases[recipientbase][BASE_LOCATION]*-1)-2
        if allhexes[actionhex][HEX_TERRAIN]=='F':
            allhexes[actionhex][HEX_MILL]=(allbases[recipientbase][BASE_LOCATION]*-1)-2
        if allhexes[actionhex][HEX_TERRAIN]=='O':
            allhexes[actionhex][HEX_RIG]=(allbases[recipientbase][BASE_LOCATION]*-1)-2
        allbases[base][BASE_ACTIONS]=allbases[base][BASE_ACTIONS]-1
def giveBase(actionhex, unit):

    #Update faction control in allbases.
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex and allunits[unit][UNIT_LOCATION]==actionhex and allfactions[allunits[unit][UNIT_FACTION]]==allfactions[allbases[x][BASE_FACTION]]:
            allbases[x][BASE_FACTION] = allunits[unit][UNIT_FACTION]
            allbases[x][BASE_ACTIONS]=0

def commerce(actionhex, resourceOut, resourceIn):

    #Update resource totals in allbases.
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex and allbases[x][resourceOut]>1:
            allbases[x][resourceIn] = allbases[x][resourceIn] + 1
            allbases[x][resourceOut] = allbases[x][resourceOut] - 2
            ResourceLimit()
            allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1

def harvest(actionhex):

    #Update resource totals in allbases.
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex:
            allbases[x][BASE_GOLD]=allbases[x][BASE_GOLD]+int(allhexes[actionhex][HEX_GOLD])
            for y in range(len(allhexes)):
                if int(allhexes[y][HEX_MILL])==actionhex:
                    allbases[x][BASE_LUMBER]=allbases[x][BASE_LUMBER]+1
                    allbases[x][BASE_GOLD]=allbases[x][BASE_GOLD]+int(allhexes[y][HEX_GOLD])
                if int(allhexes[y][HEX_FARM])==actionhex:
                    allbases[x][BASE_GOLD]=allbases[x][BASE_GOLD]+int(allhexes[y][HEX_GOLD])
                if int(allhexes[y][HEX_RIG])==actionhex:
                    allbases[x][BASE_OIL]=allbases[x][BASE_OIL]+1
            ResourceLimit()
            allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1

def expand(actionhex, targetHex):
    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex and allbases[x][BASE_LUMBER]>0 and (allhexes[targetHex][HEX_TERRAIN]=='F' or allhexes[targetHex][HEX_TERRAIN]=='C' or (allhexes[targetHex][HEX_TERRAIN]=='O' and int(allhexes[targetHex][HEX_OIL])==1)) and IsItThere(targetHex,allexpandables[x])==1:
            successfulexpansionorder=[actionhex,targetHex]
            successfulexpansionorders.append(successfulexpansionorder)
            allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1
def resolveExpansions():
    toberesolved=[]
    for x in range(len(successfulexpansionorders)):#what the hell does this do?? i guess it's checking if multiple bases try to expand to the same place?
        copy=0
        copytarget=0
        for y in range(len(toberesolved)):
            print 'toberesolved:',toberesolved
            if successfulexpansionorders[x][1]==toberesolved[y][0][1]:######the old line is below not sure if this fix is correct BUT LOOKS LIKE IT WORKS, SUCK IT
            #if IsItThere(successfulexpansionorders[x][1],toberesolved[y][0][1])==0:
                copy=1
                copytarget=y
                break
        if copy==1:
            toberesolved[copytarget].append(successfulexpansionorders[x])  #toberesolved=[[[1,1][2,1]],[[1,2][2,2]]]
        else:
            toberesolved.append([])
            toberesolved[len(toberesolved)-1].append(successfulexpansionorders[x])
    print 'to be resolved:',toberesolved
    for x in range(len(toberesolved)):
        pick=randint(0,len(toberesolved[x])-1)
        baseid=-1
        for y in range(len(allbases)):
            if allbases[y][BASE_LOCATION]==toberesolved[x][pick][0]:
                baseid=y
        allbases[baseid][BASE_LUMBER] = allbases[baseid][BASE_LUMBER] - 1
        #Update allhexes with new expansion information.
        if allhexes[toberesolved[x][pick][1]][HEX_TERRAIN]=='F':
            allhexes[toberesolved[x][pick][1]][HEX_MILL]=toberesolved[x][pick][0]
        if allhexes[toberesolved[x][pick][1]][HEX_TERRAIN]=='C':
            allhexes[toberesolved[x][pick][1]][HEX_FARM]=toberesolved[x][pick][0]
        if allhexes[toberesolved[x][pick][1]][HEX_TERRAIN]=='O' and int(allhexes[toberesolved[x][pick][1]][HEX_OIL])==1:#####jimnir needs this line
            allhexes[toberesolved[x][pick][1]][HEX_RIG]=toberesolved[x][pick][0]#####jimnir needs this line
        allbases[baseid][BASE_ACTIONS]=allbases[baseid][BASE_ACTIONS]-1
        
        #Update resource totals in allbases.
    

def upgradeBase(actionhex):

    for x in range(len(allbases)):
        if allbases[x][BASE_LOCATION] == actionhex and ((allbases[x][BASE_TIER]==1 and allbases[x][BASE_GOLD]>5 and allbases[x][BASE_LUMBER]>5) or (allbases[x][BASE_TIER]==2 and allbases[x][BASE_GOLD]>7 and allbases[x][BASE_LUMBER]>7 and allbases[x][BASE_OIL]>3)):
            connectedres=0
            connectedres=connectedres+int(allhexes[actionhex][HEX_GOLD])
            for y in range(len(allhexes)):
                if int(allhexes[y][HEX_MILL])==actionhex:
                    connectedres=connectedres+1
                    connectedres=connectedres+int(allhexes[y][HEX_GOLD])
                if int(allhexes[y][HEX_FARM])==actionhex:
                    connectedres=connectedres+int(allhexes[y][HEX_GOLD])
                if int(allhexes[y][HEX_RIG])==actionhex:
                    connectedres=connectedres+1
            #Tier 1 to Tier 2
            if allbases[x][BASE_TIER] == 1 and connectedres>1:
                allbases[x][BASE_GOLD] = allbases[x][BASE_GOLD] - 6
                allbases[x][BASE_LUMBER] = allbases[x][BASE_LUMBER] - 6
                allbases[x][BASE_TIER] = 2

            #Tier 2 to Tier 3
            if allbases[x][BASE_TIER] == 2 and connectedres>3:
                allbases[x][BASE_GOLD] = allbases[x][BASE_GOLD] - 8
                allbases[x][BASE_LUMBER] = allbases[x][BASE_LUMBER] - 8
                allbases[x][BASE_OIL] = allbases[x][BASE_OIL] - 4
                allbases[x][BASE_TIER] = 3
            allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1
def restUnit(actionhex,unit):
    for x in range(len(allbases)):
        success=0
        goldcost=0
        lumbercost=0
        oilcost=0
        if allbases[x][BASE_LOCATION]==actionhex and allunits[unit][UNIT_LOCATION]==actionhex and allunits[unit][UNIT_HEX_DURATION]>1:#hex duration may need to be >2
            if (allunits[unit][UNIT_TYPE]==TYPE_GROUND or allunits[unit][UNIT_TYPE]==TYPE_AIR) and allunits[unit][UNIT_CATEGORY]!=TYPE_INTERIOR_SIEGE and allbases[x][BASE_GOLD]>0:
                success=1
                goldcost=1
            if allunits[unit][UNIT_TYPE]==TYPE_GROUND and allunits[unit][UNIT_CATEGORY]==TYPE_INTERIOR_SIEGE and allbases[x][BASE_LUMBER]>0 and allbases[x][BASE_GOLD]>0:
                success=1
                goldcost=1
                lumbercost=1
            if allunits[unit][UNIT_TYPE]==TYPE_SEA and allunits[unit][UNIT_CATEGORY]!=TYPE_INTERIOR_SIEGE and allbases[x][BASE_LUMBER]>0 and allbases[x][BASE_OIL]>0:
                success=1
                lumbercost=1
                oilcost=1
            if allunits[unit][UNIT_TYPE]==TYPE_SEA and allunits[unit][UNIT_CATEGORY]==TYPE_INTERIOR_SIEGE and allbases[x][BASE_LUMBER]>0 and allbases[x][BASE_OIL]>0 and allbases[x][BASE_GOLD]>0:
                success=1
                goldcost=1
                lumbercost=1
                oilcost=1
            if success==1:
                allunits[unit][UNIT_HIT_POINTS]=allunits[unit][UNIT_HIT_POINTS]+(allunits[unit][UNIT_MAX_HIT_POINTS]/4)
                if allunits[unit][UNIT_MAX_HIT_POINTS]%4!=0:
                    allunits[unit][UNIT_HIT_POINTS]=allunits[unit][UNIT_HIT_POINTS]+1
                if allunits[unit][UNIT_HIT_POINTS]>allunits[unit][UNIT_MAX_HIT_POINTS]:
                    allunits[unit][UNIT_HIT_POINTS]=allunits[unit][UNIT_MAX_HIT_POINTS]
                allbases[x][BASE_GOLD]=allbases[x][BASE_GOLD]-goldcost
                allbases[x][BASE_LUMBER]=allbases[x][BASE_LUMBER]-lumbercost
                allbases[x][BASE_OIL]=allbases[x][BASE_OIL]-oilcost
                allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1
            
def buildUnit(actionhex,unit):
    for x in range(len(allbases)):        
        if allbases[x][BASE_LOCATION]==actionhex and FOOD_SURPLUS[allbases[x][BASE_FACTION]]>0 and allbases[x][BASE_TIER]>=int(allstats[unit].mintier) and allbases[x][BASE_GOLD]>=int(allstats[unit].goldcost) and allbases[x][BASE_LUMBER]>=int(allstats[unit].lumbercost) and allbases[x][BASE_OIL]>=int(allstats[unit].oilcost):
            allbases[x][BASE_GOLD]=allbases[x][BASE_GOLD]-int(allstats[unit].goldcost)
            allbases[x][BASE_LUMBER]=allbases[x][BASE_LUMBER]-int(allstats[unit].lumbercost)
            allbases[x][BASE_OIL]=allbases[x][BASE_OIL]-int(allstats[unit].oilcost)
            FOOD_SURPLUS[allbases[x][BASE_FACTION]]=FOOD_SURPLUS[allbases[x][BASE_FACTION]]-1
            allunits.append([])
            allunits[len(allunits)-1].append(unit)
            allunits[len(allunits)-1].append(allstats[unit].maxhp)
            allunits[len(allunits)-1].append(allstats[unit].combat)
            allunits[len(allunits)-1].append(allstats[unit].category)
            allunits[len(allunits)-1].append(allstats[unit].type)
            allunits[len(allunits)-1].append(allstats[unit].light)
            allunits[len(allunits)-1].append(allstats[unit].heavy)
            allunits[len(allunits)-1].append(allstats[unit].natural)
            allunits[len(allunits)-1].append(allstats[unit].movement)
            allunits[len(allunits)-1].append(allstats[unit].vision)
            allunits[len(allunits)-1].append(allbases[x][BASE_FACTION])
            allunits[len(allunits)-1].append(allstats[unit].maxhp)
            allunits[len(allunits)-1].append(allbases[x][BASE_LOCATION])
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append('none')
            allunits[len(allunits)-1].append('none')
            allunits[len(allunits)-1].append('none')
            allunits[len(allunits)-1].append('none')
            allunits[len(allunits)-1].append(1)
            allunits[len(allunits)-1].append(1)#hex duration 1 maybe it should be 0?
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(allstats[unit].light)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(allstats[unit].movement)
            allunits[len(allunits)-1].append(1)
            allunits[len(allunits)-1].append(1)
            allunits[len(allunits)-1].append(allbases[x][BASE_LOCATION])
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(0)
            allunits[len(allunits)-1].append(-1)
            allunits[len(allunits)-1].append(-1)
            allunits[len(allunits)-1].append(-1)
            allbases[x][BASE_ACTIONS]=allbases[x][BASE_ACTIONS]-1
def EnemyUnitsPresent(location,faction):
    checklist=buildcombatlist(location)
    enemyunits=0
    for x in checklist:
        if allfactions[allunits[x][UNIT_FACTION]]!=allfactions[faction]:
            enemyunits=1
    return enemyunits
def ResourceLimit():
    for x in range(len(allbases)):
        if allbases[x][BASE_TIER]==1 or allbases[x][BASE_TIER]==2:
            if allbases[x][BASE_GOLD]>6*allbases[x][BASE_TIER]:
                allbases[x][BASE_GOLD]=6
            if allbases[x][BASE_LUMBER]>6*allbases[x][BASE_TIER]:
                allbases[x][BASE_LUMBER]=6
            if allbases[x][BASE_OIL]>6*allbases[x][BASE_TIER]:
                allbases[x][BASE_OIL]=6
        if allbases[x][BASE_TIER]==3:
            if allbases[x][BASE_GOLD]>20:
                allbases[x][BASE_GOLD]=20
            if allbases[x][BASE_LUMBER]>20:
                allbases[x][BASE_LUMBER]=20
            if allbases[x][BASE_OIL]>20:
                allbases[x][BASE_OIL]=20
def establishCaravan(caravan):#add checks to make sure there are no bases in the intermediate steps
    valid=1    
    if caravan.caravantype=='water':
        for x in range(1,len(caravan.path)-1):
            if Adjacent(caravan.path[x-1],caravan.path[x])==0 or allhexes[caravan.path[x]][HEX_TERRAIN]!='O' or (HexsideTerrain(caravan.path[x-1],caravan.path[x])!='O' and HexsideTerrain(caravan.path[x-1],caravan.path[x])!='K') or EnemyUnitsPresent(caravan.path,caravan.faction)==0:
                valid=0
        if Adjacent(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])==0 or HexsideTerrain(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])!='K' or allfactions[caravan.faction]!=allfactions[allbases[caravan.destinationbase][BASE_FACTION]]:
            valid=0
    if caravan.caravantype=='land':
        for x in range(1,len(caravan.path)-1):
            if Adjacent(caravan.path[x-1],caravan.path[x])==0 or (allhexes[caravan.path[x]][HEX_TERRAIN]=='O' or allhexes[caravan.path[x]][HEX_TERRAIN]=='I') or (HexsideTerrain(caravan.path[x-1],caravan.path[x])!='C' and HexsideTerrain(caravan.path[x-1],caravan.path[x])!='F' and HasRoad(caravan.path[x-1],caravan.path[x])!=1) or EnemyUnitsPresent(caravan.path,caravan.faction)==0:
                valid=0
        if Adjacent(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])==0 or (HexsideTerrain(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])!='C' and HexsideTerrain(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])!='F' and HasRoad(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])) or allfactions[caravan.faction]!=allfactions[allbases[caravan.destinationbase][BASE_FACTION]]:
            valid=0
    if valid==1:
        allcaravans.append(caravan)
        allbases[caravan.originbase][BASE_ACTIONS]=allbases[caravan.originbase][BASE_ACTIONS]-1
        if caravan.caravantype=='water':
            allbases[caravan.originbase][BASE_GOLD]=allbases[caravan.originbase][BASE_GOLD]-1
            allbases[caravan.originbase][BASE_LUMBER]=allbases[caravan.originbase][BASE_LUMBER]-1
            allbases[caravan.originbase][BASE_OIL]=allbases[caravan.originbase][BASE_OIL]-1
        if caravan.caravantype=='land':
            allbases[caravan.originbase][BASE_GOLD]=allbases[caravan.originbase][BASE_GOLD]-1
            allbases[caravan.originbase][BASE_LUMBER]=allbases[caravan.originbase][BASE_LUMBER]-1
def sendResources(origin,destination,gold,lumber,oil):
    foundbases=[origin]
    watersuccess==0
    while watersuccess==0:#check if it the bases are connected by water caravans
        newfinds=[]
        foundbasescheckcopy=copy.deepcopy(foundbases)
        for x in range(len(foundbases)):
            tempfinds=FindConnectedCaravans(x,'water',foundbases)
            for y in range(len(tempfinds)):
                newfinds.append(tempfinds[y])
        if IsItThere(destination,newfinds)==1:
            watersuccess=1
        for x in range(len(newfinds)):
            foundbases.append(newfinds[x])
        if foundbases==foundbasescheckcopy:
            break
    landsuccess==0
    while landsuccess==0:#check if the bases are connected by land caravans
        newfinds=[]
        foundbasescheckcopy=copy.deepcopy(foundbases)
        for x in range(len(foundbases)):
            tempfinds=FindConnectedCaravans(x,'land',foundbases)
            for y in range(len(tempfinds)):
                newfinds.append(tempfinds[y])
        if IsItThere(destination,newfinds)==1:
            watersuccess=1
        for x in range(len(newfinds)):
            foundbases.append(newfinds[x])
        if foundbases==foundbasescheckcopy:
            break
    if watersuccess==1 or landsuccess==1:
        allbases[destination][BASE_GOLD]=allbases[destination][BASE_GOLD]+gold
        allbases[destination][BASE_LUMBER]=allbases[destination][BASE_LUMBER]+lumber
        allbases[destination][BASE_OIL]=allbases[destination][BASE_OIL]+oil
        allbases[origin][BASE_GOLD]=allbases[origin][BASE_GOLD]-gold
        allbases[origin][BASE_LUMBER]=allbases[origin][BASE_LUMBER]-lumber
        allbases[origin][BASE_OIL]=allbases[origin][BASE_OIL]-oil
        allbases[origin][BASE_ACTIONS]=allbases[origin][BASE_ACTIONS]-1
        ResourceLimit()
def FindConnectedCaravans(base,caravantype,foundbases):
    foundcaravans=[]
    for x in range(len(allcaravans)):
        if allcaravans[x].originbase==base and allcaravans[x].type==caravantype and IsItThere(allcaravan[x].destinationbase,foundbases)==0:
            foundcaravans.append(allcaravans[x].destinationbase)
        if allcaravans[x].destinationbase==base and allcaravans[x].type==caravantype and IsItThere(allcaravan[x].originbase,foundbases)==0:
            foundcaravans.append(allcaravans[x].originbase)
    return foundcaravans
def buildbases():
    for x in range(len(basebuildorders)):
        similarcount=0
        for y in range(len(basebuildorders)):
            if basebuildorders[x]==basebuildorders[y]:
                similarcount=similarcount+1
        if similarcount==1:
            constructBase(basebuildorders[x][0],basebuildorders[x][1],basebuildorders[x][2])

        
#MOVEMENT

        
def specialorders():
    ORDER_NAME=0
    ORDER_UNIT=1

    ORDER_TARGET_HEX=2 #rangedfire
    ORDER_TARGET_TRANSPORT=2#transport
    ORDER_BASE_NAME=2#construct base
    ##assist construction
    ##board transport
    for x in range(len(allspecialorders)):
        if allspecialorders[x][ORDER_NAME]=='Rangedfire':
            if allunits[allspecialorders[x][ORDER_UNIT]][UNIT_CATEGORY]==CATEGORY_INTERIOR_SIEGE:
                if Adjacent(allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION],allspecialorders[x][ORDER_TARGET_HEX])==1:
                    if len(buildfactionslist(buildcombatlist(allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION])))==1:
                        allunits.append(copy.deepcopy(allunits[allspecialorders[x][ORDER_UNIT]]))
                        allunits[len(allunits)-1][UNIT_CATEGORY]=CATEGORY_EXTERIOR_SIEGE
                        allunits[len(allunits)-1][UNIT_LOCATION]=allspecialorders[x][ORDER_TARGET_HEX]
                        allunits[allspecialorders[x][ORDER_UNIT]][UNIT_MOVEMENT_REMAINING]=0
                        print 'unit added'
        if allspecialorders[x][ORDER_NAME]=='Board Transport' and (allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_NAME]=='Alliance Transport' or allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_NAME]=='Horde Transport') and allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_FACTION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_FACTION] and allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_TRANSPORT_TWO]==-1 and allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]:##target is a transport of the same faction with extra space in the same hex
            allunits[allspecialorders[x][ORDER_UNIT]][UNIT_ALIVE]=0
            if allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_TRANSPORT_ONE]==-1:
                allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_TRANSPORT_ONE]=allspecialorders[x][ORDER_UNIT]
            else:
                allunits[allspecialorders[x][ORDER_TARGET_TRANSPORT]][UNIT_TRANSPORT_TWO]=allspecialorders[x][ORDER_UNIT]
        if allspecialorders[x][ORDER_NAME]=='Construct Base' and buildfactionslist(buildcombatlist(allunits[allspecialorders[ORDER_UNIT]][UNIT_LOCATION]))==1:
            valid=1
            for y in range(len(allbases)):
                if allbases[y][BASE_TIER]>0:
                    if allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]+1 or allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]-1 or allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]+38 or allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]-38 or allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]+39 or allbases[y][BASE_LOCATION]==allunits[allspecialorders[x][ORDER_UNIT]][UNIT_LOCATION]-39:
                        valid=0
            if valid==1:
                allunits[allspecialorders[x][ORDER_UNIT]][UNIT_MOVEMENT_REMAINING]=0#delete movement
                neworder=[]
                neworder.append(allspecialorders[x][ORDER_HEX])
                neworder.append(allfactions(allunits[allspecialorders[x][ORDER_UNIT]][UNIT_FACTION]))
                neworder.append(allspecialorders[x][ORDER_BASE_NAME])
                basebuildorders.append(neworder)
            #in checker make sure there's ruins or an assist function pending
def economicactions():
    ACTION_NAME=0
    ACTION_HEX=1#most functions use this unless another index 1 is specified

    ACTION_UNIT=2#give base    

    ACTION_RECIPIENT_BASE=2#give expansion (hex here refers to the hex of the expansion; ownerbase to its parent base
    ACTION_OWNER_BASE=3

    ACTION_RESOURCE_IN=2#commerce
    ACTION_RESOURCE_OUT=3

    ACTION_UNIT_TYPE=2#build unit

    ACTION_EXPAND_HEX=2#expand

    ACTION_CARAVAN_PATH=1#establish caravan
    ACTION_CARAVAN_ORIGIN_BASE=2
    ACTION_CARAVAN_DESTINATION_BASE=3
    ACTION_CARAVAN_FACTION=4
    ACTION_CARAVAN_TYPE=5

    ACTION_SEND_ORIGIN=1#send resources
    ACTION_SEND_DESTINATION=2
    ACTION_SEND_GOLD=3
    ACTION_SEND_LUMBER=4
    ACTION_SEND_OIL=5
    
    for x in range(len(allbases)):#generate actions
        allbases[x][BASE_ACTIONS]=allbases[x][BASE_TIER]
    generateExpandables()#generate expandables this should probably be earlier but no harm here too?
    for x in range(len(alleconomicactions)):#destroy base
        if alleconomicactions[x][ACTION_NAME]=='Destroy Base':
            destroyBase(int(alleconomicactions[x][ACTION_HEX]))
    for x in range(len(alleconomicactions)):#give base
        if alleconomicactions[x][ACTION_NAME]=='Give Base':
            giveBase(int(alleconomicactions[x][ACTION_HEX]),int(alleconomicactions[x][ACTION_UNIT]))
    for x in range(len(alleconomicactions)):#give expansion
        if alleconomicactions[x][ACTION_NAME]=='Give Expansion':
            giveExpansion(int(alleconomicactions[x][ACTION_HEX]),int(alleconomicactions[x][ACTION_RECIPIENT_BASE]),int(alleconomicactions[x][ACTION_OWNER_BASE]))
    for x in range(len(alleconomicactions)):#harvest
        if alleconomicactions[x][ACTION_NAME]=='Harvest':
            harvest(int(alleconomicactions[x][ACTION_HEX]))
    for x in range(len(alleconomicactions)):#commerce
        if alleconomicactions[x][ACTION_NAME]=='Commerce':
            commerce(int(alleconomicactions[x][ACTION_HEX]),int(alleconomicactions[x][ACTION_RESOURCE_IN]),int(alleconomicactions[x][ACTION_RESOURCE_OUT]))
    #upgrade unit NYI
    for x in range(len(alleconomicactions)):#build unit
        if alleconomicactions[x][ACTION_NAME]=='Build Unit':
            buildUnit(int(alleconomicactions[x][ACTION_HEX]),alleconomicactions[x][ACTION_UNIT_TYPE])
    for x in range(len(alleconomicactions)):#expand
        if alleconomicactions[x][ACTION_NAME]=='Expand':
            expand(int(alleconomicactions[x][ACTION_HEX]),int(alleconomicactions[x][ACTION_EXPAND_HEX]))
    resolveExpansions()
    for x in range(len(alleconomicactions)):#establish caravan
        if alleconomicactions[x][ACTION_NAME]=='Establish Caravan':
            newcaravan=caravan()
            newcaravan.path=alleconomicactions[x][ACTION_CARAVAN_PATH]
            newcaravan.originbase=alleconomicactions[x][ACTION_CARAVAN_ORIGIN_BASE]
            newcaravan.destinationbase=alleconomicactions[x][ACTION_CARAVAN_DESTINATION_BASE]
            newcaravan.faction=alleconomicactions[x][ACTION_CARAVAN_FACTION]
            newcaravan.caravantype=alleconomicactions[x][ACTION_CARAVAN_TYPE]
            establishCaravan(newcaravan)
    for x in range(len(alleconomicactions)):#upgrade base
        if alleconomicactions[x][ACTION_NAME]=='Upgrade Base':
            upgradeBase(int(alleconomicactions[x][ACTION_HEX]))
    for x in range(len(alleconomicactions)):#send resources
        if alleconomicactions[x][ACTION_NAME]=='Send Resources':
            sendResources(alleconomicactions[x][ACTION_SEND_ORIGIN],alleconomicactions[x][ACTION_SEND_DESTINATION],alleconomicactions[x][ACTION_SEND_GOLD],alleconomicactions[x][ACTION_SEND_LUMBER],alleconomicactions[x][ACTION_SEND_OIL])
    receiveExpansions()
def moveunits():##road moves into combat?
    for x in range(len(allunits)):#prevent units from entering combats the same turn they started in one
        if len(buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION])))>1:
            allunits[x][UNIT_COMBAT_START]=1
        else:
            allunits[x][UNIT_COMBAT_START]=0
        allunits[x][UNIT_HEX_DURATION]=allunits[x][UNIT_HEX_DURATION]+1
    for x in range(1,5):#work one destination at a time
        for y in range(len(allorders)):#sort moves by hexside crossed
            if len(allorders[y])>1 and (allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]>0 or (allunits[allorders[y][0]][UNIT_ROAD_MOVE_REMAINING]==1 and allunits[allorders[y][0]][UNIT_ROAD_MOVE_ONLY]==1)):#are there any moves and does the unit have movement remaining
                hexone=allunits[allorders[y][0]][UNIT_LOCATION]
                hextwo=allorders[y][1]
                hexswitch=-1
                foundmatch=0
                match=-1
                newcheck=[]
                combatmove=movecombatcheck(allorders[y][0],hextwo)
                if Adjacent(hexone,hextwo)==1 and canMove(hexone,hextwo,allorders[y][0],combatmove)==1:#check if move legal in terms of hex and hexside terrain being passable.
                    if allunits[allorders[y][0]][UNIT_TYPE]!=TYPE_AIR:
                        if hextwo>hexone:#generate hexside ID, always bigger number first
                            hexswitch=hexone
                            hexone=hextwo
                            hextwo=hexswitch
                        for z in range(len(hexsidelimitchecks)):#prepare to assign move order to hexside. see if any move orders already categorized through that hexside
                            if hexsidelimitchecks[z][0]==hexone and hexsidelimitchecks[z][1]==hextwo:
                                foundmatch=1
                                match=z
                        if foundmatch==1:#if there are, add this to that one
                            hexsidelimitchecks[match].append(y)
                        else:#if there aren't, add a new one to hexsidelimitchecks
                            newcheck.append(hexone)
                            newcheck.append(hextwo)
                            newcheck.append(hexsidelimit(hexone,hextwo,combatmove))
                            newcheck.append(y)
                            hexsidelimitchecks.append(newcheck)
                else:
                    allorders[y]=[allorders[y][0]]
            else:
                allorders[y]=[allorders[y][0]]
        for y in range(len(hexsidelimitchecks)):#compare hexsidelimitchecks to actual hexside limits and pick losers. delete unsuccessful units from HLC, delete all further orders for unsuccessful units
            while (len(hexsidelimitchecks[y])-3)>hexsidelimitchecks[y][2]:##something wrong is happening here sometimes i think
                print 'too many units are trying to cross this hexside, remove one'
                pick=randint(0,len(hexsidelimitchecks[y])-3)+3
                for z in range(1,len(allorders[hexsidelimitchecks[y][pick]])):
                    allorders[hexsidelimitchecks[y][pick]].remove(allorders[hexsidelimitchecks[y][pick]][1])
                kill=hexsidelimitchecks[y][pick]
                hexsidelimitchecks[y].reverse()
                hexsidelimitchecks[y].remove(kill)#this is it
                hexsidelimitchecks[y].reverse()
            hexsidelimitchecks[y][2]=hexsidelimitchecks[y][2]-(len(hexsidelimitchecks[y])-3)#reduce hexside limits
            print 'hexside limit remaining: ',hexsidelimitchecks[y][2]
        for y in range(len(allorders)):#deal with each successful move
            if len(allorders[y])>1:
                hexone=allunits[allorders[y][0]][UNIT_LOCATION]
                hextwo=allorders[y][1]
                allunits[allorders[y][0]][UNIT_PREVIOUS_LOCATION]=allunits[allorders[y][0]][UNIT_LOCATION]#save unit prev location for forces and trails and terrain
                if allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]>0:#deduct movement points
                    allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]=allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]-1
                else:
                    allunits[allorders[y][0]][UNIT_ROAD_MOVE_REMAINING]=0
                ##trails
                if HasRoad(hexone,hextwo)==0 or allunits[allorders[y][0]][UNIT_TYPE]==TYPE_AIR:#if move is not across a road hexside set UNIT_ROAD_MOVE_ONLY to 0
                    allunits[allorders[y][0]][UNIT_ROAD_MOVE_ONLY]=0
                allunits[allorders[y][0]][UNIT_LOCATION]=allorders[y][1]#move unit
                allunits[allorders[y][0]][UNIT_HEX_DURATION]=0
                print 'unit has been moved to: ',allunits[allorders[y][0]][UNIT_LOCATION]
                if len(buildfactionslist(buildcombatlist(allorders[y][1])))>1:
                    allorders[y]=[allorders[y][0]]#if combat, delete all further orders
                    print 'unit has moved into combat, so all further orders have been deleted'
                else:
                    allorders[y].remove(allorders[y][1])#otherwise delete current order
        for y in range(len(hexsidelimitchecks)):#remove all units from HLC
            hexsidelimitchecks[y]=[hexsidelimitchecks[y][0],hexsidelimitchecks[y][1],hexsidelimitchecks[y][2]]
        hexsideControlSweep()
    for x in range(len(allhexes)):#reset hexside control for combats where all of one side vacated. reset new combat as well
        presentfactions=[]
        for y in range(len(allunits)):
            if allunits[y][UNIT_LOCATION]==x:
                if allunits[y][UNIT_HEX_DURATION]!=0 and IsItThere(allfactions[allunits[y][UNIT_FACTION]],presentfactions)==0:
                    presentfactions.append(allfactions[allunits[y][UNIT_FACTION]])
        if len(presentfactions)==1:
            allhexes[x][HEX_N_CONTROL]=presentfactions[0]
            allhexes[x][HEX_NW_CONTROL]=presentfactions[0]
            allhexes[x][HEX_SW_CONTROL]=presentfactions[0]
            allhexes[x][HEX_S_CONTROL]=presentfactions[0]
            allhexes[x][HEX_SE_CONTROL]=presentfactions[0]
            allhexes[x][HEX_NE_CONTROL]=presentfactions[0]
            allhexes[x][HEX_NEW_COMBAT]=1
    AssignBonuses()
    for x in range(len(allunits)):#increase hex durations, set previous locations, set hexside control
        if allunits[x][UNIT_LOCATION]!=allunits[x][UNIT_PREVIOUS_LOCATION]:
            allhexes[allunits[x][UNIT_LOCATION]][WhichHexSideControlIndex(allunits[x][UNIT_LOCATION],allunits[x][UNIT_PREVIOUS_LOCATION])]=allfactions[allunits[x][UNIT_FACTION]]
        if allunits[x][UNIT_LOCATION]==allunits[x][UNIT_PREVIOUS_LOCATION]:
            allunits[x][UNIT_HEX_DURATION]=allunits[x][UNIT_HEX_DURATION]+1
        allunits[x][UNIT_PREVIOUS_LOCATION]=allunits[x][UNIT_LOCATION]
        if allunits[x][UNIT_TRANSPORT_ONE]!=-1 and allhexes[allunits[x][UNIT_LOCATION]]=='C' and EnemyShipsPresent(x)==0:#disembark transports
            allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_ALIVE]=1
            allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_LOCATION]=allunits[x][UNIT_LOCATION]
            allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_PREVIOUS_LOCATION]=allunits[x][UNIT_LOCATION]
            allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_HEX_DURATION]=0
            allunits[x][UNIT_TRANSPORT_ONE]=-1
            if buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION]))>1:
                allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_TERRAIN]=-15
                allunits[allunits[x][UNIT_TRANSPORT_ONE]][UNIT_HOLD_BONUS]=1
        if allunits[x][UNIT_TRANSPORT_TWO]!=-1 and allhexes[allunits[x][UNIT_LOCATION]][HEX_TERRAIN]=='C' and EnemyShipsPresent(x)==0:#disembark transports
            allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_ALIVE]=1
            allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_LOCATION]=allunits[x][UNIT_LOCATION]
            allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_PREVIOUS_LOCATION]=allunits[x][UNIT_LOCATION]
            allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_HEX_DURATION]=0
            if buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION]))>1:
                allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_TERRAIN]=-15
                allunits[allunits[x][UNIT_TRANSPORT_TWO]][UNIT_HOLD_BONUS]=1
            allunits[x][UNIT_TRANSPORT_TWO]=-1
def IsItThere(value,checklist):
    answer=0
    for x in checklist:
        if value==x:
            answer=1
    return answer
def EnemyShipsPresent(unit):
    checklist=buildcombatlist(allunits[unit][UNIT_LOCATION])
    enemyships=0
    for x in checklist:
        if allunits[x][UNIT_TYPE]==TYPE_SEA and allfactions[allunits[x][UNIT_FACTION]]!=allfactions[allunits[unit][UNIT_FACTION]]:
            enemyships=1
    return enemyships
def Adjacent(one,two):
    result=one-two
    direction=0
    if result==1:
        direction=1
    elif result==39: 
        direction=1
    elif result==38:
        direction=1
    elif result==-1:
        direction=1
    elif result==-39:
        direction=1
    elif result==-38:
        direction=1
    else:
        print 'Adjacent fucked up'
    return direction
def WhichHexSideControl(one,two):
    result=one-two
    direction=0
    if result==1:
        direction=int(allhexes[one][HEX_N_CONTROL])
    elif result==39: 
        direction=int(allhexes[one][HEX_NW_CONTROL])
    elif result==38:
        direction=int(allhexes[one][HEX_SW_CONTROL])
    elif result==-1:
        direction=int(allhexes[one][HEX_S_CONTROL])
    elif result==-39:
        direction=int(allhexes[one][HEX_SE_CONTROL])
    elif result==-38:
        direction=int(allhexes[one][HEX_NE_CONTROL])
    else:
        print 'whichhexsidecontrol fucked up'
    return direction
def WhichHexSideControlIndex(one,two):
    result=one-two
    direction=0
    if result==1:
        direction=HEX_N_CONTROL
    elif result==39: 
        direction=HEX_NW_CONTROL
    elif result==38:
        direction=HEX_SW_CONTROL
    elif result==-1:
        direction=HEX_S_CONTROL
    elif result==-39:
        direction=HEX_SE_CONTROL
    elif result==-38:
        direction=HEX_NE_CONTROL
    else:
        print 'whichhexsidecontrolindex fucked up'
    return direction
def AssignBonuses():
    for x in range(len(allhexes)):
        if len(buildfactionslist(buildcombatlist(x)))>1:#is there a combat there?
            forcelist=[[],[],[],[],[],[]]
            forcetotals=[0,0,0,0,0,0]
            forceorder=[]
            for y in range(len(allunits)):
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_PREVIOUS_LOCATION]!=x and allunits[y][UNIT_HOLD_BONUS]==0:
                    print 'Unit fulfills all other criteria, check hexside control:'
                    print 'Hexside controller faction:',WhichHexSideControl(x,allunits[y][UNIT_PREVIOUS_LOCATION])
                    print 'Unit faction:',allfactions[allunits[y][UNIT_FACTION]]
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_PREVIOUS_LOCATION]!=x and allunits[y][UNIT_HOLD_BONUS]==0 and WhichHexSideControl(x,allunits[y][UNIT_PREVIOUS_LOCATION])!=allfactions[allunits[y][UNIT_FACTION]]:#find units in the location that weren't already there, haven't already received flanking bonuses, and arrived through enemy hexsides
                    forcelist[WhichForce(allunits[y][UNIT_LOCATION],allunits[y][UNIT_PREVIOUS_LOCATION])].append(y)
            for z in range(len(forcelist)):#total forcelists into forcetotals
                for xx in range(len(forcelist[z])):
                    forcetotals[z]=forcetotals[z]+allunits[forcelist[z][xx]][UNIT_HIT_POINTS]
            forcetotalscopy=forcetotals[0:6]
            for z in range(len(forcetotalscopy)):#sort forcelists into forceorder
                highestfound=0
                highestindex=0
                for xx in range(len(forcetotalscopy)):
                    if forcetotalscopy[xx]>highestfound:
                        highestfound=forcetotalscopy[xx]
                        highestindex=xx
                if highestfound>0:
                    forceorder.append(highestindex)
                    forcetotalscopy[highestindex]=0
            count=0
            print 'forcelist:',forcelist
            print 'forcetotals:',forcetotals
            print 'forceorder:',forceorder
            if int(allhexes[x][HEX_NEW_COMBAT])==1:
                bonus=0
                checker=len(forceorder)
                print 'bonusassigner detects new combat'
            else:
                bonus=10
                checker=len(forceorder)
                print 'bonusassigner detects continuing combat'
            while count<checker:#assign flanking bonuses
                currentpick=[]
                for xx in range(count,len(forceorder)):#find all with same value as first in forceorder
                    if forcetotals[forceorder[xx]]==forcetotals[forceorder[count]]:
                        currentpick.append(forceorder[xx])
                while len(currentpick)>0:#from among this group assign flanking bonuses in random order
                    pick=randint(0,len(currentpick)-1)
                    print 'currentpick:',currentpick
                    print 'pick:',pick
                    for xx in forcelist[currentpick[pick]]:
                        allunits[xx][UNIT_FLANK]=bonus
                    bonus=bonus+10
                    count=count+1#skip remaining equally valued forces
                    currentpick.remove(currentpick[pick])
            for y in range(len(allunits)):
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_LOCATION]==allunits[y][UNIT_PREVIOUS_LOCATION] and allunits[y][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:#assign terrain bonuses
                    allunits[y][UNIT_TERRAIN]=TerrainBonus(x,allhexes[x][HEX_TERRAIN],y)
                    allunits[y][UNIT_HOLD_BONUS]=1
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_LOCATION]!=allunits[y][UNIT_PREVIOUS_LOCATION] and allunits[y][UNIT_HOLD_BONUS]==0 and allunits[y][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:#assign terrain bonuses
                    allunits[y][UNIT_TERRAIN]=TerrainBonus(x,HexsideTerrain(x,allunits[y][UNIT_PREVIOUS_LOCATION]),y)
                    allunits[y][UNIT_HOLD_BONUS]=1
                if  allunits[y][UNIT_CATEGORY]==CATEGORY_EXTERIOR_SIEGE:
                    allunits[y][UNIT_TERRAIN]=TerrainBonus(x,allhexes[x][HEX_TERRAIN],y)
                    allunits[y][UNIT_HOLD_BONUS]=1
def WhichForce(one,two):
    result=one-two
    force=-1
    if result==1:
        force=0
    elif result==39: 
        force=1
    elif result==38:
        force=2
    elif result==-1:
        force=3
    elif result==-39:
        force=4
    elif result==-38:
        force=5
    else:
        print 'which force Hexes not adjacent, invalid orders'
    return force
def TerrainBonus(terrainhex,hexsideterrain,unit):
    terrainmodifiers={'O':0,'F':-10,'M':-20,'S':-20,'C':0,'R':0,'W':0,'I':0,'K':0,'Q':0,'N':0}
    initialdefendermodifiers={'O':0,'F':0,'M':0,'S':-20,'C':0,'R':0,'W':0,'I':0,'K':0,'Q':0,'N':0}
    result=0
    if terrainmodifiers[allhexes[terrainhex][HEX_TERRAIN]]<terrainmodifiers[hexsideterrain]:
        result=terrainmodifiers[allhexes[terrainhex][HEX_TERRAIN]]
    else:
        result=terrainmodifiers[hexsideterrain]
    if hexsideterrain=='R':
        result=terrainmodifiers[allhexes[terrainhex][HEX_TERRAIN]]-15
    if hexsideterrain=='W':
        result=terrainmodifiers[allhexes[terrainhex][HEX_TERRAIN]]-25
    if allunits[unit][UNIT_TYPE]==TYPE_AIR:
        result=terrainmodifiers[allhexes[terrainhex][HEX_TERRAIN]]
    print 'unit hex duration: ',allunits[unit][UNIT_HEX_DURATION]
    if allunits[unit][UNIT_HEX_DURATION]>0 and int(allhexes[terrainhex][HEX_NEW_COMBAT])==1 and allunits[unit][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:
        print 'initial defender bonus applied'
        result=initialdefendermodifiers[allhexes[terrainhex][HEX_TERRAIN]]
    ##BASE SHIT
    return result
def HexsideTerrain(one,two):
    result=one-two
    terrain='X'
    if result==1:
        terrain=allhexes[one][HEX_N_TERRAIN]
    elif result==39: 
        terrain=allhexes[one][HEX_NW_TERRAIN]
    elif result==38:
        terrain=allhexes[one][HEX_SW_TERRAIN]
    elif result==-1:
        terrain=allhexes[one][HEX_S_TERRAIN]
    elif result==-39:
        terrain=allhexes[one][HEX_SE_TERRAIN]
    elif result==-38:
        terrain=allhexes[one][HEX_NE_TERRAIN]
    else:
        print 'hexside terrain Hexes not adjacent, invalid orders'
    return terrain
def HasRoad(one,two):
    result=one-two
    road=0
    if result==1 and allroads[one][ROAD_N]:
        road=1
    elif result==39 and allroads[one][ROAD_NW]: 
        road=1
    elif result==38 and allroads[one][ROAD_SW]:
        road=1
    elif result==-1 and allroads[one][ROAD_S]:
        road=1
    elif result==-39 and allroads[one][ROAD_SE]:
        road=1
    elif result==-38 and allroads[one][ROAD_NE]:
        road=1
    return road
def canMove(one,two,unit,combatmove):
    move=0
    terrain=allhexes[two][HEX_TERRAIN]
    sideterrain=HexsideTerrain(one,two)
    if ((allunits[unit][UNIT_TYPE]==TYPE_GROUND) and (terrain=='F' or terrain=='M' or terrain=='S' or terrain=='C' or terrain=='R' or terrain=='W') and (sideterrain=='F' or sideterrain=='M' or sideterrain=='S' or sideterrain=='C' or sideterrain=='R' or sideterrain=='W')):
        move=1
    if (allunits[unit][UNIT_TYPE]==TYPE_SEA) and ((allhexes[one][HEX_TERRAIN]=='O' and (terrain=='O' or terrain=='C')) or (allhexes[one][HEX_TERRAIN]=='C' and terrain=='O')) and (sideterrain=='O' or sideterrain=='K'):
        move=1
    if allunits[unit][UNIT_TYPE]==TYPE_AIR and terrain!='I':
        move=1
    if allunits[unit][UNIT_MOVEMENT_REMAINING]==0 and HasRoad(one,two)==0:
        move=0
    if allunits[unit][UNIT_CATEGORY]==CATEGORY_INTERIOR_SIEGE and allunits[unit][UNIT_TYPE]==TYPE_GROUND and (sideterrain!='C' and sideterrain!='F' and HasRoad(one,two)==0):
        move=0
    if int(allfactions[allunits[unit][UNIT_FACTION]])!=WhichHexSideControl(one,two):#check if moving out through enemy hexside
        move=0
    if combatmove==1 and allunits[unit][UNIT_COMBAT_START]==1:
        move=0
    if combatmove==1 and allunits[unit][UNIT_MOVEMENT_REMAINING]==0:
        move=0
    if sideterrain=='X':
        move=0
    if allunits[unit][UNIT_TYPE]==TYPE_GROUND and allunits[unit][UNIT_LOCATION]!=allunits[unit][UNIT_PREVIOUS_LOCATION] and (HexsideTerrain(allunits[unit][UNIT_LOCATION],allunits[unit][UNIT_PREVIOUS_LOCATION])!='C' and HexsideTerrain(allunits[unit][UNIT_LOCATION],allunits[unit][UNIT_PREVIOUS_LOCATION])!='F') and (allunits[unit][UNIT_ROAD_MOVE_ONLY]==0 or HasRoad(one,two)==0):
        move=0
    ##if unit is land and is not where it started and (sideterrain is not clear OR side terrain is not forest) and (hasn't been all on roads OR there isn't a road)
        ##stop movement
    if move==0:
        print "unit can't move"
    return move
    ##check if siege is moving across nonsiege hexsides
def movecombatcheck(unit,destination):#this borrows a function from combat
    dFactionsList=buildfactionslist(buildcombatlist(destination))
    combat=0
    for x in dFactionsList:
        if allfactions[allunits[unit][UNIT_FACTION]]!=x:
            combat=1
    return combat
def hexsidelimit(one,two,combat):
    terrain='what'
    result=one-two
    limit=0
    road=0
    if result==1:
        terrain=allhexes[one][HEX_N_TERRAIN]
        road=allroads[one][HEX_N_TERRAIN]
    elif result==39: 
        terrain=allhexes[one][HEX_NW_TERRAIN]
        road=allroads[one][HEX_NW_TERRAIN]
    elif result==38:
        terrain=allhexes[one][HEX_SW_TERRAIN]
        road=allroads[one][HEX_SW_TERRAIN]
    else:
        print 'Hexes not adjacent, invalid orders'
    if terrain=='X':
        limit=0
    if terrain=='O':
        limit=1000
    if terrain=='F':
        limit=2
    if terrain=='M':
        limit=1
    if terrain=='S':
        limit=1
    if terrain=='C':
        limit=4
    if terrain=='R':
        limit=1
    if terrain=='W':
        limit=1
    if terrain=='I':
        limit=1
    if terrain=='K' and combat==0:
        limit=2
    if terrain=='K' and combat==1:
        limit=1
    if terrain=='Q':
        limit=1
    if terrain=='N':
        limit=0
    if combat==0 and road==1:
        limit=limit+1
    print 'hexside limit: ',limit
    return limit


#COMBAT


def allcombat():#haha this is totally wrong
    for x in range(len(allhexes)):
        if len(buildfactionslist(buildcombatlist(x)))>1 and int(allhexes[x][HEX_BATTLE_FOUGHT])==0 and IsItThere(currentinitiative[0],buildfactionslist(buildcombatlist(x)))==1:
            combat(x)
            allhexes[x][HEX_BATTLE_FOUGHT]=1
            allhexes[x][HEX_NEW_COMBAT]=0
            for y in range(len(allunits)):
                if allunits[y][UNIT_LOCATION]==x:
                    allunits[y][UNIT_HOLD_BONUS]=0
                    allunits[y][UNIT_TERRAIN]=0
                    allunits[y][UNIT_FLANK]=0
        else:
            allhexes[x][HEX_NEW_COMBAT]=1
    reset()
def combat(battlehex):
    combatlist=buildcombatlist(battlehex)
    factionslist=buildfactionslist(combatlist)
    print 'hex new combat: ',allhexes[battlehex][HEX_NEW_COMBAT]
    if int(allhexes[battlehex][HEX_NEW_COMBAT])==1:
        print 'new combat'
        for x in range(len(categorylist)):
            for y in range(len(factionslist)):
                attacklastround=1
                while attacklastround==1:
                    attacklastround=0
                    attacker=chooseattacker(combatlist,categorylist[x],y,factionslist) ##(x=category, y=faction)
                    target=choosetarget(combatlist,attacker)
                    if attacker!=-1 and target!=-1:
                        print '                 ',allunits[attacker][UNIT_NAME]
                        dealDamage(calculateDamage(attacker),target, attacker)
                        attacklastround=1
                        allunits[attacker][UNIT_HOLD_BONUS]=0#take off the bonus hold, reset flank and terrain bonuses
                        allunits[attacker][UNIT_FLANK]=0
                        allunits[attacker][UNIT_TERRAIN]=0
    elif int(allhexes[battlehex][HEX_NEW_COMBAT])==0:
        print 'continuing combat'
        saveDamage=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        saveTarget=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        saveAttacker=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        for x in range(len(categorylist)):
            attacklastround=1
            while attacklastround==1:
                attacklastround=0
                for y in range(len(factionslist)):
                    attacker=chooseattacker(combatlist,x,y,factionslist) ##(x=category, y=faction)
                    target=choosetarget(combatlist,attacker)
                    if attacker!=-1 and target!=-1:
                        print '                 ',allunits[attacker][UNIT_NAME]
                        saveDamage[y]=calculateDamage(attacker)
                        saveAttacker[y]=attacker
                        saveTarget[y]=target
                        attacklastround=1
                        allunits[attacker][UNIT_HOLD_BONUS]=0#is this the right spot for these?
                        allunits[attacker][UNIT_FLANK]=0
                        allunits[attacker][UNIT_TERRAIN]=0
                for z in range(len(factionslist)):
                    if saveDamage[z]>-1:
                        dealDamage(saveDamage[z],saveTarget[z],saveAttacker[z])#need to save all this data, not just the damage
                saveDamage=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
                saveTarget=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        saveAttacker=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
##    print 'N hexside control: ',allhexes[battlehex][HEX_N_CONTROL]
##    print 'NE hexside control: ',allhexes[battlehex][HEX_NE_CONTROL]
##    print 'NW hexside control: ',allhexes[battlehex][HEX_NW_CONTROL]
##    print 'S hexside control: ',allhexes[battlehex][HEX_S_CONTROL]
##    print 'SW hexside control: ',allhexes[battlehex][HEX_SW_CONTROL]
##    print 'SE hexside control: ',allhexes[battlehex][HEX_SE_CONTROL]
def chooseattacker(combatlist,category,faction,factionslist):
    choicelist=[]
    highesthp=0
    for x in range(len(combatlist)):
        if allunits[combatlist[x]][UNIT_CATEGORY]==category and allfactions[allunits[combatlist[x]][UNIT_FACTION]]==factionslist[faction] and allunits[combatlist[x]][UNIT_FIRED]==0 and allunits[combatlist[x]][UNIT_HIT_POINTS]>highesthp and allunits[combatlist[x]][UNIT_HIT_POINTS]>0:
            choicelist=[]
            choicelist.append(combatlist[x])
            highesthp=allunits[combatlist[x]][UNIT_HIT_POINTS]
        if allunits[combatlist[x]][UNIT_CATEGORY]==category and allfactions[allunits[combatlist[x]][UNIT_FACTION]]==factionslist[faction] and allunits[combatlist[x]][UNIT_FIRED]==0 and allunits[combatlist[x]][UNIT_HIT_POINTS]==highesthp and allunits[combatlist[x]][UNIT_HIT_POINTS]>0:
            choicelist.append(combatlist[x])
    if len(choicelist)>0:
        return choicelist[randint(0,len(choicelist)-1)]
    else:
        return -1
def choosetarget(combatlist,attacker):
    choicelist=[]
    highesthp=0
    for x in range(len(combatlist)):
##        print 'possible target faction: ',allfactions[allunits[x][UNIT_FACTION]]
##        print 'attacker faction: ',allfactions[allunits[attacker][UNIT_FACTION]]
        if allfactions[allunits[combatlist[x]][UNIT_FACTION]]!=allfactions[allunits[attacker][UNIT_FACTION]] and allunits[combatlist[x]][UNIT_HIT_POINTS]>highesthp and canHit(attacker,combatlist[x])==1 and allunits[combatlist[x]][UNIT_HIT_POINTS]>0 and allunits[combatlist[x]][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:
            choicelist=[]
            highesthp=allunits[combatlist[x]][UNIT_HIT_POINTS]
            choicelist.append(combatlist[x])
        if allfactions[allunits[combatlist[x]][UNIT_FACTION]]!=allfactions[allunits[attacker][UNIT_FACTION]] and allunits[combatlist[x]][UNIT_HIT_POINTS]==highesthp and canHit(attacker,combatlist[x])==1 and allunits[combatlist[x]][UNIT_HIT_POINTS]>0 and allunits[combatlist[x]][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:
            choicelist.append(combatlist[x])
    if len(choicelist)>0:
        return choicelist[randint(0,len(choicelist)-1)]
        print 'target chosen'
    else:
        return -1
def buildcombatlist(hex):
    combatlist=[]
    for x in range(len(allunits)):
        if allunits[x][UNIT_LOCATION]==hex and allunits[x][UNIT_ALIVE]==1:
            combatlist.append(x)
    return combatlist
def buildfactionslist(combatlist):
    factionslist=[]
    donotcopy=0
    for x in range(len(combatlist)):
        if len(factionslist)>0:
            for y in range(len(factionslist)):
                if allfactions[allunits[combatlist[x]][UNIT_FACTION]]==factionslist[y]:
                    donotcopy=1
        if donotcopy==0:
            factionslist.append(allfactions[allunits[combatlist[x]][UNIT_FACTION]])
        donotcopy=0
    reverse=0
    for x in range(1,len(combatlist)):
        if allunits[combatlist[0]][UNIT_HEX_DURATION]<allunits[combatlist[x]][UNIT_HEX_DURATION]:
            reverse=1
    if reverse==1:
        factionslist.reverse()
    return factionslist
def canHit(attacker, target):
    canbehit=0
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_EXTERIOR_SIEGE or allunits[attacker][UNIT_CATEGORY]==CATEGORY_INTERIOR_SIEGE) and (allunits[target][UNIT_TYPE]==TYPE_GROUND or allunits[target][UNIT_TYPE]==TYPE_SEA):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_RANGED) and (allunits[attacker][UNIT_TYPE]==TYPE_GROUND) and (allunits[target][UNIT_TYPE]==TYPE_GROUND):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_RANGED) and (allunits[attacker][UNIT_TYPE]==TYPE_GROUND) and (allunits[target][UNIT_TYPE]==TYPE_AIR):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_RANGED) and (allunits[attacker][UNIT_TYPE]==TYPE_SEA) and (allunits[target][UNIT_TYPE]==TYPE_AIR):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_RANGED) and (allunits[attacker][UNIT_TYPE]==TYPE_SEA) and (allunits[target][UNIT_TYPE]==TYPE_SEA):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_RANGED) and (allunits[attacker][UNIT_TYPE]==TYPE_AIR):
        canbehit=1
    if (allunits[attacker][UNIT_CATEGORY]==CATEGORY_MELEE) and (allunits[target][UNIT_TYPE]==TYPE_GROUND):
        canbehit=1
    return canbehit
def calculateDamage(attacker):
    damageDone = 0
    print 'Attacker combat: ',allunits[attacker][UNIT_COMBAT] + allunits[attacker][UNIT_FLANK] + allunits[attacker][UNIT_TERRAIN],' (stat:',allunits[attacker][UNIT_COMBAT],',flank:',allunits[attacker][UNIT_FLANK],',terrain:',allunits[attacker][UNIT_TERRAIN],')'
    print 'Attacker HP: ',allunits[attacker][UNIT_HIT_POINTS]
    damageRoll = allunits[attacker][UNIT_COMBAT] + allunits[attacker][UNIT_FLANK] + allunits[attacker][UNIT_TERRAIN]
    for i in range(allunits[attacker][UNIT_HIT_POINTS]):
        if randint(1,100) <= damageRoll:
            damageDone = damageDone +1
    allunits[attacker][UNIT_FIRED] = 1
    print 'unit fired: ',allunits[attacker][UNIT_FIRED]
    print attacker
    return damageDone
def dealDamage(damage, defender,attacker): # passed two integers referring to the number of hits rolled by the attacker and the target's index
    defenderHitsTaken = hitsTaken(damage,defender)
    resolveDefenderHP(defenderHitsTaken, defender)
    print 'Attacker has done ',defenderHitsTaken,' worth of damage to ',allunits[defender][UNIT_NAME],', reducing it to ',allunits[defender][UNIT_HIT_POINTS],' life.'
    print ' '
def hitsTaken(damage,defender): # passed damage
    damagesave=damage
    print 'damage is ',damage
    damage = damage - allunits[defender][UNIT_LIGHT_CURRENT] # reduce damage done based on light armor
    print 'damage is now ',damage,' after light armor'
    allunits[defender][UNIT_LIGHT_CURRENT] = allunits[defender][UNIT_LIGHT_CURRENT] - damagesave # update the defending unit's light armor stat
    
 

    if allunits[defender][UNIT_LIGHT_CURRENT] < 0:

        allunits[defender][UNIT_LIGHT_CURRENT] = 0
    print 'target now has ',allunits[defender][UNIT_LIGHT_CURRENT],' light armor'
     

    if  allunits[defender][UNIT_ARMORBROKEN] == 0 and damage <= allunits[defender][UNIT_HEAVY]: # if attack can0t penetrate heavy armor, immediately return 0 damage done and end function.
        print 'attack did not penetrate heavy armor'
        return 0

     

    if allunits[defender][UNIT_ARMORBROKEN] == 0 and damage > allunits[defender][UNIT_HEAVY]: # if attack penetrates but heavy armor exists, adjust damage done for armor and update defender's armor stats
        print 'target is armorbroken if it had heavy armor'
        allunits[defender][UNIT_ARMORBROKEN] = 1

        damage = damage - allunits[defender][UNIT_HEAVY]

    damage = damage - allunits[defender][UNIT_NATURAL] # subtract for natural armor
    print 'damage has been reduced to ',damage,' by natural armor'
    if damage < 0: # adjust for nonzero values

        damage = 0

    if damage > allunits[defender][UNIT_HIT_POINTS]: #adjust for too much damage

        damage=allunits[defender][UNIT_HIT_POINTS]

    return damage # return damage done as int

def resolveDefenderHP(hitsTaken,defender):
    allunits[defender][UNIT_HIT_POINTS]=allunits[defender][UNIT_HIT_POINTS]-hitsTaken
    if allunits[defender][UNIT_HIT_POINTS] < 1:
        allunits[defender][UNIT_ALIVE]=0
        print 'Defender is dead.'

        
#STATUS SHIT

def generateVision(currentfaction):
    visiblehexes=[]
    for x in range(len(allunits)):
        if allfactions[allunits[x][UNIT_FACTION]]==allfactions[currentfaction] and allunits[x][UNIT_ALIVE]==1:
            currentvisible=[allunits[x][UNIT_LOCATION]]
            for count in range(0,allunits[x][UNIT_VISION]):
                newadditions=[]
                for y in range(len(currentvisible)):
                    if Adjacent(currentvisible[y],currentvisible[y]+1)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='S'):
                        newadditions.append(currentvisible[y]+1)
                    if Adjacent(currentvisible[y],currentvisible[y]-1)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='S'):
                        newadditions.append(currentvisible[y]-1)
                    if Adjacent(currentvisible[y],currentvisible[y]+38)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='S'):
                        newadditions.append(currentvisible[y]+38)
                    if Adjacent(currentvisible[y],currentvisible[y]-38)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='S'):
                        newadditions.append(currentvisible[y]-38)
                    if Adjacent(currentvisible[y],currentvisible[y]+39)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='S'):
                        newadditions.append(currentvisible[y]+39)
                    if Adjacent(currentvisible[y],currentvisible[y]-39)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='S'):
                        newadditions.append(currentvisible[y]-39)
                for y in range(len(newadditions)):
                    if IsItThere(newadditions[y],currentvisible)==0:
                        currentvisible.append(newadditions[y])
            for y in range(len(currentvisible)):
                if IsItThere(currentvisible[y],visiblehexes)==0:
                    visiblehexes.append(currentvisible[y])
    for x in range(len(allbases)):
        if allfactions[allbases[x][BASE_FACTION]]==allfactions[currentfaction]:
            currentvisible=[allbases[x][BASE_LOCATION]]
            for count in range(0,allbases[x][BASE_TIER]):
                newadditions=[]
                for y in range(len(currentvisible)):
                    if Adjacent(currentvisible[y],currentvisible[y]+1)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+1)!='S'):
                        newadditions.append(currentvisible[y]+1)
                    if Adjacent(currentvisible[y],currentvisible[y]-1)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-1)!='S'):
                        newadditions.append(currentvisible[y]-1)
                    if Adjacent(currentvisible[y],currentvisible[y]+38)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+38)!='S'):
                        newadditions.append(currentvisible[y]+38)
                    if Adjacent(currentvisible[y],currentvisible[y]-38)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-38)!='S'):
                        newadditions.append(currentvisible[y]-38)
                    if Adjacent(currentvisible[y],currentvisible[y]+39)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]+39)!='S'):
                        newadditions.append(currentvisible[y]+39)
                    if Adjacent(currentvisible[y],currentvisible[y]-39)==1 and (HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='X' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='F' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='M' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='Q' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='N' and HexsideTerrain(currentvisible[y],currentvisible[y]-39)!='S'):
                        newadditions.append(currentvisible[y]-39)
                for y in range(len(newadditions)):
                    if IsItThere(newadditions[y],currentvisible)==0:
                        currentvisible.append(newadditions[y])
            for y in range(len(currentvisible)):
                if IsItThere(currentvisible[y],visiblehexes)==0:
                    visiblehexes.append(currentvisible[y])
    allhexescurrent=copy.deepcopy(allhexes)
    for x in range(len(allhexescurrent)):
        if IsItThere(x,visiblehexes)==0:
            allhexescurrent[x][7]=0
            for y in range(9,22):
                allhexescurrent[x][y]=-1
    allunitscurrent=[]
    allunitscurrentlegend=[]
    for x in range(len(allunits)):
        if IsItThere(allunits[x][UNIT_LOCATION],visiblehexes)==1 and allunits[x][UNIT_ALIVE]==1:
            allunitscurrent.append(allunits[x])
            allunitscurrentlegend.append(x)
        if allunits[x][UNIT_ALIVE]==0:
            for y in range(len(allunits)):
                if allunits[y][UNIT_TRANSPORT_ONE]==x:
                    allunitscurrent.append(allunits[x])
                    allunitscurrentlegend.append(x)
                if allunits[y][UNIT_TRANSPORT_TWO]==x:
                    allunitscurrent.append(allunits[x])
                    allunitscurrentlegend.append(x)
                if allunits[y][UNIT_TRANSPORT_THREE]==x:
                    allunitscurrent.append(allunits[x])
                    allunitscurrentlegend.append(x)
    for x in range(len(allunitscurrent)):
        if allunitscurrent[x][UNIT_TRANSPORT_ONE]!=-1:
            print allunitscurrent[x]
            print allunitscurrentlegend
            allunitscurrent[x][UNIT_TRANSPORT_ONE]=allunitscurrentlegend[allunitscurrent[x][UNIT_TRANSPORT_ONE]]
        if allunitscurrent[x][UNIT_TRANSPORT_TWO]!=-1:
            allunitscurrent[x][UNIT_TRANSPORT_TWO]=allunitscurrentlegend[allunitscurrent[x][UNIT_TRANSPORT_TWO]]
        if allunitscurrent[x][UNIT_TRANSPORT_THREE]!=-1:
            allunitscurrent[x][UNIT_TRANSPORT_THREE]=allunitscurrentlegend[allunitscurrent[x][UNIT_TRANSPORT_THREE]]
    allbasescurrent=[]
    allbasescurrentlegend=[]
    for x in range(len(allbases)):
        if IsItThere(allbases[x][BASE_LOCATION],visiblehexes)==1:
            allbasescurrent.append(allbases[x])
            allbasescurrentlegend.append(x)

    # save current data to DB
    db = load_db()

    hexdata_cur = db.cursor()
    hexdata_cur.execute("TRUNCATE currenthexes")
    for x in allhexescurrent:
        templist = tuple(x)
        hexdata_cur.execute("INSERT INTO currenthexes VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", templist)
    hexdata_cur.close()

    unitdata_cur = db.cursor()
    unitdata_cur.execute("TRUNCATE currentunits")
    for x in allunitscurrent:
        saverow=[]
        for y in range(len(x)):
            if y==0 or 13<y<18:
                saverow.append(x[y])
            elif 9<y<14 or y>17:
                saverow.append(int((x[y])))
        templist = tuple(saverow)
        unitdata_cur.execute("INSERT INTO currentunits VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", templist)
    unitdata_cur.close()
    
    basedata_cur = db.cursor()
    basedata_cur.execute("TRUNCATE currentbases")
    for x in allbasescurrent:
        templist = tuple(x)
        basedata_cur.execute("INSERT INTO currentbases VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", templist)
    basedata_cur.close()

    unitlegend_cur = db.cursor()
    unitlegend_cur.execute("TRUNCATE currentunitslegend")
    for x in allunitscurrentlegend:
        # templist = tuple(x)
        unitlegend_cur.execute("INSERT INTO currentunitslegend VALUES (%s)", x)
    unitlegend_cur.close()

    baselegend_cur = db.cursor()
    baselegend_cur.execute("TRUNCATE currentbaseslegend")
    for x in allbasescurrentlegend:
        # templist = tuple(x)
        baselegend_cur.execute("INSERT INTO currentbaseslegend VALUES (%s)", x)
    baselegend_cur.close()

    factiondata_cur = db.cursor()
    saved_faction_data = [currentfaction]
    factiondata_cur.execute("TRUNCATE currentfaction")
    factiondata_cur.execute("INSERT INTO currentfaction VALUES (%s)", saved_faction_data)
    factiondata_cur.close()

    visiondata_cur = db.cursor()
    visiondata_cur.execute("TRUNCATE currentvision")
    for x in visiblehexes:
        visiondata_cur.execute("INSERT INTO currentvision VALUES (%s)", x)
    visiondata_cur.close()

    buildables_cur = db.cursor()
    buildables_cur.execute("TRUNCATE currentbuildables")
    buildables_templist = tuple(allbuildables[currentfaction])
    buildables_cur.execute("INSERT INTO currentbuildables VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", buildables_templist)
    buildables_cur.close()

    #commit changes and close connection
    db.commit()
    db.close()
        
def reset():#this is run at the end of every combat to do basic resets (light armor, armorbroken, fired), will need another one for the end of the round/end of horde/alliance turns
    for x in range(len(allunits)):
        allunits[x][UNIT_FIRED]=0
        allunits[x][UNIT_LIGHT_CURRENT]=allunits[x][UNIT_LIGHT_MAX]
        allunits[x][UNIT_ARMORBROKEN]=0
        allunits[x][UNIT_MOVEMENT_REMAINING]=allunits[x][UNIT_MOVEMENT_MAX]#these movement things may not belong here
        allunits[x][UNIT_ROAD_MOVE_REMAINING]=1
        allunits[x][UNIT_ROAD_MOVE_ONLY]=1
        if allunits[x][UNIT_CATEGORY]==CATEGORY_EXTERIOR_SIEGE:#KILL THE GHOSTS
            allunits[x][UNIT_ALIVE]=0
def hexsideControlSweep():#checks for noncombat hexes and sets control to defender
    for x in range(len(allhexes)):
        dFactionsList=buildfactionslist(buildcombatlist(x))
        if len(dFactionsList)==1:
            allhexes[x][HEX_N_CONTROL]=dFactionsList[0]
            allhexes[x][HEX_NW_CONTROL]=dFactionsList[0]
            allhexes[x][HEX_SW_CONTROL]=dFactionsList[0]
            allhexes[x][HEX_S_CONTROL]=dFactionsList[0]
            allhexes[x][HEX_SE_CONTROL]=dFactionsList[0]
            allhexes[x][HEX_NE_CONTROL]=dFactionsList[0]
def InitSetStuff():
    for x in range(len(allunits)):
        allunits[x][UNIT_PREVIOUS_LOCATION]=allunits[x][UNIT_LOCATION]
        allunits[x][UNIT_HEX_DURATION]=1
        allunits[x][UNIT_TRANSPORT_ONE]=-1
        allunits[x][UNIT_TRANSPORT_TWO]=-1
    for x in range(len(allhexes)):
        allhexes[x][HEX_NEW_COMBAT]=1
def countFood():
    for x in range(len(allbases)):
        FOOD_SURPLUS[allbases[x][BASE_FACTION]]=FOOD_SURPLUS[allbases[x][BASE_FACTION]]+allbases[x][BASE_TIER]
    for x in range(len(allhexes)):
        if int(allhexes[x][HEX_FARM])!=-1:
            for y in range(len(allbases)):
                if int(allbases[y][BASE_LOCATION])==int(allhexes[x][HEX_FARM]):
                    FOOD_SURPLUS[allbases[y][BASE_FACTION]]=FOOD_SURPLUS[allbases[y][BASE_FACTION]]+1
    for x in range(len(allunits)):
        FOOD_SURPLUS[allunits[x][UNIT_FACTION]]=FOOD_SURPLUS[allunits[x][UNIT_FACTION]]-1
    print FOOD_SURPLUS


def SaveGame():
    # save current data to DB
    db = load_db()

    # clear orders, economicactions, specialorders
    clearorders_cur = db.cursor()
    clearorders_cur.execute("TRUNCATE orders")
    clearorders_cur.close()
    cleareconomics_cur = db.cursor()
    cleareconomics_cur.execute("TRUNCATE economicactions")
    cleareconomics_cur.close()
    clearspecialorders_cur = db.cursor()
    clearspecialorders_cur.execute("TRUNCATE specialorders")
    clearspecialorders_cur.close()
    
    hexdata_cur = db.cursor()
    hexdata_cur.execute("TRUNCATE savehexes")
    for x in allhexes:
        templist = tuple(x)
        hexdata_cur.execute("INSERT INTO savehexes VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", templist)
    hexdata_cur.close()

    buildables_cur = db.cursor()
    buildables_cur.execute("TRUNCATE savebuildables")
    for x in allbuildables:
        templist = tuple(x)
        buildables_cur.execute("INSERT INTO savebuildables VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", templist)
    buildables_cur.close()

    unitdata_cur = db.cursor()
    unitdata_cur.execute("TRUNCATE saveunits")
    for x in allunits:
        saverow=[]
        for y in range(len(x)):
            if y==0 or 13<y<18:
                saverow.append(x[y])
            elif 9<y<14 or y>17:
                saverow.append(int((x[y])))
        templist = tuple(saverow)
        unitdata_cur.execute("INSERT INTO saveunits VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", templist)
    unitdata_cur.close()

    basedata_cur = db.cursor()
    basedata_cur.execute("TRUNCATE savebases")
    for x in allbases:
        templist = tuple(x)
        basedata_cur.execute("INSERT INTO savebases VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", templist)
    basedata_cur.close()

    factiondata_cur = db.cursor()
    factiondata_cur.execute("TRUNCATE savefactions")
    faction_templist = tuple(allfactions)
    factiondata_cur.execute("INSERT INTO savefactions VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", faction_templist)
    factiondata_cur.close()

    # initiative_cur = db.cursor()
    # initiative_cur.execute("TRUNCATE currentinitiative")
    # initiative_cur.execute("INSERT INTO currentinitiative VALUES (%s)", currentinitiative)
    # initiative_cur.close()

    #commit data and close database
    db.commit()
    db.close()

def translateclient():######jimnir needs to add these declarations
    ACTION_NAME=0
    ACTION_HEX=1#most functions use this unless another index 1 is specified

    ACTION_UNIT=2#give base    

    ACTION_RECIPIENT_BASE=2#give expansion (hex here refers to the hex of the expansion; ownerbase to its parent base
    ACTION_OWNER_BASE=3
    ACTION_TARGET_EXPANSION=2
    ACTION_TARGET_BASE=3

    ACTION_RESOURCE_IN=2#commerce
    ACTION_RESOURCE_OUT=3

    ACTION_UNIT_TYPE=2#build unit

    ACTION_EXPAND_HEX=2#expand

    ACTION_CARAVAN_PATH=1#establish caravan
    ACTION_CARAVAN_ORIGIN_BASE=2
    ACTION_CARAVAN_DESTINATION_BASE=3
    ACTION_CARAVAN_FACTION=4
    ACTION_CARAVAN_TYPE=5

    ACTION_SEND_ORIGIN=1#send resources
    ACTION_SEND_DESTINATION=2
    ACTION_SEND_GOLD=3
    ACTION_SEND_LUMBER=4
    ACTION_SEND_OIL=5 
    loadcurrentunitslegend()
    loadcurrentbaseslegend()
    for x in range(len(allorders)):
        allorders[x][0]=int(unitslegend[allorders[x][0]])
##    for x in range(len(alleconomicactions)):
##        if alleconomicactions[x][0]=='Give Base':
##            alleconomicsactions[x][ACTION_UNIT]=unitslegend[alleconomicsactions[x][ACTION_UNIT]]
##        if alleconomicactions[x][0]=='Give Expansion':
##            alleconomicactions[x][ACTION_RECIPIENT_BASE]=baseslegend[alleconomicactions[x][ACTION_RECIPIENT_BASE]]
##            alleconomicactions[x][ACTION_OWNER_BASE]=baseslegend[alleconomicactions[x][ACTION_OWNER_BASE]]
##        if alleconomicactions[x][0]=='Establish Caravan':#unfinished
##            alleconomicactions[x][?]=baseslegend[alleconomicactions[x][?]]
##            alleconomicsactions[x][?]=unitslegend[alleconomicsactions[x][?]]
##        if alleconomicactions[x][0]=='Send Resources':#unfinished
##            alleconomicactions[x][?]=baseslegend[alleconomicactions[x][?]]
##            alleconomicsactions[x][?]=unitslegend[alleconomicsactions[x][?]]
    for x in range(len(allspecialorders)):
        allspecialorders[x][1]=int(unitslegend[allspecialorders[x][1]])
        if allspecialorders[x][0]=='Board Transport':
            ORDER_TARGET_TRANSPORT=2
            allspecialorders[x][ORDER_TARGET_TRANSPORT]=int(unitslegend[allspecialorders[x][ORDER_TARGET_TRANSPORT]])
    for x in range(len(alleconomicactions)):######jimnir needs this
        if alleconomicactions[x][0]=='Give Base':
            alleconomicactions[x][ACTION_UNIT]=int(unitslegend[int(alleconomicactions[x][ACTION_UNIT])])
        #if alleconomicactions[x][0]=='Give Expansion': #commented because it records hexes, not base IDs
            #alleconomicactions[x][ACTION_RECIPIENT_BASE]=int(baseslegend[int(alleconomicactions[x][ACTION_RECIPIENT_BASE])])
            #alleconomicactions[x][ACTION_OWNER_BASE]=int(baseslegend[int(alleconomicactions[x][ACTION_OWNER_BASE])])
        if alleconomicactions[x][0]=='Establish Caravan':
            alleconomicactions[x][ACTION_CARAVAN_ORIGIN_BASE]=int(baseslegend[int(alleconomicactions[x][ACTION_CARAVAN_ORIGIN_BASE])])
            alleconomicactions[x][ACTION_CARAVAN_DESTINATION_BASE]=int(baseslegend[int(alleconomicactions[x][ACTION_CARAVAN_DESTINATION_BASE])])
        if alleconomicactions[x][0]=='Send Resources':
            alleconomicactions[x][ACTION_SEND_ORIGIN]=int(baseslegend[int(alleconomicactions[x][ACTION_SEND_ORIGIN])])
            alleconomicactions[x][ACTION_SEND_DESTINATION]=int(baseslegend[int(alleconomicactions[x][ACTION_SEND_DESTINATION])])

def destroyStuff():######jimnir needs this
    for x in range(len(allhexes)):
        if len(buildfactionslist(buildcombatlist(x)))==1:#if there's only one faction there
            for y in range(len(allbases)):
                if allbases[y][BASE_LOCATION]==x and allbases[y][BASE_TIER]>0 and buildfactionslist(buildcombatlist(x))[0]!=int(allfactions[allbases[y][BASE_FACTION]]):#if that faction doesn't match the base
                    destroyBase(allbases[y][BASE_LOCATION])
                if int(allhexes[x][HEX_FARM])==int(allbases[y][BASE_LOCATION]) and int(allfactions[allbases[y][BASE_FACTION]])!=int(buildfactionslist(buildcombatlist(x))[0]):
                    allhexes[x][HEX_FARM]=-1
                if int(allhexes[x][HEX_MILL])==int(allbases[y][BASE_LOCATION]) and int(allfactions[allbases[y][BASE_FACTION]])!=int(buildfactionslist(buildcombatlist(x))[0]):
                    allhexes[x][HEX_MILL]=-1
                if int(allhexes[x][HEX_RIG])==int(allbases[y][BASE_LOCATION]) and int(allfactions[allbases[y][BASE_FACTION]])!=int(buildfactionslist(buildcombatlist(x))[0]):
                    allhexes[x][HEX_RIG]=-1
  
def TestGameStart():
    resetturns()
    resetorders()
    loadunits()
    loadmap()
    loadroads()
    loadbases()#update
    loadfactions()#jim put this in
    loadbuildables()
    loadinitiative()    
    InitSetStuff()
    reset()
    hexsideControlSweep()
    SaveGame()
    blank=[]
    allunits=copy.deepcopy(blank)
    allhexes=copy.deepcopy(blank)
    allbases=copy.deepcopy(blank)
    allroads=copy.deepcopy(blank)
##    for x in range(len(allunits)):
##        print factiondictionary[allunits[x][UNIT_FACTION]],allunits[x][UNIT_NAME],allunits[x][UNIT_HIT_POINTS]
##        print allunits[x][UNIT_LOCATION]
def TestGameSave():
    loadsavedunits()
    loadsavedmap()
    loadroads()
    loadsavedbases()#update
    loadsavedfactions()#jim put this in too
    loadorders()
    loadspecialorders()
    loadbuildables()
    loadcurrentinitiative()
    print currentinitiative[0]
    loadeconomicactions()
    translateclient()
    reset()
    hexsideControlSweep()
    countFood()
    specialorders()
    moveunits()
    allcombat()
    economicactions()
    #buildbases()
    if currentinitiative==4 or currentinitiative==13:
        for x in allhexes:
            x[HEX_BATTLE_FOUGHT]=0
    destroyStuff()
    SaveGame()
    resetturns()
def TestGameContinue():
    reset()
    hexsideControlSweep()
def generateTurn(faction):
    loadsavedunits()
    loadsavedmap()
    loadroads()
    loadsavedbases()#update
    loadsavedfactions()
    loadbuildables()
    generateVision(faction)

def generateInitiativeTurn():
    loadsavedunits()
    loadsavedmap()
    loadroads()
    loadsavedbases()#update
    loadsavedfactions()#also this is jim who put this in
    loadbuildables()
    updateInitiative()
    faction = getCurrentFaction()
    if faction != -1:
        generateVision(faction)

def continueInitiativeTurn():
    loadsavedunits()
    loadsavedmap()
    loadroads()
    loadsavedbases()#update
    loadsavedfactions()
    loadbuildables()
    faction = getCurrentFaction()
    if faction != -1:
        generateVision(faction)
    
active=1
while active==1:#main menu
    choice=ordermenu('Main Menu','Set Start Positions','Generate Turn','Resolve Orders','Quit NYI', 'Generate Initiative Turn')
    if choice==0:
        TestGameStart()
    if choice==1:
        subactive=1
        while subactive==1:
            print 'Please input faction ID.'
            subchoice=raw_input()
            if subchoice.isdigit():
                if -1<int(subchoice)<len(allfactions):
                    subactive=0
                    generateTurn(int(subchoice))
    if choice==2:
        TestGameSave()
    if choice==3:
        active=0
    if choice==4:
        if checkturns() == 0:
            generateInitiativeTurn()
        elif checkturns() == 1:
            continueInitiativeTurn()
        else:
            print 'something fucked up'
        
##    for x in range(len(allunits)):
##        print factiondictionary[allunits[x][UNIT_FACTION]],allunits[x][UNIT_NAME],allunits[x][UNIT_HIT_POINTS]
##        print allunits[x][UNIT_LOCATION]
##TestGameStart()
##loadunits()
##loadmap()
##loadroads()
##loadorders()
##loadspecialorders()
##InitSetStuff()
##reset()
##hexsideControlSweep()
##returneddata=movechecker.movecheckermain(allroads,allhexes,allunits,allorders)
##print returneddata
##movedata=csv.writer(open('successfulmoves.csv','wb'))
##for x in returneddata[1]:
##    movedata.writerow(x)
