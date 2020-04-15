import pygame, sys, time, copy, string
from pygame.locals import *
import csv
import MySQLdb

#DATABASE VARIABLES
host_var="98.113.150.18"
port_var=3306
user_var="alex"
passwd_var="smashblade"
db_var="warcraft"

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
#TYPES
TYPE_GROUND=0
TYPE_AIR=1
TYPE_SEA=2
#BASES
BASE_NAME=0
BASE_HEX=1
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
factiondictionary={0:'Amani',1:'Bleeding Hollow',2:'Black Tooth Grin',3:'Dragonmaw',4:'Stormreaver',5:"Twilight's Hammer",6:'Blackrock',7:'Silvermoon',8:'Aerie Peak',9:'Ironforge',10:'Dalaran',11:'Kul Tiras',12:'Stromgarde',13:'Azeroth',14:'Lordaeron',15:'Gilneas',16:'Alterac',17:'Dark Iron',18:'Burning Blade',19:'Frostwolf',20:'Dalaran Rebel',21:'Gilnean Rebel',22:'Firetree',23:'Smolderthorn',24:'Shadowpine',25:'Shadowglen',26:'Revantusk',27:'Mossflayer',28:'Witherbark',29:'Vilebranch',30:'Dragon',31:'Demon'}
replacedictionary={"'":"", " ":""}
categorylist=[CATEGORY_EXTERIOR_SIEGE,CATEGORY_RANGED,CATEGORY_MELEE,CATEGORY_INTERIOR_SIEGE]#this can be replaced by just a loop through the numbers, but change it elsewhere before deleting
allfactions=[0,5,5,5,5,5,5,6,6,7,15,9,10,15,15,13,14,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
allunits=[]
allorders=[]
allspecialorders=[]
alleconomicactions=[]
hexsidelimitchecks=[]
allhexes=[]
allroads=[]
allbases=[]
allbuildables=[]
allvision=[]
allcurrentfaction=[]
allcurrentturn=[]
tempcaravanlist=[]
currentfaction=-1
turnstatus=-1
errormessagetext=['Errors: ']
successfulmoves=[]
factionoverall='None'
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
allstats={'Grunt':unittype(),'Berserker':unittype(),'Axethrower':unittype(),'Ogre':unittype(),'Catapult':unittype(),'Death Knight':unittype(),'Wave Rider':unittype(),'Turtle':unittype(),'Juggernaut':unittype(),'Horde Transport':unittype(),'Dragon':unittype(),'Raider':unittype(),'Shaman':unittype(),'Warlock':unittype(),'Footman':unittype(),'Archer':unittype(),'Knight':unittype(),'Ballista':unittype(),'Mage':unittype(),'Destroyer':unittype(),'Submarine':unittype(),'Battleship':unittype(),'Alliance Transport':unittype(),'Gryphon':unittype(),'Dwarf':unittype(),'Swordsman':unittype(),'Wildhammer Shaman':unittype(),'Rogue':unittype(),'Skeleton':unittype(),'Demon':unittype(),'Elemental':unittype(),"Zul'jin":unittype(),'Kilrogg Deadeye':unittype(),'Rend Blackhand':unittype(),'Maim Blackhand':unittype(),'Zuluhed the Whacked':unittype(),"Gul'dan the Deceiver":unittype(),"Cho'gall":unittype(),'Orgrim Doomhammer':unittype(),'Varok Saurfang':unittype(),'Alleria Windrunner':unittype(),'Sylvanas Windrunner':unittype(),'Kurdran Wildhammer':unittype(),'Maz Drachrip':unittype(),'Magni Bronzebeard':unittype(),'Muradin Bronzebeard':unittype(),'Archmage Antonidas':unittype(),'Archmage Khadgar':unittype(),'Daelin Proudmoore':unittype(),'Derek Proudmoore':unittype(),'Thoras Trollbane':unittype(),'Danath Trollbane':unittype(),'Anduin Lothar':unittype(),'Turalyon':unittype(),'Uther the Lightbringer':unittype(),'Terenas Menethil':unittype(),'Genn Greymane':unittype(),'Darius Crowley':unittype(),'Aiden Perenolde':unittype(),'Lord Falconcrest':unittype(),'Dagran Thaurissan':unittype(),"Drek'thar":unittype(),'Nazgrel':unittype(),'Alexstrasza':unittype(),}
unitsdict={0:'Grunt',1:'Berserker',2:'Axethrower',3:'Ogre',4:'Catapult',5:'Death Knight',6:'Wave Rider',7:'Turtle',8:'Juggernaut',9:'Horde Transport',10:'Dragon',11:'Raider',12:'Shaman',13:'Warlock',14:'Footman',15:'Archer',16:'Knight',17:'Ballista',18:'Mage',19:'Destroyer',20:'Submarine',21:'Battleship',22:'Alliance Transport',23:'Gryphon',24:'Dwarf',25:'Swordsman',26:'Wildhammer Shaman',27:'Rogue',28:'Skeleton',29:'Demon',30:'Elemental'}
# method to load DB
def load_db():
    return MySQLdb.connect(host=host_var,
                           port=port_var,
                           user=user_var,
                           passwd=passwd_var,
                           db=db_var)
    
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

    unitstats_cur.close()

    unitdata_cur = db.cursor()
    unitdata_cur.execute("SELECT * FROM currentunits")
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
            if 0<=y<4 or y==8 or y>8:
                allunits[count].append(int((x[y])))#upload
            else:
                allunits[count].append((x[y]))
        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
        count=count+1
    unitdata_cur.close()
    db.close()
     
def loadsavedmap():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currenthexes")
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
    
def loadsavedbases():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currentbases")
    basedata = cur.fetchall()
    
    for x in basedata:
        templist=[]
        templist.append(x[0])
        for y in range(1,len(x)):
            templist.append(int(x[y]))
        allbases.append(templist)

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

def loadcurrentvision():
    db = load_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM currentvision")
    visiondata = cur.fetchall()
    count=0
    for x in visiondata:
        visionstring = str(x)
        strippedstring = visionstring[1:-3]
        allvision.append(strippedstring)

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
#moveChecker functions
def movechecker():##road moves into combat?
    for x in range(len(allorders)):
        successfulmoves.append([])
        successfulmoves[x].append(allorders[x][0])
    for x in range(len(allunits)):#prevent units from entering combats the same turn they started in one
        if len(buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION])))>1:
            #print 'combat found'
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
                            #print 'hexone: ',hexone
                            #print 'hextwo: ',hextwo
                            #print 'combatmove: ',combatmove
                            #print 'hexside limit for new check is: ',hexsidelimit(hexone,hextwo,combatmove)
                            newcheck.append(y)
                            hexsidelimitchecks.append(newcheck)
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
            #print 'Hexside limit remaining: ',Fchecks[y][2]
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
        hexsideControlSweep()
    #print successfulmoves
    #print errormessagetext
    ##reset any local stuff used
    #for x in successfulmoves:
        #allorders.append(x)
            
def Adjacent(one,two):
    result=one-two
    #print result
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
    #print 'HEXSIDETERRAIN() result:',terrain
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
    sideterrain=HexsideTerrain(one,two)
    errormessagetextcopy=[]
    errormessagetextcopy=copy.deepcopy(errormessagetext)
    #print 'Hexside terrain:',sideterrain
    if ((allunits[unit][UNIT_TYPE]==TYPE_GROUND) and (terrain=='F' or terrain=='M' or terrain=='S' or terrain=='C' or terrain=='R' or terrain=='W') and (sideterrain=='F' or sideterrain=='M' or sideterrain=='S' or sideterrain=='C' or sideterrain=='R' or sideterrain=='W')):
        move=1
    if (allunits[unit][UNIT_TYPE]==TYPE_SEA) and ((allhexes[one][HEX_TERRAIN]=='O' and (terrain=='O' or terrain=='C')) or (allhexes[one][HEX_TERRAIN]=='C' and terrain=='O')) and (sideterrain=='O' or sideterrain=='K'):
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
    if errormessagetext==errormessagetextcopy:
        errormessagetext.append(' Unit cannot make this move because of terrain. ')
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
    if int(combat)==0 and int(road)==1:
        limit=limit+1
    #print 'hexside limit: ',limit
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

#function to establish font
def establishFont(size):
    font_preferences = ["Sherwood", "CloisterBlack BT", "GoudyHandtooled BT", "Cornerstone", "Allegro", "EngraversGothic BT"]
    available = pygame.font.get_fonts()
    choices = map(lambda x:x.lower().replace(' ', ''), font_preferences)
    for choice in choices:
        if choice in available:
            return pygame.font.SysFont(choice, size)
    return pygame.font.Font(None, size)

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

#function to replace spaces and apostrophes from string literals
def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

#function to determine transport capacity
def transportCapacity(one, two, three):
    capacity = 0
    if one != -1:
        capacity = capacity + 1
    if two != -1:
        capacity = capacity + 1
    if three != -1:
        capacity = capacity + 1
    return capacity
        
#function to determine x coordinate of given hexside
def hexToX(hex):

    xoffset = 60
    xshift = 168
    xunit = ((columnID(hex) - 1) * xshift) + xoffset
    return xunit

#function to determine y coordinate of given hexside
def hexToY(hex):
    
    yoffsetodd = 177
    yoffseteven = 274
    yshift = 194
    if oddOrEven(hex) == 1:
        yunit = (((hex - ((((columnID(hex) - 1) / 2) * 38) + (((columnID(hex) - 1) / 2) * 39))) - 1) * yshift) + yoffsetodd
    elif oddOrEven(hex) == 0:
        yunit = (((hex - ((((columnID(hex) / 2) - 1) * 38) + ((columnID(hex) / 2) * 39))) - 1) * yshift) + yoffseteven
    return yunit

#x coordinate for minimap
def miniMapX(hex):

    resXmini = (float(resolution.current_w) / float(1366))
    xoffset = int(1006 * resXmini)
    xshift = int(13 * resXmini)
    xunit = ((columnID(hex) - 1) * xshift) + xoffset
    return xunit

#y coordinate for minimap
def miniMapY(hex):

    resYmini = (float(resolution.current_h) / float(768))
    yoffsetodd = int(8 * resYmini)
    yoffseteven = int(13 * resYmini)
    yshift = int(10 * resYmini)
    if oddOrEven(hex) == 1:
        yunit = (((hex - ((((columnID(hex) - 1) / 2) * 38) + (((columnID(hex) - 1) / 2) * 39))) - 1) * yshift) + yoffsetodd
        if yunit > int(378 * resYmini):
            yunit = int(378 * resYmini)
    elif oddOrEven(hex) == 0:
        yunit = (((hex - ((((columnID(hex) / 2) - 1) * 38) + ((columnID(hex) / 2) * 39))) - 1) * yshift) + yoffseteven
        if yunit > int(373 * resYmini):
            yunit = int(373 * resYmini)
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

    pygame.draw.polygon(windowSurface, BLACK, ((xleft, ymid), (xmidleft, ytop), (xmidright, ytop), (xright, ymid), (xmidright, ybottom), (xmidleft, ybottom)))

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
    if xsmoothed < -3400:
        xsmoothed = -3400
    if ysmoothed > 0:
        ysmoothed = 0
    if ysmoothed < -6300:
        ysmoothed = -6300
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
        rect.left = 1005 * resX
        rect.top = (600 + (order * 25)) * resY
    if order >= 6:
        rect.left = 1205 * resX
        rect.top = (600 + (order * 25 - 150)) * resY
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

def updateBaseOrderString(baseID, ordertype, ordernumber=0, resource=0, unittype='None', targetbase='None', goldsent=0, lumbersent=0, oilsent=0):
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
            bases[baseID].first_orders = 'Give Base'
        elif ordernumber == 2:
            bases[baseID].second_orders = 'Give Base'
        elif ordernumber == 3:
            bases[baseID].third_orders = 'Give Base'
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

def findBaseImage(baseID):
    if bases[baseID].overallfaction == 'Horde':
        if bases[baseID].tier == 1:
            return 'HordeGreatHallOrigImage'
        if bases[baseID].tier == 2:
            return 'HordeStrongholdOrigImage'
        if bases[baseID].tier == 3:
            return 'HordeFortressOrigImage'
    elif bases[baseID].overallfaction == 'Alliance':
        if bases[baseID].tier == 1:
            return 'AllianceTownHallOrigImage'
        if bases[baseID].tier == 2:
            return 'AllianceKeepOrigImage'
        if bases[baseID].tier == 3:
            return 'AllianceCastleOrigImage'     
                    
xcord = 0
ycord = 0
# resX = 1
# resY = 1        

def redraw():

    #update hexSurfaces
    for i in range(1116):
        hexSurfaces[i] = (pygame.Rect((hexToX(i) - 60) + xcord, (hexToY(i) - 70) + ycord, 130, 150))

    #update units per hex
    unitsPer = [ 0 for i in range(1116) ]
    for j in range(len(units)):
        unitsPer[units[j].hexnumber] = unitsPer[units[j].hexnumber] + 1

    #update resource tracking
    SEND_GOLD_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, GOLD)
    SEND_GOLD_TWO_TEXTrect = SEND_GOLD_TWO_TEXT.get_rect()
    SEND_GOLD_TWO_TEXTrect.left = 1005 * resX
    SEND_GOLD_TWO_TEXTrect.top = 675 * resY

    SEND_LUMBER_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, GOLD)
    SEND_LUMBER_TWO_TEXTrect = SEND_LUMBER_TWO_TEXT.get_rect()
    SEND_LUMBER_TWO_TEXTrect.left = 1005 * resX
    SEND_LUMBER_TWO_TEXTrect.top = 675 * resY

    SEND_OIL_TWO_TEXT = menuFont.render(str(RESOURCE_COUNTER), True, GOLD)
    SEND_OIL_TWO_TEXTrect = SEND_OIL_TWO_TEXT.get_rect()
    SEND_OIL_TWO_TEXTrect.left = 1005 * resX
    SEND_OIL_TWO_TEXTrect.top = 675 * resY
    
    #redraw map
    windowSurface.blit(mapImage, (xcord, ycord))

    #redraw bases
    for i in range(len(bases)):
        bases[i].area = (pygame.Rect(hexToX(bases[i].hexnumber) - 60 + xcord, hexToY(bases[i].hexnumber) - 60 + ycord, BASE_WIDTH, BASE_LENGTH))
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 1:
            windowSurface.blit(HordeGreatHallImage, bases[i].area)
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 2:
            windowSurface.blit(HordeStrongholdImage, bases[i].area)
        if bases[i].overallfaction == 'Horde' and bases[i].tier == 3:
            windowSurface.blit(HordeFortressImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 1:
            windowSurface.blit(AllianceTownHallImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 2:
            windowSurface.blit(AllianceKeepImage, bases[i].area)
        if bases[i].overallfaction == 'Alliance' and bases[i].tier == 3:
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
                    
    #redraw units
    for i in range(len(units)):
        units[i].area = (pygame.Rect(hexToX(units[i].hexnumber) + xcord, hexToY(units[i].hexnumber) + ycord, UNIT_WIDTH, UNIT_LENGTH))
        if unitsPer[units[i].hexnumber] == 1:
            units[i].area = units[i].area.move(-50, 60)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 2:
            units[i].area = units[i].area.move(-10, 60)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 3:
            units[i].area = units[i].area.move(30, 60)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 4:
            units[i].area = units[i].area.move(-50, 20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 5:
            units[i].area = units[i].area.move(-10, 20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 6:
            units[i].area = units[i].area.move(30, 20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 7:
            units[i].area = units[i].area.move(-50, -20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 8:
            units[i].area = units[i].area.move(-10, -20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
        if unitsPer[units[i].hexnumber] == 9:
            units[i].area = units[i].area.move(30, -20)
            unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
            windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
            windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area) 

    #update fog of war (if toggled)
    if FOG_TOGGLE == 1:
        for i in range(len(fogOfWarList)):
            fogOfWar(fogOfWarList[i])

    #update and draw arrows
    if ARROWS_TOGGLE == 0:
        for i in range(len(allorders)):
            if len(allorders[i]) > 1:
                pygame.draw.line(windowSurface, BLACK, (units[allorders[i][0]].area.centerx, units[allorders[i][0]].area.centery), (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), 3) 
                pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), 5, 0)
                if len(allorders[i]) > 2:
                    pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][1]].centerx, hexSurfaces[allorders[i][1]].centery), (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), 3) 
                    pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), 5, 0)
                    if len(allorders[i]) > 3:
                        pygame.draw.line(windowSurface, BLACK, (hexSurfaces[allorders[i][2]].centerx, hexSurfaces[allorders[i][2]].centery), (hexSurfaces[allorders[i][3]].centerx, hexSurfaces[allorders[i][3]].centery), 3) 
                        pygame.draw.circle(windowSurface, LIME, (hexSurfaces[allorders[i][3]].centerx, hexSurfaces[allorders[i][3]].centery), 5, 0)
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
    if GIVE_BASE_TOGGLE == 1:
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
    elif CARAVAN_TOGGLE == 1:
        windowSurface.blit(CARAVAN_ONE_TEXT, CARAVAN_ONE_TEXTrect)
        windowSurface.blit(CARAVAN_TWO_TEXT, CARAVAN_TWO_TEXTrect)
        windowSurface.blit(CARAVAN_THREE_TEXT, CARAVAN_THREE_TEXTrect)
        if len(tempcaravanlist) > 1:
            for i in range(len(tempcaravanlist) - 1):
                pygame.draw.line(windowSurface, BLUE, (hexSurfaces[tempcaravanlist[i]].centerx, hexSurfaces[tempcaravanlist[i]].centery), (hexSurfaces[tempcaravanlist[i + 1]].centerx, hexSurfaces[tempcaravanlist[i + 1]].centery), 3) 
                pygame.draw.circle(windowSurface, LIME, (hexSurfaces[tempcaravanlist[i + 1]].centerx, hexSurfaces[tempcaravanlist[i + 1]].centery), 5, 0)                
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
    elif checkSelected() == -1 and checkBaseSelected() == -1:
        windowSurface.blit(MENU_ONE_TEXT, MENU_ONE_TEXTrect)
        windowSurface.blit(MENU_TWO_TEXT, MENU_TWO_TEXTrect)
        windowSurface.blit(MENU_THREE_TEXT, MENU_THREE_TEXTrect)
        if turnstatus==1:
            windowSurface.blit(MENU_FOUR_ALT_TEXT, MENU_FOUR_ALT_TEXTrect)
        else:
            windowSurface.blit(MENU_FOUR_TEXT, MENU_FOUR_TEXTrect)
        windowSurface.blit(MENU_FIVE_TEXT, MENU_FIVE_TEXTrect)
        windowSurface.blit(MENU_SIX_TEXT, MENU_SIX_TEXTrect)
    elif checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction:
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
    elif checkSelected() != -1 and units[checkSelected()].faction == currentfaction:
        windowSurface.blit(UNIT_ONE_TEXT, UNIT_ONE_TEXTrect)
        windowSurface.blit(UNIT_TWO_TEXT, UNIT_TWO_TEXTrect)
        windowSurface.blit(UNIT_THREE_TEXT, UNIT_THREE_TEXTrect)
        windowSurface.blit(UNIT_FOUR_TEXT, UNIT_FOUR_TEXTrect)  

    #redraw minimap
    windowSurface.blit(miniMapImage, miniMap)

    #redraw minimap fog (if toggled)
    if FOG_TOGGLE == 1:
        for i in range(len(fogOfWarList)):
            fogMiniMap(fogOfWarList[i])

    #draw white square in miniMap
    pygame.draw.rect(windowSurface, WHITE, ((1003 - xcord/13) * resX, (0 - ycord/19.5) * resY, 75 * resX, 40 * resY), 2)

    #redraw menu lines
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (0 * resY)), ((1001 * resX), (1000 * resY)), 3)
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (375 * resY)), ((1400 * resX), (375 * resY)), 7)
    pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (593 * resY)), ((1400 * resX), (593 * resY)), 7)

    #if base selected, display base menu
    if checkBaseSelected() != -1:

        BASE_BACKGROUND_RECT = pygame.Rect((1010 * resX), (385 * resY), (200 * resX), (200 * resY))
        BASE_PORTRAIT_RECT = pygame.Rect((1035 * resX), (410 * resY), (200 * resX), (200 * resY))

        BASE_NAME_TEXT = menuFont.render(bases[checkBaseSelected()].name, True, GOLD)
        BASE_NAME_TEXTrect = BASE_NAME_TEXT.get_rect()
        BASE_NAME_TEXTrect.left = 1225 * resX
        BASE_NAME_TEXTrect.top = 390 * resY

        BASE_FACTION_TEXT = statsFont.render(factionString(bases[checkBaseSelected()].faction), True, GOLD)
        BASE_FACTION_TEXTrect = BASE_FACTION_TEXT.get_rect()
        BASE_FACTION_TEXTrect.left = 1225 * resX
        BASE_FACTION_TEXTrect.top = 415 * resY

        BASE_GOLD_TEXT = statsFont.render('Gold: ' + str(bases[checkBaseSelected()].gold), True, GOLD)
        BASE_GOLD_TEXTrect = BASE_GOLD_TEXT.get_rect()
        BASE_GOLD_TEXTrect.left = 1225 * resX
        BASE_GOLD_TEXTrect.top = 430 * resY

        BASE_LUMBER_TEXT = statsFont.render('Lumber: ' + str(bases[checkBaseSelected()].lumber), True, GOLD)
        BASE_LUMBER_TEXTrect = BASE_LUMBER_TEXT.get_rect()
        BASE_LUMBER_TEXTrect.left = 1225 * resX
        BASE_LUMBER_TEXTrect.top = 445 * resY

        BASE_OIL_TEXT = statsFont.render('Oil: ' + str(bases[checkBaseSelected()].oil), True, GOLD)
        BASE_OIL_TEXTrect = BASE_OIL_TEXT.get_rect()
        BASE_OIL_TEXTrect.left = 1225 * resX
        BASE_OIL_TEXTrect.top = 460 * resY

        BASE_ORDERS_TEXT = statsFont.render('Base Orders (1):', True, GOLD)
        BASE_ORDERS_TEXTrect = BASE_ORDERS_TEXT.get_rect()
        BASE_ORDERS_TEXTrect.left = 1225 * resX
        BASE_ORDERS_TEXTrect.top = 490 * resY

        BASE_ORDERS_TWO_TEXT = statsFont.render(bases[checkBaseSelected()].first_orders, True, GOLD)
        BASE_ORDERS_TWO_TEXTrect = BASE_ORDERS_TWO_TEXT.get_rect()
        BASE_ORDERS_TWO_TEXTrect.left = 1225 * resX
        BASE_ORDERS_TWO_TEXTrect.top = 505 * resY

        BASE_ORDERS_THREE_TEXT = statsFont.render('Base Orders (2):', True, GOLD)
        BASE_ORDERS_THREE_TEXTrect = BASE_ORDERS_THREE_TEXT.get_rect()
        BASE_ORDERS_THREE_TEXTrect.left = 1225 * resX
        BASE_ORDERS_THREE_TEXTrect.top = 520 * resY

        BASE_ORDERS_FOUR_TEXT = statsFont.render(bases[checkBaseSelected()].second_orders, True, GOLD)
        BASE_ORDERS_FOUR_TEXTrect = BASE_ORDERS_FOUR_TEXT.get_rect()
        BASE_ORDERS_FOUR_TEXTrect.left = 1225 * resX
        BASE_ORDERS_FOUR_TEXTrect.top = 535 * resY

        BASE_ORDERS_FIVE_TEXT = statsFont.render('Base Orders (3):', True, GOLD)
        BASE_ORDERS_FIVE_TEXTrect = BASE_ORDERS_FIVE_TEXT.get_rect()
        BASE_ORDERS_FIVE_TEXTrect.left = 1225 * resX
        BASE_ORDERS_FIVE_TEXTrect.top = 550 * resY

        BASE_ORDERS_SIX_TEXT = statsFont.render(bases[checkBaseSelected()].third_orders, True, GOLD)
        BASE_ORDERS_SIX_TEXTrect = BASE_ORDERS_SIX_TEXT.get_rect()
        BASE_ORDERS_SIX_TEXTrect.left = 1225 * resX
        BASE_ORDERS_SIX_TEXTrect.top = 565 * resY

        windowSurface.blit(eval(factionString(bases[checkBaseSelected()].faction).replace(' ','')+'BackgroundImage'), BASE_BACKGROUND_RECT)
        windowSurface.blit(eval(findBaseImage(checkBaseSelected())), BASE_PORTRAIT_RECT)
        windowSurface.blit(BASE_NAME_TEXT, BASE_NAME_TEXTrect)
        windowSurface.blit(BASE_FACTION_TEXT, BASE_FACTION_TEXTrect)
        windowSurface.blit(BASE_GOLD_TEXT, BASE_GOLD_TEXTrect)
        windowSurface.blit(BASE_LUMBER_TEXT, BASE_LUMBER_TEXTrect)
        windowSurface.blit(BASE_OIL_TEXT, BASE_OIL_TEXTrect)
        if 'Caravan' in bases[checkBaseSelected()].first_orders or 'Caravan' in bases[checkBaseSelected()].second_orders or 'Caravan' in bases[checkBaseSelected()].third_orders:
            for i in range(len(alleconomicactions)):
                if alleconomicactions[i][1] == bases[checkBaseSelected()].hexnumber:
                    for j in range(len(alleconomicactions[i][2])- 1):
                        pygame.draw.line(windowSurface, BLUE, (hexSurfaces[alleconomicactions[i][2][j]].centerx, hexSurfaces[alleconomicactions[i][2][j]].centery), (hexSurfaces[alleconomicactions[i][2][j + 1]].centerx, hexSurfaces[alleconomicactions[i][2][j + 1]].centery), 3) 
                        pygame.draw.circle(windowSurface, LIME, (hexSurfaces[alleconomicactions[i][2][j + 1]].centerx, hexSurfaces[alleconomicactions[i][2][j + 1]].centery), 5, 0)
                           
        if bases[checkBaseSelected()].faction == currentfaction:
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

        FACTION_TEXT = statsFont.render(factionString(units[checkSelected()].faction), True, GOLD)
        FACTION_TEXTrect = FACTION_TEXT.get_rect()
        FACTION_TEXTrect.left = 1225 * resX
        FACTION_TEXTrect.top = 400 * resY

        UNIT_TEXT = statsFont.render(units[checkSelected()].unitType, True, GOLD)
        UNIT_TEXTrect = UNIT_TEXT.get_rect()
        UNIT_TEXTrect.left = 1225 * resX
        UNIT_TEXTrect.top = 415 * resY

        HP_TEXT = statsFont.render('HP: ' + str(units[checkSelected()].HP) + ' / ' + str(units[checkSelected()].maxHP), True, GOLD)
        HP_TEXTrect = HP_TEXT.get_rect()
        HP_TEXTrect.left = 1225 * resX
        HP_TEXTrect.top = 455 * resY

        COMBAT_TEXT = statsFont.render('Combat: ' + str(units[checkSelected()].combat), True, GOLD)
        COMBAT_TEXTrect = COMBAT_TEXT.get_rect()
        COMBAT_TEXTrect.left = 1225 * resX
        COMBAT_TEXTrect.top = 470 * resY

        VISION_TEXT = statsFont.render('Vision: ' + str(units[checkSelected()].vision), True, GOLD)
        VISION_TEXTrect = VISION_TEXT.get_rect()
        VISION_TEXTrect.left = 1225 * resX
        VISION_TEXTrect.top = 485 * resY

        MOVES_TEXT = statsFont.render('Moves: ' + str(units[checkSelected()].movesleft), True, GOLD)
        MOVES_TEXTrect = MOVES_TEXT.get_rect()
        MOVES_TEXTrect.left = 1225 * resX
        MOVES_TEXTrect.top = 500 * resY

        CATEGORY_TEXT = statsFont.render('Category: ' + categoryToString(units[checkSelected()].category), True, GOLD)
        CATEGORY_TEXTrect = CATEGORY_TEXT.get_rect()
        CATEGORY_TEXTrect.left = 1225 * resX
        CATEGORY_TEXTrect.top = 515 * resY

        ORDERS_TEXT = statsFont.render('Orders:', True, GOLD)
        ORDERS_TEXTrect = ORDERS_TEXT.get_rect()
        ORDERS_TEXTrect.left = 1225 * resX
        ORDERS_TEXTrect.top = 550 * resY

        ORDERS_TWO_TEXT = statsFont.render(units[checkSelected()].orders, True, GOLD)
        ORDERS_TWO_TEXTrect = ORDERS_TWO_TEXT.get_rect()
        ORDERS_TWO_TEXTrect.left = 1225 * resX
        ORDERS_TWO_TEXTrect.top = 565 * resY

        windowSurface.blit(eval(factionString(units[checkSelected()].faction).replace(' ','')+'BackgroundImage'), UNIT_BACKGROUND_RECT)
        windowSurface.blit(eval(replace_all(units[checkSelected()].unitType, replacedictionary)+'UnitImage'), UNIT_PORTRAIT_RECT)
        windowSurface.blit(FACTION_TEXT, FACTION_TEXTrect)
        windowSurface.blit(UNIT_TEXT, UNIT_TEXTrect)
        windowSurface.blit(HP_TEXT, HP_TEXTrect)
        windowSurface.blit(COMBAT_TEXT, COMBAT_TEXTrect)
        windowSurface.blit(VISION_TEXT, VISION_TEXTrect)
        windowSurface.blit(MOVES_TEXT, MOVES_TEXTrect)
        windowSurface.blit(CATEGORY_TEXT, CATEGORY_TEXTrect)
        if units[checkSelected()].faction == currentfaction:
            windowSurface.blit(ORDERS_TEXT, ORDERS_TEXTrect)
            windowSurface.blit(ORDERS_TWO_TEXT, ORDERS_TWO_TEXTrect)

loadsavedunits()
loadsavedmap()
loadroads()
loadsavedbases()
loadcurrentbuildables()
loadcurrentvision()

#load current faction information
loadcurrentfaction()
currentfaction = int(allcurrentfaction[0][0])

#load current turn information
loadturnstatus()
turnstatus = int(allcurrentturn[0][0])

InitSetStuff()
reset()
hexsideControlSweep()
backupallunits=copy.deepcopy(allunits)
backupallhexes=copy.deepcopy(allhexes)

#initialize pygame
pygame.init()

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

#set up fonts
basicFont = establishFont(48)
menuFont = establishFont(24)
statsFont = establishFont(16)

#allow for extended key pressdown
pygame.key.set_repeat(10, 10)

#resolution test
resolution = pygame.display.Info()

#set up window variables
WINDOW_WIDTH = 0
WINDOW_LENGTH = 0
resX = (float(resolution.current_w) / float(1366))
resY = (float(resolution.current_h) / float(768))

#set up window
windowSurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_LENGTH), 0, 32)
# windowSurface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, 32)
pygame.display.set_caption('Warcraft World Map')

#set up map images and stretch to window
mapImage = pygame.image.load('images/mainmap.jpg')
miniMap_Image = pygame.image.load('images/minimap.jpg')
mapStretchedImage = pygame.transform.scale(mapImage, (1000, 1000))
miniMapImage = pygame.transform.scale(miniMap_Image, (int(375 * resX), int(375 * resY)))

#set up menu image
rightMenu_Image = pygame.image.load('images/rightmenu.jpg')
rightMenuImage = pygame.transform.scale(rightMenu_Image, (int(500 * resX), int(1000 * resY)))

#generate clickable hex rect surfaces
hexSurfaces = []
for i in range(1116):
    hexSurfaces.append(pygame.Rect(hexToX(i) - 60, hexToY(i) - 70, 130, 150))

#declare current faction
# currentfaction = int(allcurrentfaction[0][0])

#set up defaults
UNIT_WIDTH = 30
UNIT_LENGTH = 30
BASE_WIDTH = 120
BASE_LENGTH = 120
EXPANSION_WIDTH = 120
EXPANSION_LENGTH = 120
EXPANSION_X_OFFSET = 55
EXPANSION_Y_OFFSET = 55
POTENTIAL_GOLD = 0
POTENTIAL_LUMBER = 0
POTENTIAL_OIL = 0
RESOURCE_COUNTER = 0

#load unit images
AlexstraszaUnitImage = pygame.image.load('images/Units/alexstrasza.png')
AlexstraszaImage = pygame.transform.scale(AlexstraszaUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AlleriaWindrunnerUnitImage = pygame.image.load('images/Units/alleria.png')
AlleriaWindrunnerImage = pygame.transform.scale(AlleriaWindrunnerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AllianceTransportUnitImage = pygame.image.load('images/Units/alliancetransport.png')
AllianceTransportImage = pygame.transform.scale(AllianceTransportUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArchmageAntonidasUnitImage = pygame.image.load('images/Units/antonidas.png')
ArchmageAntonidasImage = pygame.transform.scale(ArchmageAntonidasUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArcherUnitImage = pygame.image.load('images/Units/archer.png')
ArcherImage = pygame.transform.scale(ArcherUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AxethrowerUnitImage = pygame.image.load('images/Units/axethrower.png')
AxethrowerImage = pygame.transform.scale(AxethrowerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BallistaUnitImage = pygame.image.load('images/Units/ballista.png')
BallistaImage = pygame.transform.scale(BallistaUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BattleshipUnitImage = pygame.image.load('images/Units/battleship.png')
BattleshipImage = pygame.transform.scale(BattleshipUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
BerserkerUnitImage = pygame.image.load('images/Units/berserker.png')
BerserkerImage = pygame.transform.scale(BerserkerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
CatapultUnitImage = pygame.image.load('images/Units/catapult.png')
CatapultImage = pygame.transform.scale(CatapultUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ChogallUnitImage = pygame.image.load('images/Units/chogall.png')
ChogallImage = pygame.transform.scale(ChogallUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DariusCrowleyUnitImage = pygame.image.load('images/Units/crowley.png')
DariusCrowleyImage = pygame.transform.scale(DariusCrowleyUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DaelinProudmooreUnitImage = pygame.image.load('images/Units/daelinproudmoore.png')
DaelinProudmooreImage = pygame.transform.scale(DaelinProudmooreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DanathTrollbaneUnitImage = pygame.image.load('images/Units/danath.png')
DanathTrollbaneImage = pygame.transform.scale(DanathTrollbaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DeathKnightUnitImage = pygame.image.load('images/Units/deathknight.png')
DeathKnightImage = pygame.transform.scale(DeathKnightUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DemonUnitImage = pygame.image.load('images/Units/demon.png')
DemonImage = pygame.transform.scale(DemonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DerekProudmooreUnitImage = pygame.image.load('images/Units/derekproudmoore.png')
DerekProudmooreImage = pygame.transform.scale(DerekProudmooreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DestroyerUnitImage = pygame.image.load('images/Units/destroyer.png')
DestroyerImage = pygame.transform.scale(DestroyerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
OrgrimDoomhammerUnitImage = pygame.image.load('images/Units/doomhammer.png')
OrgrimDoomhammerImage = pygame.transform.scale(OrgrimDoomhammerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonUnitImage = pygame.image.load('images/Units/dragon.png')
DragonImage = pygame.transform.scale(DragonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DrektharUnitImage = pygame.image.load('images/Units/drekthar.png')
DrektharImage = pygame.transform.scale(DrektharUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DwarfUnitImage = pygame.image.load('images/Units/dwarf.png')
DwarfImage = pygame.transform.scale(DwarfUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WildhammerShamanUnitImage = pygame.image.load('images/Units/dwarfshaman.png')
WildhammerShamanImage = pygame.transform.scale(WildhammerShamanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ElementalUnitImage = pygame.image.load('images/Units/elemental.png')
ElementalImage = pygame.transform.scale(ElementalUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
LordFalconcrestUnitImage = pygame.image.load('images/Units/falconcrest.png')
LordFalconcrestImage = pygame.transform.scale(LordFalconcrestUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
FootmanUnitImage = pygame.image.load('images/Units/footman.png')
FootmanImage = pygame.transform.scale(FootmanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GennGreymaneUnitImage = pygame.image.load('images/Units/greymane.png')
GennGreymaneImage = pygame.transform.scale(GennGreymaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GruntUnitImage = pygame.image.load('images/Units/grunt.png')
GruntImage = pygame.transform.scale(GruntUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GryphonUnitImage = pygame.image.load('images/Units/gryphon.png')
GryphonImage = pygame.transform.scale(GryphonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
GuldantheDeceiverUnitImage = pygame.image.load('images/Units/guldan.png')
GuldantheDeceiverImage = pygame.transform.scale(GuldantheDeceiverUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
HordeTransportUnitImage = pygame.image.load('images/Units/hordetransport.png')
HordeTransportImage = pygame.transform.scale(HordeTransportUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
JuggernautUnitImage = pygame.image.load('images/Units/juggernaut.png')
JuggernautImage = pygame.transform.scale(JuggernautUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ArchmageKhadgarUnitImage = pygame.image.load('images/Units/khadgar.png')
ArchmageKhadgarImage = pygame.transform.scale(ArchmageKhadgarUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KilroggDeadeyeUnitImage = pygame.image.load('images/Units/kilroggdeadeye.png')
KilroggDeadeyeImage = pygame.transform.scale(KilroggDeadeyeUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KnightUnitImage = pygame.image.load('images/Units/knight.png')
KnightImage = pygame.transform.scale(KnightUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
KurdranWildhammerUnitImage = pygame.image.load('images/Units/kurdran.png')
KurdranWildhammerImage = pygame.transform.scale(KurdranWildhammerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AnduinLotharUnitImage = pygame.image.load('images/Units/lothar.png')
AnduinLotharImage = pygame.transform.scale(AnduinLotharUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MageUnitImage = pygame.image.load('images/Units/mage.png')
MageImage = pygame.transform.scale(MageUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MagniBronzebeardUnitImage = pygame.image.load('images/Units/magni.png')
MagniBronzebeardImage = pygame.transform.scale(MagniBronzebeardUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MaimBlackhandUnitImage = pygame.image.load('images/Units/maimblackhand.png')
MaimBlackhandImage = pygame.transform.scale(MaimBlackhandUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MazDrachripUnitImage = pygame.image.load('images/Units/maz.png')
MazDrachripImage = pygame.transform.scale(MazDrachripUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
MuradinBronzebeardUnitImage = pygame.image.load('images/Units/muradin.png')
MuradinBronzebeardImage = pygame.transform.scale(MuradinBronzebeardUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
NazgrelUnitImage = pygame.image.load('images/Units/nazgrel.png')
NazgrelImage = pygame.transform.scale(NazgrelUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
OgreUnitImage = pygame.image.load('images/Units/ogre.png')
OgreImage = pygame.transform.scale(OgreUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
AidenPerenoldeUnitImage = pygame.image.load('images/Units/perenolde.png')
AidenPerenoldeImage = pygame.transform.scale(AidenPerenoldeUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
RaiderUnitImage = pygame.image.load('images/Units/raider.png')
RaiderImage = pygame.transform.scale(RaiderUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
RendBlackhandUnitImage = pygame.image.load('images/Units/rendblackhand.png')
RendBlackhandImage = pygame.transform.scale(RendBlackhandUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
VarokSaurfangUnitImage = pygame.image.load('images/Units/saurfang.png')
VarokSaurfangImage = pygame.transform.scale(VarokSaurfangUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ShamanUnitImage = pygame.image.load('images/Units/shaman.png')
ShamanImage = pygame.transform.scale(ShamanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SkeletonUnitImage = pygame.image.load('images/Units/skeleton.png')
SkeletonImage = pygame.transform.scale(SkeletonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SubmarineUnitImage = pygame.image.load('images/Units/submarine.png')
SubmarineImage = pygame.transform.scale(SubmarineUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SwordsmanUnitImage = pygame.image.load('images/Units/swordsman.png')
SwordsmanImage = pygame.transform.scale(SwordsmanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
SylvanasWindrunnerUnitImage = pygame.image.load('images/Units/sylvanas.png')
SylvanasWindrunnerImage = pygame.transform.scale(SylvanasWindrunnerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TerenasMenethilUnitImage = pygame.image.load('images/Units/terenas.png')
TerenasMenethilImage = pygame.transform.scale(TerenasMenethilUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
DagranThaurissanUnitImage = pygame.image.load('images/Units/thaurissan.png')
DagranThaurissanImage = pygame.transform.scale(DagranThaurissanUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ThorasTrollbaneUnitImage = pygame.image.load('images/Units/thoras.png')
ThorasTrollbaneImage = pygame.transform.scale(ThorasTrollbaneUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TuralyonUnitImage = pygame.image.load('images/Units/turalyon.png')
TuralyonImage = pygame.transform.scale(TuralyonUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
TurtleUnitImage = pygame.image.load('images/Units/turtle.png')
TurtleImage = pygame.transform.scale(TurtleUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
UthertheLightbringerUnitImage = pygame.image.load('images/Units/uther.png')
UthertheLightbringerImage = pygame.transform.scale(UthertheLightbringerUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WarlockUnitImage = pygame.image.load('images/Units/warlock.png')
WarlockImage = pygame.transform.scale(WarlockUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
WaveRiderUnitImage = pygame.image.load('images/Units/waverider.png')
WaveRiderImage = pygame.transform.scale(WaveRiderUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ZuljinUnitImage = pygame.image.load('images/Units/zuljin.png')
ZuljinImage = pygame.transform.scale(ZuljinUnitImage, (UNIT_WIDTH, UNIT_LENGTH))
ZuluhedtheWhackedUnitImage = pygame.image.load('images/Units/zuluhed.png')
ZuluhedtheWhackedImage = pygame.transform.scale(ZuluhedtheWhackedUnitImage, (UNIT_WIDTH, UNIT_LENGTH))

#load faction backgrounds
AeriePeakBackgroundImage = pygame.image.load('images/Backgrounds/aeriepeakBackground.png')
AeriePeakBackground = pygame.transform.scale(AeriePeakBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AlteracBackgroundImage = pygame.image.load('images/Backgrounds/alteracBackground.png')
AlteracBackground = pygame.transform.scale(AlteracBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AmaniBackgroundImage = pygame.image.load('images/Backgrounds/amaniBackground.png')
AmaniBackground = pygame.transform.scale(AmaniBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
AzerothBackgroundImage = pygame.image.load('images/Backgrounds/azerothBackground.png')
AzerothBackground = pygame.transform.scale(AzerothBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BlackrockBackgroundImage = pygame.image.load('images/Backgrounds/blackrockBackground.png')
BlackrockBackground = pygame.transform.scale(BlackrockBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BlackToothGrinBackgroundImage = pygame.image.load('images/Backgrounds/blacktoothgrinBackground.png')
BlackToothGrinBackground = pygame.transform.scale(BlackToothGrinBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BleedingHollowBackgroundImage = pygame.image.load('images/Backgrounds/bleedinghollowBackground.png')
BleedingHollowBackground = pygame.transform.scale(BleedingHollowBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
BurningBladeBackgroundImage = pygame.image.load('images/Backgrounds/burningbladeBackground.png')
BurningBladeBackground = pygame.transform.scale(BurningBladeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DalaranBackgroundImage = pygame.image.load('images/Backgrounds/dalaranBackground.png')
DalaranBackground = pygame.transform.scale(DalaranBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DalaranRebelBackgroundImage = pygame.image.load('images/Backgrounds/dalaranrebelBackground.png')
DalaranRebelBackground = pygame.transform.scale(DalaranRebelBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DarkIronBackgroundImage = pygame.image.load('images/Backgrounds/darkironBackground.png')
DarkIronBackground = pygame.transform.scale(DarkIronBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DemonBackgroundImage = pygame.image.load('images/Backgrounds/demonBackground.png')
DemonBackground = pygame.transform.scale(DemonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonBackgroundImage = pygame.image.load('images/Backgrounds/dragonBackground.png')
DragonBackground = pygame.transform.scale(DragonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
DragonmawBackgroundImage = pygame.image.load('images/Backgrounds/dragonmawBackground.png')
DragonmawBackground = pygame.transform.scale(DragonmawBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
FiretreeBackgroundImage = pygame.image.load('images/Backgrounds/firetreeBackground.png')
FiretreeBackground = pygame.transform.scale(FiretreeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
FrostwolfBackgroundImage = pygame.image.load('images/Backgrounds/frostwolfBackground.png')
FrostwolfBackground = pygame.transform.scale(FrostwolfBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
GilneasBackgroundImage = pygame.image.load('images/Backgrounds/gilneasBackground.png')
GilneasBackground = pygame.transform.scale(GilneasBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
GilneasRebelBackgroundImage = pygame.image.load('images/Backgrounds/gilneasrebelBackground.png')
GilneasRebelBackground = pygame.transform.scale(GilneasRebelBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
IronforgeBackgroundImage = pygame.image.load('images/Backgrounds/ironforgeBackground.png')
IronforgeBackground = pygame.transform.scale(IronforgeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
KulTirasBackgroundImage = pygame.image.load('images/Backgrounds/kultirasBackground.png')
KulTirasBackground = pygame.transform.scale(KulTirasBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
LordaeronBackgroundImage = pygame.image.load('images/Backgrounds/lordaeronBackground.png')
LordaeronBackground = pygame.transform.scale(LordaeronBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
MossflayerBackgroundImage = pygame.image.load('images/Backgrounds/mossflayerBackground.png')
MossflayerBackground = pygame.transform.scale(MossflayerBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
RevantuskBackgroundImage = pygame.image.load('images/Backgrounds/revantuskBackground.png')
RevantuskBackground = pygame.transform.scale(RevantuskBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
ShadowglenBackgroundImage = pygame.image.load('images/Backgrounds/shadowglenBackground.png')
ShadowglenBackground = pygame.transform.scale(ShadowglenBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
ShadowpineBackgroundImage = pygame.image.load('images/Backgrounds/shadowpineBackground.png')
ShadowpineBackground = pygame.transform.scale(ShadowpineBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
SilvermoonBackgroundImage = pygame.image.load('images/Backgrounds/silvermoonBackground.png')
SilvermoonBackground = pygame.transform.scale(SilvermoonBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
SmolderthornBackgroundImage = pygame.image.load('images/Backgrounds/smolderthornBackground.png')
SmolderthornBackground = pygame.transform.scale(SmolderthornBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
StormreaverBackgroundImage = pygame.image.load('images/Backgrounds/stormreaversBackground.png')
StormreaverBackground = pygame.transform.scale(StormreaverBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
StromgardeBackgroundImage = pygame.image.load('images/Backgrounds/stromgardeBackground.png')
StromgardeBackground = pygame.transform.scale(StromgardeBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
TwilightHammerBackgroundImage = pygame.image.load('images/Backgrounds/twilightshammerBackground.png')
TwilightHammerBackground = pygame.transform.scale(TwilightHammerBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
VilebranchBackgroundImage = pygame.image.load('images/Backgrounds/vilebranchBackground.png')
VilebranchBackground = pygame.transform.scale(VilebranchBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))
WitherbarkBackgroundImage = pygame.image.load('images/Backgrounds/witherbarkBackground.png')
WitherbarkBackground = pygame.transform.scale(WitherbarkBackgroundImage, (UNIT_WIDTH, UNIT_LENGTH))

#load flags
#AeriePeakFlagImage = pygame.image.load('images/flags/aeriepeakFLAG.png')
#AeriePeakFlag = pygame.transform.scale(AeriePeakFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#AlteracFlagImage = pygame.image.load('images/flags/alteracFLAG.png')
#AlteracFlag = pygame.transform.scale(AlteracFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#AzerothFlagImage = pygame.image.load('images/flags/azerothFLAG.png')
#AzerothFlag = pygame.transform.scale(AzerothFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#BlackrockFlagImage = pygame.image.load('images/flags/blackrockFLAG.png')
#BlackrockFlag = pygame.transform.scale(BlackrockFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#BlackToothGrinFlagImage = pygame.image.load('images/flags/blacktoothgrinFLAG.png')
#BlackToothGrinFlag = pygame.transform.scale(BlackToothGrinFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#BleedingHollowFlagImage = pygame.image.load('images/flags/bleedinghollowFLAG.png')
#BleedingHollowFlag = pygame.transform.scale(BleedingHollowFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#BurningBladeFlagImage = pygame.image.load('images/flags/burningbladeFLAG.png')
#BurningBladeFlag = pygame.transform.scale(BurningBladeFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#DalaranFlagImage = pygame.image.load('images/flags/dalaranFLAG.png')
#DalaranFlag = pygame.transform.scale(DalaranFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#DalaranRebelFlagImage = pygame.image.load('images/flags/dalaranrebelFLAG.png')
#DalaranRebelFlag = pygame.transform.scale(DalaranRebelFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#DragonmawFlagImage = pygame.image.load('images/flags/dragonmawFLAG.png')
#DragonmawFlag = pygame.transform.scale(DragonmawFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#FrostwolfFlagImage = pygame.image.load('images/flags/frostwolfFLAG.png')
#FrostwolfFlag = pygame.transform.scale(FrostwolfFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#GilneasFlagImage = pygame.image.load('images/flags/gilneasFLAG.png')
#GilneasFlag = pygame.transform.scale(GilneasFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#GilneasRebelFlagImage = pygame.image.load('images/flags/gilneasrebelFLAG.png')
#GilneasRebelFlag = pygame.transform.scale(GilneasRebelFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#IronforgeFlagImage = pygame.image.load('images/flags/ironforgeFLAG.png')
#IronforgeFlag = pygame.transform.scale(IronforgeFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#KulTirasFlagImage = pygame.image.load('images/flags/kultirasFLAG.png')
#KulTirasFlag = pygame.transform.scale(KulTirasFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#LordaeronFlagImage = pygame.image.load('images/flags/lordaeronFLAG.png')
#LordaeronFlag = pygame.transform.scale(LordaeronFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#SilvermoonFlagImage = pygame.image.load('images/flags/silvermoonFLAG.png')
#SilvermoonFlag = pygame.transform.scale(SilvermoonFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#StormreaverFlagImage = pygame.image.load('images/flags/stormreaversFLAG.png')
#StormreaverFlag = pygame.transform.scale(StormreaverFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#StromgardeFlagImage = pygame.image.load('images/flags/stromgardeFLAG.png')
#StromgardeFlag = pygame.transform.scale(StromgardeFlagImage, (UNIT_WIDTH, UNIT_LENGTH))
#TwilightHammerFlagImage = pygame.image.load('images/flags/twilightshammerFLAG.png')
#TwilightHammerFlag = pygame.transform.scale(TwilightHammerFlagImage, (UNIT_WIDTH, UNIT_LENGTH))

#load base images
AllianceTownHallOrigImage = pygame.image.load('images/Buildings/townhall.png')
AllianceTownHallImage = pygame.transform.scale(AllianceTownHallOrigImage, (BASE_WIDTH, BASE_LENGTH))
AllianceKeepOrigImage = pygame.image.load('images/Buildings/keep.png')
AllianceKeepImage = pygame.transform.scale(AllianceKeepOrigImage, (BASE_WIDTH, BASE_LENGTH))
AllianceCastleOrigImage = pygame.image.load('images/Buildings/castle.png')
AllianceCastleImage = pygame.transform.scale(AllianceCastleOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeGreatHallOrigImage = pygame.image.load('images/Buildings/greathall.png')
HordeGreatHallImage = pygame.transform.scale(HordeGreatHallOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeStrongholdOrigImage = pygame.image.load('images/Buildings/stronghold.png')
HordeStrongholdImage = pygame.transform.scale(HordeStrongholdOrigImage, (BASE_WIDTH, BASE_LENGTH))
HordeFortressOrigImage = pygame.image.load('images/Buildings/fortress.png')
HordeFortressImage = pygame.transform.scale(HordeFortressOrigImage, (BASE_WIDTH, BASE_LENGTH))

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

#draw map to window
windowSurface.blit(mapImage, (0, 0))
pygame.display.Info

#set up mapUnit class
class mapUnit:
    def __init__(self, hexnumber, overallfaction, capacity, domain, category, movesleft, movesmax, vision, combat, HP, maxHP, faction, unitType, area, selected, movesMade, destination, orders):
        self.hexnumber = hexnumber
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

#set up mapBase class
class mapBase:
    def __init__(self, name, selected, gold, lumber, oil, hexnumber, faction, tier, area, overallfaction, first_orders, second_orders, third_orders):
        self.name = name
        self.selected = selected
        self.gold = gold
        self.lumber = lumber
        self.oil = oil
        self.hexnumber = hexnumber
        self.faction = faction
        self.tier = tier
        self.area = area
        self.overallfaction = overallfaction
        self.first_orders = first_orders
        self.second_orders = second_orders
        self.third_orders = third_orders
        
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
pygame.draw.rect(windowSurface, WHITE, ((1003 * resX), (0 * resY), (75 * resX), (40 * resY)), 2)

#draw menu lines
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (0 * resY)), ((1001 * resX), (1000 * resY)), 3)
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (375 * resY)), ((1400 * resX), (375 * resY)), 7)
pygame.draw.line(windowSurface, CHOCOLATE, ((1001 * resX), (593 * resY)), ((1400 * resX), (593 * resY)), 7)

#establish menu info
MENU_ONE_TEXT = menuFont.render('Space = Clear moves for selected', True, GOLD)
MENU_ONE_TEXTrect = MENU_ONE_TEXT.get_rect()
MENU_ONE_TEXTrect.left = 1005 * resX
MENU_ONE_TEXTrect.top = 600 * resY

MENU_TWO_TEXT = menuFont.render('T = View all arrows or only selected', True, GOLD)
MENU_TWO_TEXTrect = MENU_TWO_TEXT.get_rect()
MENU_TWO_TEXTrect.left = 1005 * resX
MENU_TWO_TEXTrect.top = 625 * resY

MENU_THREE_TEXT = menuFont.render('U = Switch between unit and faction view', True, GOLD)
MENU_THREE_TEXTrect = MENU_THREE_TEXT.get_rect()
MENU_THREE_TEXTrect.left = 1005 * resX
MENU_THREE_TEXTrect.top = 650 * resY

MENU_FOUR_TEXT = menuFont.render('Enter = Submit moves', True, GOLD)
MENU_FOUR_TEXTrect = MENU_FOUR_TEXT.get_rect()
MENU_FOUR_TEXTrect.left = 1005 * resX
MENU_FOUR_TEXTrect.top = 700 * resY

MENU_FOUR_ALT_TEXT = menuFont.render('Moves have been submitted!', True, RED)
MENU_FOUR_ALT_TEXTrect = MENU_FOUR_ALT_TEXT.get_rect()
MENU_FOUR_ALT_TEXTrect.left = 1005 * resX
MENU_FOUR_ALT_TEXTrect.top = 700 * resY

MENU_FIVE_TEXT = menuFont.render('Esc = Quit', True, GOLD)
MENU_FIVE_TEXTrect = MENU_FIVE_TEXT.get_rect()
MENU_FIVE_TEXTrect.left = 1005 * resX
MENU_FIVE_TEXTrect.top = 725 * resY

MENU_SIX_TEXT = menuFont.render('F = Toggle fog of war', True, GOLD)
MENU_SIX_TEXTrect = MENU_SIX_TEXT.get_rect()
MENU_SIX_TEXTrect.left = 1005 * resX
MENU_SIX_TEXTrect.top = 675 * resY

#establish special order menu info
GIVE_BASE_TEXT = menuFont.render('Left-click viable unit to give base.', True, GOLD)
GIVE_BASE_TEXTrect = GIVE_BASE_TEXT.get_rect()
GIVE_BASE_TEXTrect.left = 1005 * resX
GIVE_BASE_TEXTrect.top = 600 * resY

GIVE_EXPANSION_TEXT_ONE = menuFont.render('Left-click expansion to be given away.', True, GOLD)
GIVE_EXPANSION_TEXT_ONErect = GIVE_EXPANSION_TEXT_ONE.get_rect()
GIVE_EXPANSION_TEXT_ONErect.left = 1005 * resX
GIVE_EXPANSION_TEXT_ONErect.top = 600 * resY

GIVE_EXPANSION_TEXT_TWO = menuFont.render('Left-click target base.', True, GOLD)
GIVE_EXPANSION_TEXT_TWOrect = GIVE_EXPANSION_TEXT_TWO.get_rect()
GIVE_EXPANSION_TEXT_TWOrect.left = 1005 * resX
GIVE_EXPANSION_TEXT_TWOrect.top = 600 * resY

COMMERCE_IN_TEXT = menuFont.render('Left-click resource type to convert.', True, GOLD)
COMMERCE_IN_TEXTrect = COMMERCE_IN_TEXT.get_rect()
COMMERCE_IN_TEXTrect.left = 1005 * resX
COMMERCE_IN_TEXTrect.top = 600 * resY

COMMERCE_OUT_TEXT = menuFont.render('Left-click resource type to receive.', True, GOLD)
COMMERCE_OUT_TEXTrect = COMMERCE_OUT_TEXT.get_rect()
COMMERCE_OUT_TEXTrect.left = 1005 * resX
COMMERCE_OUT_TEXTrect.top = 600 * resY

COMMERCE_GOLD_TEXT = menuFont.render('GOLD', True, GOLD)
COMMERCE_GOLD_TEXTrect = COMMERCE_GOLD_TEXT.get_rect()
COMMERCE_GOLD_TEXTrect.left = 1005 * resX
COMMERCE_GOLD_TEXTrect.top = 650 * resY

COMMERCE_LUMBER_TEXT = menuFont.render('LUMBER', True, FOREST)
COMMERCE_LUMBER_TEXTrect = COMMERCE_LUMBER_TEXT.get_rect()
COMMERCE_LUMBER_TEXTrect.left = 1005 * resX
COMMERCE_LUMBER_TEXTrect.top = 675 * resY

COMMERCE_OIL_TEXT = menuFont.render('OIL', True, GRAY)
COMMERCE_OIL_TEXTrect = COMMERCE_OIL_TEXT.get_rect()
COMMERCE_OIL_TEXTrect.left = 1005 * resX
COMMERCE_OIL_TEXTrect.top = 700 * resY

EXPAND_TEXT = menuFont.render('Left-click hex for expansion', True, GOLD)
EXPAND_TEXTrect = EXPAND_TEXT.get_rect()
EXPAND_TEXTrect.left = 1005 * resX
EXPAND_TEXTrect.top = 600 * resY

CARAVAN_ONE_TEXT = menuFont.render('Left-click hexes to build caravan route,', True, GOLD)
CARAVAN_ONE_TEXTrect = CARAVAN_ONE_TEXT.get_rect()
CARAVAN_ONE_TEXTrect.left = 1005 * resX
CARAVAN_ONE_TEXTrect.top = 600 * resY

CARAVAN_TWO_TEXT = menuFont.render('starting one hex from initial base.', True, GOLD)
CARAVAN_TWO_TEXTrect = CARAVAN_TWO_TEXT.get_rect()
CARAVAN_TWO_TEXTrect.left = 1005 * resX
CARAVAN_TWO_TEXTrect.top = 625 * resY

CARAVAN_THREE_TEXT = menuFont.render('Left-click target base to finish.', True, GOLD)
CARAVAN_THREE_TEXTrect = CARAVAN_THREE_TEXT.get_rect()
CARAVAN_THREE_TEXTrect.left = 1005 * resX
CARAVAN_THREE_TEXTrect.top = 650 * resY

SEND_EXPLANATION_TEXT = menuFont.render('Use up/down arrows to scroll, SPACE to enter.', True, GOLD)
SEND_EXPLANATION_TEXTrect = SEND_EXPLANATION_TEXT.get_rect()
SEND_EXPLANATION_TEXTrect.left = 1005 * resX
SEND_EXPLANATION_TEXTrect.top = 625 * resY

SEND_GOLD_ONE_TEXT = menuFont.render('Enter amount of gold to be sent.', True, GOLD)
SEND_GOLD_ONE_TEXTrect = SEND_GOLD_ONE_TEXT.get_rect()
SEND_GOLD_ONE_TEXTrect.left = 1005 * resX
SEND_GOLD_ONE_TEXTrect.top = 600 * resY

SEND_LUMBER_ONE_TEXT = menuFont.render('Enter amount of lumber to be sent.', True, GOLD)
SEND_LUMBER_ONE_TEXTrect = SEND_LUMBER_ONE_TEXT.get_rect()
SEND_LUMBER_ONE_TEXTrect.left = 1005 * resX
SEND_LUMBER_ONE_TEXTrect.top = 600 * resY

SEND_OIL_ONE_TEXT = menuFont.render('Enter amount of oil to be sent.', True, GOLD)
SEND_OIL_ONE_TEXTrect = SEND_OIL_ONE_TEXT.get_rect()
SEND_OIL_ONE_TEXTrect.left = 1005 * resX
SEND_OIL_ONE_TEXTrect.top = 600 * resY

SEND_RESOURCES_TEXT = menuFont.render('Left-click target base.', True, GOLD)
SEND_RESOURCES_TEXTrect = SEND_RESOURCES_TEXT.get_rect()
SEND_RESOURCES_TEXTrect.left = 1005 * resX
SEND_RESOURCES_TEXTrect.top = 600 * resY

#establish list of units faction could build (currently Lordaeron)
unitBuildList = []
#unitBuildList = ['Footman','Archer','Knight','Ballista','Mage','Destroyer','Submarine','Battleship','Alliance Transport']
validBuildList = []
establishUnitBuildList()

for i in range(len(unitBuildList)):
    validBuildList.append(buildList(unitBuildList[i], unitListArea(unitBuildList[i], i), menuFont.render(unitBuildList[i], True, GOLD)))

#establish base menu info
BASE_ONE_TEXT = statsFont.render('D = Destroy Base', True, GOLD)
BASE_ONE_TEXTrect = BASE_ONE_TEXT.get_rect()
BASE_ONE_TEXTrect.left = 1005 * resX
BASE_ONE_TEXTrect.top = 600 * resY

BASE_TWO_TEXT = statsFont.render('G = Give Base', True, GOLD)
BASE_TWO_TEXTrect = BASE_TWO_TEXT.get_rect()
BASE_TWO_TEXTrect.left = 1005 * resX
BASE_TWO_TEXTrect.top = 615 * resY

BASE_THREE_TEXT = statsFont.render('E = Give Expansion', True, GOLD)
BASE_THREE_TEXTrect = BASE_THREE_TEXT.get_rect()
BASE_THREE_TEXTrect.left = 1005 * resX
BASE_THREE_TEXTrect.top = 630 * resY

BASE_FOUR_TEXT = statsFont.render('H = Harvest', True, GOLD)
BASE_FOUR_TEXTrect = BASE_FOUR_TEXT.get_rect()
BASE_FOUR_TEXTrect.left = 1005 * resX
BASE_FOUR_TEXTrect.top = 645 * resY

BASE_FIVE_TEXT = statsFont.render('C = Commerce', True, GOLD)
BASE_FIVE_TEXTrect = BASE_FIVE_TEXT.get_rect()
BASE_FIVE_TEXTrect.left = 1005 * resX
BASE_FIVE_TEXTrect.top = 660 * resY

BASE_SIX_TEXT = statsFont.render('N = Build Unit', True, GOLD)
BASE_SIX_TEXTrect = BASE_SIX_TEXT.get_rect()
BASE_SIX_TEXTrect.left = 1005 * resX
BASE_SIX_TEXTrect.top = 675 * resY

BASE_SEVEN_TEXT = statsFont.render('X = Expand', True, GOLD)
BASE_SEVEN_TEXTrect = BASE_SEVEN_TEXT.get_rect()
BASE_SEVEN_TEXTrect.left = 1005 * resX
BASE_SEVEN_TEXTrect.top = 690 * resY

BASE_EIGHT_TEXT = statsFont.render('V = Establish Caravan', True, GOLD)
BASE_EIGHT_TEXTrect = BASE_EIGHT_TEXT.get_rect()
BASE_EIGHT_TEXTrect.left = 1005 * resX
BASE_EIGHT_TEXTrect.top = 705 * resY

BASE_NINE_TEXT = statsFont.render('P = Upgrade Base', True, GOLD)
BASE_NINE_TEXTrect = BASE_NINE_TEXT.get_rect()
BASE_NINE_TEXTrect.left = 1005 * resX
BASE_NINE_TEXTrect.top = 720 * resY

BASE_TEN_TEXT = statsFont.render('S = Send Resources', True, GOLD)
BASE_TEN_TEXTrect = BASE_TEN_TEXT.get_rect()
BASE_TEN_TEXTrect.left = 1005 * resX
BASE_TEN_TEXTrect.top = 735 * resY

BASE_ELEVEN_TEXT = statsFont.render('Space = Clear Orders', True, GOLD)
BASE_ELEVEN_TEXTrect = BASE_ELEVEN_TEXT.get_rect()
BASE_ELEVEN_TEXTrect.left = 1005 * resX
BASE_ELEVEN_TEXTrect.top = 750 * resY

#establish unit menu info
UNIT_ONE_TEXT = menuFont.render('Right-click = Set move', True, GOLD)
UNIT_ONE_TEXTrect = UNIT_ONE_TEXT.get_rect()
UNIT_ONE_TEXTrect.left = 1005 * resX
UNIT_ONE_TEXTrect.top = 600 * resY

UNIT_TWO_TEXT = menuFont.render('Space = Clear orders', True, GOLD)
UNIT_TWO_TEXTrect = UNIT_TWO_TEXT.get_rect()
UNIT_TWO_TEXTrect.left = 1005 * resX
UNIT_TWO_TEXTrect.top = 625 * resY

UNIT_THREE_TEXT = menuFont.render('R = Ranged fire (left-click target hex)', True, GOLD)
UNIT_THREE_TEXTrect = UNIT_THREE_TEXT.get_rect()
UNIT_THREE_TEXTrect.left = 1005 * resX
UNIT_THREE_TEXTrect.top = 650 * resY

UNIT_FOUR_TEXT = menuFont.render('B = Board transport (left-click transport)', True, GOLD)
UNIT_FOUR_TEXTrect = UNIT_FOUR_TEXT.get_rect()
UNIT_FOUR_TEXTrect.left = 1005 * resX
UNIT_FOUR_TEXTrect.top = 675 * resY

#check if unit is selected and draw appropriate menu info
windowSurface.blit(MENU_ONE_TEXT, MENU_ONE_TEXTrect)
windowSurface.blit(MENU_TWO_TEXT, MENU_TWO_TEXTrect)
windowSurface.blit(MENU_THREE_TEXT, MENU_THREE_TEXTrect)
if turnstatus==1:
    windowSurface.blit(MENU_FOUR_ALT_TEXT, MENU_FOUR_ALT_TEXTrect)
else:
    windowSurface.blit(MENU_FOUR_TEXT, MENU_FOUR_TEXTrect)
windowSurface.blit(MENU_FIVE_TEXT, MENU_FIVE_TEXTrect)
windowSurface.blit(MENU_SIX_TEXT, MENU_SIX_TEXTrect)

#establish units list
units = []
for i in range(len(allunits)):
    units.append(mapUnit(allunits[i][UNIT_LOCATION], hordeOrAlliance(allunits[i][UNIT_FACTION]), transportCapacity(allunits[i][UNIT_TRANSPORT_ONE], allunits[i][UNIT_TRANSPORT_TWO], allunits[i][UNIT_TRANSPORT_THREE]), allunits[i][UNIT_TYPE], allunits[i][UNIT_CATEGORY], allunits[i][UNIT_MOVEMENT_REMAINING], allunits[i][UNIT_MOVEMENT_MAX], allunits[i][UNIT_VISION], allunits[i][UNIT_COMBAT], allunits[i][UNIT_HIT_POINTS], allunits[i][UNIT_MAX_HIT_POINTS], allunits[i][UNIT_FACTION], allunits[i][UNIT_NAME], (pygame.Rect((hexToX(allunits[i][UNIT_LOCATION]), hexToY(allunits[i][UNIT_LOCATION])), (UNIT_WIDTH, UNIT_LENGTH))), 0, 0, -1, 'None'))

#establish bases list
bases = []
for i in range(len(allbases)):
    bases.append(mapBase(allbases[i][0], 0, allbases[i][BASE_GOLD], allbases[i][BASE_LUMBER], allbases[i][BASE_OIL], allbases[i][1], allbases[i][2], allbases[i][3], (pygame.Rect((hexToX(allbases[i][1]) - 60, hexToY(allbases[i][1]) - 60), (BASE_WIDTH, BASE_LENGTH))), hordeOrAlliance(allbases[i][2]), 'None', isSecondMoveAvailable(allbases[i][BASE_TIER]), isThirdMoveAvailable(allbases[i][BASE_TIER])))

#establish expansions list
expansions = []
counter = 0
for i in range(len(allhexes)):
    if int(allhexes[i][HEX_FARM]) != -1:
        expansions.append(mapExpansion(counter, 'Farm', int(allhexes[i][HEX_FARM]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), hexToOverallFaction(int(allhexes[i][HEX_FARM]))))
    if int(allhexes[i][HEX_MILL]) != -1:
        expansions.append(mapExpansion(counter, 'Mill', int(allhexes[i][HEX_RIG]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), hexToOverallFaction(int(allhexes[i][HEX_MILL]))))
    if int(allhexes[i][HEX_RIG]) != -1:
        expansions.append(mapExpansion(counter, 'Rig', int(allhexes[i][HEX_RIG]), (pygame.Rect((hexToX(counter) - EXPANSION_X_OFFSET, hexToY(counter) - EXPANSION_Y_OFFSET), (EXPANSION_WIDTH, EXPANSION_LENGTH))), hexToOverallFaction(int(allhexes[i][HEX_RIG]))))
    counter = counter + 1

#establish fog of war list
fogOfWarList = []
for i in range(1117):
    fogOfWarList.append(i)
# for i in range(len(allvision[0])):
    # fogOfWarList.remove(int(allvision[0][i]))
for i in range(len(allvision)):
    # print allvision[i]
    fogOfWarList.remove(int(allvision[i]))

#determine units per hex data
unitsPer = [ 0 for i in range(1116) ]
for j in range(len(units)):
    unitsPer[units[j].hexnumber] = unitsPer[units[j].hexnumber] + 1

#draw initial bases
for i in range(len(bases)):
    if bases[i].overallfaction == 'Horde' and bases[i].tier == 1:
        windowSurface.blit(HordeGreatHallImage, bases[i].area)
    if bases[i].overallfaction == 'Horde' and bases[i].tier == 2:
        windowSurface.blit(HordeStrongholdImage, bases[i].area)
    if bases[i].overallfaction == 'Horde' and bases[i].tier == 3:
        windowSurface.blit(HordeFortressImage, bases[i].area)
    if bases[i].overallfaction == 'Alliance' and bases[i].tier == 1:
        windowSurface.blit(AllianceTownHallImage, bases[i].area)
    if bases[i].overallfaction == 'Alliance' and bases[i].tier == 2:
        windowSurface.blit(AllianceKeepImage, bases[i].area)
    if bases[i].overallfaction == 'Alliance' and bases[i].tier == 3:
        windowSurface.blit(AllianceCastleImage, bases[i].area)
        
#draw initial expansions
for i in range(len(expansions)):
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

#draw initial units
for i in range(len(units)):   
    if unitsPer[units[i].hexnumber] == 1:
        units[i].area = units[i].area.move(-50, 60)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 2:
        units[i].area = units[i].area.move(-10, 60)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 3:
        units[i].area = units[i].area.move(30, 60)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 4:
        units[i].area = units[i].area.move(-50, 20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 5:
        units[i].area = units[i].area.move(-10, 20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 6:
        units[i].area = units[i].area.move(30, 20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 7:
        units[i].area = units[i].area.move(-50, -20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 8:
        units[i].area = units[i].area.move(-10, -20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area)
    if unitsPer[units[i].hexnumber] == 9:
        units[i].area = units[i].area.move(30, -20)
        unitsPer[units[i].hexnumber] = unitsPer[units[i].hexnumber] - 1
        windowSurface.blit(eval(factionString(units[i].faction).replace(' ','')+'Background'), units[i].area)
        windowSurface.blit(eval(replace_all(units[i].unitType, replacedictionary)+'Image'), units[i].area) 

#run game loop
clock = pygame.time.Clock()

#establish toggles
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
CARAVAN_TOGGLE = 0
SEND_RESOURCES_TOGGLE_ONE = 0
SEND_RESOURCES_TOGGLE_TWO = 0
SEND_RESOURCES_TOGGLE_THREE = 0
SEND_RESOURCES_TOGGLE_FOUR = 0

while True:
    clock.tick(15)

    #draw window onto screen
    pygame.display.update()

    #responding to player input
    for event in pygame.event.get():  

        #allow for scrolling
        if event.type == pygame.KEYDOWN:
            if SEND_RESOURCES_TOGGLE_ONE == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < 20:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            elif SEND_RESOURCES_TOGGLE_TWO == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < 20:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            elif SEND_RESOURCES_TOGGLE_THREE == 1:
                if event.key == pygame.K_UP:
                    if RESOURCE_COUNTER < 20:
                        RESOURCE_COUNTER += 1
                if event.key == pygame.K_DOWN:
                    if RESOURCE_COUNTER > 0:
                        RESOURCE_COUNTER -= 1
            else:
                if event.key == pygame.K_LEFT:
                    if xcord < 0:
                        xcord += 100
                if event.key == pygame.K_RIGHT:
                    if xcord > -3400:
                        xcord += -100
                if event.key == pygame.K_UP:
                    if ycord < 0:
                        ycord += 100
                if event.key == pygame.K_DOWN:
                    if ycord > -6300:
                        ycord += -100

        #redraw based on scroll
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT or event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                redraw()

        #check for left mouseclick and select if applicable
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #if left click is on miniMap, jump to map location
                if miniMapClickable.collidepoint(pygame.mouse.get_pos()) == 1:
                    a, b = pygame.mouse.get_pos()
                    xcord, ycord = miniMapScale(a,b)
                #if ranged attacking, allow for targeting
                elif RANGED_TOGGLE == 1:
                    for i in range(1116):
                        if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                            allspecialorders.append(["Rangedfire", checkSelected(), i])
                            updateOrderString(checkSelected(), 'Ranged')
                    clearSelected()
                    RANGED_TOGGLE = 0
                #if boarding transport, allow for targeting
                elif BOARD_TRANSPORT_TOGGLE == 1:
                    for i in range(len(units)):
                        if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            if isThereRoom(units[i].capacity) > 0:
                                allspecialorders.append(["Board Transport", checkSelected(), i])
                                updateOrderString(checkSelected(), 'Board Transport')
                    clearSelected()
                    BOARD_TRANSPORT_TOGGLE = 0
                #if giving base, allow for targeting
                elif GIVE_BASE_TOGGLE == 1:
                    for i in range(len(units)):
                        if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            if units[i].hexnumber == bases[checkBaseSelected()].hexnumber:
                                alleconomicactions.append(["Give Base", bases[checkBaseSelected()].hexnumber, i])
                                updateBaseOrderString(checkBaseSelected(), 'Give Base', ordernumber=1)
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
                    if COMMERCE_GOLD_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_GOLD
                    if COMMERCE_LUMBER_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_LUMBER
                    if COMMERCE_OIL_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1:
                        COMMERCE_TOGGLE_TWO = 1
                        POTENTIAL_RESOURCE = BASE_OIL
                    if COMMERCE_TOGGLE_TWO == 0:
                        clearSelected()
                    COMMERCE_TOGGLE_ONE = 0
                elif COMMERCE_TOGGLE_TWO == 1:
                    if COMMERCE_GOLD_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_GOLD:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_GOLD])
                        if bases[checkBaseSelected()].first_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=1, resource=BASE_GOLD)
                        elif bases[checkBaseSelected()].second_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=2, resource=BASE_GOLD)
                        elif bases[checkBaseSelected()].third_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=3, resource=BASE_GOLD)
                    if COMMERCE_LUMBER_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_LUMBER:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_LUMBER])
                        if bases[checkBaseSelected()].first_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=1, resource=BASE_LUMBER)
                        elif bases[checkBaseSelected()].second_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=2, resource=BASE_LUMBER)
                        elif bases[checkBaseSelected()].third_orders == 'None':
                            updateBaseOrderString(checkBaseSelected(), 'Commerce', ordernumber=3, resource=BASE_LUMBER)
                    if COMMERCE_OIL_TEXTrect.collidepoint(pygame.mouse.get_pos()) == 1 and POTENTIAL_RESOURCE != BASE_OIL:
                        alleconomicactions.append(["Commerce", bases[checkBaseSelected()].hexnumber, POTENTIAL_RESOURCE, BASE_OIL])
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
                    for i in range(1116):
                        if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                            alleconomicactions.append(["Expand", bases[checkBaseSelected()].hexnumber, i])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=1)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=2)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Expand', ordernumber=3)
                    EXPAND_TOGGLE = 0
                #if build unit order, allow for unit to be chosen
                elif BUILD_UNIT_TOGGLE == 1:
                    for i in range(len(validBuildList)):
                        if validBuildList[i].rect.collidepoint(pygame.mouse.get_pos()) == 1:
                            alleconomicactions.append(["Build Unit", bases[checkBaseSelected()].hexnumber, validBuildList[i].unitType])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=1, unittype=validBuildList[i].unitType)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=2, unittype=validBuildList[i].unitType)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Build Unit', ordernumber=3, unittype=validBuildList[i].unitType)
                   
                    BUILD_UNIT_TOGGLE = 0
                #if establish caravan order, allow for route to be established
                elif CARAVAN_TOGGLE == 1:
                    for i in range(len(bases)):
                        if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1:
                            tempcaravanlist.append(bases[i].hexnumber)
                            alleconomicactions.append(["Establish Caravan", bases[checkBaseSelected()].hexnumber, tempcaravanlist, bases[i].hexnumber, LandOrSea(HexsideTerrain(tempcaravanlist[0], tempcaravanlist[1]))] + tempcaravanlist)
                            
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=1, targetbase=bases[i].name)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=2, targetbase=bases[i].name)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Establish Caravan', ordernumber=3, targetbase=bases[i].name)
                            CARAVAN_TOGGLE = 0
                    if CARAVAN_TOGGLE == 1:
                        count = 0
                        for i in range(1116):
                            if hexSurfaces[i].collidepoint(pygame.mouse.get_pos()) == 1:
                                tempcaravanlist.append(count)
                            count = count + 1
                #if send resources order, allow for selecting of destination hex
                elif SEND_RESOURCES_TOGGLE_ONE == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_TWO == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_THREE == 1:
                    pass
                elif SEND_RESOURCES_TOGGLE_FOUR == 1:
                    for i in range(len(bases)):
                        if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and bases[i].name != bases[checkBaseSelected()].name:
                            alleconomicactions.append(["Send Resources", bases[checkBaseSelected()].hexnumber, bases[i].hexnumber, POTENTIAL_GOLD, POTENTIAL_LUMBER, POTENTIAL_OIL])
                            if bases[checkBaseSelected()].first_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=1, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                            elif bases[checkBaseSelected()].second_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=2, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                            elif bases[checkBaseSelected()].third_orders == 'None':
                                updateBaseOrderString(checkBaseSelected(), 'Send Resources', ordernumber=3, targetbase=bases[i].name, goldsent=POTENTIAL_GOLD, lumbersent=POTENTIAL_LUMBER, oilsent=POTENTIAL_OIL)
                            SEND_RESOURCES_TOGGLE_FOUR = 0
                #else select/deselect units as applicable                    
                else:    
                    if checkSelected() != -1 or checkBaseSelected() != -1:
                        clearSelected()
                    else:
                        foundUnit = 0
                        for i in range(len(units)):
                            if units[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and isAllied(units[i].faction, currentfaction) == 1:
                                clearSelected()
                                units[i].selected = 1
                                foundUnit = 1
                        if foundUnit == 0:
                            for i in range(len(bases)):
                                if bases[i].area.collidepoint(pygame.mouse.get_pos()) == 1 and isAllied(bases[i].faction, currentfaction) == 1:
                                    clearSelected()
                                    bases[i].selected = 1
                redraw()
        
        #check for right mouseclick and move if applicable
        target = -1
        initial = -1
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                if checkSelected() != -1 and units[checkSelected()].faction == currentfaction:
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
                    for i in range(1116):
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
                            movechecker()
                            allorders=copy.deepcopy(successfulmoves)
                            successfulmoves=[]
                            del allunits[:]
                            del allhexes[:]
                            allunits=copy.deepcopy(backupallunits)
                            allhexes=copy.deepcopy(backupallhexes)
                            #print errormessagetext
                            #print allorders
                            updateOrderString(initial, 'Move')
                            redraw()

        #use SPACE to clear all orders for a selected unit
        if event.type == pygame.KEYDOWN:
            if SEND_RESOURCES_TOGGLE_ONE == 1:
                if event.key == pygame.K_SPACE:
                    POTENTIAL_GOLD = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_TWO = 1
                    SEND_RESOURCES_TOGGLE_ONE = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_TWO == 1:
                if event.key == pygame.K_SPACE:
                    POTENTIAL_LUMBER = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_THREE = 1
                    SEND_RESOURCES_TOGGLE_TWO = 0
                    redraw()
            elif SEND_RESOURCES_TOGGLE_THREE == 1:
                if event.key == pygame.K_SPACE:
                    POTENTIAL_OIL = RESOURCE_COUNTER
                    RESOURCE_COUNTER = 0
                    SEND_RESOURCES_TOGGLE_FOUR = 1
                    SEND_RESOURCES_TOGGLE_THREE = 0
                    redraw()
            else:
                if event.key == pygame.K_SPACE:
                    if checkSelected() != -1:
                        to_clear = checkSelected()
                        to_clear_index = -1
                        to_clear_index_special = -1
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
                        if to_clear_index_special != -1:
                            allspecialorders.pop(to_clear_index_special)
                            updateOrderString(to_clear, 'Clear')
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
                            alleconomicactions.pop(to_clear_index)
                            updateBaseOrderString(checkBaseSelected(), 'Clear', ordernumber=ordertracker)
                            redraw()

        #hit ENTER to output orders to spreadsheet
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if turnstatus==0:

                    # establish connection to database
                    db = load_db()

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

                    orderdata=open('orders.csv', 'wb')
                    writer = csv.writer(orderdata)
                    for i in allorders:
                        writer.writerow(i)
                    orderdata.close()

                    economicdata_cur = db.cursor()

                    for i in alleconomicactions:
                        templist = tuple(i)
                        templist = map(str, templist)
                        if len(templist) == 2:
                            economicdata_cur.execute("INSERT INTO economicactions (action_type, base_hex) VALUES (%s, %s)", (templist[0], templist[1])) 
                        if len(templist) == 3:
                            economicdata_cur.execute("INSERT INTO economicactions (action_type, base_hex, action_one) VALUES (%s, %s, %s)", (templist[0], templist[1], templist[2]))
                        if len(templist) == 4:
                            economicdata_cur.execute("INSERT INTO economicactions (action_type, base_hex, action_one, action_two) VALUES (%s, %s, %s, %s)", (templist[0], templist[1], templist[2], templist[3]))
                        if len(templist) == 5:
                            economicdata_cur.execute("INSERT INTO economicactions (action_type, base_hex, action_one, action_two, action_three) VALUES (%s, %s, %s, %s, %s)", (templist[0], templist[1], templist[2], templist[3], templist[4]))

                    economicdata_cur.close()

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

                    economicactionsdata=open('economicactions.csv', 'wb')
                    economicwriter = csv.writer(economicactionsdata)
                    for i in alleconomicactions:
                        economicwriter.writerow(i)
                    economicactionsdata.close()

                    specialorderdata=open('specialorders.csv', 'wb')
                    specialwriter = csv.writer(specialorderdata)
                    for i in allspecialorders:
                        specialwriter.writerow(i)
                    specialorderdata.close()

                    redraw()

        #hit T to toggle between arrows display
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                ARROWS_TOGGLE = toggle(ARROWS_TOGGLE)
                redraw()
                
        #hit F to toggle fog of war on/off
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                FOG_TOGGLE = toggle(FOG_TOGGLE)
                redraw()

        #hit R for ranged fire
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                if checkSelected() != -1 and units[checkSelected()].faction == currentfaction and units[checkSelected()].category == CATEGORY_INTERIOR_SIEGE and units[checkSelected()].orders == 'None':
                    RANGED_TOGGLE = toggle(RANGED_TOGGLE)
                    
        #hit B to board transport
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                if checkSelected() != -1 and units[checkSelected()].faction == currentfaction and units[checkSelected()].domain == TYPE_GROUND and units[checkSelected()].orders == 'None':
                    BOARD_TRANSPORT_TOGGLE = toggle(BOARD_TRANSPORT_TOGGLE)

        #hit D for destroy base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].first_orders == 'None':
                    alleconomicactions.append(["Destroy Base", bases[checkBaseSelected()].hexnumber])
                    updateBaseOrderString(checkBaseSelected(), 'Destroy Base', ordernumber=1)
                    redraw()

        #hit G for give base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and bases[checkBaseSelected()].first_orders == 'None':
                    GIVE_BASE_TOGGLE = toggle(GIVE_BASE_TOGGLE)
                    redraw()

        #hit E for give expansion order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    GIVE_EXPANSION_TOGGLE_ONE = toggle(GIVE_EXPANSION_TOGGLE_ONE)
                    redraw()    

        #hit H for harvest order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
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
            if event.key == pygame.K_c:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    COMMERCE_TOGGLE_ONE = toggle(COMMERCE_TOGGLE_ONE)
                    redraw()  

        #hit N for build unit order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    BUILD_UNIT_TOGGLE = toggle(BUILD_UNIT_TOGGLE)
                    redraw()

        #hit X for expand order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    EXPAND_TOGGLE = toggle(EXPAND_TOGGLE)
                    redraw()

        #hit V for establish caravan order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    tempcaravanlist[:] = []
                    tempcaravanlist.append(bases[checkBaseSelected()].hexnumber)
                    CARAVAN_TOGGLE = toggle(CARAVAN_TOGGLE)
                    redraw()

        #hit P for upgrade base order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    alleconomicactions.append(["Upgrade Base", bases[checkBaseSelected()].hexnumber])
                    if bases[checkBaseSelected()].first_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=1)
                    elif bases[checkBaseSelected()].second_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=2)
                    elif bases[checkBaseSelected()].third_orders == 'None':
                        updateBaseOrderString(checkBaseSelected(), 'Upgrade Base', ordernumber=3)
                    redraw()             

        #hit S for send resources order
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                if checkBaseSelected() != -1 and bases[checkBaseSelected()].faction == currentfaction and (bases[checkBaseSelected()].first_orders == 'None' or bases[checkBaseSelected()].second_orders == 'None' or bases[checkBaseSelected()].third_orders == 'None'):
                    POTENTIAL_GOLD = 0
                    POTENTIAL_LUMBER = 0
                    POTENTIAL_OIL = 0
                    SEND_RESOURCES_TOGGLE_ONE = toggle(SEND_RESOURCES_TOGGLE_ONE)
                    redraw()

        #hit esc to quit
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
                
        #allow for quitting 
        if event.type == QUIT:
            pygame.quit()
            sys.exit()


    


    
    
