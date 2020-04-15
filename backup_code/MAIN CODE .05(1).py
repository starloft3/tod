from random import randint
import csv
#CATEGORYLIST
CATEGORY_EXTERIOR_SIEGE=0
CATEGORY_RANGED=1
CATEGORY_MELEE=2
CATEGORY_INTERIOR_SIEGE=3
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
#TYPES
TYPE_GROUND=0
TYPE_AIR=1
TYPE_SEA=2
#BASES

#ALLHEXES
HEX_TERRAIN=0
HEX_N_TERRAIN=1
HEX_NE_TERRAIN=2
HEX_SE_TERRAIN=3
HEX_S_TERRAIN=4
HEX_SW_TERRAIN=5
HEX_NW_TERRAIN=6
HEX_FACTION=7
HEX_BASE=8# BASE OR UNIQUE STRUCTURE PRESENT
HEX_ROAD=9# ROAD PRESENT
HEX_OIL=10# OIL PRESENT
HEX_FARM=11# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_MILL=12# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_RIG=13# (0 = NONE, INTEGER = YES + ASSOCIATED HEX)
HEX_GOLD=14#TOTAL GOLD VALUE OF HEX
HEX_NEW_COMBAT=15
HEX_BATTLE_FOUGHT=16
HEX_N_CONTROL=17
HEX_NE_CONTROL=18
HEX_SE_CONTROL=19
HEX_S_CONTROL=20
HEX_SW_CONTROL=21
HEX_NW_CONTROL=22
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
categorylist=[CATEGORY_EXTERIOR_SIEGE,CATEGORY_RANGED,CATEGORY_MELEE,CATEGORY_INTERIOR_SIEGE]#this can be replaced by just a loop through the numbers, but change it elsewhere before deleting
allfactions=[0,5,5,5,5,5,5,6,6,7,15,9,10,15,15,13,14,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]#each faction's initiative count (diplomatic standing)
allunits=[]
allorders=[]
allspecialorders=[]
hexsidelimitchecks=[]
allhexes=[]
allroads=[]
allbases=[]
#STUFF
def ordermenu(prompt,*options):#haven't used this yet. For testing purposes this can be used to make menus
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
allstats={'Grunt':unittype(),'Berserker':unittype(),'Axethrower':unittype(),'Ogre':unittype(),'Catapult':unittype(),'Death Knight':unittype(),'Wave Rider':unittype(),'Turtle':unittype(),'Juggernaut':unittype(),'Horde Transport':unittype(),'Dragon':unittype(),'Raider':unittype(),'Shaman':unittype(),'Warlock':unittype(),'Footman':unittype(),'Archer':unittype(),'Knight':unittype(),'Ballista':unittype(),'Mage':unittype(),'Destroyer':unittype(),'Submarine':unittype(),'Battleship':unittype(),'Alliance Transport':unittype(),'Gryphon':unittype(),'Dwarf':unittype(),'Swordsman':unittype(),'Wildhammer Shaman':unittype(),'Exterior Catapult':unittype(),'Exterior Juggernaut':unittype(),'Exterior Ballista':unittype(),'Exterior Battleship':unittype()}
#LOAD GAME STATE
def loadunits():
    unitdata=csv.reader(open('unitdata.csv'))
    unitstats=csv.reader(open('unitstats.csv'))
    leaderdata=csv.reader(open('leaderdata.csv'))
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
        for y in range(0,16):
            allunits[count].append(0)
        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
        count=count+1
##    count=0
##    for x in leaderdata:
##        allunits[count][UNIT_NAME]=x[0]
##        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+int(x[1])
##        allunits[count][UNIT_COMBAT]=allunits[count][UNIT_COMBAT]+int(x[2])
##        allunits[count][UNIT_LIGHT_MAX]=allunits[count][UNIT_LIGHT_MAX]+int(x[3])
##        count=count+1
def loadsavedunits():
    unitdata=csv.reader(open('saveunits.csv'))
    unitstats=csv.reader(open('unitstats.csv'))
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
        for y in range(0,16):
            allunits[count].append(0)
        allunits[count][UNIT_MAX_HIT_POINTS]=allunits[count][UNIT_MAX_HIT_POINTS]+allunits[count][UNIT_TIER]
        count=count+1
def loadorders():
    orderdata=csv.reader(open('orders.csv'))
    for x in orderdata:
        templist=[]
        for y in x:
            templist.append(int(y))
        allorders.append(templist)
def loadspecialorders():
    orderdata=csv.reader(open('specialorders.csv'))
    for x in orderdata:
        templist=[]
        for y in range(len(x)):
            if y==0:
                templist.append(x[y])
            else:
                templist.append(int(x[y]))
        allspecialorders.append(templist)
def loadmap():
    mapdata=csv.reader(open('hexdata.csv'))
    for x in mapdata:
        templist=[]
        for y in range(0,9):
            templist.append(x[y])
        for y in range(9,len(x)):
            templist.append(x[int(y)])
        allhexes.append(templist)
def loadsavedmap():
    mapdata=csv.reader(open('savehexes.csv'))
    for x in mapdata:
        templist=[]
        for y in range(0,9):
            templist.append(x[y])
        for y in range(9,len(x)):
            templist.append(x[int(y)])
        allhexes.append(templist)
def loadroads():
    roaddata=csv.reader(open('roaddata.csv'))
    for x in roaddata:
        templist=[]
        for y in x:
            templist.append(int(y))
        allroads.append(templist)
def loadbases():
    basedata=csv.reader(open('basedata.csv'))
    for x in basedata:
        templist=[]
        templist.append(x[0])
        for y in range(1,len(x)):
            templist.append(int(x[y]))
        allbases.append(templist)
def loadsavedbases():
    basedata=csv.reader(open('savebases.csv'))
    for x in basedata:
        templist=[]
        templist.append(x[0])
        for y in range(1,len(x)):
            templist.append(int(x[y]))
        allbases.append(templist)
#MOVEMENT
def specialorders():
    ##assist construction
    print 'yes'
    for x in range(len(allspecialorders)):##ranged fire
        print 'yes'
        print allspecialorders[x][0],allspecialorders[x][1],allspecialorders[x][2]
        if allspecialorders[x][0]=='Rangedfire' and allunits[allspecialorders[x][1]][UNIT_CATEGORY]==CATEGORY_INTERIOR_SIEGE and Adjacent(allunits[allspecialorders[x][1]][UNIT_LOCATION],allspecialorders[x][2])==1:
            allunits.append(allunits[allspecialorders[x][1]][0:len(allunits[allspecialorders[x][1]])])
            allunits[len(allunits)-1][UNIT_CATEGORY]=CATEGORY_EXTERIOR_SIEGE
            allunits[len(allunits)-1][UNIT_LOCATION]=allspecialorders[x][2]
            allunits[allspecialorders[x][1]][UNIT_MOVEMENT_REMAINING]=0
            print allunits[len(allunits)-1]
            print 'stuff happened'
def moveunits():##road moves into combat?
    for x in range(len(allunits)):#prevent units from entering combats the same turn they started in one
        if len(buildfactionslist(buildcombatlist(allunits[x][UNIT_LOCATION])))>1:
            allunits[x][UNIT_COMBAT_START]=1
        else:
            allunits[x][UNIT_COMBAT_START]=0
    for x in range(1,4):#work one destination at a time
        for y in range(len(allorders)):#sort moves by hexside crossed
            if len(allorders[y])>1 and (allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]>0 or (allunits[allorders[y][0]][UNIT_ROAD_MOVE_REMAINING]==1 and allunits[allorders[y][0]][UNIT_ROAD_MOVE_ONLY]==1)):#are there any moves and does the unit have movement remaining
                print 'order found, sufficient movement remaining'
                hexone=allunits[allorders[y][0]][UNIT_LOCATION]
                print 'origin hex: ',hexone
                hextwo=allorders[y][1]
                print 'destination hex: ',hextwo
                hexswitch=-1
                foundmatch=0
                match=-1
                newcheck=[]
                combatmove=movecombatcheck(allorders[y][0],hextwo)
                print 'combat move: ',combatmove
                if canMove(hexone,hextwo,allorders[y][0],combatmove)==1:#check if move legal in terms of hex and hexside terrain being passable.
                    print 'unit can move to destination'
                    if allunits[allorders[y][0]][UNIT_TYPE]!=TYPE_AIR:
                        if hextwo>hexone:#generate hexside ID, always bigger number first
                            print "destination was higher index than origin so they've been switched"
                            hexswitch=hexone
                            hexone=hextwo
                            hextwo=hexswitch
                        for z in range(len(hexsidelimitchecks)):#prepare to assign move order to hexside. see if any move orders already categorized through that hexside
                            if hexsidelimitchecks[z][0]==hexone and hexsidelimitchecks[z][1]==hextwo:
                                foundmatch=1
                                match=z
                        if foundmatch==1:#if there are, add this to that one
                            hexsidelimitchecks[match].append(y)
                            print 'another unit has moved this way before so current unit is tacked onto that hexside check'
                        else:#if there aren't, add a new one to hexsidelimitchecks
                            print 'no units have moved this way before so current unit is tacked onto a new check'
                            newcheck.append(hexone)
                            newcheck.append(hextwo)
                            newcheck.append(hexsidelimit(hexone,hextwo,combatmove))
                            newcheck.append(y)
                            hexsidelimitchecks.append(newcheck)
                else:
                    allorders[y]=[allorders[y][0]]
                    print "unit can't move"
            else:
                allorders[y]=[allorders[y][0]]
        for y in range(len(hexsidelimitchecks)):#compare hexsidelimitchecks to actual hexside limits and pick losers. delete unsuccessful units from HLC, delete all further orders for unsuccessful units
            while (len(hexsidelimitchecks[y])-3)>hexsidelimitchecks[y][2]:##something wrong is happening here sometimes i think
                print 'too many units are trying to cross this hexside, remove one'
                pick=randint(0,(len(hexsidelimitchecks[y])-4))+3
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
                allunits[allorders[y][0]][UNIT_PREVIOUS_LOCATION]=allunits[allorders[y][0]][UNIT_LOCATION]#save unit prev location for forces and trails and terrain
                print 'unit previous location set to: ',allunits[allorders[y][0]][UNIT_PREVIOUS_LOCATION]
                if allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]>0:#deduct movement points
                    allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]=allunits[allorders[y][0]][UNIT_MOVEMENT_REMAINING]-1
                    print 'one movement point deducted'
                else:
                    allunits[allorders[y][0]][UNIT_ROAD_MOVE_REMAINING]=0
                    print 'one road movement point deducted'
                ##trails
                if HasRoad(hexone,hextwo)==0 or allunits[allorders[y][0]][UNIT_TYPE]==TYPE_AIR:#if move is not across a road hexside set UNIT_ROAD_MOVE_ONLY to 0
                    allunits[allorders[y][0]][UNIT_ROAD_MOVE_ONLY]=0
                    print 'unit is no longer moving on roads'
                allunits[allorders[y][0]][UNIT_LOCATION]=allorders[y][1]#move unit
                allunits[allorders[y][0]][UNIT_HEX_DURATION]=0
                print 'unit has been moved to: ',allunits[allorders[y][0]][UNIT_LOCATION]
                if len(buildfactionslist(buildcombatlist(allorders[y][1])))>1:
                    allorders[y]=[allorders[y][0]]#if combat, delete all further orders
                    print 'unit has moved into combat, so all further orders have been deleted'
                else:
                    allorders[y].remove(allorders[y][1])#otherwise delete current order
                    print 'unit has not moved into combat, so only this order has been deleted'
        for y in range(len(hexsidelimitchecks)):#remove all units from HLC
            hexsidelimitchecks[y]=[hexsidelimitchecks[y][0],hexsidelimitchecks[y][1],hexsidelimitchecks[y][2]]
            print 'units removed from hexsidelimitchecks'
        hexsideControlSweep()
        print 'hexside control changed'
    AssignBonuses()
    for x in range(len(allunits)):#increase hex durations, set previous locations, set hexside control
        if allunits[x][UNIT_LOCATION]!=allunits[x][UNIT_PREVIOUS_LOCATION]:
            allhexes[allunits[x][UNIT_LOCATION]][WhichHexSideControl(allunits[x][UNIT_LOCATION],allunits[x][UNIT_PREVIOUS_LOCATION])]=allfactions[allunits[x][UNIT_FACTION]]
        if allunits[x][UNIT_LOCATION]==allunits[x][UNIT_PREVIOUS_LOCATION]:
            allunits[x][UNIT_HEX_DURATION]=allunits[x][UNIT_HEX_DURATION]+1
        allunits[x][UNIT_PREVIOUS_LOCATION]=allunits[x][UNIT_LOCATION]
def Adjacent(one,two):
    result=one-two
    print result
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
        print 'whichhexsidecontrol fucked up'
    return direction
def AssignBonuses():
    for x in range(len(allhexes)):
        if len(buildfactionslist(buildcombatlist(x)))>1:#is there a combat there?
            forcelist=[[],[],[],[],[],[]]
            forcetotals=[0,0,0,0,0,0]
            forceorder=[]
            for y in range(len(allunits)):
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
            bonus=0
            while count<(len(forceorder)-1):#assign flanking bonuses
                currentpick=[]
                for xx in range(count,len(forceorder)):#find all with same value as first in forceorder
                    if forcetotals[forceorder[xx]]==forcetotals[forceorder[count]]:
                        currentpick.append(forceorder[xx])
                while len(currentpick)>0:#from among this group assign flanking bonuses in random order
                    pick=randint(0,len(currentpick)-1)
                    for xx in forcelist[currentpick[pick]]:
                        allunits[xx][UNIT_FLANK]=bonus
                    bonus=bonus+10
                    count=count+1#skip remaining equally valued forces
                    currentpick.remove(currentpick[pick])
            for y in range(len(allunits)):
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_LOCATION]==allunits[y][UNIT_PREVIOUS_LOCATION]:#assign terrain bonuses
                    allunits[y][UNIT_TERRAIN]=TerrainBonus(x,allhexes[x][HEX_TERRAIN],y)
                    allunits[y][UNIT_HOLD_BONUS]=1
                if allunits[y][UNIT_LOCATION]==x and allunits[y][UNIT_LOCATION]!=allunits[y][UNIT_PREVIOUS_LOCATION] and allunits[y][UNIT_HOLD_BONUS]==0:#assign terrain bonuses
                    allunits[y][UNIT_TERRAIN]=TerrainBonus(x,HexsideTerrain(x,allunits[y][UNIT_PREVIOUS_LOCATION]),y)
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
        print 'Hexes not adjacent, invalid orders'
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
    if allunits[unit][UNIT_HEX_DURATION]>0 and allhexes[terrainhex][HEX_NEW_COMBAT]==1:
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
        print 'Hexes not adjacent, invalid orders'
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
    else:
        print 'Hexes not adjacent, invalid orders'
    return road
def canMove(one,two,unit,combatmove):
    move=0
    terrain=allhexes[two][HEX_TERRAIN]
    if ((allunits[unit][UNIT_TYPE]==TYPE_GROUND) and (terrain=='F' or terrain=='M' or terrain=='S' or terrain=='C' or terrain=='R' or terrain=='W') and (HexsideTerrain(one,two)=='F' or HexsideTerrain(one,two)=='M' or HexsideTerrain(one,two)=='S' or HexsideTerrain(one,two)=='C' or HexsideTerrain(one,two)=='R' or HexsideTerrain(one,two)=='W')):
        move=1
        print 'unit is ground moving across legal hexside'
    if (allunits[unit][UNIT_TYPE]==TYPE_SEA) and ((allhexes[one][HEX_TERRAIN]=='O' and (terrain=='O' or terrain=='K' or terrain=='C')) or (allhexes[one][HEX_TERRAIN]=='K' and terrain=='O')):
        move=1
        print 'unit is sea moving across legal hexside'
    if allunits[unit][UNIT_TYPE]==TYPE_AIR:
        move=1
        print 'unit is air'
    if allunits[unit][UNIT_MOVEMENT_REMAINING]==0 and HasRoad(one,two)==0:
        move=0
        print 'move canceled because no road available for road move'
    print 'unitfaction: ',allfactions[allunits[unit][UNIT_FACTION]]
    print 'hexsidecontroller: ',allhexes[one][WhichHexSideControl(one,two)]
    if allfactions[allunits[unit][UNIT_FACTION]]!=allhexes[one][WhichHexSideControl(one,two)]:#check if moving out through enemy hexside
        move=0
        print 'unit is trying to move out of an enemy hexside, cancel move'
    if combatmove==1 and allunits[unit][UNIT_COMBAT_START]==1:
        move=0
        print 'unit is trying to move into combat but started this turn in a combat'
    return move
    ##check if siege is moving across nonsiege hexsides
def movecombatcheck(unit,destination):#this borrows a function from combat
    dFactionsList=buildfactionslist(buildcombatlist(destination))
    combat=0
    for x in dFactionsList:
        if allfactions[allunits[unit][UNIT_FACTION]]!=allfactions[x]:
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
        road=allroads[one][HEX_N_TERRAIN]
    elif result==38:
        terrain=allhexes[one][HEX_SW_TERRAIN]
        road=allroads[one][HEX_N_TERRAIN]
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
        if len(buildfactionslist(buildcombatlist(x)))>1 and int(allhexes[x][HEX_BATTLE_FOUGHT])==0:
            combat(x)
            allhexes[x][HEX_BATTLE_FOUGHT]=1
            allhexes[x][HEX_NEW_COMBAT]=0
        else:
            allhexes[x][HEX_NEW_COMBAT]=1
    reset()
def combat(battlehex):
    print 'combat'
    combatlist=buildcombatlist(battlehex)
    factionslist=buildfactionslist(combatlist)
    if allhexes[battlehex][HEX_NEW_COMBAT]==1:
        print 'new combat'
        for x in range(len(categorylist)):
            for y in range(len(factionslist)):
                attacklastround=1
                while attacklastround==1:
                    attacklastround=0
                    attacker=chooseattacker(combatlist,x,y,factionslist) ##(x=category, y=faction)
                    target=choosetarget(combatlist,attacker)
                    if attacker!=-1 and target!=-1:
                        print '                 ',allunits[attacker][UNIT_NAME]
                        dealDamage(calculateDamage(attacker),target, attacker)
                        attacklastround=1
                    allunits[attacker][UNIT_HOLD_BONUS]=0#take off the bonus hold, reset flank and terrain bonuses
                    allunits[attacker][UNIT_FLANK]=0
                    allunits[attacker][UNIT_TERRAIN]=0
    else:
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
        if allfactions[allunits[x][UNIT_FACTION]]!=allfactions[allunits[attacker][UNIT_FACTION]] and allunits[combatlist[x]][UNIT_HIT_POINTS]>highesthp and canHit(attacker,combatlist[x])==1 and allunits[combatlist[x]][UNIT_HIT_POINTS]>0 and allunits[combatlist[x]][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:
            choicelist=[]
            highesthp=allunits[combatlist[x]][UNIT_HIT_POINTS]
            choicelist.append(combatlist[x])
        if allfactions[allunits[x][UNIT_FACTION]]!=allfactions[allunits[attacker][UNIT_FACTION]] and allunits[combatlist[x]][UNIT_HIT_POINTS]==highesthp and canHit(attacker,combatlist[x])==1 and allunits[combatlist[x]][UNIT_HIT_POINTS]>0 and allunits[combatlist[x]][UNIT_CATEGORY]!=CATEGORY_EXTERIOR_SIEGE:
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
    for x in range(len(allhexes)):
        allhexes[x][HEX_NEW_COMBAT]=1
def SaveGame():
    hexdata=csv.writer(open('savehexes.csv','wb'))
    unitdata=csv.writer(open('saveunits.csv','wb'))
    factiondata=csv.writer(open('savefactions.csv','wb'))
    basedata=csv.writer(open('savebases.csv','wb'))
    for x in allhexes:
        hexdata.writerow(x)    
    for x in allunits:
        saverow=[]
        for y in range(len(x)):
            if y==0 or 13<y<18:
                saverow.append(x[y])
            elif 9<y<14 or y==18:
                saverow.append(int((x[y])))
        unitdata.writerow(saverow)
    factiondata.writerow(allfactions)
    for x in allbases:
        basedata.writerow(allbases)
def TestGameStart():
    loadunits()
    loadmap()
    loadroads()
    #loadbases()
    loadorders()
    loadspecialorders()
    InitSetStuff()
    reset()
    hexsideControlSweep()
    specialorders()
    moveunits()
    allcombat()
    SaveGame()
##    for x in range(len(allunits)):
##        print factiondictionary[allunits[x][UNIT_FACTION]],allunits[x][UNIT_NAME],allunits[x][UNIT_HIT_POINTS]
##        print allunits[x][UNIT_LOCATION]
def TestGameSave():
    loadsavedunits()
    loadsavedmap()
    loadroads()
    #loadsavedbases()
    loadorders()
    loadspecialorders()
    InitSetStuff()
    reset()
    hexsideControlSweep()
    specialorders()
    moveunits()
    allcombat()
    for x in allhexes:
        x[HEX_BATTLE_FOUGHT]=0
    SaveGame()
##    for x in range(len(allunits)):
##        print factiondictionary[allunits[x][UNIT_FACTION]],allunits[x][UNIT_NAME],allunits[x][UNIT_HIT_POINTS]
##        print allunits[x][UNIT_LOCATION]
TestGameSave()
print allunits[153][UNIT_LOCATION]
