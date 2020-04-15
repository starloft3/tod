if Adjacent(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])==0
or (HexsideTerrain(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])!='C'
and HexsideTerrain(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2])!='F'
and HasRoad(caravan.path[len(caravan.path)-1],caravan.path[len(caravan.path)-2]))
or allfactions[caravan.faction]!=allfactions[allbases[caravan.destinationbase][BASE_FACTION]]:
