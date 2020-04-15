import pygame, sys, time, copy, string
from pygame.locals import *

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

def loadImages():
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

    #load special images
    RunestoneOrigImage = pygame.image.load('images/Buildings/runestone.png')
    RunestoneImage = pygame.transform.scale(RunestoneOrigImage, (BASE_WIDTH, BASE_LENGTH))
    DarkPortalOrigImage = pygame.image.load('images/Buildings/darkportal.png')
    DarkPortalImage = pygame.transform.scale(DarkPortalOrigImage, (BASE_WIDTH, BASE_LENGTH))
    DragonRoostOrigImage = pygame.image.load('images/Buildings/roost.png')
    DragonRoostImage = pygame.transform.scale(DragonRoostOrigImage, (BASE_WIDTH, BASE_LENGTH))