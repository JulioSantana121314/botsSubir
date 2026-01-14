import pymongo

# Tu diccionario original de juegos, cuentas y passwords
WEBSITES = {
    "ORION STARS": {
        "url": "https://orionstars.vip:8781/default.aspx",
        "accounts": [
            {"usuario": "LupesweepsOS", "password": '!@PEus4321'},
            {"usuario": "Wisegangautostore", "password": "Auto1989!@"},
            {"usuario": "AmandaP_BOT", "password": "Focus999@@159"},
            {"usuario": "slapitgames3", "password": "Sl4piTG@m3z!"},
            {"usuario": "kobegames3", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "Whatever777", "password": "Mkingdom77@@"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987@#6152"},
            {"usuario": "LuckyCas", "password": "Lucky9709@!$"},
            {"usuario": "a5games3", "password": "haileysPh656!@"},
            {"usuario": "ReggiesProducts_Cashier", "password": "Monchie21Monchie21!!"},
            {"usuario": "CashierTDCRB1", "password": 'DVASBFU!"182571982152'},
            {"usuario": "CashierTAPEC_1", "password": "TAPsdpTDC_62!"},
        ],
    },
    "JUWA": {
        "url": "https://ht.juwa777.com/login",
        "accounts": [
            {"usuario": "PeruLogin", "password": "newone123"},
            {"usuario": "autostore", "password": "Auto1989!@"},
            {"usuario": "AmandaP_BOT", "password": "Focus999@@159"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "kcheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "Whatever777", "password": "Mkingdom7"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987@#6152"},
            {"usuario": "iluckyroomjw", "password": "Juwa$777"},
            {"usuario": "a5games", "password": "HaiLey8888"},
            {"usuario": "JWStoreDistro", "password": "JWStoreDistro123!#$"},
            {"usuario": "TAPJuwaMewa6131", "password": "JurTapMyTap!875"},
        ],
    },
    "FIRE KIRIN": {
        "url": "https://firekirin.xyz:8888/default.aspx",
        "accounts": [
            {"usuario": "VasquezCash", "password": "!@PEus4321"},
            {"usuario": "Wisegangautostore", "password": "Auto1989"},
            {"usuario": "AmandaP_BOT", "password": "Focus999159"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987_6152"},
            {"usuario": " IluckyroomFK", "password": "k3wMBwN6"},
            {"usuario": "a5games", "password": "!Hailey_8800_!"},
            {"usuario": "ReggiesProducts_Cashier", "password": "Winning6543"},
            {"usuario": "CashierTDCRB1", "password": "DVASBFU_81236871250"},
            {"usuario": "TAPTS_CSH_1", "password": "fkes1dragon"},
        ],
    },
    "PANDA MASTER": {
        "url": "https://pandamaster.vip/default.aspx",
        "accounts": [
            {"usuario": "LVasquezPMc", "password": "Free123!@#"},
            {"usuario": "Wisegangautostore", "password": "Auto1989"},
            {"usuario": "AmandaP_BOT", "password": "Focus999159"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@"},
            {"usuario": "OceanSluggerz001_Cashier", "password": "Focus987_6152"},
            {"usuario": "a5games", "password": "!Hailey_8800_!"},
            {"usuario": "ReggiesProducts_Cashier", "password": "Winning4276"},
            {"usuario": "CashierTDCRB1", "password": "192371_pm_DVASBFU"},
            {"usuario": "TdcTaPm_Cash1", "password": "TaptapcashPM_127"},
        ],
    },
    "MILKY WAY": {
        "url": "https://milkywayapp.xyz:8781/Store.aspx",
        "accounts": [
            {"usuario": "CashierLV", "password": "!@PEus4321"},
            {"usuario": "Autostore", "password": "Auto1989"},
            {"usuario": "bworldweb007", "password": "Agent38"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987_6152"},
            {"usuario": "MWTapCash", "password": "BashCraqZs_2"},
        ],
    },
    "VBLINK": {
        "url": "https://gm.vblink777.club/#/login?redirect=%2Findex",
        "accounts": [
            {"usuario": "atencionpre1", "password": "PPPE@$123456"},
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebsiteCashier", "password": "Winning@7777"},
            {"usuario": "slapitnow", "password": "$l@p$l@p8#8"},
            {"usuario": "playoakcreek", "password": "0aKcR33kpL@y!"},
            {"usuario": "Whatever777", "password": "Mkingdom777@"},
            {"usuario": "OceanSluggerz01B", "password": "Focus987@#6152"},
            {"usuario": "Cashilucky", "password": "v53FMZcg$123"},
           # {"usuario": "HaileyBE", "password": "Haileys8825!@"},
            {"usuario": "playerbot", "password": "TIme2plan!$"},
            {"usuario": "DisTDCroVB15163", "password": "TDCvbCPRV!61365"},
            {"usuario": "VtapBLINK182CASH", "password": "TapTopVbSAC11!"},
        ],
    },
    "ULTRA PANDA": {
        "url": "https://ht.ultrapanda.mobi/#/login",
        "accounts": [
            {"usuario": "atencionpre", "password": "PPPE@$123456"},
            {"usuario": "Automatedside", "password": "Auto1989!@"},
            {"usuario": "WebsiteBOT", "password": "Winning@7777"},
            {"usuario": "slapitnow", "password": "$l@p$l@p8#8"},
            {"usuario": "playoakcreek", "password": "0aKcR33kpL@y!"},
            {"usuario": "Whatever777", "password": "Mkingdom777@"},
            {"usuario": "OceanSluggerz01B", "password": "Focus987@#6152"},
            {"usuario": "CashiluckyR", "password": "UltraPanda$1$1"},
            {"usuario": "HaileyBE", "password": "Haileys8825!@"},
            {"usuario": "playerbot", "password": "TIme2plan!$"},
            {"usuario": "UPTDCSUB19751", "password": "tudpc182351soobs"},
            {"usuario": "TAuPSub1LPMP", "password": "Tap@TappinUP44!"},
        ],
    },
    "GOLDEN TREASURE": {
        "url": "https://fus.goldentreasure.mobi/?#/login",
        "accounts": [
            {"usuario": "Perubot", "password": "AtGC123456!!"},
            {"usuario": "Autostore1", "password": "Auto1989!@"},
            {"usuario": "AmandasPBOT", "password": "Focus999@@159"},
            {"usuario": "iluckyCash", "password": "GoldenT111$"},
            {"usuario": "playerbot", "password": "TIme2plan!$"},
            {"usuario": "GTDCCSUB35857", "password": "gtdcsub835gt2"},
            {"usuario": "TapDBGTSub123", "password": "PanPass91!67"},
        ],
    },
    "Egames": {
        "url": "https://pko.egame99.club/",
        "accounts": [
            {"usuario": "Perubot", "password": "AtXG123456!!"},
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "BallerzWebBOT", "password": "Baller$1578Z"},
            {"usuario": "ReggiesProducts1", "password": "Monchie21!"},
            {"usuario": "DisTDCroVB15163", "password": "EGTDCroVB15164"},
            {"usuario": "TAPEGGsBOT0", "password": "BreakfastBun234!"},
        ],
    },
    "ACE BOOK": {
        "url": "https://djwae.playacebook.mobi/#/login",
        "accounts": [
            {"usuario": "Wisegangauto", "password": "Auto1989!@"},
            {"usuario": "AmandasPBOT", "password": "Focus999@@159"},
            {"usuario": "playerbot", "password": "TIme2plan!$"},
            {"usuario": "ABTDCDistro", "password": "ABCDEFDis2025!"},
            {"usuario": "ACNOABtap175", "password": "Baltapz!!4ev4"},
        ],
    },
    "GAME VAULT": {
        "url": "https://agent.gamevault999.com/login",
        "accounts": [
            {"usuario": "perubot", "password": "Lima123!@#"},
            {"usuario": "Autostore", "password": "Auto1989!@#"},
            {"usuario": "AmandaP_BOT", "password": "Focus999@@159"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "kcheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "whatever", "password": "Mkingdom7"},
            {"usuario": "iluckyroomGV", "password": "fP95yrWM"},
            {"usuario": "a5games", "password": "reseT99_!"},
            {"usuario": "ReggiesProducts01", "password": "Winning2563"},
            {"usuario": "GVStoreDistro", "password": "!GVStoreDistros125$#1"},
            {"usuario": "GVotDTapBno1", "password": "GVPSWFJQM1!&613"},
        ],
    },
    "HIGHSTAKES": {
        "url": "https://ht.highstakesweeps.com/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
        ],
    },
    "GALAXY WORLD": {
        "url": "https://agent.galaxyworld999.com/login",
        "accounts": [
            {"usuario": "automated", "password": "Auto1989!@"},
            {"usuario": "bworldweb007", "password": "Agent@884"},
            {"usuario": "ReggiesProducts01", "password": "Winning5392"},
        ],
    },
    "GAME ROOM": {
        "url": "https://agentserver.gameroom777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebBOT", "password": "Ballerz777$"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "kobecheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "MKingdomGRO", "password": "Mushking123@"},
            {"usuario": "a5games", "password": "H4!leys8888"},
        ],
    },
    "CASH MACHINE": {
        "url": "https://agentserver.cashmachine777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebCashier", "password": "Ballerz777!"},
            {"usuario": "slapit", "password": "Sl4piTG@m3z"},
            {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            {"usuario": "a5games", "password": "H4!leys8888"},
            {"usuario": "CashCaxaTap", "password": "CaxTap$123!3"},
        ],
    },
    "VEGAS SWEEPS": {
        "url": "https://agent.lasvegassweeps.com/login",
        "accounts": [
            {"usuario": "autostore", "password": "Auto1989!@"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            {"usuario": "a5games", "password": "HaiLey8888"},
        ],
    },
    "MAFIA": {
        "url": "https://agentserver.mafia77777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebCashier", "password": "Ballerz777!"},
            {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            {"usuario": "a5games", "password": "H4!leys8888"},
            {"usuario": "MafCashq112", "password": "C4shM4f6598*"},
        ],
    },
    "NOBLE": {
        "url": "https://agentserver.noble777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebCashier", "password": "Ballerz777!"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            {"usuario": "a5games", "password": "H4!leys8888"},
            {"usuario": "TapDsCash13r", "password": "NotC13rtzx!"},
        ],
    },
    "Win Star": {
        "url": "https://agent.winstar99999.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
            {"usuario": "WebBOT", "password": "Winning777"},
            {"usuario": "kobe", "password": "OaKcR3ekD4v"},
            {"usuario": "A5games", "password": "HaiLey8888"},
            {"usuario": "TapWinCash", "password": "Tap3WinCa3b2"},
        ],
    },
    "Mr. All In One": {
        "url": "https://agentserver.mrallinone777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "TAPMRCashier", "password": "TAPMrCash3!!"},
        ],
    },
    "LUCKY STARS": {
        "url": "https://agent.luckystars.games/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "WebBOT", "password": "Ballerz777$"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            {"usuario": "oakcreek", "password": "OaKcR3ekD4v!"},
            {"usuario": "haileygames", "password": "H4!leys8888"},
            {"usuario": "TapLuckyCash", "password": "TapDi3sCas!"},
        ],
    },
    "VEGAS X": {
        "url": "https://cashier.vegas-x.org/login",
        "accounts": [
            {"usuario": "WisegangAuto", "password": "Auto1989!@"},
            {"usuario": "bworldweb007", "password": "Agent38"},
            {"usuario": "slapgames", "password": "Sl4piTG@m3z!"},
            {"usuario": "oakcreek", "password": "OaKcR3ekD4v!"},
            {"usuario": "iluckyroomVX", "password": "pjDTF4p7"},
            {"usuario": "haileygame", "password": "hailey23!"},
        ],
    },
    "MEGA SPIN": {
        "url": "https://megaspinpay.com/",
        "accounts": [
            {"usuario": "Wisegang26amu", "password": "Auto1989!@"},
            {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@"},
            {"usuario": "a5games", "password": "hailey8800"},
        ],
    },
    "River Sweeps": {
        "url": "https://river-pay.com/office/login/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "OceanSluggerz01_Bot", "password": "Winning@@278"},
            {"usuario": "iLuckyRS_CashLuckyR", "password": "River$1234"},
            # {"usuario": "ReggiesProducts", "password": "Winning2"},
            {"usuario": "RVTDCDistro", "password": "RVTDCDishggsdjt5azys123!#"},
            {"usuario": "CASHriverTAPsweeps1", "password": "DTTG+Riv12456"},
        ],
    },
    "100 PLUS": {
        "url": "https://888.100plus.me",
        "accounts": [
            {"usuario": "USNBGamesBot001", "password": "Focus100123", "password2": "131854"},
        ],
    },
    "CASH FRENZY": {
        "url": "https://agentserver.cashfrenzy777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "whatever", "password": "Mkingdom7@"},
            {"usuario": "CFTaCaSt0", "password": "CashNo34zsq!"},
        ],
    },
    "BLUE DRAGON": {
        "url": "https://agent.bluedragon777.com/Login.aspx",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
           # {"usuario": "ReggiesProducts", "password": "Winning1857"},
        ],
    },
    "EASY STREET": {
        "url": "https://agent.easystreet777.com:8088/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
        ],
    },
    "FISH GLORY": {
        "url": "https://dxr.fishglory.games/#/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
        ],
    },
    "GEMINI": {
        "url": "http://admin.gemini777.io/",
        "accounts": [
            {"usuario": "NBGamesBot", "password": "Focus100@@123"},
            {"usuario": "ReggiesProducts", "password": "Winning7367"},
        ],
    },
    "GLAMOUR SPIN": {
        "url": "https://acwwf.glamourspin.mobi/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
        ],
    },
    "HIGHROLLER": {
        "url": "https://highroller.cc//",
        "accounts": [
            {"usuario": "NEWBGamesBot", "password": "Focus100_123"},
        ],
    },
    "JACKPOT FRENZY": {
        "url": "https://admin.spinfindo.com/#/login",
        "accounts": [
            {"usuario": "Crystal", "password": "Focus100@"},
        ],
    },
    "JOKER": {
        "url": "https://agent.joker777.win/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "Jok3rCashQ", "password": "NoTacA!jOK1!"},
        ],
    },
    "KING OF POP": {
        "url": "http://agentserver.slots88888.com:8003/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "oakcreek", "password": "gAmES4Uo@K"},
            {"usuario": "a5games", "password": "H4!leys8888"},
        ],
    },
    "KRAKEN": {
        "url": "https://krakenbackend.com:8781/default.aspx",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
        ],
    },
    "LEGEND FIRE": {
        "url": "https://yadsz.legendfire.xyz/#/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
        ],
    },
    "LOOT": {
        "url": "https://client.lootgame777.com/login",
        "accounts": [
            {"usuario": "NEWBGamesC", "password": "Focus@@123"},
        ],
    },
    "MOOLAH": {
        "url": "https://moolah.vip:8781/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989"},
        ],
    },
    "RIVER MONSTER": {
        "url": "https://www.rm-pay.com:8888/",
        "accounts": [
            {"usuario": "NEWBGamesC", "password": "Focus100_123"},
        ],
    },
    "SIRIUS": {
        "url": "https://agent.gamesirius999.com/login/",
        "accounts": [
            {"usuario": "NEWBGamesCashier", "password": "Focus100@@123"},
        ],
    },
    "SUPER DRAGON": {
        "url": "https://dailyug.com/gmpc/login",
        "accounts": [
            {"usuario": "oakcreek", "password": "OaKcR3ekD4ve"},
            {"usuario": "hailey", "password": "HaiLey8888"},
        ],
    },
    "VEGAS ROLL": {
        "url": "https://backend.vegas-roll.com/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "TapStoas689", "password": "TapAsSor33!q"},
        ],
    },
    "WINNERS CLUB": {
        "url": "http://agent.winnersclub777.com:8003/admin/login/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
        ],
    },
    "YOLO": {
        "url": "https://agent.yolo777.top/",
        "accounts": [
            {"usuario": "Autostore1", "password": "Auto1989!@"},
            {"usuario": "ReggiesProducts01", "password": "Winning7172"},
        ],
    },
    "LUCKY PARADISE": {
        "url": "https://agent.luckyparadise777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@"},
            {"usuario": "playerstore1", "password": "Monchie21!"},
        ],
    },
    "Fire Phoenix":{
        "url": "http://pos.fpc-mob.com/",
        "accounts": [
            {"usuario": "Autostoree2026", "password": "Auto1989!"},
        ]
    }
    # Agrega más juegos aquí...
}

# Grupos definidos con sus compañías
GRUPOS_COMPANIAS = {
    "Tierlock": [
        "The Fun Room", "Slots Gone Wild", "JJsreelsadventures", "Lucky Luxe", "Snarcade", "Lucky Buddy", "Devine Slots", "BordersWay", "Pandagod", "The Players Lounge",
    ],
    "TAP": [
        "JLEnt"
    ],
    "PPP": [
        "Play Play Play", "Lucky Lady", "The Cash Cove"
    ],
    "Wise Gang": [
        "Wise Gang", "Token Tiger", "Innercore Games", "Fast Fortunes"
    ],
    "Ballerz": [
        "Ballerz World of Gamez"
    ],
    "Slap It": [
        "Slap It"
    ],
    "Oak Creek": [
        "Play OakCreek"
    ],
    "Slap It y Oak Creek": [
        "Slap It", "Play OakCreek"
    ],
    "Mushroom Kingdom": [
        "Mushroom Kingdom"
    ],
    "Ocean Sluggerz": [
        "Ocean Sluggerz"
    ],
    "Lucky Room": [
        "Lucky Room"
    ],
    "Hailey Games": [
        "Hailey Games"
    ],
    "Players Club": [
        "The Players Club"
    ]

}

# Asignación de grupo por usuario
USERS_GRUPOS = {

    # Orion Stars
    "LupesweepsOS": "PPP",
    "Wisegangautostore": "Wise Gang",
    "AmandaP_BOT": "Ballerz",
    "slapitgames3": "Slap It",
    "kobegames3": "Oak Creek",
    "MKingdomOS": "Mushroom Kingdom",
    "OceanSluggerz01_Cashier": "Ocean Sluggerz",
    "LuckyCas": "Lucky Room",
    "a5games3": "Hailey Games",
    "ReggiesProducts_Cashier": "Players Club",
    "CashierTDCRB1": "Tierlock",
    "CashierTAPEC_1": "TAP",

    # Fire Kirin
    "VasquezCash": "PPP",
    "Wisegangautostore": "Wise Gang",
    "AmandaP_BOT": "Ballerz",
    "slapitgames": "Slap It",
    "kobe": "Oak Creek",
    "whatever": "Mushroom Kingdom",
    "OceanSluggerz01_Cashier": "Ocean Sluggerz",
    "IluckyroomFK": "Lucky Room",
    "a5games": "Hailey Games",
    "ReggiesProducts_Cashier": "Players Club",
    "CashierTDCRB1": "Tierlock",
    "TAPTS_CSH_1": "TAP",

    # Panda Master
    "LVasquezPMc": "PPP",
    "Wisegangautostore": "Wise Gang",
    "AmandaP_BOT": "Ballerz",
    "slapitgames": "Slap It",
    "kobe": "Oak Creek",
    "whatever": "Mushroom Kingdom",
    "OceanSluggerz001_Cashier": "Ocean Sluggerz",
    "a5games": "Hailey Games",
    "ReggiesProducts_Cashier": "Players Club",
    "CashierTDCRB1": "Tierlock",
    "TdcTaPm_Cash1": "TAP",

    # Milky Way
    "CashierLV": "PPP",
    "Autostore": "Wise Gang",
    "bworldweb007": "Ballerz",
    "OceanSluggerz01_Cashier": "Ocean Sluggerz",
    "MWTapCash": "TAP",

    # Vblink
    "Atencionpre1": "PPP",
    "Autostore": "Wise Gang",
    "WebsiteCashier": "Ballerz",
    "slapitnow": "Slap It",
    "playoakcreek": "Oak Creek",
    "Whatever777": "Mushroom Kingdom",
    "OceanSluggerz01B": "Ocean Sluggerz",
    "Cashilucky": "Lucky Room",
    "HaileyBE": "Hailey Games",
    "playerbot": "Players Club",
    "DisTDCroVB15163": "Tierlock",
    "VtapBLINK182CASH": "TAP",

    # Ultra Panda
    "Atencionpre": "PPP",
    "Automatedside": "Wise Gang",
    "WebsiteBOT": "Ballerz",
    "slapitnow": "Slap It",
    "playoakcreek": "Oak Creek",
    "Whatever777": "Mushroom Kingdom",
    "OceanSluggerz01B": "Ocean Sluggerz",
    "CashiluckyR": "Lucky Room",
    "HaileyBE": "Hailey Games",
    "playerbot": "Players Club",
    "UPTDCSUB19751": "Tierlock",
    "TAuPSub1LPMP": "TAP",

    # Golden Treasure
    "Perubot": "PPP",
    "Autostore1": "Wise Gang",
    "AmandasPBOT": "Ballerz",
    "iluckyCash": "Lucky Room",
    "playerbot": "Players Club",
    "GTDCCSUB35857": "Tierlock",
    "TapDBGTSub123": "TAP",

    # Egame
    "Perubot": "PPP",
    "Autostore": "Wise Gang",
    "BallerzWebBOT": "Ballerz",
    "ReggiesProducts1": "Players Club",
    "DisTDCroVB15163": "Tierlock",
    "TAPEGGsBOT0": "TAP",

    # Ace Book
    "Wisegangauto": "Wise Gang",
    "AmandasPBOT": "Ballerz",
    "playerbot": "Players Club",
    "ABTDCDistro": "Tierlock",
    "ACNOABtap175": "TAP",

    # Juwa
    "PeruLogin": "PPP",
    "autostore": "Wise Gang",
    "AmandaP_BOT": "Ballerz",
    "slapitgames": "Slap It",
    "kcheung": "Oak Creek",
    "Whatever777": "Mushroom Kingdom",
    "OceanSluggerz01_Cashier": "Ocean Sluggerz",
    "iluckyroomjw": "Lucky Room",
    "a5games": "Hailey games",
    "JWStoreDistro": "Tierlock",
    "TAPJuwaMewa6131": "TAP",

    # Game Vault
    "perubot": "PPP",
    "Autostore": "Wise Gang",
    "AmandaP_BOT": "Ballerz",
    "slapitgames": "Slap It",
    "kcheung": "Oak Creek",
    "whatever": "Mushroom Kingdom",
    "iluckyroomGV": "Lucky Room",
    "a5games": "Hailey Games",
    "ReggiesProducts01": "Players Club",
    "GVStoreDistro": "Tierlock",
    "GVotDTapBno1": "TAP",

    # Highstakes
    "Autostore": "Wise Gang",

    # Galaxy World
    "automated": "Wise Gang",
    "bworldweb007": "Ballerz",
    "ReggiesProducts01": "Players Club",

    # Gameroom
    "Autostore": "Wise Gang",
    "WebBOT": "Ballerz",
    "slapitgames": "Slap It",
    "kobecheung": "Oak Creek",
    "MKingdomGRO": "Mushroom Kingdom",
    "a5games": "Hailey Games",

    # Cash Machine
    "Autostore": "Wise Gang",
    "WebCashier": "Ballerz",
    "slapit": "Slap It",
    "kobe": "Oak Creek",
    "a5games": "Hailey",
    "CashCaxaTap": "TAP",

    # Vegas Sweeps
    "autostore": "Wise Gang",
    "slapitgames": "Slap It",
    "kobe": "Oak Creek",
    "a5games": "Hailey Games",

    # Mafia
    "Autostore": "Wise Gang",
    "WebCashier": "Ballerz",
    "kobe": "Oak Creek",
    "a5games": "Hailey Games",
    "MafCashq112": "TAP",

    # Noble
    "Autostore": "Wise Gang",
    "WebCashier": "Ballerz",
    "slapitgames": "Slap It",
    "kobe": "Oak Creek",
    "a5games": "Hailey Games",
    "TapDsCash13r": "TAP",

    # Winstar
    "Autostore": "Wise Gang",
    "WebBOT": "Ballerz",
    "kobe": "Oak Creek",
    "A5games": "Hailey Games",
    "TapWinCash": "TAP",

    # Mr All in One
    "Autostore": "Wise Gang",
    "TAPMRCashier": "TAP",

    # Lucky Stars
    "Autostore": "Wise Gang",
    "WebBOT": "Ballerz",
    "slapitgames": "Slap It",
    "oakcreek": "Oak Creek",
    "haileygames": "Hailey Games",
    "TapLuckyCash": "TAP",

    # Vegas X
    "Autostore1": "Wise Gang",
    "bworldweb007": "Ballerz",
    "slapgames": "Slap It",
    "oakcreek": "Oak Creek",
    "iluckyroomVX": "Lucky Room",
    "haileygame": "Hailey Games",

    # Mega Spin
    "Wisegang26amu": "Wise Gang",
    # "slapitgames": "Slap It",
    "kobe": "Oak Creek",
    "whatever": "Mushroom Kingdom",
    "a5games": "Hailey Games",

    # Riversweeps
    "Autostore": "Wise Gang",
    "OceanSluggerz01_Bot": "Ocean Sluggerz",
    "iLuckyRS_CashLuckyR": "Lucky Room",
    "ReggiesProducts": "Players Club",
    "RVTDCDistro": "Tierlock",
    "CASHriverTAPsweeps1": "TAP",

    # 100 Plus
    "USNBGamesBot001": "Wise Gang",

    # Cash Frenzy
    "Autostore": "Wise Gang",
    "whatever": "Mushroom Kingdom",
    "CFTaCaSt0": "TAP",

    # Blue Dragon
    "Autostore": "Wise Gang",
    "ReggiesProducts": "Players Club",

    # Easy Street
    "Autostore": "Wise Gang",

    # Fish Glory
    "Autostore": "Wise Gang",

    # Gemini
    "NBGamesBot": "Wise Gang",
    "ReggiesProducts": "Players Club",

    # Glamour Spin
    "Autostore": "Wise Gang",

    # Highroller
    "NEWBGamesBot": "Wise Gang",

    # Jackpot Frenzy
    "Crystal": "Wise Gang",

    # Joker
    "Autostore": "Wise Gang",
    "Jok3rCashQ": "TAP",

    # King of Pop
    "Autostore": "Wise Gang",
    "oakcreek": "Oak Creek",
    "a5games": "Hailey Games",

    # Kraken
    "Autostore": "Wise Gang",

    # Legend Fire
    "Autostore": "Wise Gang",

    # Loot
    "NEWBGamesC": "Wise Gang",

    # Moolah
    "Autostore": "Wise Gang",

    # River Monster
    "NEWBGamesC": "Wise Gang",

    # Sirius
    "NEWBGamesCashier": "Wise Gang",

    # Super Dragon
    "oakcreek": "Oak Creek",
    "hailey": "Hailey Games",

    # Vegas Roll
    "Autostore": "Wise Gang",
    "TapStoas689": "TAP",

    # Winners Club
    "Autostore": "Wise Gang",

    # Yolo
    "Autostore1": "Wise Gang",
    "ReggiesProducts01": "Players Club",

    # Black Mamba
    "Wisegangauto": "Wise Gang",

    # Lucky Paradise
    "Autostore": "Wise Gang",
    "playerstore1": "Players Club"

}

CAPTCHA_GRUPOS = {
    "grupo1": [
        "ORION STARS",
        "FIRE KIRIN",
        "PANDA MASTER",
        "MILKY WAY",
        "MOOLAH",
        "RIVER MONSTER",
        "KRAKEN",
    ],
    "grupo2": [
        "CASH FRENZY",
        "CASH MACHINE",
        "GAME ROOM",
        "JOKER",
        "LUCKY STARS",
        "MAFIA",
        "Mr. All In One",
        "NOBLE",
        "VEGAS ROLL",
        "WINNERS CLUB",
        "Win Star",
    ],
    "grupo3": [
        # "GALAXY WORLD",
        "GAME VAULT",
        "HIGHSTAKES",
        "JUWA",
        "LOOT",
        "LUCKY PARADISE",
        "SIRIUS",
        "VEGAS SWEEPS",
    ]
}





bulk_docs = []

for website, info in WEBSITES.items():
    for acc in info["accounts"]:
        username = acc["usuario"]
        compania = USERS_GRUPOS.get(username, None)
        bulk_docs.append({
            "website": website,
            "username": username,
            "password": acc["password"],
            "grupo": compania
        })

# ✅ SOLO ejecutar cuando se corre directamente, NO al importar
if __name__ == "__main__":
    client = pymongo.MongoClient("mongodb+srv://kam_db_user:VJbs7fgYKJokO9pz@cluster0.e8doyfk.mongodb.net/?appName=Cluster0")
    db = client["plataforma_finanzas"]
    collection = db["cuentas_companias"]
    
    # Opcional: borrar duplicados antes de insertar
    print("Limpiando duplicados existentes...")
    collection.delete_many({})  # O usa el script de mongosh que te di
    
    collection.insert_many(bulk_docs)
    print(f"✓ Insertados {len(bulk_docs)} documentos en cuentas_companias")
