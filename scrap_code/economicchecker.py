allexpandables=[]
allpotentialexpansionsreceived=[]
class caravan():
    path=[]
    originbase=-1
    destinationbase=-1
    faction=-1
    caravantype='none'
def economicchecker(order):
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
                        #print 'initiating connection search loop'
                        for x in range(len(allcaravans)):#look through all caravans
                            #print 'analyzing caravan',allcaravans[x]
                            for y in range(len(foundbases)):#while looking through a caravan, search all bases officially connected so far and compile what they're connected to
                                #print 'analyzing base',foundbases[y]
                                if allcaravans[x].originbase==foundbases[y] or allcaravans[x].destinationbase==foundbases[y]:
                                    #print 'connection found',allcaravans[x]
                                    tempadds.append(allcaravans[x].originbase)
                                    tempadds.append(allcaravans[x].destinationbase)
                        for x in range(len(tempadds)):
                            #print 'all connections found:',tempadds
                            if IsItThere(tempadds[x],foundbases)==0:
                                foundbases.append(tempadds[x])
                                progress=1
                                #print 'connection found not previously added to foundbases',tempadds[x]
                        #print 'final list of bases connected to origin',foundbases
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
                if (allhexes[targetHex][HEX_TERRAIN]=='F' or allhexes[targetHex][HEX_TERRAIN]=='C' or (allhexes[targetHex][HEX_TERRAIN]=='O' and int(allhexes[targetHex][HEX_OIL])==1)) and IsItThere(targetHex,allexpandables[x])==1 and IsItThere(targetHex,visiblehexes)==1:
                    success=1
                else:
                    success=0
    if order[0]=='Establish Caravan':
        ACTION_HEX=1
        ACTION_CARAVAN_ORIGIN_BASE=1
        ACTION_CARAVAN_TYPE=2
        newcaravan=caravan()
        newcaravan.path=[]
        #print 'the caravan order currently being worked with is:',order
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
        #print "caravan origin base:",newcaravan.originbase
        #print "caravan destination base:",newcaravan.destinationbase
        #print "caravan faction:",newcaravan.faction
        #print "caravan type:",newcaravan.caravantype
        for z in range(len(newcaravan.path)):
            print "caravan path hex",z,':',newcaravan.path[z]
        currentcaravan=newcaravan
        valid=1
        targetbase=0
        actingbase=0
        for x in range(len(allbases)):
            if allbases[x][BASE_LOCATION]==currentcaravan.destinationbase:
                targetbase=x
            if allbases[x][BASE_LOCATION]==currentcaravan.originbase:
                actingbase=x
        if len(buildfactionslist(buildcombatlist(int(currentcaravan.destinationbase))))>1:
            valid=0
            #print 'currentcaravan found illegal because combat in destination hex'
        for x in range(len(currentcaravan.path)):
            if IsItThere(currentcaravan.path[x],visiblehexes)==0:
                valid=0
                #print 'currentcaravan found illegal because not all hexes visible'
        if currentcaravan.originbase==currentcaravan.destinationbase:
            valid=0
            #print 'currentcaravan found illegal because origin and destination are the fucking same you asshole'
        if len(currentcaravan.path)>16:
            valid=0
            #print "currentcaravan found illegal because it's too long fuck you"#lol this will never happen because the SQL can't hold that much but okay in case of hax
        for x in range(1,len(currentcaravan.path)-1):
            for z in range(len(allbases)):
                if currentcaravan.path[x]==allbases[z][BASE_LOCATION]:
                    valid=0
                    #print "currentcaravan found illegal because you tried to be cute and run it through another base"
        if currentcaravan.currentcaravantype=='water':
            for x in range(1,len(currentcaravan.path)-1):
                if Adjacent(currentcaravan.path[x-1],currentcaravan.path[x])==0:
                    valid=0
                    #print 'currentcaravan canceled because hexes not adjacent'
                if allhexes[currentcaravan.path[x]][HEX_TERRAIN]!='O':
                    valid=0
                    #print 'currentcaravan canceled because intermediate hex not ocean'
                if HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='O' and HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='K':
                    valid=0
                    #print 'currentcaravan canceled because hexside terrain not ocean or coastal'
                if EnemyUnitsPresent(currentcaravan.path[x],currentcaravan.faction)==1:
                    valid=0
                    #print 'water currentcaravan order found illegal because enemy units being present'
            if Adjacent(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0 or HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='K' or allfactions[currentcaravan.faction]!=allfactions[allbases[targetbase][BASE_FACTION]]:
                valid=0
                #print 'water currentcaravan order found illegal because of final step between hex and destination illegal or factions not matching up'
        if currentcaravan.currentcaravantype=='land':
            for x in range(1,len(currentcaravan.path)-1):
                if Adjacent(currentcaravan.path[x-1],currentcaravan.path[x])==0:
                    valid=0
                    #print 'canceled because hexes not adjacent'
                if allhexes[currentcaravan.path[x]][HEX_TERRAIN]=='O' or allhexes[currentcaravan.path[x]][HEX_TERRAIN]=='I':
                    valid=0
                    #print 'canceled because hex is ocean or impassable'
                if HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='C' and HexsideTerrain(currentcaravan.path[x-1],currentcaravan.path[x])!='F' and HasRoad(currentcaravan.path[x-1],currentcaravan.path[x])!=1:
                    valid=0
                    #print 'canceled because not clear, not forest, and not road'
                if EnemyUnitsPresent(currentcaravan.path[x],currentcaravan.faction)==1:
                    valid=0
                    #print 'canceled because enemy units present'
            if Adjacent(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0 or (HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='C' and HexsideTerrain(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])!='F' and HasRoad(currentcaravan.path[len(currentcaravan.path)-1],currentcaravan.path[len(currentcaravan.path)-2])==0) or allfactions[currentcaravan.faction]!=allfactions[allbases[targetbase][BASE_FACTION]]:
                valid=0
                #print 'land currentcaravan order found illegal because final step between hex and destination illegal or factions not matching up'
        if valid==1:
            success=1
        else:
            success=0
    if order[0]=='Assist Construction':
        success=0
        if allhexes[order[2]][HEX_TERRAIN]=='C' and buildfactionslist(buildcombatlist(order[2]))<2:
            for x in range(len(allbases)):
                if int(allbases[x][BASE_LOCATION])==int(order[1]):
                    unitspresent=buildcombatlist(int(order[2]))
                    for y in range(len(unitspresent)):
                        if isLeader(unitspresent[y])==1 and allfactions[allbases[x][BASE_FACTION]]==allfactions[allunits[unitspresent[y]][UNIT_FACTION]]:
                            success=1
    if order[0]=='Give Expansion':
        valid=1
        recipientbase=0
        base=0
        for x in range(len(allbases)):
            if allbases[x][BASE_LOCATION]==order[2]:
                recipientbase=x
            if allbases[x][BASE_LOCATION]==order[1]:
                base=x
        ##print recipientbase
        ##print base
        if allfactions[allbases[recipientbase][BASE_FACTION]]!=allfactions[allbases[base][BASE_FACTION]]:
            valid=0
            ##print 'factions are not friendly'
        if int(allhexes[actionhex][HEX_FARM])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_RIG])!=allbases[base][BASE_LOCATION] and int(allhexes[actionhex][HEX_MILL])!=allbases[base][BASE_LOCATION]:
            valid=0
            ##print 'expo does not belong to parent base'
        ##print 'allpotentialexpansionsreceived:',allpotentialexpansionsreceived
        if IsItThere(actionhex,allpotentialexpansionsreceived[recipientbase])==0:
            valid=0
            ##print 'not in allpotentialexpansionsreceived'
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
