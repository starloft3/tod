def closestBase(hex, faction):

    #get list of faction base hexes
    basehexes = []
    for x in range(len(allbases)):
        if allbases[x][BASE_FACTION] == faction:
            basehexes.append(allbases[x][BASE_LOCATION])

    #loop through, adding surrounding hexes and checking
    hexlist = [hex]
    all_hexlist = [hex]
    found = 0
    while found == 0:
        temp_hexlist = []
        temp_baselist = []
        for y in hexlist:
            if allhexes[y][HEX_N_TERRAIN] != 'X' and (y-1) not in all_hexlist:
                all_hexlist.append(y-1)
                temp_hexlist.append(y-1)
                if (y-1) in basehexes:
                    temp_baselist.append(y-1)
            if allhexes[y][HEX_NE_TERRAIN] != 'X' and (y+38) not in all_hexlist:
                all_hexlist.append(y+38)
                temp_hexlist.append(y+38)
                if (y+38) in basehexes:
                    temp_baselist.append(y+38)
            if allhexes[y][HEX_SE_TERRAIN] != 'X' and (y+39) not in all_hexlist:
                all_hexlist.append(y+39)
                temp_hexlist.append(y+39)
                if (y+39) in basehexes:
                    temp_baselist.append(y+39)
            if allhexes[y][HEX_S_TERRAIN] != 'X' and (y+1) not in all_hexlist:
                all_hexlist.append(y+1)
                temp_hexlist.append(y+1)
                if (y+1) in basehexes:
                    temp_baselist.append(y+1)
            if allhexes[y][HEX_SW_TERRAIN] != 'X' and (y-38) not in all_hexlist:
                all_hexlist.append(y-38)
                temp_hexlist.append(y-38)
                if (y-38) in basehexes:
                    temp_baselist.append(y-38)
            if allhexes[y][HEX_NW_TERRAIN] != 'X' and (y-39) not in all_hexlist:
                all_hexlist.append(y-39)
                temp_hexlist.append(y-39)
                if (y-39) in basehexes:
                    temp_baselist.append(y-39)

        #check if winners found
        if len(temp_baselist) > 0:
            winner = random.choice(temp_baselist)
            return winner

        #if no bases found (very rare!), return
        if len(temp_hexlist) == 0:
            return

        #set up for next cycle
        hexlist = temp_hexlist
