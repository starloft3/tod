import pygame, sys, time, copy, string
from pygame.locals import *
import csv
import MySQLdb
import inputbox

#DATABASE VARIABLES
host_var="warcraft-db.cvs4kmdmsx2d.us-east-1.rds.amazonaws.com"
port_var=3306
user_var="wcadmin"
passwd_var="sythegar"
db_var="warcraft"

#DEBUG TOOLS
DEBUG_HEXCHECKER = 0

#SCROLLING VARIABLES
#X_CORD_SCROLL=-3400
#Y_CORD_SCROLL=-6500

#create local data copies

#define globals
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
UNIT_STEALTH=10
UNIT_FACTION=11
UNIT_HIT_POINTS=12
UNIT_LOCATION=13
UNIT_TIER=14
UNIT_TIER_1=15
UNIT_TIER_2=16
UNIT_TIER_3=17
UNIT_TIER_4=18
UNIT_ALIVE=19
UNIT_HEX_DURATION=20
UNIT_FIRED=21
UNIT_LIGHT_CURRENT=22
UNIT_ARMORBROKEN=23
UNIT_TERRAIN=24
UNIT_FLANK=25
UNIT_MOVEMENT_REMAINING=26
UNIT_ROAD_MOVE_REMAINING=27
UNIT_ROAD_MOVE_ONLY=28
UNIT_PREVIOUS_LOCATION=29
UNIT_HOLD_BONUS=30
UNIT_COMBAT_START=31
UNIT_TIER_1_DATA=32
UNIT_TIER_2_DATA=33
UNIT_TIER_3_DATA=34
UNIT_TIER_4_DATA=35
UNIT_TRANSPORT_ONE=36
UNIT_TRANSPORT_TWO=37
UNIT_TRANSPORT_THREE=38
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
FACTION_DATA_MOUNTAINEER=32
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
BASE_ALIVE=7
#ALLHEXES FIX FIX FIX FIX FIX
HEX_TERRAIN=0
HEX_N_TERRAIN=1
HEX_NE_TERRAIN=2
HEX_SE_TERRAIN=3
HEX_S_TERRAIN=4
HEX_SW_TERRAIN=5
HEX_NW_TERRAIN=6
HEX_BUILDING=7# non-base building
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
HEX_EXPANSION_OWNER=22

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
alterachome=[476,514,553,554,555,591,592,593,630,631,668]
gilneashome=[20,21,58,59,60,61,62,96,97,98,99,100,101,134,135,136,137,138,139,140,172,173,174,175,176,177,178,179,210,211,212,213,214,215,216,217,253,254,255]
silvermoonhome=[463,464,502,503,504,540,695,696,699,700,701,734,736,738,739,773,774,775,776,777,778,811,812,813,814,815,816,849,850,851,852,853,854,887,888,889,890,891,926,927,928,929,966,967,968,1006]
factiondictionary={0:'Amani',1:'Bleeding Hollow',2:'Black Tooth Grin',3:'Dragonmaw',4:'Stormreaver',5:"Twilight's Hammer",6:'Blackrock',7:'Silvermoon',8:'Aerie Peak',9:'Ironforge',10:'Dalaran',11:'Kul Tiras',12:'Stromgarde',13:'Azeroth',14:'Lordaeron',15:'Gilneas',16:'Alterac',17:'Dark Iron',18:'Burning Blade',19:'Frostwolf',20:'Dalaran Rebel',21:'Gilnean Rebel',22:'Firetree',23:'Smolderthorn',24:'Shadowpine',25:'Shadowglen',26:'Revantusk',27:'Mossflayer',28:'Witherbark',29:'Vilebranch',30:'Dragon',31:'Demon'}
colordictionary={
    0:(27, 135, 34),
    1:(42, 236, 171),
    2:(0, 0, 0),
    3:(255, 255, 255),
    4:(61, 86, 245),
    5:(120, 35, 151),
    6:(230, 63, 63),
    7:(255, 255, 162),
    8:(255, 255, 0),
    9:(141, 27, 46),
    10:(226, 116, 226),
    11:(134, 235, 138),
    12:(230, 63, 63),
    13:(61, 86, 245),
    14:(255, 255, 255),
    15:(0, 0, 0),
    16:(245, 183, 61),
    17:(141, 27, 46),
    18:(245, 183, 61),
    19:(255, 255, 255),
    20:(226, 116, 226),
    21:(0, 0, 0)
    }
replacedictionary={"'":"", " ":""}
categorylist=[CATEGORY_EXTERIOR_SIEGE,CATEGORY_RANGED,CATEGORY_MELEE,CATEGORY_INTERIOR_SIEGE]#this can be replaced by just a loop through the numbers, but change it elsewhere before deleting
allfactionsB=[0,5,5,5,5,5,5,6,6,7,15,9,10,15,15,13,14,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
nearbyfoglist=[-40,-39,-38,-37,-36,-35,-34,-33,-2,-1,0,1,2,3,4,5,6,37,38,39,40,41,42,43,44,75,76,77,78,79,80,81,82,83,114,115,116,117,118,119,120,121,152,153,154,155,156,157,158,159,160,191,192,193,194,195,196,197,198,229,230,231,232,233,234,235,236,237,268,269,270,271,272,273,274,275,306,307,308,309,310,311,312,313,314,345,346,347,348,349,350,351,352]
allfactions=[]
allunits=[]
allorders=[]
allspecialorders=[]
alleconomicactions=[]
hexsidelimitchecks=[]
airlimitchecks=[]
allhexes=[]
allroads=[]
allbases=[]
allbuildables=[]
allspecialbuildings=[]
allvision=[]
allcurrentfaction=[]
allcurrentturn=[]
allturns=[]
allcaravans=[]
allroutes=[]
allexpandables=[]
allpotentialexpansionsreceived=[]
tempcaravanlist=[]
combathexes=[]
currentfaction=-1
currentinitiative=[]
turnstatus=-1
errormessagetext=['Errors: ']
successfulmoves=[]
unitcosts=[]
buildunit=['None', 0, 0, 0, 0]
confirmunit=''
factionoverall='None'
foodcount=[0]
foodcost=[0]
dalarancombat=[0]
spectator=[0]
specialevents=[]
class unittype():
    maxhp=0
    combat=0
    category=0
    unittype=0
    light=0
    heavy=0
    natural=0
    movement=0
    vision=0
    stealth=0
class caravan():
    path=[]
    originbase=-1
    destinationbase=-1
    faction=-1
    caravantype='none'
allstats={'Grunt':unittype(),'Berserker':unittype(),'Axethrower':unittype(),'Ogre':unittype(),'Catapult':unittype(),'Death Knight':unittype(),'Wave Rider':unittype(),'Turtle':unittype(),'Juggernaut':unittype(),'Horde Transport':unittype(),'Dragon':unittype(),'Raider':unittype(),'Shaman':unittype(),'Warlock':unittype(),'Footman':unittype(),'Archer':unittype(),'Knight':unittype(),'Ballista':unittype(),'Mage':unittype(),'Destroyer':unittype(),'Submarine':unittype(),'Battleship':unittype(),'Alliance Transport':unittype(),'Gryphon':unittype(),'Dwarf':unittype(),'Swordsman':unittype(),'Wildhammer Shaman':unittype(),'Rogue':unittype(),'Skeleton':unittype(),'Demon':unittype(),'Elemental':unittype(),'Mountaineer':unittype(),"Zul'jin":unittype(),'Kilrogg Deadeye':unittype(),'Rend Blackhand':unittype(),'Maim Blackhand':unittype(),'Zuluhed the Whacked':unittype(),"Gul'dan the Deceiver":unittype(),"Drak'thul":unittype(),'Gorfrunch Smashblade':unittype(),"Cho'gall":unittype(),'Orgrim Doomhammer':unittype(),'Varok Saurfang':unittype(),'Alleria Windrunner':unittype(),'Sylvanas Windrunner':unittype(),'Kurdran Wildhammer':unittype(),'Maz Drachrip':unittype(),'Magni Bronzebeard':unittype(),'Muradin Bronzebeard':unittype(),'Archmage Antonidas':unittype(),'Archmage Khadgar':unittype(),'Daelin Proudmoore':unittype(),'Derek Proudmoore':unittype(),'Thoras Trollbane':unittype(),'Danath Trollbane':unittype(),'Anduin Lothar':unittype(),'Turalyon':unittype(),'Uther the Lightbringer':unittype(),'Terenas Menethil':unittype(),'Genn Greymane':unittype(),'Darius Crowley':unittype(),'Aiden Perenolde':unittype(),'Lord Falconcrest':unittype(),'Dagran Thaurissan':unittype(),"Drek'thar":unittype(),'Nazgrel':unittype(),'Alexstrasza':unittype()}
unitsdict={0:'Grunt',1:'Berserker',2:'Axethrower',3:'Ogre',4:'Catapult',5:'Death Knight',6:'Wave Rider',7:'Turtle',8:'Juggernaut',9:'Horde Transport',10:'Dragon',11:'Raider',12:'Shaman',13:'Warlock',14:'Footman',15:'Archer',16:'Knight',17:'Ballista',18:'Mage',19:'Destroyer',20:'Submarine',21:'Battleship',22:'Alliance Transport',23:'Gryphon',24:'Dwarf',25:'Swordsman',26:'Wildhammer Shaman',27:'Rogue',28:'Skeleton',29:'Demon',30:'Elemental',31:'Mountaineer'}
# method to load DB
def load_db():
    return MySQLdb.connect(host=host_var,
                           user=user_var,
                           passwd=passwd_var,
                           db=db_var)


# method to accept faction password, load faction if exists, or quit otherwise
def loadgame():
    status_list = []
    for x in range(len(allfactions)):
        if allfactions[x] == currentinitiative[0] and allturns[x] == 0:
            status_list.append(factiondictionary[x] + ' - OUTSTANDING')
        elif allfactions[x] == currentinitiative[0] and allturns[x] == 1:
            status_list.append(factiondictionary[x] + ' - SUBMITTED')
    inputbox.display_faction_status(windowSurface, status_list)
    inputbox.display_quit_option(windowSurface)

    db = load_db()

    playerdata_cur = db.cursor()
    playerdata_cur.execute("SELECT * FROM playerdata")
    playerdata = playerdata_cur.fetchall()

    playerdata_cur.close()
    db.close()
    
    answer = inputbox.ask(windowSurface, "Password")

    match = 0
    currentfaction = -1
    for x in range(len(playerdata)):
        if playerdata[x][0] == answer:
            currentfaction = playerdata[x][1]
            match = 1
    
    #if password matches...
    if match == 1:
        #check if input faction is on current initiative turn
        if allfactions[currentfaction] == currentinitiative[0]:
            #allow game to load if so
            allcurrentfaction.append(currentfaction)
            return
        else:
            #otherwise launch game in spectator mode
            spectator[0] = 1
            allcurrentfaction.append(currentfaction)
            return
    #if password doesn't match, quit
    else:
        pygame.quit()
        sys.exit()
    
def loadsavedunits():
    db = load_db()
    
    unitstats_cur = db.cursor()
    unitstats_cur.execute("SELECT * FROM unitstats")
    unitstats = unitstats_cur.fetchall()
    count=0
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
        allstats[x[0]].stealth=x[10]
        allstats[x[0]].goldcost=x[11]
        allstats[x[0]].lumbercost=x[12]
        allstats[x[0]].oilcost=x[13]
        allstats[x[0]].mintier=x[14]

        templist = []
        templist.append(x[0])
        templist.append(int(x[11]))
        templist.append(int(x[12]))
        templist.append(int(x[13]))
        templist.append(int(x[14]))
        unitcosts.append(templist)

    unitstats_cur.close()

    if spectator[0] == 0:
        unitdata_cur = db.cursor()
        unitdata_cur.execute("SELECT * FROM currentunits")
        unitdata = unitdata_cur.fetchall()
        count=0
        for x in unitdata:
            allunits.append([])
            allunits[count].append(x[0])
            x = list(x)
            x.remove(x[0])
            for y in range(len(x)):
                if 0<=y<14 or y>17:
                    allunits[count].append(int((x[y])))#upload
                else:
                    allunits[count].append((x[y]))
            allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
            if allunits[count][UNIT_CATEGORY]!=CATEGORY_NO_FIRE:
                allunits[count][UNIT_COMBAT]=allunits[count][UNIT_COMBAT]+(allunits[count][UNIT_TIER]*5)#remove this when we get real vets
            count=count+1
        unitdata_cur.close()
        db.close()
    elif spectator[0] == 1:
        unitdata_cur = db.cursor()
        unitdata_cur.execute("SELECT * FROM spectatorunits")
        unitdata = unitdata_cur.fetchall()
        count=0
        for x in unitdata:
            allunits.append([])
            allunits[count].append(x[0])
            x = list(x)
            x.remove(x[0])
            for y in range(len(x)):
                if 0<=y<14 or y>17:
                    allunits[count].append(int((x[y])))#upload
                else:
                    allunits[count].append((x[y]))
            allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
            if allunits[count][UNIT_CATEGORY]!=CATEGORY_NO_FIRE:
                allunits[count][UNIT_COMBAT]=allunits[count][UNIT_COMBAT]+(allunits[count][UNIT_TIER]*5)#remove this when we get real vets
            count=count+1
        unitdata_cur.close()
        db.close()

def loadspecialevents():
    db = load_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM specialevents")
    data = cur.fetchall()
    for x in data:
        specialevents.append(list(x))

    cur.close()
    db.close()

def loadsavedmap():
    db = load_db()
    cur = db.cursor()

    if spectator[0] == 0:
        cur.execute("SELECT * FROM currenthexes")
        mapdata = cur.fetchall()
        
        for x in mapdata:
            templist=[]
            for y in range(0,7):
                templist.append(x[y])
            for y in range(7,len(x)):
                templist.append(x[int(y)])
            allhexes.append(templist)

        # create list of special buildings
        for i in range(len(allhexes)):
            if int(allhexes[i][HEX_BUILDING]) != 0:
                allspecialbuildings.append(i)

        cur.close()
        db.close()
    elif spectator[0] == 1:
        cur.execute("SELECT * FROM spectatorhexes")
        mapdata = cur.fetchall()
        
        for x in mapdata:
            templist=[]
            for y in range(0,7):
                templist.append(x[y])
            for y in range(7,len(x)):
                templist.append(x[int(y)])
            allhexes.append(templist)

        # create list of special buildings
        for i in range(len(allhexes)):
            if int(allhexes[i][HEX_BUILDING]) != 0:
                allspecialbuildings.append(i)

        cur.close()
        db.close()

def loadroads():#loads caravans too
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

    if spectator[0] == 0:
        c_cur = db.cursor()
        c_cur.execute("SELECT * FROM currentcaravans")
        caravandata = c_cur.fetchall()

        for x in caravandata:
            templist = list(x)
            allcaravans.append(templist)        

        c_cur.close()
    elif spectator[0] == 1:
        c_cur = db.cursor()
        c_cur.execute("SELECT * FROM spectatorcaravans")
        caravandata = c_cur.fetchall()

        for x in caravandata:
            templist = list(x)
            allcaravans.append(templist)        

        c_cur.close()
    db.close()
    
def loadsavedbases():
    db = load_db()
    cur = db.cursor()

    if spectator[0] == 0:
        cur.execute("SELECT * FROM currentbases")
        basedata = cur.fetchall()
        
        for x in basedata:
            templist=[]
            templist.append(x[0])
            for y in range(1,len(x)):
                templist.append(int(x[y]))
            allbases.append(templist)
    elif spectator[0] == 1:
        cur.execute("SELECT * FROM spectatorbases")
        basedata = cur.fetchall()
        
        for x in basedata:
            templist=[]
            templist.append(x[0])
            for y in range(1,len(x)):
                templist.append(int(x[y]))
            allbases.append(templist)

    cur.close()
    db.close()

def loadsavefactions():
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

def loadcurrentbuildables():
    db = load_db()
    cur = db.cursor()

    if spectator[0] == 0:
        cur.execute("SELECT * FROM currentbuildables")
        orderdata = cur.fetchall()
        count=0
        for x in orderdata:
            if count==0:
                allbuildables.append(x)
                count=count+1
    elif spectator[0] == 1:
        cur.execute("SELECT * FROM spectatorbuildables")
        orderdata = cur.fetchall()
        count=0
        for x in orderdata:
            if count==0:
                allbuildables.append(x)
                count=count+1


    cur.close()
    db.close()

def loadbuildables():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM savebuildables")
    orderdata = cur.fetchall()
    allbuildables.append(orderdata[currentfaction])
    cur.close()
    db.close()

def loadcurrentvision():
    db = load_db()
    cur = db.cursor()

    if spectator[0] == 0:
        cur.execute("SELECT * FROM currentvision")
        visiondata = cur.fetchall()
        count=0
        for x in visiondata:
            visionstring = str(x)
            strippedstring = visionstring[1:-2]
            allvision.append(strippedstring)
    elif spectator[0] == 1:
        cur.execute("SELECT * FROM spectatorvision")
        visiondata = cur.fetchall()
        count=0
        for x in visiondata:
            visionstring = str(x)
            strippedstring = visionstring[1:-2]
            allvision.append(strippedstring)

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

def loadallturns():
    db = load_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM turnstatus")
    allturnsdata = cur.fetchall()
    templist=[]
    for x in allturnsdata:
        templist=list(x)
    for i in range(len(templist)):
        allturns.append(int(templist[i]))
    cur.close()
    db.close()

def loadturnstatus():
    db = load_db()
    cur = db.cursor()
    factionstring = 'COL_' + str(currentfaction)
    loadstring = "SELECT " + factionstring + " FROM turnstatus"
    cur.execute(loadstring)
    currentturndata = cur.fetchall()
    count = 0
    for x in currentturndata:
        if count==0:
            allcurrentturn.append(x)
            count=count+1

    cur.close()
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
        #allunits[x][UNIT_TRANSPORT_ONE]=-1
        #allunits[x][UNIT_TRANSPORT_TWO]=-1
    for x in range(len(allhexes)):
        allhexes[x][HEX_NEW_COMBAT]=1
def IsItThere(value,checklist):
    answer=0
    for x in checklist:
        if value==x:
            answer=1
    return answer
def IntIsItThere(value,checklist):
    answer=0
    for x in checklist:
        if int(value)==int(x):
            answer=1
    return answer
#moveChecker functions
# noinspection PyUnboundLocalVariable,PyUnboundLocalVariable
def movechecker():##road moves into combat?
    for x in range(len(allorders)):
        successfulmoves.append([])
        successfulmoves[x].append(allorders[x][0])
    for x in range(len(allunits)):#prevent units from entering combats the same turn they started in one
        if len(buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION])))>1:
            allunits[x][UNIT_COMBAT_START]=1
        else:
            allunits[x][UNIT_COMBAT_START]=0
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
                        if hextwo>hexone:#generate hexside ID, always bigger number first
                            hexswitch=hexone
                            hexone=hextwo
                            hextwo=hexswitch
                        for z in range(len(airlimitchecks)):#prepare to assign move order to hexside. see if any move orders already categorized through that hexside
                            if airlimitchecks[z][0]==hexone and airlimitchecks[z][1]==hextwo:
                                foundmatch=1
                                match=z
                        if foundmatch==1:#if there are, add this to that one
                            airlimitchecks[match].append(y)
                        else:#if there aren't, add a new one to hexsidelimitchecks
                            newcheck.append(hexone)
                            newcheck.append(hextwo)
                            newcheck.append(1)
                            newcheck.append(y)
                            airlimitchecks.append(newcheck)
                else:
                    allorders[y]=[allorders[y][0]]
            elif len(allorders[y])==1:
                allorders[y]=[allorders[y][0]]
            else:
                allorders[y]=[allorders[y][0]]
                errormessagetext.append(' Insufficient movement remaining. ')
        for y in range(len(hexsidelimitchecks)):#compare hexsidelimitchecks to actual hexside limits and pick losers. delete unsuccessful units from HLC, delete all further orders for unsuccessful units
            while (len(hexsidelimitchecks[y])-3)>hexsidelimitchecks[y][2]:##something wrong is happening here sometimes i think
                errormessagetext.append(' Move exceeds hexside limits. ')
                pick=len(hexsidelimitchecks[y])-1
                for z in range(1,len(allorders[hexsidelimitchecks[y][pick]])):
                    allorders[hexsidelimitchecks[y][pick]].remove(allorders[hexsidelimitchecks[y][pick]][1])
                kill=hexsidelimitchecks[y][pick]
                hexsidelimitchecks[y].reverse()
                hexsidelimitchecks[y].remove(kill)#this is it
                hexsidelimitchecks[y].reverse()
            hexsidelimitchecks[y][2]=hexsidelimitchecks[y][2]-(len(hexsidelimitchecks[y])-3)#reduce hexside limits
        for y in range(len(airlimitchecks)):#compare hexsidelimitchecks to actual hexside limits and pick losers. delete unsuccessful units from HLC, delete all further orders for unsuccessful units
            while (len(airlimitchecks[y])-3)>airlimitchecks[y][2]:##something wrong is happening here sometimes i think
                errormessagetext.append(' Move exceeds hexside limits. ')
                pick=len(airlimitchecks[y])-1
                for z in range(1,len(allorders[airlimitchecks[y][pick]])):
                    allorders[airlimitchecks[y][pick]].remove(allorders[airlimitchecks[y][pick]][1])
                kill=airlimitchecks[y][pick]
                airlimitchecks[y].reverse()
                airlimitchecks[y].remove(kill)#this is it
                airlimitchecks[y].reverse()
            airlimitchecks[y][2]=airlimitchecks[y][2]-(len(airlimitchecks[y])-3)#reduce hexside limits
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
                successfulmoves[y].append(allorders[y][1])
                if len(buildfactionslist(buildcombatlist(allorders[y][1])))>1:
                    allorders[y]=[allorders[y][0]]#if combat, delete all further orders
                    errormessagetext.append(' Unit has moved into combat. ')
                else:
                    allorders[y].remove(allorders[y][1])#otherwise delete current order
        for y in range(len(hexsidelimitchecks)):#remove all units from HLC
            hexsidelimitchecks[y]=[hexsidelimitchecks[y][0],hexsidelimitchecks[y][1],hexsidelimitchecks[y][2]]
        for y in range(len(airlimitchecks)):#remove all units from HLC
            airlimitchecks[y]=[airlimitchecks[y][0],airlimitchecks[y][1],airlimitchecks[y][2]]
        hexsideControlSweep()

    ##reset any local stuff used
    #for x in successfulmoves:
        #allorders.append(x)

#economicactions checker
def economicchecker(order):
    success=1
    if order[0]=='Upgrade Base':
        actionhex=order[1]
        success=0
        for x in range(len(allbases)):
            if allbases[x][BASE_LOCATION] == actionhex:
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
                if allbases[x][BASE_TIER] == 1 and connectedres>1:
                    success=1
                if allbases[x][BASE_TIER] == 2 and connectedres>3:
                    success=1
    if order[0]=='Send Resources':
        origin=int(order[1])
        destination=int(order[2])
        success=0
        for z in range(len(allbases)):
            if int(allbases[z][BASE_LOCATION])==int(origin):
                if origin!=destination:
                    progress=1
                    foundbases=[origin]
                    while progress==1:#cancel if the caravans are looked through and no additional connections are made
                        progress=0
                        tempadds=[]
                        for x in range(len(allcaravans)):#look through all caravans
                            for y in range(len(foundbases)):#while looking through a caravan, search all bases officially connected so far and compile what they're connected to
                                if int(allcaravans[x][0])==foundbases[y] or int(allcaravans[x][1])==foundbases[y]:
                                    tempadds.append(int(allcaravans[x][0]))
                                    tempadds.append(int(allcaravans[x][1]))
                        for x in range(len(tempadds)):
                            if IsItThere(tempadds[x],foundbases)==0:
                                foundbases.append(tempadds[x])
                                progress=1
                    if IsItThere(destination,foundbases)==1:#send resources
                        success=1
                    else:
                        success=0
    if order[0]=='Expand':
        actionhex=int(order[1])
        targetHex=int(order[2])
        success=0
        for x in range(len(allbases)):
            if int(allbases[x][BASE_LOCATION])==int(actionhex):
                if (allhexes[targetHex][HEX_TERRAIN]=='F' or allhexes[targetHex][HEX_TERRAIN]=='C' or (allhexes[targetHex][HEX_TERRAIN]=='O' and int(allhexes[targetHex][HEX_OIL])==1)):
                    if IsItThere(targetHex,allexpandables[x])==1:
                        if IntIsItThere(targetHex,allvision)==1:
                            success=1
                else:
                    success=0
    if order[0]=='Establish Caravan':
        ACTION_HEX=1
        ACTION_CARAVAN_ORIGIN_BASE=1
        ACTION_CARAVAN_TYPE=2
        newcaravan=caravan()
        newcaravan.path=[]
        orderpathlength=0
        for y in range(len(order)-3):
            newcaravan.path.append(int(order[y+3]))
            orderpathlength=orderpathlength+1
        newcaravan.originbase=int(order[ACTION_CARAVAN_ORIGIN_BASE])
        newcaravan.destinationbase=int(order[orderpathlength+2])
        for y in range(len(allbases)):
            if allbases[y][BASE_LOCATION]==int(order[ACTION_CARAVAN_ORIGIN_BASE]):
                newcaravan.faction=int(allbases[y][BASE_FACTION])
        newcaravan.caravantype=order[ACTION_CARAVAN_TYPE]
        currentcaravan=newcaravan
        valid=1
        targetbase=0
        actingbase=0
        for x in range(len(allbases)):
            if int(allbases[x][BASE_LOCATION])==currentcaravan.destinationbase:
                targetbase=x
            if int(allbases[x][BASE_LOCATION])==currentcaravan.originbase:
                actingbase=x
        if len(buildfactionslist(buildcombatlist(int(currentcaravan.destinationbase))))>1:
            valid=0
        for x in range(len(currentcaravan.path)):
            if IntIsItThere(currentcaravan.path[x],allvision)==0:
                valid=0
        if currentcaravan.originbase==currentcaravan.destinationbase:
            valid=0
        if len(currentcaravan.path)>16:
            valid=0
        for x in range(1,len(currentcaravan.path)-1):
            for z in range(len(allbases)):
                if currentcaravan.path[x]==int(allbases[z][BASE_LOCATION]):
                    valid=0
        if currentcaravan.caravantype=='water':
            for x in range(1,len(currentcaravan.path)-1):
                if Adjacent(currentcaravan.path[x-1],currentcaravan.path[x])==0:
                    valid=0
                if allhexes[currentcaravan.path[x]][HEX_TERRAIN]!='O':
                    valid=0
                if HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='O' and HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='K':
                    valid=0
                if EnemyUnitsPresent(currentcaravan.path[x],currentcaravan.faction)==1:
                    valid=0
            if Adjacent(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0 or HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='K' or allfactions[currentcaravan.faction]!=allfactions[allbases[targetbase][BASE_FACTION]]:
                valid=0
        if currentcaravan.caravantype=='land':
            for x in range(1,len(currentcaravan.path)-1):
                if Adjacent(currentcaravan.path[x-1],currentcaravan.path[x])==0:
                    valid=0
                if allhexes[currentcaravan.path[x]][HEX_TERRAIN]=='O' or allhexes[currentcaravan.path[x]][HEX_TERRAIN]=='I':
                    valid=0
                if HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='C' and HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='F' and HasRoad(currentcaravan.path[x-1],currentcaravan.path[x])!=1:
                    valid=0
                if EnemyUnitsPresent(currentcaravan.path[x],currentcaravan.faction)==1:
                    valid=0
            if Adjacent(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0 or (HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='C' and HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='F' and HasRoad(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0) or allfactions[currentcaravan.faction]!=allfactions[allbases[targetbase][BASE_FACTION]]:
                valid=0
        if valid==1:
            success=1
        else:
            success=0
    if order[0]=='Assist Construction':
        success=0
        if allhexes[order[2]][HEX_TERRAIN]=='C':
            if len(buildfactionslist(buildcombatlist(order[2])))<2:
                for x in range(len(allbases)):
                    if int(allbases[x][BASE_LOCATION])==int(order[1]):
                        unitspresent=buildcombatlist(int(order[2]))
                        for y in range(len(unitspresent)):
                            if units[unitspresent[y]].isLeader==1:
                                if int(allfactions[allbases[x][BASE_FACTION]])==int(allfactions[allunits[unitspresent[y]][UNIT_FACTION]]):
                                    success=1
    if order[0]=='Give Expansion':
        actionhex=order[2]
        valid=1
        recipientbase=0
        base=0
        for x in range(len(allbases)):
            if allbases[x][BASE_LOCATION]==order[3]:
                recipientbase=x
            if allbases[x][BASE_LOCATION]==order[1]:
                base=x
        if allfactions[allbases[recipientbase][BASE_FACTION]]!=allfactions[allbases[base][BASE_FACTION]]:
            valid=0
        if int(allhexes[actionhex][HEX_FARM])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_RIG])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_MILL])!=allbases[base][BASE_LOCATION]:
            valid=0
        if IsItThere(actionhex,allpotentialexpansionsreceived[recipientbase])==0:
            valid=0
        if valid==1:
            success=1
        else:
            success=0
    return success
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
                if allbases[z][BASE_LOCATION]==allexpandables[x][y] and allbases[z][BASE_TIER] != 0:
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
def EnemyUnitsPresent(location,faction):
    checklist=buildcombatlist(location)
    enemyunits=0
    if len(checklist)>0:
        for x in range(len(checklist)):
            if allfactions[allunits[checklist[x]][UNIT_FACTION]]!=allfactions[faction]:
                enemyunits=1
    return enemyunits            
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
        return direction
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
        return direction
    return direction

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
        return terrain
    return terrain

def LandOrSea(terrain):
    if terrain == 'K':
        return 'water'
    else:
        return 'land'

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

    hex_one_terrain = allhexes[one][HEX_TERRAIN]
    hex_two_terrain = allhexes[two][HEX_TERRAIN]
    
    sideterrain=HexsideTerrain(one,two)
    errormessagetextcopy=[]
    errormessagetextcopy=copy.deepcopy(errormessagetext)
    if ((allunits[unit][UNIT_TYPE]==TYPE_GROUND) and (terrain=='F' or terrain=='M' or terrain=='S' or terrain=='C' or terrain=='R' or terrain=='W') and (sideterrain=='F' or sideterrain=='M' or sideterrain=='S' or sideterrain=='C' or sideterrain=='R' or sideterrain=='W')):
        move=1
    #if (allunits[unit][UNIT_TYPE]==TYPE_SEA) and ((allhexes[one][HEX_TERRAIN]=='O' and (terrain=='O' or terrain=='C')) or (allhexes[one][HEX_TERRAIN]=='C' and terrain=='O')) and (sideterrain=='O' or sideterrain=='K'):
        #move=1
    if allunits[unit][UNIT_TYPE] == TYPE_SEA:
        if hex_one_terrain == 'O' and hex_two_terrain == 'O':
            move=1
        if (hex_one_terrain == 'O' or hex_two_terrain == 'O') and sideterrain == 'K':
            move=1
    if allunits[unit][UNIT_TYPE]==TYPE_AIR and terrain!='I':
        move=1
    if allunits[unit][UNIT_MOVEMENT_REMAINING]==0 and HasRoad(one,two)==0:
        move=0
        errormessagetext.append(' Unit may only use road bonus move along a hexside with a road. ')
    if int(allfactions[allunits[unit][UNIT_FACTION]])!=WhichHexSideControl(one,two):#check if moving out through enemy hexside
        move=0
        errormessagetext.append(' Unit is trying to exit combat through enemy-controlled hexside. ')
    if combatmove==1 and allunits[unit][UNIT_COMBAT_START]==1:
        move=0
        errormessagetext.append(' Unit is trying to enter combat, but it began this turn in a combat. ')
    if combatmove==1 and allunits[unit][UNIT_MOVEMENT_REMAINING]==0:
        move=0
        errormessagetext.append(' Unit is trying to enter combat using a road move. ')
    if sideterrain=='X':
        move=0
    if allunits[unit][UNIT_CATEGORY]==CATEGORY_INTERIOR_SIEGE and allunits[unit][UNIT_TYPE]==TYPE_GROUND and (sideterrain!='C' and sideterrain!='F' and HasRoad(one,two)==0):
        move=0
        errormessagetext.append(' Unit is siege trying to move through a non-clear, non-forest hexside without a road. ')
    if allunits[unit][UNIT_TYPE]==TYPE_GROUND and allunits[unit][UNIT_LOCATION]!=allunits[unit][UNIT_PREVIOUS_LOCATION] and (HexsideTerrain(allunits[unit][UNIT_LOCATION],allunits[unit][UNIT_PREVIOUS_LOCATION])!='C' and HexsideTerrain(allunits[unit][UNIT_LOCATION],allunits[unit][UNIT_PREVIOUS_LOCATION])!='F') and (allunits[unit][UNIT_ROAD_MOVE_ONLY]==0 or HasRoad(one,two)==0):
        move=0
        errormessagetext.append(' Unit has crossed a mountain, swamp, forest, river, or fortification and has not followed roads for its entire move. ')
    ##if unit is land and is not where it started and (sideterrain is not clear OR side terrain is not forest) and (hasn't been all on roads OR there isn't a road)
        ##stop movement
    if allunits[unit][UNIT_FACTION]==FACTION_GILNEAS and gilneascheck(one,two,unit)==1:
        move=0
    if allunits[unit][UNIT_FACTION]==FACTION_ALTERAC and alteraccheck(one,two,unit)==1:
        move=0
    if allunits[unit][UNIT_FACTION]==FACTION_SILVERMOON and silvermooncheck(one,two,unit)==1:
        move=0
    if allunits[unit][UNIT_NAME]=='Alexstrasza':
        move=0
    if errormessagetext==errormessagetextcopy:
        errormessagetext.append(' Unit cannot make this move because of terrain. ')
    return move
    ##check if siege is moving across nonsiege hexsides
def alteraccheck(one,two,unit):#i don't think this will work in the checker for transports because it may not do specialorders first
    foreignunittotal=0
    foreignunitmax=2
    for x in range(len(backupallunits)):#search backup for units present outside of alterac
        if backupallunits[x][UNIT_FACTION]==FACTION_ALTERAC and IsItThere(backupallunits[x][UNIT_LOCATION],alterachome)==0 and backupallunits[x][UNIT_ALIVE]==1:
            foreignunittotal=foreignunittotal+1
            if backupallunits[x][UNIT_TRANSPORT_ONE]!=-1 and backupallunits[x][UNIT_TRANSPORT_ONE]!=-2:
                foreignunittotal=foreignunittotal+1
            if backupallunits[x][UNIT_TRANSPORT_TWO]!=-1 and backupallunits[x][UNIT_TRANSPORT_TWO]!=-2:
                foreignunittotal=foreignunittotal+1
    for x in range(len(allorders)):#total units that start inside alterac and are trying to move out
        if allunits[allorders[x][0]][UNIT_FACTION]==FACTION_ALTERAC and IsItThere(backupallunits[allorders[x][0]][UNIT_LOCATION],alterachome)==1:
            departurecheck=0
            for y in range(len(allorders[x])-1):
                if IsItThere(allorders[x][y+1],alterachome)==0:
                    departurecheck=1
            if departurecheck==1:
                foreignunittotal=foreignunittotal+1
                for y in range(len(allspecialorders)):
                    if allspecialorders[y][0]=='Board Transport' and allspecialorders[y][2]==allorders[x][0]:
                        foreignunittotal=foreignunittotal+1
    if foreignunittotal>foreignunitmax:
        return 1
    else:
        return 0
def gilneascheck(one,two,unit):#i don't think this will work in the checker for transports because it may not do specialorders first
    foreignunittotal=0
    foreignunitmax=3
    for x in range(len(backupallunits)):#search backup for units present outside of alterac
        if backupallunits[x][UNIT_FACTION]==FACTION_GILNEAS and IsItThere(backupallunits[x][UNIT_LOCATION],gilneashome)==0 and backupallunits[x][UNIT_ALIVE]==1:
            foreignunittotal=foreignunittotal+1
            if backupallunits[x][UNIT_TRANSPORT_ONE]!=-1 and backupallunits[x][UNIT_TRANSPORT_ONE]!=-2:
                foreignunittotal=foreignunittotal+1
            if backupallunits[x][UNIT_TRANSPORT_TWO]!=-1 and backupallunits[x][UNIT_TRANSPORT_TWO]!=-2:
                foreignunittotal=foreignunittotal+1
    for x in range(len(allorders)):#total units that start inside alterac and are trying to move out
        if allunits[allorders[x][0]][UNIT_FACTION]==FACTION_GILNEAS and IsItThere(backupallunits[allorders[x][0]][UNIT_LOCATION],gilneashome)==1:
            departurecheck=0
            for y in range(len(allorders[x])-1):
                if IsItThere(allorders[x][y+1],gilneashome)==0:
                    departurecheck=1
            if departurecheck==1:
                foreignunittotal=foreignunittotal+1
                for y in range(len(allspecialorders)):
                    if allspecialorders[y][0]=='Board Transport' and allspecialorders[y][2]==allorders[x][0]:
                        foreignunittotal=foreignunittotal+1

    if foreignunittotal>foreignunitmax:
        return 1
    else:
        return 0
def silvermooncheck(one,two,unit):
    invalid=0
    #if unit is moving to a nonhome destination and is not an archer, leader, transport, or destroyer
    if IsItThere(two,silvermoonhome)==0:
        if allunits[unit][UNIT_NAME]!='Archer' and allunits[unit][UNIT_NAME]!='Alliance Transport' and allunits[unit][UNIT_NAME]!='Destroyer' and isLeader(allunits[unit][UNIT_NAME])==0:
            invalid=1
    #if unit is a transport containing a unit that is not an archer or leader
    if allunits[unit][UNIT_NAME]=='Alliance Transport':
        if allunits[unit][UNIT_TRANSPORT_ONE]!=-2 and (allunits[allunits[unit][UNIT_TRANSPORT_ONE]][UNIT_NAME]!='Archer' and isLeader(allunits[allunits[unit][UNIT_TRANSPORT_ONE]][UNIT_NAME])==0):
            invalid=1
        if allunits[unit][UNIT_TRANSPORT_TWO]!=-2 and (allunits[allunits[unit][UNIT_TRANSPORT_TWO]][UNIT_NAME]!='Archer' and isLeader(allunits[allunits[unit][UNIT_TRANSPORT_TWO]][UNIT_NAME])==0):
            invalid=1
    return invalid
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
    if int(combat)==0 and int(road)==1:
        limit=limit+1
    return limit

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

def countFood():
    for x in range(len(bases)):
        if bases[x].faction == currentfaction:
            foodcount[0] += bases[x].tier
    for x in range(len(allhexes)):
        if int(allhexes[x][HEX_FARM])!=-1:
            for y in range(len(bases)):
                if int(bases[y].hexnumber)==int(allhexes[x][HEX_FARM]) and bases[y].faction == currentfaction:
                    foodcount[0] += 1
    for x in range(len(units)):
        #if units[x].alive==1 and units[x].faction == currentfaction:
        if units[x].faction == currentfaction:
            foodcost[0] += 1

################### BEGIN MAPBUILDER CODE HERE ###################


#function to establish font
def establishFont(size):
    font_preferences = ["Sherwood", "CloisterBlack BT", "GoudyHandtooled BT", "Cornerstone", "Allegro", "EngraversGothic BT"]
    available = pygame.font.get_fonts()
    choices = map(lambda x:x.lower().replace(' ', ''), font_preferences)
    for choice in choices:
        if choice in available:
            return pygame.font.SysFont(choice, size)
    return pygame.font.SysFont('Tahoma', size)

#function to take faction and determine if Horde or Alliance
def hordeOrAlliance(input):
    if input == 0 or input == 1 or input == 2 or input == 3 or input == 4 or input == 5 or input == 6 or input == 18 or input == 19 or input == 22 or input == 23 or input == 24 or input == 25 or input == 26 or input == 27 or input == 28 or input == 29 or input == 30 or input == 31:
        return 'Horde'
    else:
        return 'Alliance'

def hexToOverallFaction(input):
    for i in range(len(bases)):
        if bases[i].hexnumber == input:
            return hordeOrAlliance(bases[i].faction)

#function to interpret HEX_EXPANSION_OWNER
def expansionOwner(input):
    if input == 1:
        return 'Horde'
    elif input == 2:
        return 'Alliance'
    else:
        return 'Fuckup'

#function to determine if two factions are allied
def isAllied(one, two):
    if allfactions[one] == allfactions[two]:
        return 1
    else:
        return 0

#function to return unit category as string
def categoryToString(input):
    if input == 0 or input == 4:
        return 'Siege'
    if input == 1:
        return 'Ranged'
    if input == 2:
        return 'Expert'
    if input == 3:
        return 'Melee'
    if input == 5:
        return 'Passive'
    
#define odd/even function
def oddOrEven(input):

    if input < 38 or 76 < input < 116 or 153 < input < 193 or 230 < input < 270 or 307 < input < 347 or 384 < input < 424 or 461 < input < 501 or 538 < input < 578 or 615 < input < 655 or 692 < input < 732 or 769 < input < 809 or 846 < input < 886 or 923 < input < 962 or 1000 < input < 1040 or 1077 < input < 1117:
        return 1
    else:
        return 0

#function to determine hex column
def columnID(input):

    if input <= 38:
        return 1
    if 39 <= input <= 76:
        return 2
    if 77 <= input <= 115:
        return 3
    if 116 <= input <= 153:
        return 4
    if 154 <= input <= 192:
        return 5
    if 193 <= input <= 230:
        return 6
    if 231 <= input <= 269:
        return 7
    if 270 <= input <= 307:
        return 8
    if 308 <= input <= 346:
        return 9
    if 347 <= input <= 384:
        return 10
    if 385 <= input <= 423:
        return 11
    if 424 <= input <= 461:
        return 12
    if 462 <= input <= 500:
        return 13
    if 501 <= input <= 538:
        return 14
    if 539 <= input <= 577:
        return 15
    if 578 <= input <= 615:
        return 16
    if 616 <= input <= 654:
        return 17
    if 655 <= input <= 692:
        return 18
    if 693 <= input <= 731:
        return 19
    if 732 <= input <= 769:
        return 20
    if 770 <= input <= 808:
        return 21
    if 809 <= input <= 846:
        return 22
    if 847 <= input <= 885:
        return 23
    if 886 <= input <= 923:
        return 24
    if 924 <= input <= 962:
        return 25
    if 963 <= input <= 1000:
        return 26
    if 1001 <= input <= 1039:
        return 27
    if 1040 <= input <= 1077:
        return 28
    if 1078 <= input <= 1116:
        return 29

#function to return top hex in column
def topHexInColumn(id):
    if id == 1:
        return 0
    if id == 2:
        return 39
    if id == 3:
        return 77
    if id == 4:
        return 116
    if id == 5:
        return 154
    if id == 6:
        return 193
    if id == 7:
        return 231
    if id == 8:
        return 270
    if id == 9:
        return 308
    if id == 10:
        return 347
    if id == 11:
        return 385
    if id == 12:
        return 424
    if id == 13:
        return 462
    if id == 14:
        return 501
    if id == 15:
        return 539
    if id == 16:
        return 578
    if id == 17:
        return 616
    if id == 18:
        return 655
    if id == 19:
        return 693
    if id == 20:
        return 732
    if id == 21:
        return 770
    if id == 22:
        return 809
    if id == 23:
        return 847
    if id == 24:
        return 886
    if id == 25:
        return 924
    if id == 26:
        return 963
    if id == 27:
        return 1001
    if id == 28:
        return 1040
    if id == 29:
        return 1078

#function to accept x and y coords and return hex
def coordsToHex(x, y):
    x_divisor = int(X_CORD_SCROLL/21)
    y_divisor = int(Y_CORD_SCROLL/34)
    columnID = int(x/x_divisor) + 1
    x_top = topHexInColumn(columnID)
    y_shift = int(y/y_divisor)
    result = x_top + y_shift
    return result

#function to accept hex and return list of hexes to fog
def fogHexes(hex):
    hexlist = []
    for x in range(len(nearbyfoglist)):
        if (hex + nearbyfoglist[x]) >= 0 and (hex + nearbyfoglist[x]) <= 1116:
            hexlist.append(hex + nearbyfoglist[x])
    for y in range(len(allvision)):
        if int(allvision[y]) in hexlist:
            hexlist.remove(int(allvision[y]))
    return hexlist

#function to replace spaces and apostrophes from string literals
def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

#function to determine transport capacity
def transportCapacity(one, two, three):
    capacity = 0
    if one == -2:
        capacity = capacity + 1
    if two == -2:
        capacity = capacity + 1
    if three == -2:
        capacity = capacity + 1
    return capacity

#function to generate starting map coordinates based on faction 
def setMap():
    if currentfaction == 0:
        return (-3400, -1400)
    if currentfaction == 1:
        return (-3000, -5700)
    if currentfaction == 2:
        return (-3400, -6300)
    if currentfaction == 3:
        return (-3400, -4200)
    if currentfaction == 4:
        return (0, -6300)
    if currentfaction == 5:
        return (-700, -6300)
    if currentfaction == 6:
        return (-2500, -6000)
    if currentfaction == 7:
        return (-2800, 0)
    if currentfaction == 8:
        return (-3000, -2400)
    if currentfaction == 9:
        return (-2500, -4600)
    if currentfaction == 10:
        return (-1000, -2600)
    if currentfaction == 11:
        return (-100, -5100)
    if currentfaction == 12:
        return (-2500, -3000)
    if currentfaction == 13:
        return (-1500, -6200)
    if currentfaction == 14:
        return (-1200, -1900)
    if currentfaction == 15:
        return (0, -3700)
    if currentfaction == 16:
        return (-1700, -2400)
    else:
        return (0, 0)
        
#function to determine x coordinate of given hexside
def hexToX(hex):

    xoffset = 60
    xshift = 168
    xunit = ((columnID(hex) - 1) * xshift) + xoffset
    return xunit

#function to determine y coordinate of given hexside
def hexToY(hex):
    
    #yoffsetodd = 177
    yoffsetodd = 279
    #yoffseteven = 274
    yoffseteven = 376
    yshift = 194
    if oddOrEven(hex) == 1:
        yunit = (((hex - ((((columnID(hex) - 1) / 2) * 38) + (((columnID(hex) - 1) / 2) * 39))) - 1) * yshift) + yoffsetodd
    elif oddOrEven(hex) == 0:
        yunit = (((hex - ((((columnID(hex) / 2) - 1) * 38) + ((columnID(hex) / 2) * 39))) - 1) * yshift) + yoffseteven
    else:
        yunit = -1
    return yunit

#x coordinate for minimap
def miniMapX(hex):

    resXmini = (float(resolution.current_w) / float(1366))
    xoffset = int(1006 * resXmini)
    xshift = int(13 * resXmini)
    xunit = ((columnID(hex) - 1) * xshift) + xoffset
    return xunit

def miniMapXbackup(hex):

    xoffset = 1006
    xshift = 13
    xunit = ((columnID(hex) - 1) * xshift) + xoffset
    return xunit

#y coordinate for minimap
def miniMapY(hex):

    resYmini = (float(resolution.current_h) / float(768))
    yoffsetodd = int(8 * resYmini)
    yoffseteven = int(13 * resYmini)
    yshift = int(10 * resYmini)
    yunit = -1
    if oddOrEven(hex) == 1:
        yunit = (((hex - ((((columnID(hex) - 1) / 2) * 38) + (((columnID(hex) - 1) / 2) * 39))) - 1) * yshift) + yoffsetodd
        if yunit > int(378 * resYmini):
            yunit = int(378 * resYmini)
    elif oddOrEven(hex) == 0:
        yunit = (((hex - ((((columnID(hex) / 2) - 1) * 38) + ((columnID(hex) / 2) * 39))) - 1) * yshift) + yoffseteven
        if yunit > int(373 * resYmini):
            yunit = int(373 * resYmini)
    return yunit

def miniMapYbackup(hex):

    yoffsetodd = 8
    yoffseteven = 13
    yshift = 10
    yunit = -1
    if oddOrEven(hex) == 1:
        yunit = (((hex - ((((columnID(hex) - 1) / 2) * 38) + (((columnID(hex) - 1) / 2) * 39))) - 1) * yshift) + yoffsetodd
        if yunit > 378:
            yunit = 378
    elif oddOrEven(hex) == 0:
        yunit = (((hex - ((((columnID(hex) / 2) - 1) * 38) + ((columnID(hex) / 2) * 39))) - 1) * yshift) + yoffseteven
        if yunit > 373:
            yunit = 373
    return yunit

#function to detect if unit is selected
def checkSelected():
    selectedUnit = -1
    for i in range(len(units)):
        if units[i].selected == 1:
            selectedUnit = i
    return selectedUnit

#function to detect if base is selected
def checkBaseSelected():
    selectedBase = -1
    for i in range(len(bases)):
        if bases[i].selected == 1:
            selectedBase = i
    return selectedBase
    
#function to mark all units as unselected
def clearSelected():

    for i in range(len(units)):
        units[i].selected = 0
    for i in range(len(bases)):
        bases[i].selected = 0

#determine if target hex is feasible
def isTargetAcceptable(initial, target):
    if initial == 0 and (target == 1 or target == 39):
        return 1
    elif (initial >= 1 and initial <= 37) and (target == initial - 1 or target == initial + 38 or target == initial + 39 or target == initial + 1):
        return 1
    elif initial == 38 and (target == 37 or target == 16):
        return 1
    elif (initial == 77 or initial == 154 or initial == 231 or initial == 308 or initial == 385 or initial == 462 or initial == 539 or initial == 616 or initial == 693 or initial == 770 or initial == 847 or initial == 924 or initial == 1001) and (target == initial - 38 or target == initial + 1 or target == initial + 39):
        return 1
    elif (initial == 39 or initial == 116 or initial == 193 or initial == 270 or initial == 347 or initial == 424 or initial == 501 or initial == 578 or initial == 655 or initial == 732 or initial == 809 or initial == 886 or initial == 963 or initial == 1040) and (target == initial - 39 or target == initial - 38 or target == initial + 1 or target == initial + 39 or target == initial +38):
        return 1
    elif (initial == 115 or initial == 192 or initial == 269 or initial == 346 or initial == 423 or initial == 500 or initial == 577 or initial == 654 or initial == 731 or initial == 808 or initial == 885 or initial == 962 or initial == 1039) and (target == initial - 39 or target == initial - 1 or target == initial + 38):
        return 1
    elif (initial == 76 or initial == 153 or initial == 230 or initial == 307 or initial == 384 or initial == 461 or initial == 538 or initial == 615 or initial == 692 or initial == 769 or initial == 846 or initial == 923 or initial == 1000 or initial == 1077) and (target == initial - 39 or target == initial - 38 or target == initial + 1 or target == initial + 39 or target == initial + 38):
        return 1
    elif initial == 1078 and (target == 1040 or target == 1079):
        return 1
    elif (initial >= 1079 and i <= 1115) and (target == initial - 1 or target == initial - 39 or target == initial - 38 or target == initial + 1):
        return 1
    elif initial == 1116 and (target == 1077 or target == 1115):
        return 1
    elif target == initial - 1 or target == initial + 38 or target == initial + 39 or target == initial + 1 or target == initial - 38 or target == initial - 39:
        return 1
    else:
        return 0

#function to determine if room remains on a transport
def isThereRoom(unitID):
    subtractor = 0
    for i in range(len(allspecialorders)):
        if allspecialorders[i][2] == unitID:
            subtractor = subtractor + 1
    return units[unitID].capacity - subtractor

#function to determine if unit is a leader
def isLeader(x):
    if x == "Zul'jin" or x == "Kilrogg Deadeye" or x == "Rend Blackhand" or x == "Maim Blackhand" or x == "Zuluhed the Whacked" or x == "Gul'dan the Deceiver" or x == "Cho'gall" or x == "Orgrim Doomhammer" or x == "Varok Saurfang" or x == "Alleria Windrunner" or x == "Sylvanas Windrunner" or x == "Kurdran Wildhammer" or x == "Maz Drachrip" or x == "Magni Bronzebeard" or x == "Muradin Bronzebeard" or x == "Archmage Antonidas" or x == "Archmage Khadgar" or x == "Daelin Proudmoore" or x == "Derek Proudmoore" or x == "Thoras Trollbane" or x == "Danath Trollbane" or x == "Anduin Lothar" or x == "Turalyon" or x == "Uther the Lightbringer" or x == "Terenas Menethil" or x == "Genn Greymane" or x == "Darius Crowley" or x == "Aiden Perenolde" or x == "Lord Falconcrest" or x == "Dagran Thaurissan" or x == "Drek'thar" or x == "Nazgrel" or x == "Drak'thul" or x== "Gorfrunch Smashblade":
        return 1
    else:
        return 0

#function to convert faction number to faction string
def factionString(factionNumber):
    if factionNumber == 0:
        return 'Amani'
    if factionNumber == 1:
        return 'Bleeding Hollow'
    if factionNumber == 2:
        return 'Black Tooth Grin'
    if factionNumber == 3:
        return 'Dragonmaw'
    if factionNumber == 4:
        return 'Stormreaver'
    if factionNumber == 5:
        return 'Twilight Hammer'
    if factionNumber == 6:
        return 'Blackrock'
    if factionNumber == 7:
        return 'Silvermoon'
    if factionNumber == 8:
        return 'Aerie Peak'
    if factionNumber == 9:
        return 'Ironforge'
    if factionNumber == 10:
        return 'Dalaran'
    if factionNumber == 11:
        return 'Kul Tiras'
    if factionNumber == 12:
        return 'Stromgarde'
    if factionNumber == 13:
        return 'Azeroth'
    if factionNumber == 14:
        return 'Lordaeron'
    if factionNumber == 15:
        return 'Gilneas'
    if factionNumber == 16:
        return 'Alterac'
    if factionNumber == 17:
        return 'Dark Iron'
    if factionNumber == 18:
        return 'Burning Blade'
    if factionNumber == 19:
        return 'Frostwolf'
    if factionNumber == 20:
        return 'Dalaran Rebel'
    if factionNumber == 21:
        return 'Gilneas Rebel'
    if factionNumber == 22:
        return 'Firetree'
    if factionNumber == 23:
        return 'Smolderthorn'
    if factionNumber == 24:
        return 'Shadowpine'
    if factionNumber == 25:
        return 'Shadowglen'
    if factionNumber == 26:
        return 'Revantusk'
    if factionNumber == 27:
        return 'Mossflayer'
    if factionNumber == 28:
        return 'Witherbark'
    if factionNumber == 29:
        return 'Vilebranch'
    if factionNumber == 30:
        return 'Dragon'
    if factionNumber == 31:
        return 'Demon'
    
#input initial hex and target hex, return direction
def whatDirection(initial, target):
    if initial - target == 1:
        return 'N'
    if initial - target == -38:
        return 'NE'
    if initial - target == -39:
        return 'SE'
    if initial - target == -1:
        return 'S'
    if initial - target == 38:
        return 'SW'
    if initial - target == 39:
        return 'NW'
    else:
        return 'FAR'

#toggles between 1 and 0 when necessary
def toggle(input):
    if input == 1:
        return 0
    if input == 0:
        return 1

#function to black out an input hex
def fogOfWar(hex):

    pygame.draw.polygon(windowSurface, BLACK, ((hexToX(hex) - 107 + xcord, hexToY(hex) + 4 + ycord), (hexToX(hex) - 53 + xcord, hexToY(hex) - 93 + ycord), (hexToX(hex) + 60 + xcord, hexToY(hex) - 93 + ycord), (hexToX(hex) + 114 + xcord, hexToY(hex) + 4 + ycord), (hexToX(hex) + 60 + xcord, hexToY(hex) + 101 + ycord), (hexToX(hex) - 53 + xcord, hexToY(hex) + 101 + ycord)))

#function to convert initiative count to color
def convertColor(input):
    if input == 0:
        return (27, 135, 34)
    if input == 1:
        return (42, 236, 171)
    if input == 2:
        return (138, 138, 138)
    if input == 3:
        return (120, 35, 151)
    if input == 4:
        return (230, 63, 63)
    if input == 5:
        return (255, 255, 162)
    if input == 6:
        return (141, 27, 46)
    if input == 7:
        return (226, 116, 226)
    if input == 8:
        return (134, 235, 138)
    if input == 9:
        return (255, 139, 139)
    if input == 10:
        return (61, 86, 245)
    if input == 11:
        return (255, 255, 255)
    if input == 11:
        return (245, 183, 61)
    if input == 12:
        return (0, 0, 0)
    if input == 13:
        return (245, 183, 61)
    if input == 14:
        return (61, 86, 245)
    if input == -1:
        return (33, 255, 249)
    else:
        return (255, 255, 255)

#function to draw hexside control lines for combat hexes
def drawHexsideControl(hex):
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_N_CONTROL]),
                     (hexToX(hex) - 50 + xcord, hexToY(hex) - 87 + ycord),
                     (hexToX(hex) + 57 + xcord, hexToY(hex) - 87 + ycord),
                     5)
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_NE_CONTROL]),
                     (hexToX(hex) + 57 + xcord, hexToY(hex) - 87 + ycord),
                     (hexToX(hex) + 110 + xcord, hexToY(hex) + 4 + ycord),
                     5)
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_SE_CONTROL]),
                     (hexToX(hex) + 111 + xcord, hexToY(hex) + 5 + ycord),
                     (hexToX(hex) + 58 + xcord, hexToY(hex) + 98 + ycord),
                     5)
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_S_CONTROL]),
                     (hexToX(hex) + 57 + xcord, hexToY(hex) + 98 + ycord),
                     (hexToX(hex) - 50 + xcord, hexToY(hex) + 98 + ycord),
                     5)
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_SW_CONTROL]),
                     (hexToX(hex) - 51 + xcord, hexToY(hex) + 98 + ycord),
                     (hexToX(hex) - 105 + xcord, hexToY(hex) + 5 + ycord),
                     5)
    pygame.draw.line(windowSurface,
                     convertColor(allhexes[hex][HEX_NW_CONTROL]),
                     (hexToX(hex) - 103 + xcord, hexToY(hex) + 5 + ycord),
                     (hexToX(hex) - 50 + xcord, hexToY(hex) - 87 + ycord),
                     5)

#function to generate unit cost data
def getUnitCost(unit):
    for i in range(len(unitcosts)):
        if unitcosts[i][0] == unit:
            return unitcosts[i]

#function to apply fog of war to minimap hex
def fogMiniMap(hex):
    resXmini = (float(resolution.current_w) / float(1366))
    resYmini = (float(resolution.current_h) / float(768))
    x = miniMapX(hex)
    y = miniMapY(hex)
    xleft = x - int(8 * resXmini)
    if xleft <= 1000:
        xleft = 1001
    xmidleft = x - int(5 * resXmini)
    if xmidleft <= 1000:
        xmidleft = 1001
    xmidright = x + int(5 * resXmini)
    xright = x + int(8 * resXmini)
    ytop = y - int(5 * resYmini)
    ymid = y
    if ymid >= int(376 * resYmini):
        ymid = int(375 * resYmini)
    ybottom = y + int(5 * resYmini)
    if ybottom >= int(376 * resYmini):
        ybottom = int(375 * resYmini)

    windowSurface.lock()
    pygame.draw.polygon(windowSurface, (128, 128, 128, 64), ((xleft, ymid), (xmidleft, ytop), (xmidright, ytop), (xright, ymid), (xmidright, ybottom), (xmidleft, ybottom)))
    windowSurface.unlock()

#function to draw faction squares on hexes
def drawBaseFactionHexes(hex, faction):
    resXmini = (float(resolution.current_w) / float(1920))
    resYmini = (float(resolution.current_h) / float(1080))
    x = miniMapX(hex)
    y = miniMapY(hex)
    xleft = (x * resXmini)
    if xleft <= 1000:
        xleft = 1001
    ytop = (y * resYmini)

    windowSurface.lock()
    pygame.draw.rect(windowSurface, BLACK, (x + 4, y - 3, 6, 6))
    windowSurface.unlock()
    
def drawUnitFactionHexes(hex, faction):
    resXmini = (float(resolution.current_w) / float(1920))
    resYmini = (float(resolution.current_h) / float(1080))
    x = miniMapX(hex)
    y = miniMapY(hex)
    xleft = x + int(4 * resXmini)
    if xleft <= 1000:
        xleft = 1001
    ytop = y - int(2 * resYmini)

    windowSurface.lock()
    pygame.draw.rect(windowSurface, BLACK, (x + 5, y - 2, 4, 4))
    windowSurface.unlock()
        
#function to check for pre-existing base at hex
def doesBaseExist(hex):
    for x in range(len(bases)):
        if bases[x].hexnumber == hex:
            if bases[x].tier == 0:
                return 2
            return 1
    return 0

#function to get data for confirm caravans menu
def caravanLengthCost(input):
    if input < 6:
        return 2
    elif 5 < input < 11:
        return 3
    elif input > 10:
        return 4

def getCaravanData():
    targetbase = "None"
    targetlumber = 0
    targetoil = 0
    if len(tempcaravanlist) > 1:
        for i in range(len(bases)):
            if bases[i].hexnumber == tempcaravanlist[-1]:
                targetbase = bases[i].name
        targetlumber = caravanLengthCost(len(tempcaravanlist) - 1)        
        if LandOrSea(HexsideTerrain(tempcaravanlist[0], tempcaravanlist[1])) == 'water':
            targetoil = targetlumber
    return (targetbase, targetlumber, targetoil)

#function to check transport and return proper menu data
def getTransportString(unit, listnumber):
    if listnumber == 1:
        return_string = 'Slot 1: Empty'
        if units[unit].transportOne != -2:
            unit_string = units[units[unit].transportOne].unitType
            return_string = 'Slot 1: ' + unit_string
            return return_string
        for i in range(len(allspecialorders)):
            if allspecialorders[i][0] == 'Board Transport' and allspecialorders[i][2] == unit:
                target_id = allspecialorders[i][1]
                unit_string = units[target_id].unitType
                return_string = 'Slot 1: ' + unit_string
                return return_string
        return return_string

    if listnumber == 2:
        return_string = 'Slot 2: Empty'
        if units[unit].transportTwo != -2:
            unit_string = units[units[unit].transportTwo].unitType
            return_string = 'Slot 2: ' + unit_string
            return return_string
        count = 0
        for i in range(len(allspecialorders)):
            if allspecialorders[i][0] == 'Board Transport' and allspecialorders[i][2] == unit:
                if units[unit].transportOne != -2:
                    target_id = allspecialorders[i][1]
                    unit_string = units[target_id].unitType
                    return_string = 'Slot 2: ' + unit_string
                    return return_string
                if count > 0:
                    target_id = allspecialorders[i][1]
                    unit_string = units[target_id].unitType
                    return_string = 'Slot 2: ' + unit_string
                    return return_string
            count += 1
        return return_string

    if listnumber == 3:
        return_string = 'Slot 3: Empty'
        count = 0
        for i in range(len(allspecialorders)):
            if allspecialorders[i][0] == 'Board Transport' and allspecialorders[i][2] == unit:
                if count > 1:
                    target_id = allspecialorders[i][1]
                    unit_string = units[target_id].unitType
                    return_string = 'Slot 2: ' + unit_string
                    return return_string
            count += 1
        return return_string
    
#function to determine which hexes are visible to input faction
def establishVisibility(faction):
    visibleHexes = []
    del visibleHexes[:]
    for i in range(len(units)):
        if units[i].faction == faction:
            visibleHexes.append(units[i].hexnumber)
            if units[i].hexnumber - 39 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 39) == 1:
                visibleHexes.append(units[i].hexnumber - 39)
            if units[i].hexnumber - 38 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 38) == 1:
                visibleHexes.append(units[i].hexnumber - 38)
            if units[i].hexnumber - 1 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 1) == 0:
                visibleHexes.append(units[i].hexnumber - 1)
            if units[i].hexnumber - 77 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 77) == 2:
                visibleHexes.append(units[i].hexnumber - 77)
            if units[i].hexnumber - 78 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 78) == 2:
                visibleHexes.append(units[i].hexnumber - 78)
            if units[i].hexnumber - 40 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 40) == 1:
                visibleHexes.append(units[i].hexnumber - 40)
            if units[i].hexnumber - 2 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 2) == 0:
                visibleHexes.append(units[i].hexnumber - 2)
            if units[i].hexnumber - 37 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 37) == 1:
                visibleHexes.append(units[i].hexnumber - 37)
            if units[i].hexnumber - 76 >= 0 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber - 76) == 2:
                visibleHexes.append(units[i].hexnumber - 76)
            if units[i].hexnumber + 1 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 1) == 0:
                visibleHexes.append(units[i].hexnumber + 1)
            if units[i].hexnumber + 38 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 38) == -1:
                visibleHexes.append(units[i].hexnumber + 38)
            if units[i].hexnumber + 39 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 39) == -1:
                visibleHexes.append(units[i].hexnumber + 39)
            if units[i].hexnumber + 37 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 37) == -1:
                visibleHexes.append(units[i].hexnumber + 37)
            if units[i].hexnumber + 76 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 76) == -2:
                visibleHexes.append(units[i].hexnumber + 76)
            if units[i].hexnumber + 77 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 77) == -2:
                visibleHexes.append(units[i].hexnumber + 77)
            if units[i].hexnumber + 78 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 78) == -2:
                visibleHexes.append(units[i].hexnumber + 78)
            if units[i].hexnumber + 40 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 40) == -1:
                visibleHexes.append(units[i].hexnumber + 40)
            if units[i].hexnumber + 2 <= 1116 and columnID(units[i].hexnumber) - columnID(units[i].hexnumber + 2) == 0:
                visibleHexes.append(units[i].hexnumber + 2)
    for i in range(len(allbases)):
        if allbases[i][2] == faction:
            visibleHexes.append(allbases[i][1])
            if allbases[i][1] - 39 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 39) == 1:
                visibleHexes.append(allbases[i][1] - 39)
            if allbases[i][1] - 38 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 38) == 1:
                visibleHexes.append(allbases[i][1] - 38)
            if allbases[i][1] - 1 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 1) == 0:
                visibleHexes.append(allbases[i][1] - 1)
            if allbases[i][1] - 77 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 77) == 2:
                visibleHexes.append(allbases[i][1] - 77)
            if allbases[i][1] - 78 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 78) == 2:
                visibleHexes.append(allbases[i][1] - 78)
            if allbases[i][1] - 40 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 40) == 1:
                visibleHexes.append(allbases[i][1] - 40)
            if allbases[i][1] - 2 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 2) == 0:
                visibleHexes.append(allbases[i][1] - 2)
            if allbases[i][1] - 37 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 37) == 1:
                visibleHexes.append(allbases[i][1] - 37)
            if allbases[i][1] - 76 >= 0 and columnID(allbases[i][1]) - columnID(allbases[i][1] - 76) == 2:
                visibleHexes.append(allbases[i][1] - 76)
            if allbases[i][1] + 1 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 1) == 0:
                visibleHexes.append(allbases[i][1] + 1)
            if allbases[i][1] + 38 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 38) == -1:
                visibleHexes.append(allbases[i][1] + 38)
            if allbases[i][1] + 39 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 39) == -1:
                visibleHexes.append(allbases[i][1] + 39)
            if allbases[i][1] + 37 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 37) == -1:
                visibleHexes.append(allbases[i][1] + 37)
            if allbases[i][1] + 76 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 76) == -2:
                visibleHexes.append(allbases[i][1] + 76)
            if allbases[i][1] + 77 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 77) == -2:
                visibleHexes.append(allbases[i][1] + 77)
            if allbases[i][1] + 78 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 78) == -2:
                visibleHexes.append(allbases[i][1] + 78)
            if allbases[i][1] + 40 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 40) == -1:
                visibleHexes.append(allbases[i][1] + 40)
            if allbases[i][1] + 2 <= 1116 and columnID(allbases[i][1]) - columnID(allbases[i][1] + 2) == 0:
                visibleHexes.append(allbases[i][1] + 2)
    visibleHexes = list(set(visibleHexes))
    return visibleHexes

def miniMapScale(x,y):
    resXmini = (float(resolution.current_w) / float(1366))
    resYmini = (float(resolution.current_h) / float(768))
    x = x - int(1020 * resXmini)
    y = y - int(10 * resYmini)
    xscale = float(11.34 / resXmini)
    yscale = float(18.59 / resYmini)
    xsmoothed = ((x * xscale) - ((x * xscale) % 100))
    ysmoothed = ((y * yscale) - ((y * yscale) % 100))
    xsmoothed = -1 * xsmoothed
    ysmoothed = -1 * ysmoothed
    if xsmoothed > 0:
        xsmoothed = 0
    if xsmoothed < X_CORD_SCROLL:
        xsmoothed = X_CORD_SCROLL
    if ysmoothed > 0:
        ysmoothed = 0
    if ysmoothed < Y_CORD_SCROLL:
        ysmoothed = Y_CORD_SCROLL
    return (xsmoothed, ysmoothed)

def establishUnitBuildList():
    for i in range(len(allbuildables[0])):
        if int(allbuildables[0][i]) != -1:
            unitBuildList.append(unitsdict[i])
            

#function to return rects for unit build
def unitListArea(unit, order):
    text_rect = menuFont.render(unit, True, GOLD)
    rect = text_rect.get_rect()
    if order < 6:
        rect.left = 1010 * resX
        rect.top = (600 + (order * 20)) * resY
    if order >= 6:
        rect.left = 1205 * resX
        rect.top = (600 + (order * 20 - 120)) * resY
    return rect

def updateOrderString(unitID, ordertype):
    if ordertype == 'Move':
        for i in range(len(allorders)):
            if allorders[i][0] == unitID and len(allorders[i]) > 1:
                if len(allorders[i]) == 5:
                    units[unitID].orders = 'Move ' + whatDirection(units[unitID].hexnumber, allorders[i][1]) + ' ' + whatDirection(allorders[i][1], allorders[i][2]) + ' ' + whatDirection(allorders[i][2], allorders[i][3]) + ' ' + whatDirection(allorders[i][3], allorders[i][4])
                if len(allorders[i]) == 4:
                    units[unitID].orders = 'Move ' + whatDirection(units[unitID].hexnumber, allorders[i][1]) + ' ' + whatDirection(allorders[i][1], allorders[i][2]) + ' ' + whatDirection(allorders[i][2], allorders[i][3])
                if len(allorders[i]) == 3:
                    units[unitID].orders = 'Move ' + whatDirection(units[unitID].hexnumber, allorders[i][1]) + ' ' + whatDirection(allorders[i][1], allorders[i][2])
                if len(allorders[i]) == 2:
                    units[unitID].orders = 'Move ' + whatDirection(units[unitID].hexnumber, allorders[i][1])
    if ordertype == 'Clear':
        units[unitID].orders = 'None'
    if ordertype == 'Ranged':
        for i in range(len(allspecialorders)):
            if allspecialorders[i][1] == unitID and len(allspecialorders[i]) > 1:
                units[unitID].orders = 'Ranged Fire ' + whatDirection(units[unitID].hexnumber, allspecialorders[i][2])
    if ordertype == 'Board Transport':
        for i in range(len(allspecialorders)):
            if allspecialorders[i][1] == unitID and len(allspecialorders[i]) > 1:
                units[unitID].orders = 'Board Transport'
    if ordertype == 'Build Base':
        units[unitID].orders = 'Build Base'
    if ordertype == 'Teleport Dalaran':
        units[unitID].orders = 'Teleport: Dalaran'
    
def intToResource(int):
    if int == 4:
        return 'Gold'
    if int == 5:
        return 'Lumber'
    if int == 6:
        return 'Oil'

def isSecondMoveAvailable(tier):
    if tier == 2 or tier == 3:
        return 'None'
    else:
        return 'Locked'

def isThirdMoveAvailable(tier):
    if tier == 3:
        return 'None'
    else:
        return 'Locked'

#method to return proper upgrade base cost string
def upgradeBaseString():
    if bases[checkBaseSelected()].tier == 1:
        return 'Tier 2 upgrade cost: 6 gold, 6 lumber, 2 oil'
    elif bases[checkBaseSelected()].tier == 2:
        return 'Tier 3 upgrade cost: 8 gold, 8 lumber, 4 oil'
    else:
        return 'Cannot upgrade base.'
def upgradeBaseStringTwo():
    if bases[checkBaseSelected()].tier == 1:
        return 'Requires at least 2 resources per harvest.'
    elif bases[checkBaseSelected()].tier == 2:
        return 'Requires at least 4 resources per harvest.'
    else:
        return 'Cannot upgrade base.'

#method to draw caravan lines
def drawCaravans():
    for x in range(len(allcaravans)):
        color = convertColor(int(allfactions[int(allcaravans[x][2])]))
        templist = allcaravans[x]
        templistB = templist[4:]
        route = list(filter(lambda a: a != None, templistB))
        for z in range(len(route) - 1):

            pygame.draw.line(windowSurface, color, (hexSurfaces[int(route[z])].centerx, hexSurfaces[int(route[z])].centery), (hexSurfaces[int(route[z + 1])].centerx, hexSurfaces[int(route[z + 1])].centery), 15)

#method to draw rangefire lines
def drawRangeFireLines():
    for i in range(len(allspecialorders)):
        if allspecialorders[i][0] == "Rangedfire":
            pygame.draw.line(windowSurface, CORNFLOWER_BLUE, (units[allspecialorders[i][1]].area.centerx, units[allspecialorders[i][1]].area.centery), (hexSurfaces[int(allspecialorders[i][2])].centerx, hexSurfaces[int(allspecialorders[i][2])].centery), 3)

#method to draw board transport lines
def drawBoardTransportLines():
    for i in range(len(allspecialorders)):
        if allspecialorders[i][0] == "Board Transport":
            pygame.draw.line(windowSurface, GOLD, (units[allspecialorders[i][1]].area.centerx, units[allspecialorders[i][1]].area.centery), (units[allspecialorders[i][2]].area.centerx, units[allspecialorders[i][2]].area.centery), 3)

#method to calculate harvest yield for a hex
def calculateHarvest(temphex):
    tempresources = [0,0,0]
    tempresources[0] += int(allhexes[temphex][HEX_GOLD])
    for i in range(len(allhexes)):
        if int(allhexes[i][HEX_MILL]) == temphex:
            tempresources[1] += 1
            tempresources[0] += int(allhexes[i][HEX_GOLD])
        if int(allhexes[i][HEX_FARM]) == temphex:
            tempresources[0] += int(allhexes[i][HEX_GOLD])
        if int(allhexes[i][HEX_RIG]) == temphex:
            tempresources[2] += 1
    return tempresources

#method to reset available base resources when economic actions cleared
def resetResources(index):
    if alleconomicactions[index][0] == 'Build Unit':
        bases[checkBaseSelected()].goldleft += getUnitCost(alleconomicactions[index][2])[1]
        bases[checkBaseSelected()].lumberleft += getUnitCost(alleconomicactions[index][2])[2]
        bases[checkBaseSelected()].oilleft += getUnitCost(alleconomicactions[index][2])[3]
        foodcost[0] -= 1
    if alleconomicactions[index][0] == 'Harvest':
        resources = calculateHarvest(bases[checkBaseSelected()].hexnumber)
        bases[checkBaseSelected()].goldleft -= resources[0]
        bases[checkBaseSelected()].lumberleft -= resources[1]
        bases[checkBaseSelected()].oilleft -= resources[2]
    if alleconomicactions[index][0] == 'Send Resources':
        bases[checkBaseSelected()].goldleft += alleconomicactions[index][3]
        bases[checkBaseSelected()].lumberleft += alleconomicactions[index][4]
        bases[checkBaseSelected()].oilleft += alleconomicactions[index][5]
    if alleconomicactions[index][0] == 'Commerce':
        if alleconomicactions[index][2] == BASE_GOLD:
            bases[checkBaseSelected()].goldleft += 2
        if alleconomicactions[index][2] == BASE_LUMBER:
            bases[checkBaseSelected()].lumberleft += 2
        if alleconomicactions[index][2] == BASE_OIL:
            bases[checkBaseSelected()].oilleft += 2
        if alleconomicactions[index][3] == BASE_GOLD:
            bases[checkBaseSelected()].goldleft -= 1
        if alleconomicactions[index][3] == BASE_LUMBER:
            bases[checkBaseSelected()].lumberleft -= 1
        if alleconomicactions[index][3] == BASE_OIL:
            bases[checkBaseSelected()].oilleft -= 1
    if alleconomicactions[index][0] == 'Assist Construction':
        if doesBaseExist(alleconomicactions[index][2]) == 2:
            bases[checkBaseSelected()].goldleft += 2
            bases[checkBaseSelected()].lumberleft += 2
        else:
            bases[checkBaseSelected()].goldleft += 4
            bases[checkBaseSelected()].lumberleft += 4
    if alleconomicactions[index][0] == 'Expand':
        bases[checkBaseSelected()].lumberleft += 2
    if alleconomicactions[index][0] == 'Upgrade Base':
        if bases[checkBaseSelected()].tier == 1:
            bases[checkBaseSelected()].goldleft += 6
            bases[checkBaseSelected()].lumberleft += 6
            bases[checkBaseSelected()].oilleft += 2
        if bases[checkBaseSelected()].tier == 2:
            bases[checkBaseSelected()].goldleft += 8
            bases[checkBaseSelected()].lumberleft += 8
            bases[checkBaseSelected()].oilleft += 4
    if alleconomicactions[index][0] == 'Establish Caravan':
        if alleconomicactions[index][2] == 'land':
            if len(alleconomicactions[index]) < 10:
                bases[checkBaseSelected()].lumberleft += 2
            if 9 < len(alleconomicactions[index]) < 15:
                bases[checkBaseSelected()].lumberleft += 3
            if len(alleconomicactions[index]) > 14:
                bases[checkBaseSelected()].lumberleft += 4
        if alleconomicactions[index][2] == 'water':
            if len(alleconomicactions[index]) < 10:
                bases[checkBaseSelected()].lumberleft += 2
                bases[checkBaseSelected()].oilleft += 2
            if 9 < len(alleconomicactions[index]) < 15:
                bases[checkBaseSelected()].lumberleft += 3
                bases[checkBaseSelected()].oilleft += 3
            if len(alleconomicactions[index]) > 14:
                bases[checkBaseSelected()].lumberleft += 4
                bases[checkBaseSelected()].oilleft += 4
    if alleconomicactions[index][0] == 'Rest Unit':
        bases[checkBaseSelected()].goldleft += 2
        
def updateBaseOrderString(baseID, ordertype, ordernumber=0, resource=0, unittype='None', targetbase='None', goldsent=0, lumbersent=0, oilsent=0, faction='None'):
    if ordertype == 'Clear':
        if ordernumber == 1:
            bases[baseID].first_orders = 'None'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'None'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'None'
    if ordertype == 'Destroy Base':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Destroy Base'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Destroy Base'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Destroy Base'
    if ordertype == 'Give Base':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Give Base - ' + factionString(faction)
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Give Base - ' + factionString(faction)
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Give Base - ' + factionString(faction)
    if ordertype == 'Give Expansion':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Give Expansion'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Give Expansion'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Give Expansion'
    if ordertype == 'Harvest':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Harvest'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Harvest'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Harvest'
    if ordertype == 'Commerce':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Commerce: ' + intToResource(POTENTIAL_RESOURCE) + ' to ' + intToResource(resource)
        if ordernumber == 2:
            bases[baseID].second_orders = 'Commerce: ' + intToResource(POTENTIAL_RESOURCE) + ' to ' + intToResource(resource)
        if ordernumber == 3:
            bases[baseID].third_orders = 'Commerce: ' + intToResource(POTENTIAL_RESOURCE) + ' to ' + intToResource(resource)
    if ordertype == 'Expand':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Expand'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Expand'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Expand'
    if ordertype == 'Upgrade Base':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Upgrade Base'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Upgrade Base'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Upgrade Base'
    if ordertype == 'Build Unit':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Build ' + unittype
        if ordernumber == 2:
            bases[baseID].second_orders = 'Build ' + unittype
        if ordernumber == 3:
            bases[baseID].third_orders = 'Build ' + unittype
    if ordertype == 'Establish Caravan':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Caravan ' + targetbase
        if ordernumber == 2:
            bases[baseID].second_orders = 'Caravan ' + targetbase
        if ordernumber == 3:
            bases[baseID].third_orders = 'Caravan ' + targetbase
    if ordertype == 'Send Resources':
        if ordernumber == 1:
            bases[baseID].first_orders = str(goldsent)+ 'g ' + str(lumbersent) + 'l ' + str(oilsent) + 'o to ' + targetbase
        if ordernumber == 2:
            bases[baseID].second_orders = str(goldsent)+ 'g ' + str(lumbersent) + 'l ' + str(oilsent) + 'o to ' + targetbase
        if ordernumber == 3:
            bases[baseID].third_orders = str(goldsent)+ 'g ' + str(lumbersent) + 'l ' + str(oilsent) + 'o to ' + targetbase
    if ordertype == 'Rest Unit':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Rest ' + unittype
        if ordernumber == 2:
            bases[baseID].second_orders = 'Rest ' + unittype
        if ordernumber == 3:
            bases[baseID].third_orders = 'Rest ' + unittype
    if ordertype == 'Assist Construction':
        if ordernumber == 1:
            bases[baseID].first_orders = 'Assist Construction'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Assist Construction'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Assist Construction'

def findBaseImage(baseID):
    if bases[baseID].overallfaction == 'Horde':
        if bases[baseID].tier == 1:
            return 'HordeGreatHallMenuImage'
        if bases[baseID].tier == 2:
            return 'HordeStrongholdMenuImage'
        if bases[baseID].tier == 3:
            return 'HordeFortressMenuImage'
    elif bases[baseID].overallfaction == 'Alliance':
        if bases[baseID].tier == 1:
            return 'AllianceTownHallMenuImage'
        if bases[baseID].tier == 2:
            return 'AllianceKeepMenuImage'
        if bases[baseID].tier == 3:
            return 'AllianceCastleMenuImage'         

def redraw():

    #update hexSurfaces
    for i in range(1117):
        hexSurfaces[i] = (pygame.Rect((hexToX(i) - 60) + xcord, (hexToY(i) - 70) + ycord, 130, 150))

    #update units per hex
    unitsPer = [ 0 for i in range(1116) ]
    for j in range(len(units)):
        if units[j].alive == 1:
            unitsPer[units[j].hexnumber] = unitsPer[units[j].hexnumber] + 1

    #update resource tracking
    SEND_GOLD_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, GOLD)
    SEND_GOLD_TWO_TEXTrect = SEND_GOLD_TWO_TEXT.get_rect()
    SEND_GOLD_TWO_TEXTrect.left = 1010 * resX
    SEND_GOLD_TWO_TEXTrect.top = 675 * resY

    SEND_LUMBER_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, FOREST)
    SEND_LUMBER_TWO_TEXTrect = SEND_LUMBER_TWO_TEXT.get_rect()
    SEND_LUMBER_TWO_TEXTrect.left = 1010 * resX
    SEND_LUMBER_TWO_TEXTrect.top = 675 * resY

    SEND_OIL_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, GRAY)
    SEND_OIL_TWO_TEXTrect = SEND_OIL_TWO_TEXT.get_rect()
    SEND_OIL_TWO_TEXTrect.left = 1010 * resX
    SEND_OIL_TWO_TEXTrect.top = 675 * resY
    
    #redraw map
    windowSurface.blit(mapImage, (xcord, ycord))

    #redraw bases, base names, banners
    for i in range(len(bases)):
        bases[i].area = (pygame.Rect(hexToX(bases[i].hexnumber) - 60 + xcord, hexToY(bases[i].hexnumber) - 60 + ycord, BASE_WIDTH, BASE_LENGTH))
        bases[i].banner_area = (pygame.Rect(hexToX(bases[i].hexnumber) + xcord, hexToY(bases[i].hexnumber) - 105 + ycord, BANNER_WIDTH, BANNER_LENGTH))

        BASE_NAME_TEXT = basicFont.render(bases[i].name, True, WHITE)
        BASE_NAME_TEXTrect = BASE_NAME_TEXT.get_rect()
        BASE_NAME_TEXTrect.center = (hexToX(bases[i].hexnumber) + xcord, hexToY(bases[i].hexnumber) + 105 + ycord)

        if bases[i].tier == 0:
            windowSurface.blit(RuinsImage, bases[i].area)
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 1:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(HordeGreatHallImage, bases[i].area)
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 2:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(HordeStrongholdImage, bases[i].area)
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 3:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(HordeFortressImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 1:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(AllianceTownHallImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 2:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(AllianceKeepImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 3:
            windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
            windowSurface.blit(eval(factionString(bases[i].faction).replace(' ','')+'Banner'), bases[i].banner_area)
            windowSurface.blit(AllianceCastleImage, bases[i].area)

    #redraw expansions
    for i in range(len(expansions)):
        expansions[i].area = (pygame.Rect(hexToX(expansions[i].hexnumber) - EXPANSION_X_OFFSET + xcord, hexToY(expansions[i].hexnumber) - EXPANSION_Y_OFFSET + ycord, EXPANSION_WIDTH, EXPANSION_LENGTH))
        if expansions[i].overallfaction == 'Horde':
            if expansions[i].kind == 'Farm':
                windowSurface.blit(HordeFarmImage, expansions[i].area)
            if expansions[i].kind == 'Mill':
                windowSurface.blit(HordeMillImage, expansions[i].area)
            if expansions[i].kind == 'Rig':
                windowSurface.blit(HordeRigImage, expansions[i].area)
        if expansions[i].overallfaction == 'Alliance':
            if expansions[i].kind == 'Farm':
                windowSurface.blit(AllianceFarmImage, expansions[i].area)
            if expansions[i].kind == 'Mill':
                windowSurface.blit(AllianceMillImage, expansions[i].area)
            if expansions[i].kind == 'Rig':
                windowSurface.blit(AllianceRigImage, expansions[i].area)

    #redraw special buildings
    for i in range(len(allspecialbuildings)):
        if allhexes[allspecialbuildings[i]][HEX_BUILDING] == 1:
            temparea = (pygame.Rect(hexToX(allspecialbuildings[i]) - 80 + xcord, hexToY(allspecialbuildings[i]) - 80 + ycord, BASE_WIDTH, BASE_LENGTH))
            windowSurface.blit(RunestoneImage, temparea)
        if allhexes[allspecialbuildings[i]][HEX_BUILDING] == 2:
            temparea = (pygame.Rect(hexToX(allspecialbuildings[i]) - 60 + xcord, hexToY(allspecialbuildings[i]) - 60 + ycord, BASE_WIDTH, BASE_LENGTH))
            windowSurface.blit(DarkPortalImage, temparea)
        if allhexes[allspecialbuildings[i]][HEX_BUILDING] == 3:
            temparea = (pygame.Rect(hexToX(allspecialbuildings[i]) - 60 + xcord, hexToY(allspecialbuildings[i]) - 60 + ycord, BASE_WIDTH, BASE_LENGTH))
            windowSurface.blit(DragonRoostImage, temparea)
    
    #redraw base selection box
    if checkBaseSelected() != -1:
        for i in range(len(bases)):
            if bases[i].selected == 1:
                pygame.draw.rect(windowSurface, RED, bases[i].area, 2)

    #redraw expansion selection boxes
    if checkBaseSelected() != -1:
        for i in range(len(expansions)):
            if expansions[i].owner == bases[checkBaseSelected()].hexnumber:
                pygame.draw.rect(windowSurface, RED, expansions[i].area.inflate(-40, -40), 2)

    #update and draw hexside control for combat hexes
    for i in range(len(combathexes)):
        drawHexsideControl(combathexes[i])
                 
    #redraw units
    for i in range(len(units)):
        if units[i].alive == 1:
            units[i].area = (pygame.Rect(hexToX(units[i].hexnumber) + xcord, hexToY(units[i].hexnumber) + ycord, UNIT_WIDTH, UNIT_LENGTH))
            if unitsPer[units[i].hexnumber] == 1:
                units[i].area = units[i].area.move(-45, 65)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -45
                    units[i].yshift = 65
            if unitsPer[units[i].hexnumber] == 2:
                units[i].area = units[i].area.move(-10, 65)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -10
                    units[i].yshift = 65
            if unitsPer[units[i].hexnumber] == 3:
                units[i].area = units[i].area.move(25, 65)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 25
                    units[i].yshift = 65
            if unitsPer[units[i].hexnumber] == 4:
                units[i].area = units[i].area.move(-80, 30)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -80
                    units[i].yshift = 30
            if unitsPer[units[i].hexnumber] == 5:
                units[i].area = units[i].area.move(-45, 30)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -45
                    units[i].yshift = 30
            if unitsPer[units[i].hexnumber] == 6:
                units[i].area = units[i].area.move(-10, 30)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -10
                    units[i].yshift = 30
            if unitsPer[units[i].hexnumber] == 7:
                units[i].area = units[i].area.move(25, 30)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 25
                    units[i].yshift = 30
            if unitsPer[units[i].hexnumber] == 8:
                units[i].area = units[i].area.move(60, 30)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 60
                    units[i].yshift = 30
            if unitsPer[units[i].hexnumber] == 9:
                units[i].area = units[i].area.move(-115, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -115
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 10:
                units[i].area = units[i].area.move(-80, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -80
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 11:
                units[i].area = units[i].area.move(-45, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -45
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 12:
                units[i].area = units[i].area.move(-10, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -10
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 13:
                units[i].area = units[i].area.move(25, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 25
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 14:
                units[i].area = units[i].area.move(60, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 60
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 15:
                units[i].area = units[i].area.move(95, -5)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 95
                    units[i].yshift = -5
            if unitsPer[units[i].hexnumber] == 16:
                units[i].area = units[i].area.move(-80, -40)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -80
                    units[i].yshift = -40
            if unitsPer[units[i].hexnumber] == 17:
                units[i].area = units[i].area.move(-45, -40)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -45
                    units[i].yshift = -40
            if unitsPer[units[i].hexnumber] == 18:
                units[i].area = units[i].area.move(-10, -40)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -10
                    units[i].yshift = -40
            if unitsPer[units[i].hexnumber] == 19:
                units[i].area = units[i].area.move(25, -40)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 25
                    units[i].yshift = -40
            if unitsPer[units[i].hexnumber] == 20:
                units[i].area = units[i].area.move(60, -40)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 60
                    units[i].yshift = -40
            if unitsPer[units[i].hexnumber] == 21:
                units[i].area = units[i].area.move(-45, -75)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -45
                    units[i].yshift = -75
            if unitsPer[units[i].hexnumber] == 22:
                units[i].area = units[i].area.move(-10, -75)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = -10
                    units[i].yshift = -75
            if unitsPer[units[i].hexnumber] == 23:
                units[i].area = units[i].area.move(25, -75)
                if INITIAL_TOGGLE == 0:
                    units[i].xshift = 25
                    units[i].yshift = -75

            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)

    #draw caravan maps (if toggled)
    if CARAVAN_MAP_TOGGLE == 1:
        drawCaravans()

    #update fog of war (if toggled)
    #if FOG_TOGGLE == 1:
    fogList = fogHexes(coordsToHex(xcord, ycord))
    for i in range(len(fogList)):
        fogarea = hexSurfaces[fogList[i]].move(-50,-25)
        windowSurface.blit(fogImage, fogarea)
    #for i in range(len(fogOfWarList)):

        # fogOfWar(fogOfWarList[i])
        
        #fogarea = hexSurfaces[fogOfWarList[i]].move(-50,-25)
        #windowSurface.blit(fogImage, fogarea)

    #update and draw arrows
    drawRangeFireLines()
    drawBoardTransportLines()
    if CARAVAN_TOGGLE == 1 or CONFIRM_CARAVAN_TOGGLE == 1:
        if len(tempcaravanlist) > 1:
            for i in range(len(tempcaravanlist) - 1):
                pygame.draw.line(windowSurface, BLUE, (hexSurfaces[tempcaravanlist[i]].centerx, hexSurfaces[tempcaravanlist[i]].centery), (hexSurfaces[tempcaravanlist[i + 1]].centerx, hexSurfaces[tempcaravanlist[i + 1]].centery), 3) 
                pygame.draw.circle(windowSurface, LIME, (hexSurfaces[tempcaravanlist[i + 1]].centerx, hexSurfaces[tempcaravanlist[i + 1]].centery), 5, 0)
    if checkBaseSelected() != -1:
        if 'Caravan' in bases[checkBaseSelected()].first_orders or 'Caravan' in bases[checkBaseSelected()].second_orders or 'Caravan' in bases[checkBaseSelected()].third_orders:
            for i in range(len(alleconomicactions)):
                if alleconomicactions[i][0] == 'Establish Caravan' and alleconomicactions[i][1] == bases[checkBaseSelected()].hexnumber:
                    # for j in range(len(alleconomicactions[i][2])- 1):
                    for j in range(len(alleconomicactions[i]) - 1):
                        if (j != 0) and (j != 1) and (j != 2):
                            pygame.draw.line(windowSurface, BLUE, (hexSurfaces[alleconomicactions[i][j]].centerx, hexSurfaces[alleconomicactions[i][j]].centery), (hexSurfaces[alleconomicactions[i][j + 1]].centerx, hexSurfaces[alleconomicactions[i][j + 1]].centery), 3) 
                            pygame.draw.circle(windowSurface, LIME, (hexSurfaces[alleconomicactions[i][j + 1]].centerx, hexSurfaces[alleconomicactions[i][j + 1]].centery), 5, 0)
    if ARROWS_TOGGLE == 0:
        for i in range(len(allorders)):
            if len(allorders[i]) > 1:
                pygame.draw.line(windowSurface, BLACK, (units[allorders[i][0]].area.centerx, units[allorders[i][0]].area.centery), (hexSurfaces[allorders[i][1]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][1]].centery + units[allorders[i][0]].yshift), 3) 
                pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][1]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][1]].centery + units[allorders[i][0]].yshift), 5, 0)
                if len(allorders[i]) > 2:
                    pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][1]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][1]].centery + units[allorders[i][0]].yshift), (hexSurfaces[allorders[i][2]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][2]].centery + units[allorders[i][0]].yshift), 3) 
                    pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][2]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][2]].centery + units[allorders[i][0]].yshift), 5, 0)
                    if len(allorders[i]) > 3:
                        pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][2]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][2]].centery + units[allorders[i][0]].yshift), (hexSurfaces[allorders[i][3]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][3]].centery + units[allorders[i][0]].yshift), 3) 
                        pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][3]].centerx + units[allorders[i][0]].xshift, hexSurfaces[allorders[i][3]].centery + units[allorders[i][0]].yshift), 5, 0)
    elif ARROWS_TOGGLE == 1:
        if checkSelected() != -1:
            arrowTarget = checkSelected()
            for i in range(len(allorders)):
                if allorders[i][0] == arrowTarget and len(allorders[i]) > 1:
                    pygame.draw.line(windowSurface, BLACK, (units[allorders[i][0]].area.centerx, units[allorders[i][0]].area.centery), (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), 3) 
                    pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), 5, 0)
                    if allorders[i][0] == arrowTarget and len(allorders[i]) > 2:
                        pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), 3) 
                        pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), 5, 0)
                        if allorders[i][0] == arrowTarget and len(allorders[i]) > 3:
                            pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), (hexSurfaces[allorders[i][3]].centerx, hexSurfaces[allorders[i][3]].centery), 3) 
                            pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][3]].centerx, hexSurfaces[allorders[i][3]].centery), 5, 0)

    #redraw selection box
    if checkSelected() != -1:
        for i in range(len(units)):
            if units[i].selected == 1:
                pygame.draw.rect(windowSurface, RED, units[i].area, 4)
                                   
    #redraw menus
    windowSurface.blit(rightMenuImage, rightMenu)

    #redraw menu info
    if QUIT_TOGGLE == 1:
        windowSurface.blit(QUIT_CONFIRM_TEXT, QUIT_CONFIRM_TEXTrect)
        windowSurface.blit(QUIT_CONFIRM_YES_TEXT, QUIT_CONFIRM_YES_TEXTrect)
        windowSurface.blit(QUIT_CONFIRM_NO_TEXT, QUIT_CONFIRM_NO_TEXTrect)
    elif SUBMIT_TOGGLE == 1:
        windowSurface.blit(SUBMIT_CONFIRM_TEXT, SUBMIT_CONFIRM_TEXTrect)
        windowSurface.blit(SUBMIT_CONFIRM_YES_TEXT, SUBMIT_CONFIRM_YES_TEXTrect)
        windowSurface.blit(SUBMIT_CONFIRM_NO_TEXT, SUBMIT_CONFIRM_NO_TEXTrect)
    elif GIVE_BASE_TOGGLE == 1:
        windowSurface.blit(GIVE_BASE_TEXT, GIVE_BASE_TEXTrect)
    elif GIVE_EXPANSION_TOGGLE_ONE == 1:
        windowSurface.blit(GIVE_EXPANSION_TEXT_ONE, GIVE_EXPANSION_TEXT_ONErect)
    elif GIVE_EXPANSION_TOGGLE_TWO == 1:
        windowSurface.blit(GIVE_EXPANSION_TEXT_TWO, GIVE_EXPANSION_TEXT_TWOrect)
    elif COMMERCE_TOGGLE_ONE == 1:
        windowSurface.blit(COMMERCE_IN_TEXT, COMMERCE_IN_TEXTrect)
        windowSurface.blit(COMMERCE_GOLD_TEXT, COMMERCE_GOLD_TEXTrect)
        windowSurface.blit(COMMERCE_LUMBER_TEXT, COMMERCE_LUMBER_TEXTrect)
        windowSurface.blit(COMMERCE_OIL_TEXT, COMMERCE_OIL_TEXTrect)
    elif COMMERCE_TOGGLE_TWO == 1:
        windowSurface.blit(COMMERCE_OUT_TEXT, COMMERCE_OUT_TEXTrect)
        windowSurface.blit(COMMERCE_GOLD_TEXT, COMMERCE_GOLD_TEXTrect)
        windowSurface.blit(COMMERCE_LUMBER_TEXT, COMMERCE_LUMBER_TEXTrect)
        windowSurface.blit(COMMERCE_OIL_TEXT, COMMERCE_OIL_TEXTrect)
    elif EXPAND_TOGGLE == 1:
        windowSurface.blit(EXPAND_TEXT, EXPAND_TEXTrect)
        windowSurface.blit(EXPAND_TWO_TEXT, EXPAND_TWO_TEXTrect)
        windowSurface.blit(EXPAND_THREE_TEXT, EXPAND_THREE_TEXTrect)
        windowSurface.blit(EXPAND_FOUR_TEXT, EXPAND_FOUR_TEXTrect)
    elif REST_UNIT_TOGGLE == 1:
        windowSurface.blit(REST_UNIT_TEXT, REST_UNIT_TEXTrect)
    elif ASSIST_CONSTRUCTION_TOGGLE == 1:
        windowSurface.blit(ASSIST_CONSTRUCTION_TEXT, ASSIST_CONSTRUCTION_TEXTrect)
        windowSurface.blit(ASSIST_CONSTRUCTION_TEXT_TWO, ASSIST_CONSTRUCTION_TEXT_TWOrect)
        windowSurface.blit(ASSIST_CONSTRUCTION_TEXT_THREE, ASSIST_CONSTRUCTION_TEXT_THREErect)
        windowSurface.blit(ASSIST_CONSTRUCTION_TEXT_FOUR, ASSIST_CONSTRUCTION_TEXT_FOURrect)
    elif UPGRADE_BASE_TOGGLE == 1:

        UPGRADE_BASE_TWO_TEXT = menuFont.render(upgradeBaseString(), True, GOLD)
        UPGRADE_BASE_TWO_TEXTrect = UPGRADE_BASE_TWO_TEXT.get_rect()
        UPGRADE_BASE_TWO_TEXTrect.left = 1010 * resX
        UPGRADE_BASE_TWO_TEXTrect.top = 625 * resY

        UPGRADE_BASE_THREE_TEXT = menuFont.render(upgradeBaseStringTwo(), True, GOLD)
        UPGRADE_BASE_THREE_TEXTrect = UPGRADE_BASE_THREE_TEXT.get_rect()
        UPGRADE_BASE_THREE_TEXTrect.left = 1010 * resX
        UPGRADE_BASE_THREE_TEXTrect.top = 650 * resY
        
        windowSurface.blit(UPGRADE_BASE_TEXT, UPGRADE_BASE_TEXTrect)
        windowSurface.blit(UPGRADE_BASE_TWO_TEXT, UPGRADE_BASE_TWO_TEXTrect)
        windowSurface.blit(UPGRADE_BASE_THREE_TEXT, UPGRADE_BASE_THREE_TEXTrect)
        if UPGRADE_BASE_ERROR_TOGGLE == 1:
            windowSurface.blit(UPGRADE_BASE_ERROR_TEXT, UPGRADE_BASE_ERROR_TEXTrect)
    elif CARAVAN_TOGGLE == 1:
        windowSurface.blit(CARAVAN_ONE_TEXT, CARAVAN_ONE_TEXTrect)
        windowSurface.blit(CARAVAN_TWO_TEXT, CARAVAN_TWO_TEXTrect)
        windowSurface.blit(CARAVAN_THREE_TEXT, CARAVAN_THREE_TEXTrect)
    elif CONFIRM_CARAVAN_TOGGLE == 1:
        CONFIRM_CARAVAN_ONE_TEXT = menuFont.render('Confirm caravan to ' + getCaravanData()[0] + '?', True, GOLD)
        CONFIRM_CARAVAN_ONE_TEXTrect = CONFIRM_CARAVAN_ONE_TEXT.get_rect()
        CONFIRM_CARAVAN_ONE_TEXTrect.left = 1010 * resX
        CONFIRM_CARAVAN_ONE_TEXTrect.top = 600 * resY

        CONFIRM_CARAVAN_TWO_TEXT = menuFont.render('Cost: ' + str(getCaravanData()[1]) + ' lumber, ' + str(getCaravanData()[2]) + ' oil', True, GOLD)
        CONFIRM_CARAVAN_TWO_TEXTrect = CONFIRM_CARAVAN_TWO_TEXT.get_rect()
        CONFIRM_CARAVAN_TWO_TEXTrect.left = 1010 * resX
        CONFIRM_CARAVAN_TWO_TEXTrect.top = 625 * resY
        
        windowSurface.blit(CONFIRM_CARAVAN_ONE_TEXT, CONFIRM_CARAVAN_ONE_TEXTrect)
        windowSurface.blit(CONFIRM_CARAVAN_TWO_TEXT, CONFIRM_CARAVAN_TWO_TEXTrect)
        windowSurface.blit(CONFIRM_CARAVAN_YES_TEXT, CONFIRM_CARAVAN_YES_TEXTrect)
        windowSurface.blit(CONFIRM_CARAVAN_NO_TEXT, CONFIRM_CARAVAN_NO_TEXTrect)
        if CONFIRM_CARAVAN_ERROR_TOGGLE == 1:
            windowSurface.blit(CONFIRM_CARAVAN_ERROR_TEXT, CONFIRM_CARAVAN_ERROR_TEXTrect)
    elif SEND_RESOURCES_TOGGLE_ONE == 1:
        windowSurface.blit(SEND_EXPLANATION_TEXT, SEND_EXPLANATION_TEXTrect)
        windowSurface.blit(SEND_GOLD_ONE_TEXT, SEND_GOLD_ONE_TEXTrect)
        windowSurface.blit(SEND_GOLD_TWO_TEXT, SEND_GOLD_TWO_TEXTrect)
    elif SEND_RESOURCES_TOGGLE_TWO == 1:
        windowSurface.blit(SEND_EXPLANATION_TEXT, SEND_EXPLANATION_TEXTrect)
        windowSurface.blit(SEND_LUMBER_ONE_TEXT, SEND_LUMBER_ONE_TEXTrect)
        windowSurface.blit(SEND_LUMBER_TWO_TEXT, SEND_LUMBER_TWO_TEXTrect)
    elif SEND_RESOURCES_TOGGLE_THREE == 1:
        windowSurface.blit(SEND_EXPLANATION_TEXT, SEND_EXPLANATION_TEXTrect)
        windowSurface.blit(SEND_OIL_ONE_TEXT, SEND_OIL_ONE_TEXTrect)
        windowSurface.blit(SEND_OIL_TWO_TEXT, SEND_OIL_TWO_TEXTrect)
    elif SEND_RESOURCES_TOGGLE_FOUR == 1:
        windowSurface.blit(SEND_RESOURCES_TEXT, SEND_RESOURCES_TEXTrect)
    elif BUILD_UNIT_TOGGLE == 1:
        for i in range(len(validBuildList)):
            windowSurface.blit(validBuildList[i].textrect, validBuildList[i].rect)
    elif CONFIRM_UNIT_TOGGLE == 1:
        windowSurface.blit(CONFIRM_UNIT_COST_TEXT, CONFIRM_UNIT_COST_TEXTrect)
        windowSurface.blit(CONFIRM_UNIT_TIER_TEXT, CONFIRM_UNIT_TIER_TEXTrect)
        windowSurface.blit(CONFIRM_UNIT_YES_TEXT, CONFIRM_UNIT_YES_TEXTrect)
        windowSurface.blit(CONFIRM_UNIT_NO_TEXT, CONFIRM_UNIT_NO_TEXTrect)
        if CONFIRM_UNIT_ERROR_TOGGLE == 1:
            windowSurface.blit(CONFIRM_UNIT_ERROR_TEXT, CONFIRM_UNIT_ERROR_TEXTrect)
        if CONFIRM_UNIT_FOOD_ERROR_TOGGLE == 1:
            windowSurface.blit(CONFIRM_UNIT_FOOD_ERROR_TEXT, CONFIRM_UNIT_FOOD_ERROR_TEXTrect)
        if CONFIRM_UNIT_TIER_ERROR_TOGGLE == 1:
            windowSurface.blit(CONFIRM_UNIT_TIER_ERROR_TEXT, CONFIRM_UNIT_TIER_ERROR_TEXTrect)
    elif BOARD_TRANSPORT_TOGGLE == 1:
        windowSurface.blit(BOARD_TRANSPORT_TEXT, BOARD_TRANSPORT_TEXTrect)
    elif RANGED_TOGGLE == 1:
        windowSurface.blit(RANGED_FIRE_TEXT, RANGED_FIRE_TEXTrect)
    elif checkSelected() == -1 and checkBaseSelected() == -1:
        BASIC_TWO_TEXT = mainFont.render('Food supply: ' + str(foodcost[0]) + '/' + str(foodcount[0]), True, GOLD)
        windowSurface.blit(BASIC_ONE_TEXT, BASIC_ONE_TEXTrect)
        windowSurface.blit(BASIC_TWO_TEXT, BASIC_TWO_TEXTrect)
        windowSurface.blit(MENU_ONE_TEXT, MENU_ONE_TEXTrect)
        windowSurface.blit(MENU_TWO_TEXT, MENU_TWO_TEXTrect)
        if spectator[0] == 1:
            windowSurface.blit(MENU_FOUR_SPECTATOR_TEXT, MENU_FOUR_SPECTATOR_TEXTrect)
        elif turnstatus==1:
            windowSurface.blit(MENU_FOUR_ALT_TEXT, MENU_FOUR_ALT_TEXTrect)
        else:
            windowSurface.blit(MENU_FOUR_TEXT, MENU_FOUR_TEXTrect)
        windowSurface.blit(MENU_FIVE_TEXT, MENU_FIVE_TEXTrect)
        #windowSurface.blit(MENU_SIX_TEXT, MENU_SIX_TEXTrect)
        windowSurface.blit(MENU_SEVEN_TEXT, MENU_SEVEN_TEXTrect)
        if CARAVAN_MAP_TOGGLE == 0:
            windowSurface.blit(MENU_SEVEN_OFF_TEXT, MENU_SEVEN_OFF_TEXTrect)
        if CARAVAN_MAP_TOGGLE == 1:
            windowSurface.blit(MENU_SEVEN_ON_TEXT, MENU_SEVEN_ON_TEXTrect)
    elif checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].hexnumber not in combathexes and spectator[0] == 0:
        windowSurface.blit(BASE_ONE_TEXT, BASE_ONE_TEXTrect)
        windowSurface.blit(BASE_TWO_TEXT, BASE_TWO_TEXTrect)
        windowSurface.blit(BASE_THREE_TEXT, BASE_THREE_TEXTrect)
        windowSurface.blit(BASE_FOUR_TEXT, BASE_FOUR_TEXTrect)
        windowSurface.blit(BASE_FIVE_TEXT, BASE_FIVE_TEXTrect)
        windowSurface.blit(BASE_SIX_TEXT, BASE_SIX_TEXTrect)
        windowSurface.blit(BASE_SEVEN_TEXT, BASE_SEVEN_TEXTrect)
        windowSurface.blit(BASE_EIGHT_TEXT, BASE_EIGHT_TEXTrect)
        windowSurface.blit(BASE_NINE_TEXT, BASE_NINE_TEXTrect)
        windowSurface.blit(BASE_TEN_TEXT, BASE_TEN_TEXTrect)
        windowSurface.blit(BASE_ELEVEN_TEXT, BASE_ELEVEN_TEXTrect)
        windowSurface.blit(BASE_TWELVE_TEXT, BASE_TWELVE_TEXTrect)
        windowSurface.blit(BASE_THIRTEEN_TEXT, BASE_THIRTEEN_TEXTrect) 
    elif checkSelected() != -1 and units[checkSelected()].faction == currentfaction and spectator[0] == 0:
        windowSurface.blit(UNIT_ONE_TEXT, UNIT_ONE_TEXTrect)
        windowSurface.blit(UNIT_TWO_TEXT, UNIT_TWO_TEXTrect)
        windowSurface.blit(UNIT_THREE_TEXT, UNIT_THREE_TEXTrect)
        windowSurface.blit(UNIT_FOUR_TEXT, UNIT_FOUR_TEXTrect)
        if units[checkSelected()].isLeader == 1:
            windowSurface.blit(UNIT_FIVE_TEXT, UNIT_FIVE_TEXTrect)
        if currentfaction==FACTION_DALARAN and (units[checkSelected()].unitType == "Mage" or units[checkSelected()].isLeader == 1):
            if dalarancombat[0] == 0:
                if units[checkSelected()].hexnumber not in combathexes:
                    windowSurface.blit(UNIT_SIX_TEXT, UNIT_SIX_TEXTrect)

    #redraw minimap
    windowSurface.blit(miniMapImage, miniMap)

    #redraw faction hex control
    for j in FactionBaseHexes:
        drawBaseFactionHexes(j, currentfaction)
    for i in FactionUnitHexes:
        drawUnitFactionHexes(i, currentfaction)

    #redraw minimap fog (if toggled)
    #if FOG_TOGGLE == 1:
    for i in range(len(fogOfWarList)):
        #fogMiniMap(fogOfWarList[i])
        windowSurface.blit(fogMiniImage, (miniMapX(fogOfWarList[i]) - 7, miniMapY(fogOfWarList[i]) - 9))

    #draw white square in miniMap
    pygame.draw.rect(windowSurface, WHITE, ((1005 - xcord/13) * resX, (0 - ycord/19.5) * resY, 105 * resX, 50 * resY), 2)

    #redraw menu lines
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (0 * resY)), ((1001 * resX), (1000 * resY)), 12)
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (379 * resY)), ((1400 * resX), (379 * resY)), 12)
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (590 * resY)), ((1400 * resX), (590 * resY)), 12)

    #if base selected, display base menu
    if checkBaseSelected() != -1:

        BASE_BACKGROUND_RECT = (pygame.Rect(int(1010 * resX), int(385 * resY), int(200 * resX), int(200 * resY)))
        BASE_PORTRAIT_RECT = (pygame.Rect(int(1010 * resX), int(390 * resY), int(200 * resX), int(200 * resY)))

        BASE_NAME_TEXT = menuFont.render(bases[checkBaseSelected()].name, True, GOLD)
        BASE_NAME_TEXTrect = BASE_NAME_TEXT.get_rect()
        BASE_NAME_TEXTrect.left = 1175 * resX
        BASE_NAME_TEXTrect.top = 390 * resY

        BASE_FACTION_TEXT = statsFont.render(factionString(bases[checkBaseSelected()].faction), True, GOLD)
        BASE_FACTION_TEXTrect = BASE_FACTION_TEXT.get_rect()
        BASE_FACTION_TEXTrect.left = 1175 * resX
        BASE_FACTION_TEXTrect.top = 415 * resY

        BASE_GOLD_TEXT = statsFont.render('Gold: ' + str(bases[checkBaseSelected()].goldleft), True, GOLD)
        BASE_GOLD_TEXTrect = BASE_GOLD_TEXT.get_rect()
        BASE_GOLD_TEXTrect.left = 1175 * resX
        BASE_GOLD_TEXTrect.top = 430 * resY

        BASE_LUMBER_TEXT = statsFont.render('Lumber: ' + str(bases[checkBaseSelected()].lumberleft), True, GOLD)
        BASE_LUMBER_TEXTrect = BASE_LUMBER_TEXT.get_rect()
        BASE_LUMBER_TEXTrect.left = 1175 * resX
        BASE_LUMBER_TEXTrect.top = 445 * resY

        BASE_OIL_TEXT = statsFont.render('Oil: ' + str(bases[checkBaseSelected()].oilleft), True, GOLD)
        BASE_OIL_TEXTrect = BASE_OIL_TEXT.get_rect()
        BASE_OIL_TEXTrect.left = 1175 * resX
        BASE_OIL_TEXTrect.top = 460 * resY

        BASE_ORDERS_TEXT = statsFont.render('Order #1:', True, GOLD)
        BASE_ORDERS_TEXTrect = BASE_ORDERS_TEXT.get_rect()
        BASE_ORDERS_TEXTrect.left = 1175 * resX
        BASE_ORDERS_TEXTrect.top = 490 * resY

        BASE_ORDERS_TWO_TEXT = statsFont.render(bases[checkBaseSelected()].first_orders, True, GOLD)
        BASE_ORDERS_TWO_TEXTrect = BASE_ORDERS_TWO_TEXT.get_rect()
        BASE_ORDERS_TWO_TEXTrect.left = 1175 * resX
        BASE_ORDERS_TWO_TEXTrect.top = 505 * resY

        BASE_ORDERS_THREE_TEXT = statsFont.render('Order #2:', True, GOLD)
        BASE_ORDERS_THREE_TEXTrect = BASE_ORDERS_THREE_TEXT.get_rect()
        BASE_ORDERS_THREE_TEXTrect.left = 1175 * resX
        BASE_ORDERS_THREE_TEXTrect.top = 520 * resY

        BASE_ORDERS_FOUR_TEXT = statsFont.render(bases[checkBaseSelected()].second_orders, True, GOLD)
        BASE_ORDERS_FOUR_TEXTrect = BASE_ORDERS_FOUR_TEXT.get_rect()
        BASE_ORDERS_FOUR_TEXTrect.left = 1175 * resX
        BASE_ORDERS_FOUR_TEXTrect.top = 535 * resY

        BASE_ORDERS_FIVE_TEXT = statsFont.render('Order #3:', True, GOLD)
        BASE_ORDERS_FIVE_TEXTrect = BASE_ORDERS_FIVE_TEXT.get_rect()
        BASE_ORDERS_FIVE_TEXTrect.left = 1175 * resX
        BASE_ORDERS_FIVE_TEXTrect.top = 550 * resY

        BASE_ORDERS_SIX_TEXT = statsFont.render(bases[checkBaseSelected()].third_orders, True, GOLD)
        BASE_ORDERS_SIX_TEXTrect = BASE_ORDERS_SIX_TEXT.get_rect()
        BASE_ORDERS_SIX_TEXTrect.left = 1175 * resX
        BASE_ORDERS_SIX_TEXTrect.top = 565 * resY

        windowSurface.blit(eval(factionString(bases[checkBaseSelected()].faction).replace(' ','')+'MenuBackground'), BASE_BACKGROUND_RECT)
        windowSurface.blit(eval(findBaseImage(checkBaseSelected())), BASE_PORTRAIT_RECT)
        windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
        windowSurface.blit(BASE_FACTION_TEXT, BASE_FACTION_TEXTrect)
        windowSurface.blit(BASE_GOLD_TEXT, BASE_GOLD_TEXTrect)
        windowSurface.blit(BASE_LUMBER_TEXT, BASE_LUMBER_TEXTrect)
        windowSurface.blit(BASE_OIL_TEXT, BASE_OIL_TEXTrect)
                           
        if bases[checkBaseSelected()].faction == currentfaction and spectator[0] == 0:
            if bases[checkBaseSelected()].hexnumber not in combathexes:
                windowSurface.blit(BASE_ORDERS_TEXT, BASE_ORDERS_TEXTrect)
                windowSurface.blit(BASE_ORDERS_TWO_TEXT, BASE_ORDERS_TWO_TEXTrect)
                windowSurface.blit(BASE_ORDERS_THREE_TEXT, BASE_ORDERS_THREE_TEXTrect)
                windowSurface.blit(BASE_ORDERS_FOUR_TEXT, BASE_ORDERS_FOUR_TEXTrect)
                windowSurface.blit(BASE_ORDERS_FIVE_TEXT, BASE_ORDERS_FIVE_TEXTrect)
                windowSurface.blit(BASE_ORDERS_SIX_TEXT, BASE_ORDERS_SIX_TEXTrect)

    #if unit selected, display stats
    if checkSelected() != -1:

        UNIT_BACKGROUND_RECT = pygame.Rect((1010 * resX), (385 * resY), (200 * resX), (200 * resY))
        UNIT_PORTRAIT_RECT = pygame.Rect((1010 * resX), (385 * resY), (200 * resX), (200 * resY))

        FACTION_TEXT = menuFont.render(factionString(units[checkSelected()].faction), True, GOLD)
        FACTION_TEXTrect = FACTION_TEXT.get_rect()
        FACTION_TEXTrect.left = 1175 * resX
        FACTION_TEXTrect.top = 388 * resY

        UNIT_TEXT = menuFont.render(units[checkSelected()].unitType, True, GOLD)
        UNIT_TEXTrect = UNIT_TEXT.get_rect()
        UNIT_TEXTrect.left = 1175 * resX
        UNIT_TEXTrect.top = 406 * resY

        TIER_TEXT = statsFont.render('Tier: ' + str(units[checkSelected()].tier), True, GOLD)
        TIER_TEXTrect = TIER_TEXT.get_rect()
        TIER_TEXTrect.left = 1175 * resX
        TIER_TEXTrect.top = 425 * resY

        HP_TEXT = statsFont.render('HP: ' + str(units[checkSelected()].HP) + ' / ' + str(units[checkSelected()].maxHP), True, GOLD)
        HP_TEXTrect = HP_TEXT.get_rect()
        HP_TEXTrect.left = 1175 * resX
        HP_TEXTrect.top =  437 * resY

        COMBAT_TEXT = statsFont.render('Combat: ' + str(units[checkSelected()].combat), True, GOLD)
        COMBAT_TEXTrect = COMBAT_TEXT.get_rect()
        COMBAT_TEXTrect.left = 1175 * resX
        COMBAT_TEXTrect.top = 449 * resY

        VISION_TEXT = statsFont.render('Vision: ' + str(units[checkSelected()].vision), True, GOLD)
        VISION_TEXTrect = VISION_TEXT.get_rect()
        VISION_TEXTrect.left = 1175 * resX
        VISION_TEXTrect.top = 461 * resY

        MOVES_TEXT = statsFont.render('Moves: ' + str(units[checkSelected()].movesleft), True, GOLD)
        MOVES_TEXTrect = MOVES_TEXT.get_rect()
        MOVES_TEXTrect.left = 1175 * resX
        MOVES_TEXTrect.top = 473 * resY

        CATEGORY_TEXT = statsFont.render('Category: ' + categoryToString(units[checkSelected()].category), True, GOLD)
        CATEGORY_TEXTrect = CATEGORY_TEXT.get_rect()
        CATEGORY_TEXTrect.left = 1175 * resX
        CATEGORY_TEXTrect.top = 485 * resY

        ORDERS_TEXT = statsFont.render('Orders:', True, GOLD)
        ORDERS_TEXTrect = ORDERS_TEXT.get_rect()
        ORDERS_TEXTrect.left = 1175 * resX
        ORDERS_TEXTrect.top = 545 * resY

        ORDERS_TWO_TEXT = statsFont.render(units[checkSelected()].orders, True, GOLD)
        ORDERS_TWO_TEXTrect = ORDERS_TWO_TEXT.get_rect()
        ORDERS_TWO_TEXTrect.left = 1175 * resX
        ORDERS_TWO_TEXTrect.top = 557 * resY

        LIGHT_ARMOR_TEXT = statsFont.render('Light Armor: ' + str(units[checkSelected()].lightarmor), True, GOLD)
        LIGHT_ARMOR_TEXTrect = LIGHT_ARMOR_TEXT.get_rect()
        LIGHT_ARMOR_TEXTrect.left = 1175 * resX
        LIGHT_ARMOR_TEXTrect.top = 497 * resY

        HEAVY_ARMOR_TEXT = statsFont.render('Heavy Armor: ' + str(units[checkSelected()].heavyarmor), True, GOLD)
        HEAVY_ARMOR_TEXTrect = HEAVY_ARMOR_TEXT.get_rect()
        HEAVY_ARMOR_TEXTrect.left = 1175 * resX
        HEAVY_ARMOR_TEXTrect.top = 509 * resY

        NATURAL_ARMOR_TEXT = statsFont.render('Natural Armor: ' + str(units[checkSelected()].naturalarmor), True, GOLD)
        NATURAL_ARMOR_TEXTrect = NATURAL_ARMOR_TEXT.get_rect()
        NATURAL_ARMOR_TEXTrect.left = 1175 * resX
        NATURAL_ARMOR_TEXTrect.top = 521 * resY

        windowSurface.blit(eval(factionString(units[checkSelected()].faction).replace(' ','')+'MenuBackground'), UNIT_BACKGROUND_RECT)
        windowSurface.blit(eval(replace_all(units[checkSelected()].unitType, replacedictionary)+'MenuImage'), UNIT_PORTRAIT_RECT)
        windowSurface.blit(FACTION_TEXT, FACTION_TEXTrect)
        windowSurface.blit(UNIT_TEXT, UNIT_TEXTrect)
        windowSurface.blit(TIER_TEXT, TIER_TEXTrect)
        windowSurface.blit(HP_TEXT, HP_TEXTrect)
        windowSurface.blit(COMBAT_TEXT, COMBAT_TEXTrect)
        windowSurface.blit(VISION_TEXT, VISION_TEXTrect)
        windowSurface.blit(MOVES_TEXT, MOVES_TEXTrect)
        windowSurface.blit(CATEGORY_TEXT, CATEGORY_TEXTrect)
        windowSurface.blit(LIGHT_ARMOR_TEXT, LIGHT_ARMOR_TEXTrect)
        windowSurface.blit(HEAVY_ARMOR_TEXT, HEAVY_ARMOR_TEXTrect)
        windowSurface.blit(NATURAL_ARMOR_TEXT, NATURAL_ARMOR_TEXTrect)
        if units[checkSelected()].faction == currentfaction and spectator[0] == 0:
            windowSurface.blit(ORDERS_TEXT, ORDERS_TEXTrect)
            windowSurface.blit(ORDERS_TWO_TEXT, ORDERS_TWO_TEXTrect)                        

        if (units[checkSelected()].unitType == "Alliance Transport" or units[checkSelected()].unitType == "Horde Transport") and isAllied(units[checkSelected()].faction, currentfaction) == 1: #can only select allied units
            TRANSPORT_ONE_TEXT = statsFont.render(getTransportString(checkSelected(), 1), True, GOLD)
            TRANSPORT_ONE_TEXTrect = TRANSPORT_ONE_TEXT.get_rect()
            TRANSPORT_ONE_TEXTrect.left = 1010 * resX
            TRANSPORT_ONE_TEXTrect.top = 545 * resY

            TRANSPORT_TWO_TEXT = statsFont.render(getTransportString(checkSelected(), 2), True, GOLD)
            TRANSPORT_TWO_TEXTrect = TRANSPORT_TWO_TEXT.get_rect()
            TRANSPORT_TWO_TEXTrect.left = 1010 * resX
            TRANSPORT_TWO_TEXTrect.top = 560 * resY

            #TRANSPORT_THREE_TEXT = statsFont.render(getTransportString(checkSelected(), 3), True, GOLD)
            #TRANSPORT_THREE_TEXTrect = TRANSPORT_THREE_TEXT.get_rect()
            #TRANSPORT_THREE_TEXTrect.left = 1010 * resX
            #TRANSPORT_THREE_TEXTrect.top = 570 * resY

            windowSurface.blit(TRANSPORT_ONE_TEXT, TRANSPORT_ONE_TEXTrect)
            windowSurface.blit(TRANSPORT_TWO_TEXT, TRANSPORT_TWO_TEXTrect)
            #windowSurface.blit(TRANSPORT_THREE_TEXT, TRANSPORT_THREE_TEXTrect)

################### LOAD/RUN GAME BEGINS HERE ###################

#initialize pygame
pygame.init()

#resolution test
resolution = pygame.display.Info()

#set up window variables
WINDOW_WIDTH = 0
WINDOW_LENGTH = 0
resX = (float(resolution.current_w) / float(1366))
resY = (float(resolution.current_h) / float(768))
miniX = (float(resolution.current_w) / float(1920))
miniY = (float(resolution.current_h) / float(1080))
flags = RESIZABLE | DOUBLEBUF

#set up window
# windowSurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_LENGTH), flags, 32)
windowSurface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('Tides of Darkness')

# request faction password, quit if invalid or not faction turn
loadcurrentinitiative()
loadsavefactions()
loadallturns()
loadgame()

currentfaction = allcurrentfaction[0]
inputbox.display_loading_status(windowSurface, 'Loading buildables...', -200)
loadbuildables()
inputbox.display_loading_status(windowSurface, 'Loading units...', -175)
loadsavedunits()
inputbox.display_loading_status(windowSurface, 'Loading map...', -150)
loadsavedmap()
inputbox.display_loading_status(windowSurface, 'Loading roads...', -125)
loadroads()
inputbox.display_loading_status(windowSurface, 'Loading bases...', -100)
loadsavedbases()
inputbox.display_loading_status(windowSurface, 'Loading vision...', -75)
loadcurrentvision()

#load current faction information (obsolete w/simultaneous turns)
# loadcurrentfaction()
# currentfaction = int(allcurrentfaction[0][0])

#load current turn information
inputbox.display_loading_status(windowSurface, 'Loading turn status...', -50)
loadturnstatus()
turnstatus = int(allcurrentturn[0][0])

inputbox.display_loading_status(windowSurface, 'Creating gameboard...', -25)
InitSetStuff()
reset()
hexsideControlSweep()
backupallunits=copy.deepcopy(allunits)
backupallhexes=copy.deepcopy(allhexes)

#generate combathexes list
for x in range(len(allhexes)):
    if len(buildfactionslist(buildcombatlist(x))) > 1:
        combathexes.append(x)
#set up dalaran in combat bool (for teleport)
if 401 in combathexes:
    dalarancombat[0] == 1
        
#set up colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
LIME = (0, 255, 0)
BLUE = (0, 0, 255)
CORNFLOWER_BLUE = (100, 149, 237)
FUCHSIA = (255, 0, 255)
GRAY = (128, 128, 128)
CHOCOLATE = (139, 69, 19)
GOLD = (255, 215, 0)
FOREST = (0, 130, 0)

TRANSPARENT = (128, 128, 128, 128)

#set up fonts
basicFont = establishFont(int(40*miniX))
mainFont = establishFont(int(28*miniX))
menuFont = establishFont(int(18*miniX))
statsFont = establishFont(int(14*miniX))

#allow for extended key pressdown
pygame.key.set_repeat(10, 10)

#set up initial map coordinates based on faction
init_coords = setMap()
xcord = init_coords[0]
ycord = init_coords[1]

#set up map images and stretch to window
mapImage = pygame.image.load('images/finalterrain5.jpg')
miniMap_Image = pygame.image.load('images/minimap.jpg')
mapStretchedImage = pygame.transform.scale(mapImage, (1000, 1000))
miniMapImage = pygame.transform.scale(miniMap_Image, (int(375 * resX), int(375 * resY)))

#set up menu image
rightMenu_Image = pygame.image.load('images/rightmenu.jpg')
rightMenuImage = pygame.transform.scale(rightMenu_Image, (int(500 * resX), int(1000 * resY)))

#set up fog hex image
fogImage = pygame.image.load('images/transparenthex.png')

#set up fog minimap hex image
fogMiniImage = pygame.transform.scale(fogImage, (int(24 * miniX), int(15 * miniY)))

#generate clickable hex rect surfaces
hexSurfaces = []
for i in range(1117):
    hexSurfaces.append(pygame.Rect(hexToX(i) - 60, hexToY(i) - 70, 130, 150))

#set up defaults
UNIT_WIDTH = 30
UNIT_LENGTH = 30
MENU_WIDTH = 125
MENU_LENGTH = 125
BASE_WIDTH = 120
BASE_LENGTH = 120
EXPANSION_WIDTH = 120
EXPANSION_LENGTH = 120
EXPANSION_X_OFFSET = 55
EXPANSION_Y_OFFSET = 55
BANNER_WIDTH = 60
BANNER_LENGTH = 90
RUNESTONE_WIDTH = 45
RUNESTONE_LENGTH = 60
POTENTIAL_GOLD = 0
POTENTIAL_LUMBER = 0
POTENTIAL_OIL = 0
RESOURCE_COUNTER = 0

#load unit images
AlexstraszaUnitImage = pygame.image.load('images/Units/alexstrasza.png')
AlexstraszaImage = pygame.transform.scale(AlexstraszaUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AlexstraszaMenuImage = pygame.transform.scale(AlexstraszaUnitImage, (MENU_WIDTH, MENU_LENGTH))
AlleriaWindrunnerUnitImage = pygame.image.load('images/Units/alleria.png')
AlleriaWindrunnerImage = pygame.transform.scale(AlleriaWindrunnerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AlleriaWindrunnerMenuImage = pygame.transform.scale(AlleriaWindrunnerUnitImage, (MENU_WIDTH, MENU_LENGTH))
AllianceTransportUnitImage = pygame.image.load('images/Units/alliancetransport.png')
AllianceTransportImage = pygame.transform.scale(AllianceTransportUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AllianceTransportMenuImage = pygame.transform.scale(AllianceTransportUnitImage, (MENU_WIDTH, MENU_LENGTH))
ArchmageAntonidasUnitImage = pygame.image.load('images/Units/antonidas.png')
ArchmageAntonidasImage = pygame.transform.scale(ArchmageAntonidasUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArchmageAntonidasMenuImage = pygame.transform.scale(ArchmageAntonidasUnitImage, (MENU_WIDTH, MENU_LENGTH))
ArcherUnitImage = pygame.image.load('images/Units/archer.png')
ArcherImage = pygame.transform.scale(ArcherUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArcherMenuImage = pygame.transform.scale(ArcherUnitImage, (MENU_WIDTH, MENU_LENGTH))
AxethrowerUnitImage = pygame.image.load('images/Units/axethrower.png')
AxethrowerImage = pygame.transform.scale(AxethrowerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AxethrowerMenuImage = pygame.transform.scale(AxethrowerUnitImage, (MENU_WIDTH, MENU_LENGTH))
BallistaUnitImage = pygame.image.load('images/Units/ballista.png')
BallistaImage = pygame.transform.scale(BallistaUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BallistaMenuImage = pygame.transform.scale(BallistaUnitImage, (MENU_WIDTH, MENU_LENGTH))
BattleshipUnitImage = pygame.image.load('images/Units/battleship.png')
BattleshipImage = pygame.transform.scale(BattleshipUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BattleshipMenuImage = pygame.transform.scale(BattleshipUnitImage, (MENU_WIDTH, MENU_LENGTH))
BerserkerUnitImage = pygame.image.load('images/Units/berserker.png')
BerserkerImage = pygame.transform.scale(BerserkerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BerserkerMenuImage = pygame.transform.scale(BerserkerUnitImage, (MENU_WIDTH, MENU_LENGTH))
CatapultUnitImage = pygame.image.load('images/Units/catapult.png')
CatapultImage = pygame.transform.scale(CatapultUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
CatapultMenuImage = pygame.transform.scale(CatapultUnitImage, (MENU_WIDTH, MENU_LENGTH))
ChogallUnitImage = pygame.image.load('images/Units/chogall.png')
ChogallImage = pygame.transform.scale(ChogallUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ChogallMenuImage = pygame.transform.scale(ChogallUnitImage, (MENU_WIDTH, MENU_LENGTH))
DariusCrowleyUnitImage = pygame.image.load('images/Units/crowley.png')
DariusCrowleyImage = pygame.transform.scale(DariusCrowleyUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DariusCrowleyMenuImage = pygame.transform.scale(DariusCrowleyUnitImage, (MENU_WIDTH, MENU_LENGTH))
DaelinProudmooreUnitImage = pygame.image.load('images/Units/daelinproudmoore.png')
DaelinProudmooreImage = pygame.transform.scale(DaelinProudmooreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DaelinProudmooreMenuImage = pygame.transform.scale(DaelinProudmooreUnitImage, (MENU_WIDTH, MENU_LENGTH))
DanathTrollbaneUnitImage = pygame.image.load('images/Units/danath.png')
DanathTrollbaneImage = pygame.transform.scale(DanathTrollbaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DanathTrollbaneMenuImage = pygame.transform.scale(DanathTrollbaneUnitImage, (MENU_WIDTH, MENU_LENGTH))
DeathKnightUnitImage = pygame.image.load('images/Units/deathknight.png')
DeathKnightImage = pygame.transform.scale(DeathKnightUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DeathKnightMenuImage = pygame.transform.scale(DeathKnightUnitImage, (MENU_WIDTH, MENU_LENGTH))
DemonUnitImage = pygame.image.load('images/Units/demon.png')
DemonImage = pygame.transform.scale(DemonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DemonMenuImage = pygame.transform.scale(DemonUnitImage, (MENU_WIDTH, MENU_LENGTH))
DerekProudmooreUnitImage = pygame.image.load('images/Units/derekproudmoore.png')
DerekProudmooreImage = pygame.transform.scale(DerekProudmooreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DerekProudmooreMenuImage = pygame.transform.scale(DerekProudmooreUnitImage, (MENU_WIDTH, MENU_LENGTH))
DestroyerUnitImage = pygame.image.load('images/Units/destroyer.png')
DestroyerImage = pygame.transform.scale(DestroyerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DestroyerMenuImage = pygame.transform.scale(DestroyerUnitImage, (MENU_WIDTH, MENU_LENGTH))
OrgrimDoomhammerUnitImage = pygame.image.load('images/Units/doomhammer.png')
OrgrimDoomhammerImage = pygame.transform.scale(OrgrimDoomhammerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
OrgrimDoomhammerMenuImage = pygame.transform.scale(OrgrimDoomhammerUnitImage, (MENU_WIDTH, MENU_LENGTH))
DragonUnitImage = pygame.image.load('images/Units/dragon.png')
DragonImage = pygame.transform.scale(DragonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonMenuImage = pygame.transform.scale(DragonUnitImage, (MENU_WIDTH, MENU_LENGTH))
DrektharUnitImage = pygame.image.load('images/Units/drekthar.png')
DrektharImage = pygame.transform.scale(DrektharUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DrektharMenuImage = pygame.transform.scale(DrektharUnitImage, (MENU_WIDTH, MENU_LENGTH))
DwarfUnitImage = pygame.image.load('images/Units/dwarf.png')
DwarfImage = pygame.transform.scale(DwarfUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DwarfMenuImage = pygame.transform.scale(DwarfUnitImage, (MENU_WIDTH, MENU_LENGTH))
WildhammerShamanUnitImage = pygame.image.load('images/Units/dwarfshaman.png')
WildhammerShamanImage = pygame.transform.scale(WildhammerShamanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WildhammerShamanMenuImage = pygame.transform.scale(WildhammerShamanUnitImage, (MENU_WIDTH, MENU_LENGTH))
ElementalUnitImage = pygame.image.load('images/Units/elemental.png')
ElementalImage = pygame.transform.scale(ElementalUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ElementalMenuImage = pygame.transform.scale(ElementalUnitImage, (MENU_WIDTH, MENU_LENGTH))
MountaineerUnitImage = pygame.image.load('images/Units/mountaineer.png')
MountaineerImage = pygame.transform.scale(MountaineerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MountaineerMenuImage = pygame.transform.scale(MountaineerUnitImage, (MENU_WIDTH, MENU_LENGTH))
LordFalconcrestUnitImage = pygame.image.load('images/Units/falconcrest.png')
LordFalconcrestImage = pygame.transform.scale(LordFalconcrestUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
LordFalconcrestMenuImage = pygame.transform.scale(LordFalconcrestUnitImage, (MENU_WIDTH, MENU_LENGTH))
FootmanUnitImage = pygame.image.load('images/Units/footman.png')
FootmanImage = pygame.transform.scale(FootmanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
FootmanMenuImage = pygame.transform.scale(FootmanUnitImage, (MENU_WIDTH, MENU_LENGTH))
GennGreymaneUnitImage = pygame.image.load('images/Units/greymane.png')
GennGreymaneImage = pygame.transform.scale(GennGreymaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GennGreymaneMenuImage = pygame.transform.scale(GennGreymaneUnitImage, (MENU_WIDTH, MENU_LENGTH))
GruntUnitImage = pygame.image.load('images/Units/grunt.png')
GruntImage = pygame.transform.scale(GruntUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GruntMenuImage = pygame.transform.scale(GruntUnitImage, (MENU_WIDTH, MENU_LENGTH))
GryphonUnitImage = pygame.image.load('images/Units/gryphon.png')
GryphonImage = pygame.transform.scale(GryphonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GryphonMenuImage = pygame.transform.scale(GryphonUnitImage, (MENU_WIDTH, MENU_LENGTH))
GuldantheDeceiverUnitImage = pygame.image.load('images/Units/guldan.png')
GuldantheDeceiverImage = pygame.transform.scale(GuldantheDeceiverUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GuldantheDeceiverMenuImage = pygame.transform.scale(GuldantheDeceiverUnitImage, (MENU_WIDTH, MENU_LENGTH))
DrakthulUnitImage = pygame.image.load('images/Units/drakthul.png')
DrakthulImage = pygame.transform.scale(DrakthulUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DrakthulMenuImage = pygame.transform.scale(DrakthulUnitImage, (MENU_WIDTH, MENU_LENGTH))
GorfrunchSmashbladeUnitImage = pygame.image.load('images/Units/gorfrunch.png')
GorfrunchSmashbladeImage = pygame.transform.scale(GorfrunchSmashbladeUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GorfrunchSmashbladeMenuImage = pygame.transform.scale(GorfrunchSmashbladeUnitImage, (MENU_WIDTH, MENU_LENGTH))
HordeTransportUnitImage = pygame.image.load('images/Units/hordetransport.png')
HordeTransportImage = pygame.transform.scale(HordeTransportUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
HordeTransportMenuImage = pygame.transform.scale(HordeTransportUnitImage, (MENU_WIDTH, MENU_LENGTH))
JuggernautUnitImage = pygame.image.load('images/Units/juggernaut.png')
JuggernautImage = pygame.transform.scale(JuggernautUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
JuggernautMenuImage = pygame.transform.scale(JuggernautUnitImage, (MENU_WIDTH, MENU_LENGTH))
ArchmageKhadgarUnitImage = pygame.image.load('images/Units/khadgar.png')
ArchmageKhadgarImage = pygame.transform.scale(ArchmageKhadgarUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArchmageKhadgarMenuImage = pygame.transform.scale(ArchmageKhadgarUnitImage, (MENU_WIDTH, MENU_LENGTH))
KilroggDeadeyeUnitImage = pygame.image.load('images/Units/kilroggdeadeye.png')
KilroggDeadeyeImage = pygame.transform.scale(KilroggDeadeyeUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KilroggDeadeyeMenuImage = pygame.transform.scale(KilroggDeadeyeUnitImage, (MENU_WIDTH, MENU_LENGTH))
KnightUnitImage = pygame.image.load('images/Units/knight.png')
KnightImage = pygame.transform.scale(KnightUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KnightMenuImage = pygame.transform.scale(KnightUnitImage, (MENU_WIDTH, MENU_LENGTH))
KurdranWildhammerUnitImage = pygame.image.load('images/Units/kurdran.png')
KurdranWildhammerImage = pygame.transform.scale(KurdranWildhammerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KurdranWildhammerMenuImage = pygame.transform.scale(KurdranWildhammerUnitImage, (MENU_WIDTH, MENU_LENGTH))
AnduinLotharUnitImage = pygame.image.load('images/Units/lothar.png')
AnduinLotharImage = pygame.transform.scale(AnduinLotharUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AnduinLotharMenuImage = pygame.transform.scale(AnduinLotharUnitImage, (MENU_WIDTH, MENU_LENGTH))
MageUnitImage = pygame.image.load('images/Units/mage.png')
MageImage = pygame.transform.scale(MageUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MageMenuImage = pygame.transform.scale(MageUnitImage, (MENU_WIDTH, MENU_LENGTH))
MagniBronzebeardUnitImage = pygame.image.load('images/Units/magni.png')
MagniBronzebeardImage = pygame.transform.scale(MagniBronzebeardUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MagniBronzebeardMenuImage = pygame.transform.scale(MagniBronzebeardUnitImage, (MENU_WIDTH, MENU_LENGTH))
MaimBlackhandUnitImage = pygame.image.load('images/Units/maimblackhand.png')
MaimBlackhandImage = pygame.transform.scale(MaimBlackhandUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MaimBlackhandMenuImage = pygame.transform.scale(MaimBlackhandUnitImage, (MENU_WIDTH, MENU_LENGTH))
MazDrachripUnitImage = pygame.image.load('images/Units/maz.png')
MazDrachripImage = pygame.transform.scale(MazDrachripUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MazDrachripMenuImage = pygame.transform.scale(MazDrachripUnitImage, (MENU_WIDTH, MENU_LENGTH))
MuradinBronzebeardUnitImage = pygame.image.load('images/Units/muradin.png')
MuradinBronzebeardImage = pygame.transform.scale(MuradinBronzebeardUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MuradinBronzebeardMenuImage = pygame.transform.scale(MuradinBronzebeardUnitImage, (MENU_WIDTH, MENU_LENGTH))
NazgrelUnitImage = pygame.image.load('images/Units/nazgrel.png')
NazgrelImage = pygame.transform.scale(NazgrelUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
NazgrelMenuImage = pygame.transform.scale(NazgrelUnitImage, (MENU_WIDTH, MENU_LENGTH))
OgreUnitImage = pygame.image.load('images/Units/ogre.png')
OgreImage = pygame.transform.scale(OgreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
OgreMenuImage = pygame.transform.scale(OgreUnitImage, (MENU_WIDTH, MENU_LENGTH))
AidenPerenoldeUnitImage = pygame.image.load('images/Units/perenolde.png')
AidenPerenoldeImage = pygame.transform.scale(AidenPerenoldeUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AidenPerenoldeMenuImage = pygame.transform.scale(AidenPerenoldeUnitImage, (MENU_WIDTH, MENU_LENGTH))
RaiderUnitImage = pygame.image.load('images/Units/raider.png')
RaiderImage = pygame.transform.scale(RaiderUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
RaiderMenuImage = pygame.transform.scale(RaiderUnitImage, (MENU_WIDTH, MENU_LENGTH))
RendBlackhandUnitImage = pygame.image.load('images/Units/rendblackhand.png')
RendBlackhandImage = pygame.transform.scale(RendBlackhandUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
RendBlackhandMenuImage = pygame.transform.scale(RendBlackhandUnitImage, (MENU_WIDTH, MENU_LENGTH))
VarokSaurfangUnitImage = pygame.image.load('images/Units/saurfang.png')
VarokSaurfangImage = pygame.transform.scale(VarokSaurfangUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
VarokSaurfangMenuImage = pygame.transform.scale(VarokSaurfangUnitImage, (MENU_WIDTH, MENU_LENGTH))
ShamanUnitImage = pygame.image.load('images/Units/shaman.png')
ShamanImage = pygame.transform.scale(ShamanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ShamanMenuImage = pygame.transform.scale(ShamanUnitImage, (MENU_WIDTH, MENU_LENGTH))
SkeletonUnitImage = pygame.image.load('images/Units/skeleton.png')
SkeletonImage = pygame.transform.scale(SkeletonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SkeletonMenuImage = pygame.transform.scale(SkeletonUnitImage, (MENU_WIDTH, MENU_LENGTH))
SubmarineUnitImage = pygame.image.load('images/Units/submarine.png')
SubmarineImage = pygame.transform.scale(SubmarineUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SubmarineMenuImage = pygame.transform.scale(SubmarineUnitImage, (MENU_WIDTH, MENU_LENGTH))
SwordsmanUnitImage = pygame.image.load('images/Units/swordsman.png')
SwordsmanImage = pygame.transform.scale(SwordsmanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SwordsmanMenuImage = pygame.transform.scale(SwordsmanUnitImage, (MENU_WIDTH, MENU_LENGTH))
SylvanasWindrunnerUnitImage = pygame.image.load('images/Units/sylvanas.png')
SylvanasWindrunnerImage = pygame.transform.scale(SylvanasWindrunnerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SylvanasWindrunnerMenuImage = pygame.transform.scale(SylvanasWindrunnerUnitImage, (MENU_WIDTH, MENU_LENGTH))
TerenasMenethilUnitImage = pygame.image.load('images/Units/terenas.png')
TerenasMenethilImage = pygame.transform.scale(TerenasMenethilUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TerenasMenethilMenuImage = pygame.transform.scale(TerenasMenethilUnitImage, (MENU_WIDTH, MENU_LENGTH))
DagranThaurissanUnitImage = pygame.image.load('images/Units/thaurissan.png')
DagranThaurissanImage = pygame.transform.scale(DagranThaurissanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DagranThaurissanMenuImage = pygame.transform.scale(DagranThaurissanUnitImage, (MENU_WIDTH, MENU_LENGTH))
ThorasTrollbaneUnitImage = pygame.image.load('images/Units/thoras.png')
ThorasTrollbaneImage = pygame.transform.scale(ThorasTrollbaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ThorasTrollbaneMenuImage = pygame.transform.scale(ThorasTrollbaneUnitImage, (MENU_WIDTH, MENU_LENGTH))
TuralyonUnitImage = pygame.image.load('images/Units/turalyon.png')
TuralyonImage = pygame.transform.scale(TuralyonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TuralyonMenuImage = pygame.transform.scale(TuralyonUnitImage, (MENU_WIDTH, MENU_LENGTH))
TurtleUnitImage = pygame.image.load('images/Units/turtle.png')
TurtleImage = pygame.transform.scale(TurtleUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TurtleMenuImage = pygame.transform.scale(TurtleUnitImage, (MENU_WIDTH, MENU_LENGTH))
UthertheLightbringerUnitImage = pygame.image.load('images/Units/uther.png')
UthertheLightbringerImage = pygame.transform.scale(UthertheLightbringerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
UthertheLightbringerMenuImage = pygame.transform.scale(UthertheLightbringerUnitImage, (MENU_WIDTH, MENU_LENGTH))
WarlockUnitImage = pygame.image.load('images/Units/warlock.png')
WarlockImage = pygame.transform.scale(WarlockUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WarlockMenuImage = pygame.transform.scale(WarlockUnitImage, (MENU_WIDTH, MENU_LENGTH))
WaveRiderUnitImage = pygame.image.load('images/Units/waverider.png')
WaveRiderImage = pygame.transform.scale(WaveRiderUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WaveRiderMenuImage = pygame.transform.scale(WaveRiderUnitImage, (MENU_WIDTH, MENU_LENGTH))
ZuljinUnitImage = pygame.image.load('images/Units/zuljin.png')
ZuljinImage = pygame.transform.scale(ZuljinUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ZuljinMenuImage = pygame.transform.scale(ZuljinUnitImage, (MENU_WIDTH, MENU_LENGTH))
ZuluhedtheWhackedUnitImage = pygame.image.load('images/Units/zuluhed.png')
ZuluhedtheWhackedImage = pygame.transform.scale(ZuluhedtheWhackedUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ZuluhedtheWhackedMenuImage = pygame.transform.scale(ZuluhedtheWhackedUnitImage, (MENU_WIDTH, MENU_LENGTH))

#load faction backgrounds
AeriePeakBackgroundImage = pygame.image.load('images/Backgrounds/aeriepeakBackground.png')
AeriePeakBackground = pygame.transform.scale(AeriePeakBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AeriePeakMenuBackground = pygame.transform.scale(AeriePeakBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
AlteracBackgroundImage = pygame.image.load('images/Backgrounds/alteracBackground.png')
AlteracBackground = pygame.transform.scale(AlteracBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AlteracMenuBackground = pygame.transform.scale(AlteracBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
AmaniBackgroundImage = pygame.image.load('images/Backgrounds/amaniBackground.png')
AmaniBackground = pygame.transform.scale(AmaniBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AmaniMenuBackground = pygame.transform.scale(AmaniBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
AzerothBackgroundImage = pygame.image.load('images/Backgrounds/azerothBackground.png')
AzerothBackground = pygame.transform.scale(AzerothBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AzerothMenuBackground = pygame.transform.scale(AzerothBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
BlackrockBackgroundImage = pygame.image.load('images/Backgrounds/blackrockBackground.png')
BlackrockBackground = pygame.transform.scale(BlackrockBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BlackrockMenuBackground = pygame.transform.scale(BlackrockBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
BlackToothGrinBackgroundImage = pygame.image.load('images/Backgrounds/blacktoothgrinBackground.png')
BlackToothGrinBackground = pygame.transform.scale(BlackToothGrinBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BlackToothGrinMenuBackground = pygame.transform.scale(BlackToothGrinBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
BleedingHollowBackgroundImage = pygame.image.load('images/Backgrounds/bleedinghollowBackground.png')
BleedingHollowBackground = pygame.transform.scale(BleedingHollowBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BleedingHollowMenuBackground = pygame.transform.scale(BleedingHollowBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
BurningBladeBackgroundImage = pygame.image.load('images/Backgrounds/burningbladeBackground.png')
BurningBladeBackground = pygame.transform.scale(BurningBladeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BurningBladeMenuBackground = pygame.transform.scale(BurningBladeBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DalaranBackgroundImage = pygame.image.load('images/Backgrounds/dalaranBackground.png')
DalaranBackground = pygame.transform.scale(DalaranBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DalaranMenuBackground = pygame.transform.scale(DalaranBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DalaranRebelBackgroundImage = pygame.image.load('images/Backgrounds/dalaranrebelBackground.png')
DalaranRebelBackground = pygame.transform.scale(DalaranRebelBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DalaranRebelMenuBackground = pygame.transform.scale(DalaranRebelBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DarkIronBackgroundImage = pygame.image.load('images/Backgrounds/darkironBackground.png')
DarkIronBackground = pygame.transform.scale(DarkIronBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DarkIronMenuBackground = pygame.transform.scale(DarkIronBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DemonBackgroundImage = pygame.image.load('images/Backgrounds/demonBackground.png')
DemonBackground = pygame.transform.scale(DemonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DemonMenuBackground = pygame.transform.scale(DemonBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DragonBackgroundImage = pygame.image.load('images/Backgrounds/dragonBackground.png')
DragonBackground = pygame.transform.scale(DragonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonMenuBackground = pygame.transform.scale(DragonBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
DragonmawBackgroundImage = pygame.image.load('images/Backgrounds/dragonmawBackground.png')
DragonmawBackground = pygame.transform.scale(DragonmawBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonmawMenuBackground = pygame.transform.scale(DragonmawBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
FiretreeBackgroundImage = pygame.image.load('images/Backgrounds/firetreeBackground.png')
FiretreeBackground = pygame.transform.scale(FiretreeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
FiretreeMenuBackground = pygame.transform.scale(FiretreeBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
FrostwolfBackgroundImage = pygame.image.load('images/Backgrounds/frostwolfBackground.png')
FrostwolfBackground = pygame.transform.scale(FrostwolfBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
FrostwolfMenuBackground = pygame.transform.scale(FrostwolfBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
GilneasBackgroundImage = pygame.image.load('images/Backgrounds/gilneasBackground.png')
GilneasBackground = pygame.transform.scale(GilneasBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
GilneasMenuBackground = pygame.transform.scale(GilneasBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
GilneasRebelBackgroundImage = pygame.image.load('images/Backgrounds/gilneasrebelBackground.png')
GilneasRebelBackground = pygame.transform.scale(GilneasRebelBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
GilneasRebelMenuBackground = pygame.transform.scale(GilneasRebelBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
IronforgeBackgroundImage = pygame.image.load('images/Backgrounds/ironforgeBackground.png')
IronforgeBackground = pygame.transform.scale(IronforgeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
IronforgeMenuBackground = pygame.transform.scale(IronforgeBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
KulTirasBackgroundImage = pygame.image.load('images/Backgrounds/kultirasBackground.png')
KulTirasBackground = pygame.transform.scale(KulTirasBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
KulTirasMenuBackground = pygame.transform.scale(KulTirasBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
LordaeronBackgroundImage = pygame.image.load('images/Backgrounds/lordaeronBackground.png')
LordaeronBackground = pygame.transform.scale(LordaeronBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
LordaeronMenuBackground = pygame.transform.scale(LordaeronBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
MossflayerBackgroundImage = pygame.image.load('images/Backgrounds/mossflayerBackground.png')
MossflayerBackground = pygame.transform.scale(MossflayerBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
MossflayerMenuBackground = pygame.transform.scale(MossflayerBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
RevantuskBackgroundImage = pygame.image.load('images/Backgrounds/revantuskBackground.png')
RevantuskBackground = pygame.transform.scale(RevantuskBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
RevantuskMenuBackground = pygame.transform.scale(RevantuskBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
ShadowglenBackgroundImage = pygame.image.load('images/Backgrounds/shadowglenBackground.png')
ShadowglenBackground = pygame.transform.scale(ShadowglenBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
ShadowglenMenuBackground = pygame.transform.scale(ShadowglenBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
ShadowpineBackgroundImage = pygame.image.load('images/Backgrounds/shadowpineBackground.png')
ShadowpineBackground = pygame.transform.scale(ShadowpineBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
ShadowpineMenuBackground = pygame.transform.scale(ShadowpineBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
SilvermoonBackgroundImage = pygame.image.load('images/Backgrounds/silvermoonBackground.png')
SilvermoonBackground = pygame.transform.scale(SilvermoonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
SilvermoonMenuBackground = pygame.transform.scale(SilvermoonBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
SmolderthornBackgroundImage = pygame.image.load('images/Backgrounds/smolderthornBackground.png')
SmolderthornBackground = pygame.transform.scale(SmolderthornBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
SmolderthornMenuBackground = pygame.transform.scale(SmolderthornBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
StormreaverBackgroundImage = pygame.image.load('images/Backgrounds/stormreaversBackground.png')
StormreaverBackground = pygame.transform.scale(StormreaverBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
StormreaverMenuBackground = pygame.transform.scale(StormreaverBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
StromgardeBackgroundImage = pygame.image.load('images/Backgrounds/stromgardeBackground.png')
StromgardeBackground = pygame.transform.scale(StromgardeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
StromgardeMenuBackground = pygame.transform.scale(StromgardeBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
TwilightHammerBackgroundImage = pygame.image.load('images/Backgrounds/twilightshammerBackground.png')
TwilightHammerBackground = pygame.transform.scale(TwilightHammerBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
TwilightHammerMenuBackground = pygame.transform.scale(TwilightHammerBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
VilebranchBackgroundImage = pygame.image.load('images/Backgrounds/vilebranchBackground.png')
VilebranchBackground = pygame.transform.scale(VilebranchBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
VilebranchMenuBackground = pygame.transform.scale(VilebranchBackgroundImage, (MENU_WIDTH, MENU_LENGTH))
WitherbarkBackgroundImage = pygame.image.load('images/Backgrounds/witherbarkBackground.png')
WitherbarkBackground = pygame.transform.scale(WitherbarkBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
WitherbarkMenuBackground = pygame.transform.scale(WitherbarkBackgroundImage, (MENU_WIDTH, MENU_LENGTH))

#load base images
AllianceTownHallOrigImage = pygame.image.load('images/Buildings/townhall.png')
AllianceTownHallImage = pygame.transform.scale(AllianceTownHallOrigImage, (BASE_WIDTH, BASE_LENGTH))
AllianceTownHallMenuImage = pygame.transform.scale(AllianceTownHallOrigImage, (MENU_WIDTH, MENU_LENGTH))
AllianceKeepOrigImage = pygame.image.load('images/Buildings/keep.png')
AllianceKeepImage = pygame.transform.scale(AllianceKeepOrigImage, (BASE_WIDTH, BASE_LENGTH))
AllianceKeepMenuImage = pygame.transform.scale(AllianceKeepOrigImage, (MENU_WIDTH, MENU_LENGTH))
AllianceCastleOrigImage = pygame.image.load('images/Buildings/castle.png')
AllianceCastleImage = pygame.transform.scale(AllianceCastleOrigImage, (BASE_WIDTH, BASE_LENGTH))
AllianceCastleMenuImage = pygame.transform.scale(AllianceCastleOrigImage, (MENU_WIDTH, MENU_LENGTH))
HordeGreatHallOrigImage = pygame.image.load('images/Buildings/greathall.png')
HordeGreatHallImage = pygame.transform.scale(HordeGreatHallOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeGreatHallMenuImage = pygame.transform.scale(HordeGreatHallOrigImage, (MENU_WIDTH, MENU_LENGTH))
HordeStrongholdOrigImage = pygame.image.load('images/Buildings/stronghold.png')
HordeStrongholdImage = pygame.transform.scale(HordeStrongholdOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeStrongholdMenuImage = pygame.transform.scale(HordeStrongholdOrigImage, (MENU_WIDTH, MENU_LENGTH))
HordeFortressOrigImage = pygame.image.load('images/Buildings/fortress.png')
HordeFortressImage = pygame.transform.scale(HordeFortressOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeFortressMenuImage = pygame.transform.scale(HordeFortressOrigImage, (MENU_WIDTH, MENU_LENGTH))

#load expansion images
AllianceFarmOrigImage = pygame.image.load('images/Buildings/alliancefarm.png')
AllianceFarmImage = pygame.transform.scale(AllianceFarmOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))
AllianceMillOrigImage = pygame.image.load('images/Buildings/alliancemill.png')
AllianceMillImage = pygame.transform.scale(AllianceMillOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))
AllianceRigOrigImage = pygame.image.load('images/Buildings/alliancerig.png')
AllianceRigImage = pygame.transform.scale(AllianceRigOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))
HordeFarmOrigImage = pygame.image.load('images/Buildings/hordefarm.png')
HordeFarmImage = pygame.transform.scale(HordeFarmOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))
HordeMillOrigImage = pygame.image.load('images/Buildings/hordemill.png')
HordeMillImage = pygame.transform.scale(HordeMillOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))
HordeRigOrigImage = pygame.image.load('images/Buildings/horderig.png')
HordeRigImage = pygame.transform.scale(HordeRigOrigImage, (EXPANSION_WIDTH, EXPANSION_LENGTH))

#load special images
RunestoneOrigImage = pygame.image.load('images/Buildings/runestone.png')
RunestoneImage = pygame.transform.scale(RunestoneOrigImage, (RUNESTONE_WIDTH, RUNESTONE_LENGTH))
DarkPortalOrigImage = pygame.image.load('images/Buildings/darkportal.png')
DarkPortalImage = pygame.transform.scale(DarkPortalOrigImage, (BASE_WIDTH, BASE_LENGTH))
DragonRoostOrigImage = pygame.image.load('images/Buildings/roost.png')
DragonRoostImage = pygame.transform.scale(DragonRoostOrigImage, (BASE_WIDTH, BASE_LENGTH))
RuinsOrigImage = pygame.image.load('images/Buildings/ruins.png')
RuinsImage = pygame.transform.scale(RuinsOrigImage, (BASE_WIDTH, BASE_LENGTH))

#load banners
AeriePeakOrigBanner = pygame.image.load('images/Banners/aeriepeak.png')
AeriePeakBanner = pygame.transform.scale(AeriePeakOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
AlteracOrigBanner = pygame.image.load('images/Banners/alterac.png')
AlteracBanner = pygame.transform.scale(AlteracOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
AmaniOrigBanner = pygame.image.load('images/Banners/amani.png')
AmaniBanner = pygame.transform.scale(AmaniOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
AzerothOrigBanner = pygame.image.load('images/Banners/azeroth.png')
AzerothBanner = pygame.transform.scale(AzerothOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
BlackrockOrigBanner = pygame.image.load('images/Banners/blackrock.png')
BlackrockBanner = pygame.transform.scale(BlackrockOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
BlackToothGrinOrigBanner = pygame.image.load('images/Banners/blacktoothgrin.png')
BlackToothGrinBanner = pygame.transform.scale(BlackToothGrinOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
BleedingHollowOrigBanner = pygame.image.load('images/Banners/bleedinghollow.png')
BleedingHollowBanner = pygame.transform.scale(BleedingHollowOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
BurningBladeOrigBanner = pygame.image.load('images/Banners/burningblade.png')
BurningBladeBanner = pygame.transform.scale(BurningBladeOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
DalaranOrigBanner = pygame.image.load('images/Banners/dalaran.png')
DalaranBanner = pygame.transform.scale(DalaranOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
DalaranRebelOrigBanner = pygame.image.load('images/Banners/dalaranrebel.png')
DalaranRebelBanner = pygame.transform.scale(DalaranRebelOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
DragonmawOrigBanner = pygame.image.load('images/Banners/dragonmaw.png')
DragonmawBanner = pygame.transform.scale(DragonmawOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
FiretreeOrigBanner = pygame.image.load('images/Banners/firetree.png')
FiretreeBanner = pygame.transform.scale(FiretreeOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
FrostwolfOrigBanner = pygame.image.load('images/Banners/frostwolf.png')
FrostwolfBanner = pygame.transform.scale(FrostwolfOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
GilneasOrigBanner = pygame.image.load('images/Banners/gilneas.png')
GilneasBanner = pygame.transform.scale(GilneasOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
GilneasRebelOrigBanner = pygame.image.load('images/Banners/gilneasrebel.png')
GilneasRebelBanner = pygame.transform.scale(GilneasRebelOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
IronforgeOrigBanner = pygame.image.load('images/Banners/ironforge.png')
IronforgeBanner = pygame.transform.scale(IronforgeOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
KulTirasOrigBanner = pygame.image.load('images/Banners/kultiras.png')
KulTirasBanner = pygame.transform.scale(KulTirasOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
LordaeronOrigBanner = pygame.image.load('images/Banners/lordaeron.png')
LordaeronBanner = pygame.transform.scale(LordaeronOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
MossflayerOrigBanner = pygame.image.load('images/Banners/mossflayer.png')
MossflayerBanner = pygame.transform.scale(MossflayerOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
RevantuskOrigBanner = pygame.image.load('images/Banners/revantusk.png')
RevantuskBanner = pygame.transform.scale(RevantuskOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
ShadowglenOrigBanner = pygame.image.load('images/Banners/shadowglen.png')
ShadowglenBanner = pygame.transform.scale(ShadowglenOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
ShadowpineOrigBanner = pygame.image.load('images/Banners/shadowpine.png')
ShadowpineBanner = pygame.transform.scale(ShadowpineOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
SilvermoonOrigBanner = pygame.image.load('images/Banners/silvermoon.png')
SilvermoonBanner = pygame.transform.scale(SilvermoonOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
SmolderthornOrigBanner = pygame.image.load('images/Banners/smolderthorn.png')
SmolderthornBanner = pygame.transform.scale(SmolderthornOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
StormreaverOrigBanner = pygame.image.load('images/Banners/stormreaver.png')
StormreaverBanner = pygame.transform.scale(StormreaverOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
StromgardeOrigBanner = pygame.image.load('images/Banners/stromgarde.png')
StromgardeBanner = pygame.transform.scale(StromgardeOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
TwilightHammerOrigBanner = pygame.image.load('images/Banners/twilightshammer.png')
TwilightHammerBanner = pygame.transform.scale(TwilightHammerOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
VilebranchOrigBanner = pygame.image.load('images/Banners/vilebranch.png')
VilebranchBanner = pygame.transform.scale(VilebranchOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))
WitherbarkOrigBanner = pygame.image.load('images/Banners/witherbark.png')
WitherbarkBanner = pygame.transform.scale(WitherbarkOrigBanner, (BANNER_WIDTH, BANNER_LENGTH))

#draw map to window
windowSurface.blit(mapImage, (0, 0))
pygame.display.Info

#set up mapUnit class
class mapUnit:
    def __init__(self, hexnumber, tier, overallfaction, capacity, domain, category, movesleft, movesmax, vision, combat, HP, maxHP, faction, unitType, area, selected, movesMade, destination, orders, alive, transportOne, transportTwo, isLeader, xshift, yshift, lightarmor, heavyarmor, naturalarmor):
        self.hexnumber = hexnumber
        self.tier = tier
        self.overallfaction = overallfaction
        self.capacity = capacity
        self.domain = domain
        self.category = category
        self.movesleft = movesleft
        self.movesmax = movesmax
        self.vision = vision
        self.combat = combat
        self.HP = HP
        self.maxHP = maxHP
        self.faction = faction
        self.unitType = unitType
        self.area = area
        self.selected = selected
        self.movesMade = movesMade
        self.destination = destination
        self.orders = orders
        self.alive = alive
        self.transportOne = transportOne
        self.transportTwo = transportTwo
        self.isLeader = isLeader
        self.xshift = xshift
        self.yshift = yshift
        self.lightarmor = lightarmor
        self.heavyarmor = heavyarmor
        self.naturalarmor = naturalarmor

#set up mapBase class
class mapBase:
    def __init__(self, name, selected, gold, lumber, oil, goldleft, lumberleft, oilleft, hexnumber, faction, tier, area, overallfaction, first_orders, second_orders, third_orders, banner_area):
        self.name = name
        self.selected = selected
        self.gold = gold
        self.lumber = lumber
        self.oil = oil
        self.goldleft = goldleft
        self.lumberleft = lumberleft
        self.oilleft = oilleft
        self.hexnumber = hexnumber
        self.faction = faction
        self.tier = tier
        self.area = area
        self.overallfaction = overallfaction
        self.first_orders = first_orders
        self.second_orders = second_orders
        self.third_orders = third_orders
        self.banner_area = banner_area
        
class mapExpansion:
    def __init__(self, hexnumber, kind, owner, area, overallfaction):
        self.hexnumber = hexnumber
        self.kind = kind
        self.owner = owner
        self.area = area
        self.overallfaction = overallfaction

class buildList:
    def __init__(self, unitType, rect, textrect):
        self.unitType = unitType
        self.rect = rect
        self.textrect = textrect

#establish units list
units = []
for i in range(len(allunits)):
    units.append(mapUnit(allunits[i][UNIT_LOCATION], allunits[i][UNIT_TIER], hordeOrAlliance(allunits[i][UNIT_FACTION]), transportCapacity(allunits[i][UNIT_TRANSPORT_ONE], allunits[i][UNIT_TRANSPORT_TWO], allunits[i][UNIT_TRANSPORT_THREE]), allunits[i][UNIT_TYPE], allunits[i][UNIT_CATEGORY], allunits[i][UNIT_MOVEMENT_REMAINING], allunits[i][UNIT_MOVEMENT_MAX], allunits[i][UNIT_VISION], allunits[i][UNIT_COMBAT], allunits[i][UNIT_HIT_POINTS], allunits[i][UNIT_MAX_HIT_POINTS], allunits[i][UNIT_FACTION], allunits[i][UNIT_NAME], (pygame.Rect((hexToX(allunits[i][UNIT_LOCATION]), hexToY(allunits[i][UNIT_LOCATION])), (UNIT_WIDTH, UNIT_LENGTH))), 0, 0, -1, 'None', allunits[i][UNIT_ALIVE], allunits[i][UNIT_TRANSPORT_ONE], allunits[i][UNIT_TRANSPORT_TWO], isLeader(allunits[i][UNIT_NAME]), 0, 0, allunits[i][UNIT_LIGHT_MAX], allunits[i][UNIT_HEAVY], allunits[i][UNIT_NATURAL]))

#establish bases list
bases = []
for i in range(len(allbases)):
    bases.append(mapBase(allbases[i][0], 0, allbases[i][BASE_GOLD], allbases[i][BASE_LUMBER], allbases[i][BASE_OIL], allbases[i][BASE_GOLD], allbases[i][BASE_LUMBER], allbases[i][BASE_OIL], allbases[i][1], allbases[i][2], allbases[i][3], (pygame.Rect((hexToX(allbases[i][1]) - 60, hexToY(allbases[i][1]) - 60), (BASE_WIDTH, BASE_LENGTH))), hordeOrAlliance(allbases[i][2]), 'None', isSecondMoveAvailable(allbases[i][BASE_TIER]), isThirdMoveAvailable(allbases[i][BASE_TIER]), (pygame.Rect((hexToX(allbases[i][1]), hexToY(allbases[i][1]) - 105), (BANNER_WIDTH, BANNER_LENGTH)))))

#establish expansions list
expansions = []
counter = 0
for i in range(len(allhexes)):
    if int(allhexes[i][HEX_FARM]) != -1:
        expansions.append(mapExpansion(counter, 'Farm', int(allhexes[i][HEX_FARM]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), expansionOwner(int(allhexes[i][HEX_EXPANSION_OWNER]))))
    if int(allhexes[i][HEX_MILL]) != -1:
        expansions.append(mapExpansion(counter, 'Mill', int(allhexes[i][HEX_MILL]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), expansionOwner(int(allhexes[i][HEX_EXPANSION_OWNER]))))
    if int(allhexes[i][HEX_RIG]) != -1:
        expansions.append(mapExpansion(counter, 'Rig', int(allhexes[i][HEX_RIG]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), expansionOwner(int(allhexes[i][HEX_EXPANSION_OWNER]))))
    counter = counter + 1

#determine food surplus
countFood()

#set up right menu rect
rightMenu = pygame.Rect((1001 * resX), (0 * resY), (500 * resX), (1000 * resY))

#draw right menu
windowSurface.blit(rightMenuImage, rightMenu)

#set up minimap rect
miniMap = pygame.Rect((1001 * resX), (0 * resY), (375 * resX), (375 * resY))

#draw miniMap
windowSurface.blit(miniMapImage, miniMap)

#set up minimap clickable rect
miniMapClickable = pygame.Rect((1001 * resX), (0 * resY), (375 * resX), (375 * resY))

#draw minimap cursor
pygame.draw.rect(windowSurface, WHITE, ((1003 * resX), (0 * resY), (105 * resX), (50 * resY)), 2)

#draw menu lines
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (0 * resY)), ((1001 * resX), (1000 * resY)), 3)
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (375 * resY)), ((1400 * resX), (375 * resY)), 7)
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (593 * resY)), ((1400 * resX), (593 * resY)), 7)

#establish faction/food menu info
BASIC_ONE_TEXT = mainFont.render('Faction: ' + factiondictionary[currentfaction], True, GOLD)
BASIC_ONE_TEXTrect = BASIC_ONE_TEXT.get_rect()
BASIC_ONE_TEXTrect.left = 1010 * resX
BASIC_ONE_TEXTrect.top = 400 * resY

BASIC_TWO_TEXT = mainFont.render('Food supply: ' + str(foodcost[0]) + '/' + str(foodcount[0]), True, GOLD)
BASIC_TWO_TEXTrect = BASIC_TWO_TEXT.get_rect()
BASIC_TWO_TEXTrect.left = 1010 * resX
BASIC_TWO_TEXTrect.top = 450 * resY

#establish menu info
MENU_ONE_TEXT = menuFont.render('Space = Clear moves for selected', True, GOLD)
MENU_ONE_TEXTrect = MENU_ONE_TEXT.get_rect()
MENU_ONE_TEXTrect.left = 1010 * resX
MENU_ONE_TEXTrect.top = 600 * resY

MENU_TWO_TEXT = menuFont.render('T = View all arrows or only selected', True, GOLD)
MENU_TWO_TEXTrect = MENU_TWO_TEXT.get_rect()
MENU_TWO_TEXTrect.left = 1010 * resX
MENU_TWO_TEXTrect.top = 620 * resY

MENU_FOUR_TEXT = menuFont.render('Enter = Submit moves', True, GOLD)
MENU_FOUR_TEXTrect = MENU_FOUR_TEXT.get_rect()
MENU_FOUR_TEXTrect.left = 1010 * resX
MENU_FOUR_TEXTrect.top = 660 * resY

MENU_FOUR_ALT_TEXT = menuFont.render('Moves have been submitted!', True, RED)
MENU_FOUR_ALT_TEXTrect = MENU_FOUR_ALT_TEXT.get_rect()
MENU_FOUR_ALT_TEXTrect.left = 1010 * resX
MENU_FOUR_ALT_TEXTrect.top = 660 * resY

MENU_FOUR_SPECTATOR_TEXT = menuFont.render('Opposing faction turn - spectate only', True, RED)
MENU_FOUR_SPECTATOR_TEXTrect = MENU_FOUR_SPECTATOR_TEXT.get_rect()
MENU_FOUR_SPECTATOR_TEXTrect.left = 1010 * resX
MENU_FOUR_SPECTATOR_TEXTrect.top = 660 * resY

MENU_FIVE_TEXT = menuFont.render('Esc = Quit', True, GOLD)
MENU_FIVE_TEXTrect = MENU_FIVE_TEXT.get_rect()
MENU_FIVE_TEXTrect.left = 1010 * resX
MENU_FIVE_TEXTrect.top = 680 * resY

MENU_SIX_TEXT = menuFont.render('F = Toggle fog of war', True, GOLD)
MENU_SIX_TEXTrect = MENU_SIX_TEXT.get_rect()
MENU_SIX_TEXTrect.left = 1010 * resX
MENU_SIX_TEXTrect.top = 640 * resY

MENU_SIX_ON_TEXT = menuFont.render('- ON', True, LIME)
MENU_SIX_ON_TEXTrect = MENU_SIX_ON_TEXT.get_rect()
MENU_SIX_ON_TEXTrect.left = 1210 * resX
MENU_SIX_ON_TEXTrect.top = 640 * resY

MENU_SIX_OFF_TEXT = menuFont.render('- OFF', True, RED)
MENU_SIX_OFF_TEXTrect = MENU_SIX_OFF_TEXT.get_rect()
MENU_SIX_OFF_TEXTrect.left = 1210 * resX
MENU_SIX_OFF_TEXTrect.top = 640 * resY

MENU_SEVEN_TEXT = menuFont.render('M = Toggle caravan routes - ', True, GOLD)
MENU_SEVEN_TEXTrect = MENU_SEVEN_TEXT.get_rect()
MENU_SEVEN_TEXTrect.left = 1010 * resX
MENU_SEVEN_TEXTrect.top = 640 * resY

MENU_SEVEN_ON_TEXT = menuFont.render('ON', True, LIME)
MENU_SEVEN_ON_TEXTrect = MENU_SIX_ON_TEXT.get_rect()
MENU_SEVEN_ON_TEXTrect.left = 1190 * resX
MENU_SEVEN_ON_TEXTrect.top = 640 * resY

MENU_SEVEN_OFF_TEXT = menuFont.render('OFF', True, RED)
MENU_SEVEN_OFF_TEXTrect = MENU_SEVEN_OFF_TEXT.get_rect()
MENU_SEVEN_OFF_TEXTrect.left = 1190 * resX
MENU_SEVEN_OFF_TEXTrect.top = 640 * resY

#establish special order menu info
GIVE_BASE_TEXT = menuFont.render('Left-click allied leader to give base.', True, GOLD)
GIVE_BASE_TEXTrect = GIVE_BASE_TEXT.get_rect()
GIVE_BASE_TEXTrect.left = 1010 * resX
GIVE_BASE_TEXTrect.top = 600 * resY

GIVE_EXPANSION_TEXT_ONE = menuFont.render('Left-click expansion to be given away.', True, GOLD)
GIVE_EXPANSION_TEXT_ONErect = GIVE_EXPANSION_TEXT_ONE.get_rect()
GIVE_EXPANSION_TEXT_ONErect.left = 1010 * resX
GIVE_EXPANSION_TEXT_ONErect.top = 600 * resY

GIVE_EXPANSION_TEXT_TWO = menuFont.render('Left-click target base.', True, GOLD)
GIVE_EXPANSION_TEXT_TWOrect = GIVE_EXPANSION_TEXT_TWO.get_rect()
GIVE_EXPANSION_TEXT_TWOrect.left = 1010 * resX
GIVE_EXPANSION_TEXT_TWOrect.top = 600 * resY

COMMERCE_IN_TEXT = menuFont.render('Left-click resource type to convert (must have at least 2).', True, GOLD)
COMMERCE_IN_TEXTrect = COMMERCE_IN_TEXT.get_rect()
COMMERCE_IN_TEXTrect.left = 1010 * resX
COMMERCE_IN_TEXTrect.top = 600 * resY

COMMERCE_OUT_TEXT = menuFont.render('Left-click resource type to receive (will receive 1).', True, GOLD)
COMMERCE_OUT_TEXTrect = COMMERCE_OUT_TEXT.get_rect()
COMMERCE_OUT_TEXTrect.left = 1010 * resX
COMMERCE_OUT_TEXTrect.top = 600 * resY

COMMERCE_GOLD_TEXT = menuFont.render('GOLD', True, GOLD)
COMMERCE_GOLD_TEXTrect = COMMERCE_GOLD_TEXT.get_rect()
COMMERCE_GOLD_TEXTrect.left = 1010 * resX
COMMERCE_GOLD_TEXTrect.top = 650 * resY

COMMERCE_LUMBER_TEXT = menuFont.render('LUMBER', True, FOREST)
COMMERCE_LUMBER_TEXTrect = COMMERCE_LUMBER_TEXT.get_rect()
COMMERCE_LUMBER_TEXTrect.left = 1010 * resX
COMMERCE_LUMBER_TEXTrect.top = 675 * resY

COMMERCE_OIL_TEXT = menuFont.render('OIL', True, GRAY)
COMMERCE_OIL_TEXTrect = COMMERCE_OIL_TEXT.get_rect()
COMMERCE_OIL_TEXTrect.left = 1010 * resX
COMMERCE_OIL_TEXTrect.top = 700 * resY

EXPAND_TEXT = menuFont.render('Left-click hex for expansion.', True, GOLD)
EXPAND_TEXTrect = EXPAND_TEXT.get_rect()
EXPAND_TEXTrect.left = 1010 * resX
EXPAND_TEXTrect.top = 600 * resY

EXPAND_TWO_TEXT = menuFont.render('Expansions cost 2 lumber.  Bases can expand', True, GOLD)
EXPAND_TWO_TEXTrect = EXPAND_TWO_TEXT.get_rect()
EXPAND_TWO_TEXTrect.left = 1010 * resX
EXPAND_TWO_TEXTrect.top = 650 * resY

EXPAND_THREE_TEXT = menuFont.render('to hexes at a distance equal to', True, GOLD)
EXPAND_THREE_TEXTrect = EXPAND_THREE_TEXT.get_rect()
EXPAND_THREE_TEXTrect.left = 1010 * resX
EXPAND_THREE_TEXTrect.top = 675 * resY

EXPAND_FOUR_TEXT = menuFont.render('their tier.', True, GOLD)
EXPAND_FOUR_TEXTrect = EXPAND_FOUR_TEXT.get_rect()
EXPAND_FOUR_TEXTrect.left = 1010 * resX
EXPAND_FOUR_TEXTrect.top = 700 * resY

REST_UNIT_TEXT = menuFont.render('Left-click unit to rest (must be in base.)', True, GOLD)
REST_UNIT_TEXTrect = REST_UNIT_TEXT.get_rect()
REST_UNIT_TEXTrect.left = 1010 * resX
REST_UNIT_TEXTrect.top = 600 * resY

ASSIST_CONSTRUCTION_TEXT = menuFont.render('Left-click hex to assist construction.', True, GOLD)
ASSIST_CONSTRUCTION_TEXTrect = ASSIST_CONSTRUCTION_TEXT.get_rect()
ASSIST_CONSTRUCTION_TEXTrect.left = 1010 * resX
ASSIST_CONSTRUCTION_TEXTrect.top = 600 * resY

ASSIST_CONSTRUCTION_TEXT_FOUR = menuFont.render('Leader unit must be building base.', True, GOLD)
ASSIST_CONSTRUCTION_TEXT_FOURrect = ASSIST_CONSTRUCTION_TEXT_FOUR.get_rect()
ASSIST_CONSTRUCTION_TEXT_FOURrect.left = 1010 * resX
ASSIST_CONSTRUCTION_TEXT_FOURrect.top = 625 * resY

ASSIST_CONSTRUCTION_TEXT_TWO = menuFont.render('Requires 4 gold, 4 lumber.', True, GOLD)
ASSIST_CONSTRUCTION_TEXT_TWOrect = ASSIST_CONSTRUCTION_TEXT_TWO.get_rect()
ASSIST_CONSTRUCTION_TEXT_TWOrect.left = 1010 * resX
ASSIST_CONSTRUCTION_TEXT_TWOrect.top = 650 * resY

ASSIST_CONSTRUCTION_TEXT_THREE = menuFont.render('(2 gold, 2 lumber with ruins.)', True, GOLD)
ASSIST_CONSTRUCTION_TEXT_THREErect = ASSIST_CONSTRUCTION_TEXT_THREE.get_rect()
ASSIST_CONSTRUCTION_TEXT_THREErect.left = 1010 * resX
ASSIST_CONSTRUCTION_TEXT_THREErect.top = 675 * resY

CARAVAN_ONE_TEXT = menuFont.render('Left-click hexes to build caravan route,', True, GOLD)
CARAVAN_ONE_TEXTrect = CARAVAN_ONE_TEXT.get_rect()
CARAVAN_ONE_TEXTrect.left = 1010 * resX
CARAVAN_ONE_TEXTrect.top = 600 * resY

CARAVAN_TWO_TEXT = menuFont.render('starting one hex from initial base.', True, GOLD)
CARAVAN_TWO_TEXTrect = CARAVAN_TWO_TEXT.get_rect()
CARAVAN_TWO_TEXTrect.left = 1010 * resX
CARAVAN_TWO_TEXTrect.top = 625 * resY

CARAVAN_THREE_TEXT = menuFont.render('Left-click target base to finish.', True, GOLD)
CARAVAN_THREE_TEXTrect = CARAVAN_THREE_TEXT.get_rect()
CARAVAN_THREE_TEXTrect.left = 1010 * resX
CARAVAN_THREE_TEXTrect.top = 650 * resY

CONFIRM_CARAVAN_ERROR_TEXT = menuFont.render('Not enough resources!', True, RED)
CONFIRM_CARAVAN_ERROR_TEXTrect = CONFIRM_CARAVAN_ERROR_TEXT.get_rect()
CONFIRM_CARAVAN_ERROR_TEXTrect.left = 1010 * resX
CONFIRM_CARAVAN_ERROR_TEXTrect.top = 650 * resY

CONFIRM_CARAVAN_YES_TEXT = menuFont.render('YES', True, GOLD)
CONFIRM_CARAVAN_YES_TEXTrect = CONFIRM_CARAVAN_YES_TEXT.get_rect()
CONFIRM_CARAVAN_YES_TEXTrect.left = 1010 * resX
CONFIRM_CARAVAN_YES_TEXTrect.top = 675 * resY

CONFIRM_CARAVAN_NO_TEXT = menuFont.render('NO', True, GOLD)
CONFIRM_CARAVAN_NO_TEXTrect = CONFIRM_CARAVAN_NO_TEXT.get_rect()
CONFIRM_CARAVAN_NO_TEXTrect.left = 1010 * resX
CONFIRM_CARAVAN_NO_TEXTrect.top = 700 * resY

CONFIRM_UNIT_COST_TEXT = menuFont.render(buildunit[0] + ' cost: ' + str(buildunit[1]) + ' gold, ' + str(buildunit[2]) + ' lumber, ' + str(buildunit[3]) + ' oil', True, GOLD)
CONFIRM_UNIT_COST_TEXTrect = CONFIRM_UNIT_COST_TEXT.get_rect()
CONFIRM_UNIT_COST_TEXTrect.left = 1010 * resX
CONFIRM_UNIT_COST_TEXTrect.top = 600 * resY

CONFIRM_UNIT_TIER_TEXT = menuFont.render('Tier ' + str(buildunit[4]) + ' base required.', True, GOLD)
CONFIRM_UNIT_TIER_TEXTrect = CONFIRM_UNIT_TIER_TEXT.get_rect()
CONFIRM_UNIT_TIER_TEXTrect.left = 1010 * resX
CONFIRM_UNIT_TIER_TEXTrect.top = 625 * resY

CONFIRM_UNIT_YES_TEXT = menuFont.render('BUILD', True, GOLD)
CONFIRM_UNIT_YES_TEXTrect = CONFIRM_UNIT_YES_TEXT.get_rect()
CONFIRM_UNIT_YES_TEXTrect.left = 1010 * resX
CONFIRM_UNIT_YES_TEXTrect.top = 650 * resY

CONFIRM_UNIT_NO_TEXT = menuFont.render('CANCEL', True, GOLD)
CONFIRM_UNIT_NO_TEXTrect = CONFIRM_UNIT_NO_TEXT.get_rect()
CONFIRM_UNIT_NO_TEXTrect.left = 1010 * resX
CONFIRM_UNIT_NO_TEXTrect.top = 675 * resY

CONFIRM_UNIT_ERROR_TEXT = menuFont.render('- Not enough resources!', True, RED)
CONFIRM_UNIT_ERROR_TEXTrect = CONFIRM_UNIT_ERROR_TEXT.get_rect()
CONFIRM_UNIT_ERROR_TEXTrect.left = 1060 * resX
CONFIRM_UNIT_ERROR_TEXTrect.top = 650 * resY

CONFIRM_UNIT_FOOD_ERROR_TEXT = menuFont.render('- Not enough food!', True, RED)
CONFIRM_UNIT_FOOD_ERROR_TEXTrect = CONFIRM_UNIT_FOOD_ERROR_TEXT.get_rect()
CONFIRM_UNIT_FOOD_ERROR_TEXTrect.left = 1060 * resX
CONFIRM_UNIT_FOOD_ERROR_TEXTrect.top = 650 * resY

CONFIRM_UNIT_TIER_ERROR_TEXT = menuFont.render('- Base tier too low!', True, RED)
CONFIRM_UNIT_TIER_ERROR_TEXTrect = CONFIRM_UNIT_TIER_ERROR_TEXT.get_rect()
CONFIRM_UNIT_TIER_ERROR_TEXTrect.left = 1060 * resX
CONFIRM_UNIT_TIER_ERROR_TEXTrect.top = 650 * resY

SEND_EXPLANATION_TEXT = menuFont.render('Up/down arrows to scroll, ENTER to enter, SPACE to cancel.', True, GOLD)
SEND_EXPLANATION_TEXTrect = SEND_EXPLANATION_TEXT.get_rect()
SEND_EXPLANATION_TEXTrect.left = 1010 * resX
SEND_EXPLANATION_TEXTrect.top = 625 * resY

SEND_GOLD_ONE_TEXT = menuFont.render('Enter amount of gold to be sent.', True, GOLD)
SEND_GOLD_ONE_TEXTrect = SEND_GOLD_ONE_TEXT.get_rect()
SEND_GOLD_ONE_TEXTrect.left = 1010 * resX
SEND_GOLD_ONE_TEXTrect.top = 600 * resY

SEND_LUMBER_ONE_TEXT = menuFont.render('Enter amount of lumber to be sent.', True, GOLD)
SEND_LUMBER_ONE_TEXTrect = SEND_LUMBER_ONE_TEXT.get_rect()
SEND_LUMBER_ONE_TEXTrect.left = 1010 * resX
SEND_LUMBER_ONE_TEXTrect.top = 600 * resY

SEND_OIL_ONE_TEXT = menuFont.render('Enter amount of oil to be sent.', True, GOLD)
SEND_OIL_ONE_TEXTrect = SEND_OIL_ONE_TEXT.get_rect()
SEND_OIL_ONE_TEXTrect.left = 1010 * resX
SEND_OIL_ONE_TEXTrect.top = 600 * resY

SEND_RESOURCES_TEXT = menuFont.render('Left-click target base, SPACE to cancel.', True, GOLD)
SEND_RESOURCES_TEXTrect = SEND_RESOURCES_TEXT.get_rect()
SEND_RESOURCES_TEXTrect.left = 1010 * resX
SEND_RESOURCES_TEXTrect.top = 600 * resY

BOARD_TRANSPORT_TEXT = menuFont.render('Left-click transport to board.', True, GOLD)
BOARD_TRANSPORT_TEXTrect = BOARD_TRANSPORT_TEXT.get_rect()
BOARD_TRANSPORT_TEXTrect.left = 1010 * resX
BOARD_TRANSPORT_TEXTrect.top = 600 * resY

RANGED_FIRE_TEXT = menuFont.render('Left-click adjacent hex to target.', True, GOLD)
RANGED_FIRE_TEXTrect = RANGED_FIRE_TEXT.get_rect()
RANGED_FIRE_TEXTrect.left = 1010 * resX
RANGED_FIRE_TEXTrect.top = 600 * resY

UPGRADE_BASE_TEXT = menuFont.render('Confirm base upgrade? ENTER to confirm, SPACE to cancel.', True, GOLD)
UPGRADE_BASE_TEXTrect = UPGRADE_BASE_TEXT.get_rect()
UPGRADE_BASE_TEXTrect.left = 1010 * resX
UPGRADE_BASE_TEXTrect.top = 600 * resY

UPGRADE_BASE_ERROR_TEXT = menuFont.render('Not enough resources or harvestable goods.', True, RED)
UPGRADE_BASE_ERROR_TEXTrect = UPGRADE_BASE_ERROR_TEXT.get_rect()
UPGRADE_BASE_ERROR_TEXTrect.left = 1010 * resX
UPGRADE_BASE_ERROR_TEXTrect.top = 675 * resY

#quit + submit order menus
QUIT_CONFIRM_TEXT = menuFont.render('Are you sure you want to quit?', True, GOLD)
QUIT_CONFIRM_TEXTrect = QUIT_CONFIRM_TEXT.get_rect()
QUIT_CONFIRM_TEXTrect.left = 1010 * resX
QUIT_CONFIRM_TEXTrect.top = 600 * resY

QUIT_CONFIRM_YES_TEXT = menuFont.render('YES', True, GOLD)
QUIT_CONFIRM_YES_TEXTrect = QUIT_CONFIRM_YES_TEXT.get_rect()
QUIT_CONFIRM_YES_TEXTrect.left = 1010 * resX
QUIT_CONFIRM_YES_TEXTrect.top = 675 * resY

QUIT_CONFIRM_NO_TEXT = menuFont.render('NO', True, GOLD)
QUIT_CONFIRM_NO_TEXTrect = QUIT_CONFIRM_NO_TEXT.get_rect()
QUIT_CONFIRM_NO_TEXTrect.left = 1010 * resX
QUIT_CONFIRM_NO_TEXTrect.top = 700 * resY

SUBMIT_CONFIRM_TEXT = menuFont.render('Submit orders?', True, GOLD)
SUBMIT_CONFIRM_TEXTrect = SUBMIT_CONFIRM_TEXT.get_rect()
SUBMIT_CONFIRM_TEXTrect.left = 1010 * resX
SUBMIT_CONFIRM_TEXTrect.top = 600 * resY

SUBMIT_CONFIRM_YES_TEXT = menuFont.render('YES', True, GOLD)
SUBMIT_CONFIRM_YES_TEXTrect = SUBMIT_CONFIRM_YES_TEXT.get_rect()
SUBMIT_CONFIRM_YES_TEXTrect.left = 1010 * resX
SUBMIT_CONFIRM_YES_TEXTrect.top = 675 * resY

SUBMIT_CONFIRM_NO_TEXT = menuFont.render('NO', True, GOLD)
SUBMIT_CONFIRM_NO_TEXTrect = SUBMIT_CONFIRM_NO_TEXT.get_rect()
SUBMIT_CONFIRM_NO_TEXTrect.left = 1010 * resX
SUBMIT_CONFIRM_NO_TEXTrect.top = 700 * resY

#establish list of units faction could build
unitBuildList = []
validBuildList = []
establishUnitBuildList()

for i in range(len(unitBuildList)):
    validBuildList.append(buildList(unitBuildList[i], unitListArea(unitBuildList[i], i), menuFont.render(unitBuildList[i], True, GOLD)))

#establish base menu info
BASE_ONE_TEXT = statsFont.render('D = Destroy Base', True, GOLD)
BASE_ONE_TEXTrect = BASE_ONE_TEXT.get_rect()
BASE_ONE_TEXTrect.left = 1010 * resX
BASE_ONE_TEXTrect.top = 600 * resY

BASE_TWO_TEXT = statsFont.render('G = Give Base', True, GOLD)
BASE_TWO_TEXTrect = BASE_TWO_TEXT.get_rect()
BASE_TWO_TEXTrect.left = 1010 * resX
BASE_TWO_TEXTrect.top = 615 * resY

BASE_THREE_TEXT = statsFont.render('E = Give Expansion', True, GOLD)
BASE_THREE_TEXTrect = BASE_THREE_TEXT.get_rect()
BASE_THREE_TEXTrect.left = 1010 * resX
BASE_THREE_TEXTrect.top = 630 * resY

BASE_FOUR_TEXT = statsFont.render('H = Harvest', True, GOLD)
BASE_FOUR_TEXTrect = BASE_FOUR_TEXT.get_rect()
BASE_FOUR_TEXTrect.left = 1010 * resX
BASE_FOUR_TEXTrect.top = 645 * resY

BASE_FIVE_TEXT = statsFont.render('C = Commerce', True, GOLD)
BASE_FIVE_TEXTrect = BASE_FIVE_TEXT.get_rect()
BASE_FIVE_TEXTrect.left = 1010 * resX
BASE_FIVE_TEXTrect.top = 660 * resY

BASE_SIX_TEXT = statsFont.render('N = Build Unit', True, GOLD)
BASE_SIX_TEXTrect = BASE_SIX_TEXT.get_rect()
BASE_SIX_TEXTrect.left = 1010 * resX
BASE_SIX_TEXTrect.top = 675 * resY

BASE_SEVEN_TEXT = statsFont.render('X = Expand', True, GOLD)
BASE_SEVEN_TEXTrect = BASE_SEVEN_TEXT.get_rect()
BASE_SEVEN_TEXTrect.left = 1125 * resX
BASE_SEVEN_TEXTrect.top = 600 * resY

BASE_EIGHT_TEXT = statsFont.render('V = Establish Caravan', True, GOLD)
BASE_EIGHT_TEXTrect = BASE_EIGHT_TEXT.get_rect()
BASE_EIGHT_TEXTrect.left = 1125 * resX
BASE_EIGHT_TEXTrect.top = 615 * resY

BASE_NINE_TEXT = statsFont.render('P = Upgrade Base', True, GOLD)
BASE_NINE_TEXTrect = BASE_NINE_TEXT.get_rect()
BASE_NINE_TEXTrect.left = 1125 * resX
BASE_NINE_TEXTrect.top = 630 * resY

BASE_TEN_TEXT = statsFont.render('S = Send Resources', True, GOLD)
BASE_TEN_TEXTrect = BASE_TEN_TEXT.get_rect()
BASE_TEN_TEXTrect.left = 1125 * resX
BASE_TEN_TEXTrect.top = 645 * resY

BASE_ELEVEN_TEXT = statsFont.render('R = Rest Unit', True, GOLD)
BASE_ELEVEN_TEXTrect = BASE_ELEVEN_TEXT.get_rect()
BASE_ELEVEN_TEXTrect.left = 1125 * resX
BASE_ELEVEN_TEXTrect.top = 660 * resY

BASE_TWELVE_TEXT = statsFont.render('A = Assist Construction', True, GOLD)
BASE_TWELVE_TEXTrect = BASE_TWELVE_TEXT.get_rect()
BASE_TWELVE_TEXTrect.left = 1125 * resX
BASE_TWELVE_TEXTrect.top = 675 * resY

BASE_THIRTEEN_TEXT = statsFont.render('Space = Clear Orders', True, GOLD)
BASE_THIRTEEN_TEXTrect = BASE_THIRTEEN_TEXT.get_rect()
BASE_THIRTEEN_TEXTrect.left = 1010 * resX
BASE_THIRTEEN_TEXTrect.top = 690 * resY

#establish unit menu info
UNIT_ONE_TEXT = menuFont.render('Right-click = Set move', True, GOLD)
UNIT_ONE_TEXTrect = UNIT_ONE_TEXT.get_rect()
UNIT_ONE_TEXTrect.left = 1010 * resX
UNIT_ONE_TEXTrect.top = 600 * resY

UNIT_TWO_TEXT = menuFont.render('Space = Clear orders', True, GOLD)
UNIT_TWO_TEXTrect = UNIT_TWO_TEXT.get_rect()
UNIT_TWO_TEXTrect.left = 1010 * resX
UNIT_TWO_TEXTrect.top = 620 * resY

UNIT_THREE_TEXT = menuFont.render('R = Siege fire (siege units only)', True, GOLD)
UNIT_THREE_TEXTrect = UNIT_THREE_TEXT.get_rect()
UNIT_THREE_TEXTrect.left = 1010 * resX
UNIT_THREE_TEXTrect.top = 640 * resY

UNIT_FOUR_TEXT = menuFont.render('B = Board transport (land units only)', True, GOLD)
UNIT_FOUR_TEXTrect = UNIT_FOUR_TEXT.get_rect()
UNIT_FOUR_TEXTrect.left = 1010 * resX
UNIT_FOUR_TEXTrect.top = 660 * resY

UNIT_FIVE_TEXT = menuFont.render('N = Build base', True, GOLD)
UNIT_FIVE_TEXTrect = UNIT_FIVE_TEXT.get_rect()
UNIT_FIVE_TEXTrect.left = 1010 * resX
UNIT_FIVE_TEXTrect.top = 680 * resY

UNIT_SIX_TEXT = menuFont.render('T = Teleport: Dalaran', True, GOLD)
UNIT_SIX_TEXTrect = UNIT_SIX_TEXT.get_rect()
UNIT_SIX_TEXTrect.left = 1010 * resX
UNIT_SIX_TEXTrect.top = 700 * resY 

#establish fog of war list
fogOfWarList = []
for i in range(1117):
    fogOfWarList.append(i)
for i in range(len(allvision)):
    if int(allvision[i]) in fogOfWarList:
        fogOfWarList.remove(int(allvision[i]))

#determine units per hex data
unitsPer = [ 0 for i in range(1116) ]
for j in range(len(units)):
    unitsPer[units[j].hexnumber] = unitsPer[units[j].hexnumber] + 1

#establish hexes with faction presence
FactionBaseHexes = set()
for k in range(len(bases)):
    if bases[k].faction == currentfaction and bases[k].tier != 0:
        FactionBaseHexes.add(bases[k].hexnumber)
FactionUnitHexes = set()
for l in range(len(units)):
    if units[l].faction == currentfaction and units[l].alive == 1:
        FactionUnitHexes.add(units[l].hexnumber)

#generate expandables data
generateExpandables()

#establish toggles
INITIAL_TOGGLE = 0
QUIT_TOGGLE = 0
SUBMIT_TOGGLE = 0
ARROWS_TOGGLE = 0
UNITS_TOGGLE = 0
FOG_TOGGLE = 0
RANGED_TOGGLE = 0
BOARD_TRANSPORT_TOGGLE = 0
GIVE_BASE_TOGGLE = 0
GIVE_EXPANSION_TOGGLE_ONE = 0
POTENTIAL_EXPANSION = 0
GIVE_EXPANSION_TOGGLE_TWO = 0
COMMERCE_TOGGLE_ONE = 0
POTENTIAL_RESOURCE = 0
COMMERCE_TOGGLE_TWO = 0
EXPAND_TOGGLE = 0
BUILD_UNIT_TOGGLE = 0
CONFIRM_UNIT_TOGGLE = 0
CONFIRM_UNIT_ERROR_TOGGLE = 0
CONFIRM_UNIT_FOOD_ERROR_TOGGLE = 0
CONFIRM_UNIT_TIER_ERROR_TOGGLE = 0
CARAVAN_TOGGLE = 0
CONFIRM_CARAVAN_TOGGLE = 0
CONFIRM_CARAVAN_ERROR_TOGGLE = 0
SEND_RESOURCES_TOGGLE_ONE = 0
SEND_RESOURCES_TOGGLE_TWO = 0
SEND_RESOURCES_TOGGLE_THREE = 0
SEND_RESOURCES_TOGGLE_FOUR = 0
REST_UNIT_TOGGLE = 0
ASSIST_CONSTRUCTION_TOGGLE = 0
CARAVAN_MAP_TOGGLE = 1
UPGRADE_BASE_TOGGLE = 0
UPGRADE_BASE_ERROR_TOGGLE = 0

#SCROLLING VARIABLES
x_supplement = -3400 - (1920 - resolution.current_w)
y_supplement = -6500 - (1080 - resolution.current_h)

if (x_supplement % -100) >= -50:
    X_CORD_SCROLL = x_supplement - (x_supplement % -100)
else:
    X_CORD_SCROLL = x_supplement - (x_supplement % 100)        
if (y_supplement % -100) >= -50:
    Y_CORD_SCROLL = y_supplement - (y_supplement % -100)
else:
    Y_CORD_SCROLL = y_supplement - (y_supplement % 100) 

#draw map
redraw()
INITIAL_TOGGLE = 1

#tests

#run game loop
clock = pygame.time.Clock()

while True:
    clock.tick(60)

    #draw window onto screen
    pygame.display.update()

    #responding to player input
    for event in pygame.event.get():

        #allow for scrolling
        if event.type == pygame.KEYDOWN:
            if SEND_RESOURCES_TOGGLE_ONE == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < bases[checkBaseSelected()].goldleft:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            elif SEND_RESOURCES_TOGGLE_TWO == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < bases[checkBaseSelected()].lumberleft:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            elif SEND_RESOURCES_TOGGLE_THREE == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < bases[checkBaseSelected()].oilleft:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            else:
                if event.key == pygame.K_LEFT:
                    if xcord < 0:
                        xcord += 100
                if event.key == pygame.K_RIGHT:
                    if xcord > X_CORD_SCROLL:
                        xcord += -100
                if event.key == pygame.K_UP:
                    if ycord < 0:
                        ycord += 100
                if event.key == pygame.K_DOWN:
                    if ycord > Y_CORD_SCROLL:
                        ycord += -100

        #redraw based on scroll
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT or event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                redraw()

        #check for left mouseclick and select if applicable
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #allow for quitting
                if QUIT_TOGGLE == 1:
                    if QUIT_CONFIRM_YES_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        QUIT_TOGGLE = 0
                        pygame.quit()
                        sys.exit()
                    if QUIT_CONFIRM_NO_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        QUIT_TOGGLE = 0
                #confirm order submission
                elif SUBMIT_TOGGLE == 1:
                    if SUBMIT_CONFIRM_YES_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:

                        # establish connection to database
                        db = load_db()

                        # submit orders
                        orderdata_cur = db.cursor()
                        
                        for i in allorders:
                            templist = tuple(i)
                            # templist = map(str, templist)
                            if len(templist) == 2:
                                orderdata_cur.execute("INSERT INTO orders (unit, first_move) VALUES (%s, %s)", (templist[0], templist[1])) 
                            if len(templist) == 3:
                                orderdata_cur.execute("INSERT INTO orders (unit, first_move, second_move) VALUES (%s, %s, %s)", (templist[0], templist[1], templist[2]))
                            if len(templist) == 4:
                                orderdata_cur.execute("INSERT INTO orders (unit, first_move, second_move, third_move) VALUES (%s, %s, %s, %s)", (templist[0], templist[1], templist[2], templist[3]))

                        orderdata_cur.close()

                        # submit economic actions
                        economicdata_cur = db.cursor()

                        for i in alleconomicactions:
                            templist = tuple(i)
                            templist = map(str, templist)

                            key_string = 'action_type, base_hex'
                            values_string = '%s, %s'
                            for j in range(len(templist)):
                                if (j != 0) and (j != 1):
                                    key_string = key_string + ', action_' + str(j - 1)
                                    values_string = values_string + ', %s'
                            data_entry_string = "INSERT INTO economicactions (" + key_string + ") VALUES (" + values_string + ")"
                            economicdata_cur.execute(data_entry_string, (templist))
                                
                        economicdata_cur.close()

                        # submit special orders
                        specialorderdata_cur = db.cursor()
                        
                        for i in allspecialorders:
                            templist = tuple(i)
                            templist = map(str, templist)
                            if len(templist) == 2:
                                specialorderdata_cur.execute("INSERT INTO specialorders (action, unit) VALUES (%s, %s)", (templist[0], templist[1])) 
                            if len(templist) == 3:
                                specialorderdata_cur.execute("INSERT INTO specialorders (action, unit, data_1) VALUES (%s, %s, %s)", (templist[0], templist[1], templist[2]))
                            if len(templist) == 4:
                                specialorderdata_cur.execute("INSERT INTO specialorders (action, unit, data_1, data_2) VALUES (%s, %s, %s, %s)", (templist[0], templist[1], templist[2], templist[3]))
                            if len(templist) == 5:
                                specialorderdata_cur.execute("INSERT INTO specialorders (action, unit, data_1, data_2, data_3) VALUES (%s, %s, %s, %s, %s)", (templist[0], templist[1], templist[2], templist[3], templist[4]))

                        specialorderdata_cur.close()

                        #update turnstatus to show turn submitted
                        turnstatus_cur = db.cursor()
                        factionstring = 'COL_' + str(currentfaction)
                        savestring = "UPDATE turnstatus SET " + factionstring + " = 1"
                        turnstatus_cur.execute(savestring)
                        turnstatus_cur.close()
                        turnstatus=1

                        #commit database changes, close connection
                        db.commit()
                        db.close()
                        SUBMIT_TOGGLE = 0
                        redraw()
                    if SUBMIT_CONFIRM_NO_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        SUBMIT_TOGGLE = 0
                        redraw()
                        
                #if left click is on miniMap, jump to map location
                elif miniMapClickable.collidepoint(pygame.mouse.get_pos()) == 1:
                    a, b = pygame.mouse.get_pos()
                    xcord, ycord = miniMapScale(a,b)
                #if ranged attacking, allow for targeting
                elif RANGED_TOGGLE == 1:
                    for i in range(1117):
                        if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                            if Adjacent(units[checkSelected()].hexnumber, i) == 1:
                                allspecialorders.append(["Rangedfire", checkSelected(), i])
                                updateOrderString(checkSelected(), 'Ranged')
                    clearSelected()
                    RANGED_TOGGLE = 0
                #if boarding transport, allow for targeting
                elif BOARD_TRANSPORT_TOGGLE == 1:
                    for i in range(len(units)):
                        if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            # if isThereRoom(units[i].capacity) > 0:
                            if units[i].capacity > 0 and units[i].faction == currentfaction and units[i].hexnumber == units[checkSelected()].hexnumber and units[i].orders == "None":
                                allspecialorders.append(["Board Transport", checkSelected(), i])
                                updateOrderString(checkSelected(), 'Board Transport')
                                units[i].capacity -= 1
                                if units[i].transportOne == -2:
                                    units[i].transportOne == checkSelected()
                                else:
                                    units[i].transportTwo == checkSelected()
                    clearSelected()
                    BOARD_TRANSPORT_TOGGLE = 0
                #if giving base, allow for targeting
                elif GIVE_BASE_TOGGLE == 1:
                    for i in range(len(units)):
                        if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            if units[i].hexnumber == bases[checkBaseSelected()].hexnumber:
                                if units[i].faction != currentfaction:
                                    if isAllied(units[i].faction, currentfaction) == 1 and units[i].isLeader == 1:
                                        alleconomicactions.append(["Give Base", bases[checkBaseSelected()].hexnumber, i])
                                        updateBaseOrderString(checkBaseSelected(), 'Give Base', ordernumber=1, faction=units[i].faction)
                    clearSelected()
                    GIVE_BASE_TOGGLE = 0
                #if giving expansion, allow for targeting both expansion and target base
                elif GIVE_EXPANSION_TOGGLE_ONE == 1:
                    for i in range(len(expansions)):
                        if expansions[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            GIVE_EXPANSION_TOGGLE_TWO = 1
                            POTENTIAL_EXPANSION = expansions[i].hexnumber
                    if GIVE_EXPANSION_TOGGLE_TWO == 0:
                        clearSelected()
                    GIVE_EXPANSION_TOGGLE_ONE = 0
                elif GIVE_EXPANSION_TOGGLE_TWO == 1:
                    for i in range(len(bases)):
                        if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            if economicchecker(["Give Expansion", bases[checkBaseSelected()].hexnumber, POTENTIAL_EXPANSION, bases[i].hexnumber]) == 1:
                                alleconomicactions.append(["Give Expansion", bases[checkBaseSelected()].hexnumber, POTENTIAL_EXPANSION, bases[i].hexnumber])
                                if bases[checkBaseSelected()].first_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Give Expansion', ordernumber=1)
                                elif bases[checkBaseSelected()].second_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Give Expansion', ordernumber=2)
                                elif bases[checkBaseSelected()].third_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Give Expansion', ordernumber=3)
                    POTENTIAL_EXPANSION = 0
                    GIVE_EXPANSION_TOGGLE_TWO = 0
                #if commerce order, allow for choosing resource types
                elif COMMERCE_TOGGLE_ONE == 1:
                    if COMMERCE_GOLD_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and bases[checkBaseSelected()].goldleft >= 2:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_GOLD
                    if COMMERCE_LUMBER_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and bases[checkBaseSelected()].lumberleft >= 2:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_LUMBER
                    if COMMERCE_OIL_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and bases[checkBaseSelected()].oilleft >= 2:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_OIL
                    if COMMERCE_TOGGLE_TWO == 0:
                        clearSelected()
                    COMMERCE_TOGGLE_ONE = 0
                elif COMMERCE_TOGGLE_TWO == 1:
                    if COMMERCE_GOLD_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_GOLD:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_GOLD])
                        bases[checkBaseSelected()].goldleft += 1
                        if POTENTIAL_RESOURCE == BASE_LUMBER:
                            bases[checkBaseSelected()].lumberleft -= 2
                        elif POTENTIAL_RESOURCE == BASE_OIL:
                            bases[checkBaseSelected()].oilleft -= 2
                        if bases[checkBaseSelected()].first_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=1, resource=BASE_GOLD)
                        elif bases[checkBaseSelected()].second_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=2, resource=BASE_GOLD)
                        elif bases[checkBaseSelected()].third_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=3, resource=BASE_GOLD)
                    if COMMERCE_LUMBER_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_LUMBER:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_LUMBER])
                        bases[checkBaseSelected()].lumberleft += 1
                        if POTENTIAL_RESOURCE == BASE_GOLD:
                            bases[checkBaseSelected()].goldleft -= 2
                        elif POTENTIAL_RESOURCE == BASE_OIL:
                            bases[checkBaseSelected()].oilleft -= 2
                        if bases[checkBaseSelected()].first_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=1, resource=BASE_LUMBER)
                        elif bases[checkBaseSelected()].second_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=2, resource=BASE_LUMBER)
                        elif bases[checkBaseSelected()].third_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=3, resource=BASE_LUMBER)
                    if COMMERCE_OIL_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_OIL:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_OIL])
                        bases[checkBaseSelected()].oilleft += 1
                        if POTENTIAL_RESOURCE == BASE_GOLD:
                            bases[checkBaseSelected()].goldleft -= 2
                        elif POTENTIAL_RESOURCE == BASE_LUMBER:
                            bases[checkBaseSelected()].lumberleft -= 2
                        if bases[checkBaseSelected()].first_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=1, resource=BASE_OIL)
                        elif bases[checkBaseSelected()].second_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=2, resource=BASE_OIL)
                        elif bases[checkBaseSelected()].third_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=3, resource=BASE_OIL)
                    POTENTIAL_RESOURCE = 0
                    COMMERCE_TOGGLE_TWO = 0
                #if expand order, choose expansion location
                elif EXPAND_TOGGLE == 1:
                    for i in range(1117):
                        if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1 and bases[checkBaseSelected()].lumberleft >= 2:
                            if economicchecker(["Expand", bases[checkBaseSelected()].hexnumber, i]) == 1:
                                alleconomicactions.append(["Expand", bases[checkBaseSelected()].hexnumber, i])
                                if bases[checkBaseSelected()].first_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=1)
                                elif bases[checkBaseSelected()].second_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=2)
                                elif bases[checkBaseSelected()].third_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=3)
                                bases[checkBaseSelected()].lumberleft -= 2
                    EXPAND_TOGGLE = 0
                #if build unit order, allow for unit to be chosen
                elif BUILD_UNIT_TOGGLE == 1:
                    for i in range(len(validBuildList)):
                        if validBuildList[i].rect.collidepoint(pygame.mouse.get_pos()) == 1:
                            confirmunit = validBuildList[i].unitType
                            buildunit = getUnitCost(validBuildList[i].unitType)
                            CONFIRM_UNIT_COST_TEXT = menuFont.render(buildunit[0] + ' cost: ' + str(buildunit[1]) + ' gold, ' + str(buildunit[2]) + ' lumber, ' + str(buildunit[3]) + ' oil', True, GOLD)
                            CONFIRM_UNIT_TIER_TEXT = menuFont.render('Tier ' + str(buildunit[4]) + ' base required.', True, GOLD)
                            CONFIRM_UNIT_TOGGLE = 1
                   
                    BUILD_UNIT_TOGGLE = 0

                #confirm unit
                elif CONFIRM_UNIT_TOGGLE == 1:
                    if CONFIRM_UNIT_YES_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        if foodcount[0] - foodcost[0] < 1:
                            CONFIRM_UNIT_FOOD_ERROR_TOGGLE = 1
                        elif bases[checkBaseSelected()].tier < buildunit[4]:
                            CONFIRM_UNIT_TIER_ERROR_TOGGLE = 1
                        elif bases[checkBaseSelected()].goldleft >= buildunit[1] and bases[checkBaseSelected()].lumberleft >= buildunit[2] and bases[checkBaseSelected()].oilleft >= buildunit[3]:
                            alleconomicactions.append(["Build Unit", bases[checkBaseSelected()].hexnumber, confirmunit])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=1, unittype=confirmunit)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=2, unittype=confirmunit)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=3, unittype=confirmunit)
                            bases[checkBaseSelected()].goldleft -= buildunit[1]
                            bases[checkBaseSelected()].lumberleft -= buildunit[2]
                            bases[checkBaseSelected()].oilleft -= buildunit[3]
                            confirmunit = ''
                            buildunit = ['None', 0, 0, 0, 0]
                            foodcost[0] += 1
                            CONFIRM_UNIT_TOGGLE = 0
                        else:
                            CONFIRM_UNIT_ERROR_TOGGLE = 1
                    if CONFIRM_UNIT_NO_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        confirmunit = ''
                        buildunit = ['None', 0, 0, 0, 0]
                        CONFIRM_UNIT_ERROR_TOGGLE = 0
                        CONFIRM_UNIT_FOOD_ERROR_TOGGLE = 0
                        CONFIRM_UNIT_TIER_ERROR_TOGGLE = 0
                        CONFIRM_UNIT_TOGGLE = 0
                #if establish caravan order, allow for route to be established
                elif CARAVAN_TOGGLE == 1:
                    for i in range(len(bases)):
                        if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            tempcaravanlist.append(bases[i].hexnumber)
                            CONFIRM_CARAVAN_TOGGLE = 1
                            CARAVAN_TOGGLE = 0
                    if CARAVAN_TOGGLE == 1:
                        count = 0
                        for i in range(1117):
                            if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                                tempcaravanlist.append(count)
                            count = count + 1
                #if confirm caravan menu, allow for confirm or cancel
                elif CONFIRM_CARAVAN_TOGGLE == 1:
                    if CONFIRM_CARAVAN_YES_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        if bases[checkBaseSelected()].lumberleft >= getCaravanData()[1] and bases[checkBaseSelected()].oilleft >= getCaravanData()[2]:
                            if economicchecker(["Establish Caravan", bases[checkBaseSelected()].hexnumber, LandOrSea(HexsideTerrain(tempcaravanlist[0], tempcaravanlist[1]))] + tempcaravanlist) == 1:
                                alleconomicactions.append(["Establish Caravan", bases[checkBaseSelected()].hexnumber, LandOrSea(HexsideTerrain(tempcaravanlist[0], tempcaravanlist[1]))] + tempcaravanlist)
                                for i in range(len(bases)):
                                    if bases[i].hexnumber == tempcaravanlist[-1]:
                                        if bases[checkBaseSelected()].first_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=1, targetbase=bases[i].name)
                                        elif bases[checkBaseSelected()].second_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=2, targetbase=bases[i].name)
                                        elif bases[checkBaseSelected()].third_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=3, targetbase=bases[i].name)
                                bases[checkBaseSelected()].lumberleft -= getCaravanData()[1]
                                bases[checkBaseSelected()].oilleft -= getCaravanData()[2]
                            CONFIRM_CARAVAN_TOGGLE = 0
                        else:
                            CONFIRM_CARAVAN_ERROR_TOGGLE = 1
                    if CONFIRM_CARAVAN_NO_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        CONFIRM_CARAVAN_TOGGLE = 0
                        CONFIRM_CARAVAN_ERROR_TOGGLE = 0
                #if send resources order, allow for selecting of destination hex
                elif SEND_RESOURCES_TOGGLE_ONE == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_TWO == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_THREE == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_FOUR == 1:
                    for i in range(len(bases)):
                        if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and bases[i].name != bases[checkBaseSelected()].name and isAllied(bases[i].faction, currentfaction) == 1:
                            if economicchecker(["Send Resources", bases[checkBaseSelected()].hexnumber, bases[i].hexnumber, POTENTIAL_GOLD, POTENTIAL_LUMBER, POTENTIAL_OIL]) == 1:
                                alleconomicactions.append(["Send Resources", bases[checkBaseSelected()].hexnumber, bases[i].hexnumber, POTENTIAL_GOLD, POTENTIAL_LUMBER, POTENTIAL_OIL])
                                if bases[checkBaseSelected()].first_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=1, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                                elif bases[checkBaseSelected()].second_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=2, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                                elif bases[checkBaseSelected()].third_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=3, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                                bases[checkBaseSelected()].goldleft -= POTENTIAL_GOLD
                                bases[checkBaseSelected()].lumberleft -= POTENTIAL_LUMBER
                                bases[checkBaseSelected()].oilleft -= POTENTIAL_OIL
                                SEND_RESOURCES_TOGGLE_FOUR = 0
                #if rest unit order, allow for target unit selection
                elif REST_UNIT_TOGGLE == 1:
                    for i in range(len(units)):
                        if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and units[i].hexnumber == bases[checkBaseSelected()].hexnumber and isAllied(units[i].faction, currentfaction) == 1:
                            if units[i].HP < units[i].maxHP and bases[checkBaseSelected()].goldleft >= 2:
                                alleconomicactions.append(["Rest Unit", bases[checkBaseSelected()].hexnumber, i])
                                if bases[checkBaseSelected()].first_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Rest Unit', ordernumber=1, unittype=units[i].unitType)
                                elif bases[checkBaseSelected()].second_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Rest Unit', ordernumber=2, unittype=units[i].unitType)
                                elif bases[checkBaseSelected()].third_orders == 'None':
                                    updateBaseOrderString(checkBaseSelected(), 'Rest Unit', ordernumber=3, unittype=units[i].unitType)
                                bases[checkBaseSelected()].goldleft -= 2
                    REST_UNIT_TOGGLE = 0
                #if upgrade base order, lock main map
                elif UPGRADE_BASE_TOGGLE == 1:
                    pass
                #if assist construction order, allow for target hex selection
                elif ASSIST_CONSTRUCTION_TOGGLE == 1:
                    if bases[checkBaseSelected()].goldleft >= 2 and bases[checkBaseSelected()].lumberleft >= 2:
                        for i in range(1117):
                            if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                                if economicchecker(["Assist Construction", bases[checkBaseSelected()].hexnumber, i]) == 1:
                                    if doesBaseExist(i) == 2:
                                        alleconomicactions.append(["Assist Construction", bases[checkBaseSelected()].hexnumber, i])
                                        if bases[checkBaseSelected()].first_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=1)
                                        elif bases[checkBaseSelected()].second_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=2)
                                        elif bases[checkBaseSelected()].third_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=3)
                                        bases[checkBaseSelected()].goldleft -= 2
                                        bases[checkBaseSelected()].lumberleft -= 2
                                    elif bases[checkBaseSelected()].goldleft >= 4 and bases[checkBaseSelected()].lumberleft >= 4:
                                        alleconomicactions.append(["Assist Construction", bases[checkBaseSelected()].hexnumber, i])
                                        if bases[checkBaseSelected()].first_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=1)
                                        elif bases[checkBaseSelected()].second_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=2)
                                        elif bases[checkBaseSelected()].third_orders == 'None':
                                            updateBaseOrderString(checkBaseSelected(), 'Assist Construction', ordernumber=3)
                                        bases[checkBaseSelected()].goldleft -= 4
                                        bases[checkBaseSelected()].lumberleft -= 4
                    ASSIST_CONSTRUCTION_TOGGLE = 0
                #else select/deselect units as applicable                    
                else:
                    if checkSelected() != -1 or checkBaseSelected() != -1:
                        clearSelected()
                    else:
                        foundUnit = 0
                        for i in range(len(units)):
                            # if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and isAllied(units[i].faction, currentfaction) == 1: #can only select allied units
                            if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1: #can select all units
                                clearSelected()
                                units[i].selected = 1
                                foundUnit = 1
                        if foundUnit == 0:
                            for i in range(len(bases)):
                                # if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and isAllied(bases[i].faction, currentfaction) == 1 and bases[i].tier != 0: #can only select allied bases
                                if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and bases[i].tier != 0: #can select all bases
                                    clearSelected()
                                    bases[i].selected = 1
                redraw()
        
        #check for right mouseclick and move if applicable
        target = -1
        initial = -1
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                if spectator[0] == 0 and checkSelected() != -1 and units[checkSelected()].faction == currentfaction and (units[checkSelected()].orders == 'None' or 'Move' in units[checkSelected()].orders):
                    initial = checkSelected()
                    first_step = -1
                    second_step = -1
                    third_step = -1
                    for i in range(len(allorders)):
                        if allorders[i][0] == initial and len(allorders[i]) == 4:
                            first_step = allorders[i][1]
                            second_step = allorders[i][2]
                            third_step = allorders[i][3]
                        elif allorders[i][0] == initial and len(allorders[i]) == 3:
                            first_step = allorders[i][1]
                            second_step = allorders[i][2]
                        elif allorders[i][0] == initial and len(allorders[i]) == 2:
                            first_step = allorders[i][1]
                    for i in range(1117):
                        if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                            target = i
                        if target != -1:
                            #if isTargetAcceptable(units[initial].hexnumber, target) == 1:
                            removeIndex = -1
                            for i in range(len(allorders)):
                                if allorders[i][0] == initial:
                                    removeIndex = i
                            if removeIndex != -1:
                                allorders.pop(removeIndex)
                            if first_step != -1 and second_step != -1 and third_step != -1:
                                allorders.append([initial,first_step,second_step,third_step,target])
                            elif first_step != -1 and second_step != -1:
                                allorders.append([initial,first_step,second_step,target])
                            elif first_step != -1:
                                allorders.append([initial,first_step,target])
                            else:
                                allorders.append([initial,target])
                            target = -1
                            clearSelected()
                            hexsidelimitchecks=[]
                            airlimitchecks=[]
                            movechecker()
                            allorders=copy.deepcopy(successfulmoves)
                            successfulmoves=[]
                            del allunits[:]
                            del allhexes[:]
                            allunits=copy.deepcopy(backupallunits)
                            allhexes=copy.deepcopy(backupallhexes)
                            updateOrderString(initial, 'Move')
                            redraw()

        #use SPACE to clear all orders for a selected unit, or initiate certain base actions
        if event.type == pygame.KEYDOWN:
            if SEND_RESOURCES_TOGGLE_ONE == 1:
                if event.key == pygame.K_SPACE:
                    SEND_RESOURCES_TOGGLE_ONE = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_TWO == 1:
                if event.key == pygame.K_SPACE:
                    SEND_RESOURCES_TOGGLE_TWO = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_THREE == 1:
                if event.key == pygame.K_SPACE:
                    SEND_RESOURCES_TOGGLE_THREE = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_FOUR == 1:
                if event.key == pygame.K_SPACE:
                    SEND_RESOURCES_TOGGLE_FOUR = 0
                    redraw()
            elif UPGRADE_BASE_TOGGLE == 1:
                if event.key == pygame.K_SPACE:
                    UPGRADE_BASE_TOGGLE = 0
                    UPGRADE_BASE_ERROR_TOGGLE = 0
                    redraw()
            else:
                if event.key == pygame.K_SPACE and spectator[0] == 0:
                    if checkSelected() != -1:
                        to_clear = checkSelected()
                        to_clear_index = -1
                        to_clear_index_special = -1
                        transport_index = -1
                        for i in range(len(allorders)):
                            if allorders[i][0] == to_clear:
                                to_clear_index = i
                        if to_clear_index != -1:
                            allorders.pop(to_clear_index)
                            updateOrderString(to_clear, 'Clear')
                            redraw()
                        for i in range(len(allspecialorders)):
                            if allspecialorders[i][1] == to_clear:
                                to_clear_index_special = i
                                if allspecialorders[i][0] == 'Board Transport':
                                    transport_index = allspecialorders[i][2]
                        if to_clear_index_special != -1:
                            allspecialorders.pop(to_clear_index_special)
                            updateOrderString(to_clear, 'Clear')
                            if transport_index != -1:
                                units[transport_index].capacity += 1
                                if units[transport_index].transportTwo == -2:
                                    units[transport_index].transportOne = -2
                                else:
                                    units[transport_index].transportTwo = -2
                            redraw()
                    if checkBaseSelected() != -1:
                        to_clear = bases[checkBaseSelected()].hexnumber
                        to_clear_index = -1
                        ordertracker = 0
                        for i in range(len(alleconomicactions)):
                            if alleconomicactions[i][1] == to_clear:
                                to_clear_index = i
                                ordertracker = ordertracker + 1
                        if to_clear_index != -1:
                            resetResources(to_clear_index)
                            alleconomicactions.pop(to_clear_index)
                            updateBaseOrderString(checkBaseSelected(), 'Clear', ordernumber=ordertracker)
                            redraw()

        #hit ENTER to output orders to spreadsheet, or confirm various orders
        if event.type == pygame.KEYDOWN:
            if SEND_RESOURCES_TOGGLE_ONE == 1:
                if event.key == pygame.K_RETURN:
                    POTENTIAL_GOLD = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_TWO = 1
                    SEND_RESOURCES_TOGGLE_ONE = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_TWO == 1:
                if event.key == pygame.K_RETURN:
                    POTENTIAL_LUMBER = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_THREE = 1
                    SEND_RESOURCES_TOGGLE_TWO = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_THREE == 1:
                if event.key == pygame.K_RETURN:
                    POTENTIAL_OIL = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_FOUR = 1
                    SEND_RESOURCES_TOGGLE_THREE = 0
                    redraw()
            elif UPGRADE_BASE_TOGGLE == 1:
                if event.key == pygame.K_RETURN:
                    if bases[checkBaseSelected()].tier == 1:
                        if bases[checkBaseSelected()].goldleft >= 6 and bases[checkBaseSelected()].lumberleft >= 6 and bases[checkBaseSelected()].oilleft >= 2 and economicchecker(["Upgrade Base", bases[checkBaseSelected()].hexnumber]) == 1:
                            alleconomicactions.append(["Upgrade Base", bases[checkBaseSelected()].hexnumber])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=1)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=2)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=3)
                            bases[checkBaseSelected()].goldleft -= 6
                            bases[checkBaseSelected()].lumberleft -= 6
                            bases[checkBaseSelected()].oilleft -= 2
                            UPGRADE_BASE_TOGGLE = 0
                        else:
                            UPGRADE_BASE_ERROR_TOGGLE = 1
                    if bases[checkBaseSelected()].tier == 2:
                        if bases[checkBaseSelected()].goldleft >= 8 and bases[checkBaseSelected()].lumberleft >= 8 and bases[checkBaseSelected()].oilleft >= 4 and economicchecker(["Upgrade Base", bases[checkBaseSelected()].hexnumber]) == 1:
                            alleconomicactions.append(["Upgrade Base", bases[checkBaseSelected()].hexnumber])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=1)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=2)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=3)
                            bases[checkBaseSelected()].goldleft -= 8
                            bases[checkBaseSelected()].lumberleft -= 8
                            bases[checkBaseSelected()].oilleft -= 4
                            UPGRADE_BASE_TOGGLE = 0
                        else:
                            UPGRADE_BASE_ERROR_TOGGLE = 1
                    redraw()
            else:
                if event.key == pygame.K_RETURN and spectator[0] == 0:
                    if turnstatus==0:
                        SUBMIT_TOGGLE = 1
                        redraw()

        #hit T to toggle between arrows display (or teleport Dalaran)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                if currentfaction==FACTION_DALARAN and (units[checkSelected()].unitType == "Mage" or units[checkSelected()].isLeader == 1):
                    if units[checkSelected()].orders == 'None':
                        if dalarancombat[0] == 0:
                            if units[checkSelected()].hexnumber not in combathexes:
                                allspecialorders.append(["Teleport Dalaran", checkSelected()])
                                updateOrderString(checkSelected(), "Teleport Dalaran")
                else:
                    ARROWS_TOGGLE = toggle(ARROWS_TOGGLE)
                redraw()
                
        #hit F to toggle fog of war on/off
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                FOG_TOGGLE = toggle(FOG_TOGGLE)
                redraw()

        #hit R for ranged fire when unit selected or rest unit when base selected
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and spectator[0]==0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].goldleft >= 2 and ('Rest' not in bases[checkBaseSelected()].first_orders and 'Rest' not in bases[checkBaseSelected()].second_orders and 'Rest' not in bases[checkBaseSelected()].third_orders) and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    REST_UNIT_TOGGLE = 1
                    redraw()
                elif checkSelected() != -1 and units[checkSelected()].faction == currentfaction and units[checkSelected()].category == CATEGORY_INTERIOR_SIEGE and units[checkSelected()].orders == 'None':
                    if units[checkSelected()].hexnumber not in combathexes:
                        RANGED_TOGGLE = 1
                        redraw()
                    
        #hit B to board transport
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b and spectator[0]==0:
                if checkSelected() != -1 and units[checkSelected()].faction == currentfaction and units[checkSelected()].domain == TYPE_GROUND and units[checkSelected()].orders == 'None':
                    BOARD_TRANSPORT_TOGGLE = 1
                    redraw()

        #hit D for destroy base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d and spectator[0]==0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].first_orders == 'None':
                    alleconomicactions.append(["Destroy Base", bases[checkBaseSelected()].hexnumber])
                    updateBaseOrderString(checkBaseSelected(), 'Destroy Base', ordernumber=1)
                    redraw()

        #hit G for give base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g  and spectator[0]==0 and GIVE_BASE_TOGGLE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].first_orders == 'None':
                    GIVE_BASE_TOGGLE = 1
                    redraw()

        #hit E for give expansion order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and spectator[0]==0 and GIVE_EXPANSION_TOGGLE_ONE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders != 'Give Expansion' and bases[checkBaseSelected()].second_orders != 'Give Expansion' and bases[checkBaseSelected()].third_orders != 'Give Expansion') and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    GIVE_EXPANSION_TOGGLE_ONE = 1
                    redraw()    

        #hit H for harvest order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h and spectator[0]==0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders != 'Harvest' and bases[checkBaseSelected()].second_orders != 'Harvest' and bases[checkBaseSelected()].third_orders != 'Harvest') and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    resources = calculateHarvest(bases[checkBaseSelected()].hexnumber)
                    bases[checkBaseSelected()].goldleft += resources[0]
                    bases[checkBaseSelected()].lumberleft += resources[1]
                    bases[checkBaseSelected()].oilleft += resources[2]
                    alleconomicactions.append(["Harvest", bases[checkBaseSelected()].hexnumber])
                    if bases[checkBaseSelected()].first_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Harvest', ordernumber=1)
                    elif bases[checkBaseSelected()].second_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Harvest', ordernumber=2)
                    elif bases[checkBaseSelected()].third_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Harvest', ordernumber=3)
                    redraw()        

        #hit C for commerce order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and spectator[0]==0 and COMMERCE_TOGGLE_ONE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and ('Commerce' not in bases[checkBaseSelected()].first_orders and 'Commerce' not in bases[checkBaseSelected()].second_orders and 'Commerce' not in bases[checkBaseSelected()].third_orders) and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    COMMERCE_TOGGLE_ONE = 1
                    redraw()  

        #hit N for build base order (if unit selected) or build unit order (if base selected)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n and spectator[0]==0 and BUILD_UNIT_TOGGLE == 0:
                if checkSelected() != -1 and units[checkSelected()].faction == currentfaction and units[checkSelected()].orders == 'None':
                    if units[checkSelected()].isLeader == 1 and allhexes[units[checkSelected()].hexnumber][HEX_TERRAIN] == 'C' and doesBaseExist(units[checkSelected()].hexnumber) == 0:
                        allspecialorders.append(["Build Base", checkSelected(), units[checkSelected()].hexnumber])
                        updateOrderString(checkSelected(), 'Build Base')
                        redraw()
                    #check for ruins
                    if doesBaseExist(units[checkSelected()].hexnumber) == 2:
                        allspecialorders.append(["Build Base", checkSelected(), units[checkSelected()].hexnumber])
                        updateOrderString(checkSelected(), 'Build Base')
                        redraw()
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and ('Build' not in bases[checkBaseSelected()].first_orders and 'Build' not in bases[checkBaseSelected()].second_orders and 'Build' not in bases[checkBaseSelected()].third_orders) and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    BUILD_UNIT_TOGGLE = 1
                    redraw()

        #hit X for expand order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x and spectator[0]==0 and EXPAND_TOGGLE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and ('Expand' not in bases[checkBaseSelected()].first_orders and 'Expand' not in bases[checkBaseSelected()].second_orders and 'Expand' not in bases[checkBaseSelected()].third_orders) and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    EXPAND_TOGGLE = 1
                    redraw()

        #hit V for establish caravan order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v and spectator[0]==0 and CARAVAN_TOGGLE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and ('Caravan' not in bases[checkBaseSelected()].first_orders and 'Caravan' not in bases[checkBaseSelected()].second_orders and 'Caravan' not in bases[checkBaseSelected()].third_orders) and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    tempcaravanlist[:] = []
                    tempcaravanlist.append(bases[checkBaseSelected()].hexnumber)
                    CARAVAN_TOGGLE = 1
                    redraw()

        #hit P for upgrade base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and spectator[0]==0 and UPGRADE_BASE_TOGGLE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].tier != 3 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders != 'Upgrade Base' and bases[checkBaseSelected()].second_orders != 'Upgrade Base' and bases[checkBaseSelected()].third_orders != 'Upgrade Base') and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    UPGRADE_BASE_TOGGLE = 1
                    redraw()             

        #hit S for send resources order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and spectator[0]==0 and SEND_RESOURCES_TOGGLE_ONE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders != 'Send Resources' and bases[checkBaseSelected()].second_orders != 'Send Resources' and bases[checkBaseSelected()].third_orders != 'Send Resources') and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    POTENTIAL_GOLD = 0
                    POTENTIAL_LUMBER = 0
                    POTENTIAL_OIL = 0
                    SEND_RESOURCES_TOGGLE_ONE = 1
                    redraw()

        #hit A for assist construction order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a and spectator[0]==0 and ASSIST_CONSTRUCTION_TOGGLE == 0:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders != 'Assist Construction' and bases[checkBaseSelected()].second_orders != 'Assist Construction' and bases[checkBaseSelected()].third_orders != 'Assist Construction') and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    ASSIST_CONSTRUCTION_TOGGLE = 1
                    redraw()

        #hit M to display caravan map
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                CARAVAN_MAP_TOGGLE = toggle(CARAVAN_MAP_TOGGLE)
                redraw()

        #hit esc to quit
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                QUIT_TOGGLE = 1
                redraw()
                
        #allow for quitting 
        if event.type == QUIT:
            pygame.quit()
            sys.exit()


    


    
    
