
#this

if (allunits[unit][UNIT_TYPE]==TYPE_SEA) and ((allhexes[one][HEX_TERRAIN]=='O' and (terrain=='O' or terrain=='C')) or (allhexes[one][HEX_TERRAIN]=='C' and terrain=='O')) and (sideterrain=='O' or sideterrain=='K'):
        move=1


#was replaced by this

if allunits[unit][UNIT_TYPE] == TYPE_SEA:
        if hex_one_terrain == 'O' and hex_two_terrain == 'O':
            move=1
        if (hex_one_terrain == 'O' or hex_two_terrain == 'O') and sideterrain == 'K':
            move=1
