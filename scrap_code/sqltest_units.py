from random import randint
import csv
import MySQLdb
import copy
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
allfactions=[5,5,5,5,5,5,5,15,15,15,15,15,15,15,15,13,15,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]#each faction's initiative count (diplomatic standing)
FOOD_SURPLUS=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
allunits=[]
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

# establish connection to database
db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="sniper67", # your password
                      db="warcraft") # name of the data base

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
def loadunits():
    unitdata=csv.reader(open('unitdata.csv'))
    unitstats=csv.reader(open('unitstats.csv'))
    #leaderdata=csv.reader(open('leaderdata.csv'))
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

def loadunits_sql():

    unitstats_cur = db.cursor()

    unitstats_cur.execute("SELECT * FROM unitstats")
    unitstats = unitstats_cur.fetchall()

    # unitdata=csv.reader(open('unitdata.csv'))
    # unitstats=csv.reader(open('unitstats.csv'))
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

def loadbuildables():
    orderdata=csv.reader(open('buildables.csv'))
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            templist.append(int(x[y]))
        allbuildables.append(templist)
        
def loadbuildables_sql():
    # orderdata=csv.reader(open('buildables.csv'))
    buildables_cur = db.cursor()

    buildables_cur.execute("SELECT * FROM buildables")
    orderdata = buildables_cur.fetchall()
    
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            templist.append(int(x[y]))
        allbuildables.append(templist)

    buildables_cur.close()

# loadbuildables()
loadbuildables_sql()
print allbuildables[4][4]

# loadunits()
# loadunits_sql()
# print unitdata
# print allunits[7][15]

#close database
db.close()
