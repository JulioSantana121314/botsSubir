import os
from dotenv import load_dotenv
import pymongo

load_dotenv()

# Tu diccionario original de juegos, cuentas y passwords
WEBSITES = {
    "ORION STARS": {
        "url": "https://orionstars.vip:8781/default.aspx",
        "accounts": [
            {"usuario": "LupesweepsOS", "password": '!@PEus4321', "grupo": "PPP"},
            {"usuario": "Wisegangautostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "AmandaP_BOT", "password": "Focus999@@159", "grupo": "Ballerz"},
            # {"usuario": "slapitgames3", "password": "Sl4piTG@m3z!"}, #SI
            # {"usuario": "kobegames3", "password": "OaKcR3ekD4ve!!"}, #OC
            {"usuario": "Whatever777", "password": "Mkingdom77@@", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987@#6152", "grupo": "Ocean Sluggerz"},
            {"usuario": "LuckyCas", "password": "Lucky9709@!$", "grupo": "Lucky Room"},
            # {"usuario": "a5games3", "password": "haileysPh656!@"}, #HG
            {"usuario": "ReggiesProducts_Cashier", "password": "Monchie21Monchie21!!", "grupo": "Players Club"},
            {"usuario": "CashierTDCRB1", "password": 'DVASBFU!"182571982152', "grupo": "Tierlock"},
            {"usuario": "CashierTAPEC_1", "password": "TAPsdpTDC_62!", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234!!", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989!@2025", "grupo": "Wysaro"},
        ],
    },
    "JUWA": {
        "url": "https://ht.juwa777.com/login",
        "accounts": [
            {"usuario": "PeruLogin", "password": "newone123", "grupo": "PPP"},
            {"usuario": "autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "AmandaP_BOT", "password": "Focus999@@159", "grupo": "Ballerz"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "kcheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "Whatever777", "password": "Mkingdom7", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987@#6152", "grupo": "Ocean Sluggerz"},
            {"usuario": "iluckyroomjw", "password": "Juwa$777", "grupo": "Lucky Room"},
            # {"usuario": "a5games", "password": "HaiLey8888"},
            {"usuario": "JWStoreDistro", "password": "JWStoreDistro123!#$", "grupo": "Tierlock"},
            {"usuario": "TAPJuwaMewa6131", "password": "JurTapMyTap!875", "grupo": "TAP"},
            {"usuario": "tokenT26", "password": "Resetme1234", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989", "grupo": "Wysaro"},
        ],
    },
    "FIRE KIRIN": {
        "url": "https://firekirin.xyz:8888/default.aspx",
        "accounts": [
            {"usuario": "VasquezCash", "password": "!@PEus4321", "grupo": "PPP"},
            {"usuario": "Wisegangautostore", "password": "Auto1989", "grupo": "Wise Gang"},
            {"usuario": "AmandaP_BOT", "password": "Focus999159", "grupo": "Ballerz"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987_6152", "grupo": "Ocean Sluggerz"},
            {"usuario": " IluckyroomFK", "password": "k3wMBwN6", "grupo" : "Lucky Room"},
            # {"usuario": "a5games", "password": "!Hailey_8800_!"},
            {"usuario": "ReggiesProducts_Cashier", "password": "Winning6543", "grupo": "Players Club"},
            {"usuario": "CashierTDCRB1", "password": "DVASBFU_81236871250", "grupo": "Tierlock"},
            {"usuario": "TAPTS_CSH_1", "password": "fkes1dragon", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989", "grupo": "Wysaro"},
        ],
    },
    "PANDA MASTER": {
        "url": "https://pandamaster.vip/default.aspx",
        "accounts": [
            {"usuario": "LVasquezPMc", "password": "Free123!@#", "grupo": "PPP"},
            {"usuario": "Wisegangautostore", "password": "Auto1989", "grupo": "Wise Gang"},
            {"usuario": "AmandaP_BOT", "password": "Focus999159", "grupo": "Ballerz"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz001_Cashier", "password": "Focus987_6152", "grupo": "Ocean Sluggerz"},
            # {"usuario": "a5games", "password": "!Hailey_8800_!"},
            {"usuario": "ReggiesProducts_Cashier", "password": "Winning4276", "grupo": "Players Club"},
            {"usuario": "CashierTDCRB1", "password": "192371_pm_DVASBFU", "grupo": "Tierlock"},
            {"usuario": "TdcTaPm_Cash1", "password": "TaptapcashPM_127", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234", "grupo": "Token Tiger"},
            {"usuario": "Pandagod", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989", "grupo": "Wysaro"},
        ],
    },
    "MILKY WAY": {
        "url": "https://milkywayapp.xyz:8781/Store.aspx",
        "accounts": [
            {"usuario": "CashierLV", "password": "!@PEus4321", "grupo": "PPP"},
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
            {"usuario": "bworldweb007", "password": "Agent38", "grupo": "Ballerz"},
            {"usuario": "OceanSluggerz01_Cashier", "password": "Focus987_6152", "grupo": "Ocean Sluggerz"},
            {"usuario": "MWTapCash", "password": "BashCraqZs_2", "grupo": "TAP"},
            {"usuario": "Pandagod26", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
        ],
    },
    "VBLINK": {
        "url": "https://gm.vblink777.club/#/login?redirect=%2Findex",
        "accounts": [
            {"usuario": "atencionpre1", "password": "PPPE@$123456", "grupo" : "PPP"},
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebsiteCashier", "password": "Winning@7777", "grupo": "Ballerz"},
            # {"usuario": "slapitnow", "password": "$l@p$l@p8#8"},
            # {"usuario": "playoakcreek", "password": "0aKcR33kpL@y!"},
            {"usuario": "Whatever777", "password": "Mkingdom777@", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz01B", "password": "Focus987@#6152", "grupo": "Ocean Sluggerz"},
            {"usuario": "Cashilucky", "password": "v53FMZcg$123", "grupo": "Lucky Room"},
            # {"usuario": "HaileyBE", "password": "Haileys8825!@"},
            {"usuario": "playerbot", "password": "TIme2plan!$", "grupo": "Players Club"},
            {"usuario": "DisTDCroVB15163", "password": "TDCvbCPRV!61365", "grupo": "Tierlock"},
            {"usuario": "VtapBLINK182CASH", "password": "TapTopVbSAC11!", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234$", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": "PMAdmin567!@", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Wysar0G41!5a", "grupo": "Wysaro"},
        ],
    },
    "ULTRA PANDA": {
        "url": "https://ht.ultrapanda.mobi/#/login",
        "accounts": [
            {"usuario": "atencionpre", "password": "PPPE@$123456", "grupo" : "PPP"},
            {"usuario": "Automatedside", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebsiteBOT", "password": "Winning@7777", "grupo": "Ballerz"},
            # {"usuario": "slapitnow", "password": "$l@p$l@p8#8"},
            # {"usuario": "playoakcreek", "password": "0aKcR33kpL@y!"},
            {"usuario": "Whatever777", "password": "Mkingdom777@", "grupo": "Mushroom Kingdom"},
            {"usuario": "OceanSluggerz01B", "password": "Focus987@#6152", "grupo": "Ocean Sluggerz"},
            {"usuario": "CashiluckyR", "password": "UltraPanda$1$1", "grupo": "Lucky Room"},
            # {"usuario": "HaileyBE", "password": "Haileys8825!@"},
            {"usuario": "playerbot", "password": "TIme2plan!$", "grupo": "Players Club"},
            {"usuario": "UPTDCSUB19751", "password": "tudpc182351soobs", "grupo": "Tierlock"},
            {"usuario": "TAuPSub1LPMP", "password": "Tap@TappinUP44!", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234$", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": "PMAdmin567!@", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Wysar0G41!5", "grupo": "Wysaro"},
        ],
    },
    "GOLDEN TREASURE": {
        "url": "https://fus.goldentreasure.mobi/?#/login",
        "accounts": [
            {"usuario": "Perubot", "password": "AtGC123456!!", "grupo": "PPP"},
            {"usuario": "Autostore1", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "AmandasPBOT", "password": "Focus999@@159", "grupo": "Ballerz"},
            {"usuario": "iluckyCash", "password": "GoldenT111$", "grupo": "Lucky Room"},
            {"usuario": "playerbot", "password": "TIme2plan!$", "grupo": "Players Club"},
            {"usuario": "GTDCCSUB35857", "password": "gtdcsub835gt2", "grupo": "Tierlock"},
            {"usuario": "TapDBGTSub123", "password": "PanPass91!67", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234$", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": "PMAdmin567!@", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Wysar0G41!", "grupo": "Wysaro"},
        ],
    },
    "Egames": {
        "url": "https://pko.egame99.club/",
        "accounts": [
            {"usuario": "Perubot", "password": "AtXG123456!!", "grupo": "PPP"},
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "BallerzWebBOT", "password": "Baller$1578Z", "grupo": "Ballerz"},
            {"usuario": "ReggiesProducts1", "password": "Monchie21!", "grupo": "Players Club"},
            {"usuario": "DisTDCroVB15163", "password": "EGTDCroVB15164", "grupo": "Tierlock"},
            {"usuario": "TAPEGGsBOT0", "password": "BreakfastBun234!", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234$", "grupo": "Token Tiger"},
            {"usuario": "Pandagod", "password": "PMAdmin567!@", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Wysar0G4m1!", "grupo": "Wysaro"},
        ],
    },
    "ACE BOOK": {
        "url": "https://djwae.playacebook.mobi/#/login",
        "accounts": [
            {"usuario": "Wisegangauto", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "AmandasPBOT", "password": "Focus999@@159", "grupo": "Ballerz"},
            {"usuario": "playerbot", "password": "TIme2plan!$", "grupo": "Players Club"},
            {"usuario": "ABTDCDistro", "password": "ABCDEFDis2025!", "grupo": "Tierlock"},
            {"usuario": "ACNOABtap175", "password": "Baltapz!!4ev4", "grupo": "TAP"},
            {"usuario": "Pandagod26", "password": "PMAdmin567!@", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Wysar0G4!", "grupo": "Wysaro"},
        ],
    },
    "GAME VAULT": {
        "url": "https://agent.gamevault999.com/login",
        "accounts": [
            {"usuario": "perubot", "password": "Lima123!@#", "grupo": "PPP"},
            {"usuario": "Autostore", "password": "Auto1989!@#", "grupo": "Wise Gang"},
            {"usuario": "Amandap01_bot", "password": "Winner789!", "grupo": "Ballerz"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "kcheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "whatever", "password": "Mkingdom7", "grupo": "Mushroom Kingdom"},
            {"usuario": "iluckyroomGV", "password": "fP95yrWM", "grupo": "Lucky Room"},
            # {"usuario": "a5games", "password": "reseT99_!"},
            {"usuario": "ReggiesProducts01", "password": "Winning2563", "grupo": "Players Club"},
            {"usuario": "GVStoreDistro", "password": "!GVStoreDistros125$#1", "grupo": "Tierlock"},
            {"usuario": "GVotDTapBno1", "password": "GVPSWFJQM1!&613", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234!", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": "Money1234!", "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989!@", "grupo": "Wysaro"},
        ],
    },
    "HIGHSTAKES": {
        "url": "https://ht.highstakesweeps.com/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
        ],
    },
    "GALAXY WORLD": {
        "url": "https://agent.galaxyworld999.com/login",
        "accounts": [
            {"usuario": "automated", "password": "Auto1989!@", "grupo": "Wise Gang"},
            # {"usuario": "bworldweb007", "password": "Agent@884", "grupo": "Ballerz"},
            {"usuario": "ReggiesProducts01", "password": "Winning5392", "grupo": "Players Club"},
        ],
    },
    "GAME ROOM": {
        "url": "https://agentserver.gameroom777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebBOT", "password": "Ballerz777$", "grupo": "Ballerz"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "kobecheung", "password": "OaKcR3ekD4v!"},
            {"usuario": "MKingdomGRO", "password": "Mushking123@", "grupo": "Mushroom Kingdom"},
            # {"usuario": "a5games", "password": "H4!leys8888"},
        ],
    },
    "CASH MACHINE": {
        "url": "https://agentserver.cashmachine777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebCashier", "password": "Ballerz777!", "grupo": "Ballerz"},
            # {"usuario": "slapit", "password": "Sl4piTG@m3z"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            # {"usuario": "a5games", "password": "H4!leys8888"},
            {"usuario": "CashCaxaTap", "password": "CaxTap$123!3", "grupo": "TAP"},
        ],
    },
    "VEGAS SWEEPS": {
        "url": "https://agent.lasvegassweeps.com/login",
        "accounts": [
            {"usuario": "autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            # {"usuario": "a5games", "password": "HaiLey8888"},
        ],
    },
    "MAFIA": {
        "url": "https://agentserver.mafia77777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebCashier", "password": "Ballerz777!", "grupo": "Ballerz"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            # {"usuario": "a5games", "password": "H4!leys8888"},
            {"usuario": "MafCashq112", "password": "C4shM4f6598*", "grupo": "TAP"},
        ],
    },
    "NOBLE": {
        "url": "https://agentserver.noble777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebCashier", "password": "Ballerz777!", "grupo": "Ballerz"},
            {"usuario": "TapDsCash13r", "password": "NotC13rtzx!", "grupo": "TAP"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4v!"},
            # {"usuario": "a5games", "password": "H4!leys8888"},
        ],
    },
    "Win Star": {
        "url": "https://agent.winstar99999.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
            {"usuario": "WebBOT", "password": "Winning777", "grupo": "Ballerz"},
            {"usuario": "TapWinCash", "password": "Tap3WinCa3b2", "grupo": "TAP"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4v"},
            # {"usuario": "A5games", "password": "HaiLey8888"},
        ],
    },
    "Mr. All In One": {
        "url": "https://agentserver.mrallinone777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "TAPMRCashier", "password": "TAPMrCash3!!", "grupo": "TAP"},
        ],
    },
    "LUCKY STARS": {
        "url": "https://agent.luckystars.games/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "WebBOT", "password": "Ballerz777$", "grupo": "Ballerz"},
            {"usuario": "TapLuckyCash", "password": "TapDi3sCas!", "grupo": "TAP"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z"},
            # {"usuario": "oakcreek", "password": "OaKcR3ekD4v!"},
            # {"usuario": "haileygames", "password": "H4!leys8888"},
        ],
    },
    "VEGAS X": {
        "url": "https://cashier.vegas-x.org/login",
        "accounts": [
            {"usuario": "WisegangAuto", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "bworldweb007", "password": "Agent38", "grupo": "Ballerz"},
            # {"usuario": "slapgames", "password": "Sl4piTG@m3z!"},
            # {"usuario": "oakcreek", "password": "OaKcR3ekD4v!"},
            {"usuario": "iluckyroomVX", "password": "pjDTF4p7", "grupo": "Lucky Room"},
            # {"usuario": "haileygame", "password": "hailey23!"},
        ],
    },
    "MEGA SPIN": {
        "url": "https://megaspinpay.com/",
        "accounts": [
            {"usuario": "Wisegang26amu", "password": "Auto1989!@", "grupo": "Wise Gang"},
            # {"usuario": "slapitgames", "password": "Sl4piTG@m3z!"},
            # {"usuario": "kobe", "password": "OaKcR3ekD4ve!!"},
            {"usuario": "whatever", "password": "Mkingdom7@@", "grupo": "Mushroom Kingdom"},
            # {"usuario": "a5games", "password": "hailey8800"},
        ],
    },
    "River Sweeps": {
        "url": "https://river-pay.com/office/login/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "OceanSluggerz01_Bot", "password": "Winning@@278", "grupo": "Ocean Sluggerz"},
            {"usuario": "iLuckyRS_CashLuckyR", "password": "River$1234", "grupo": "Lucky Room"},
            # {"usuario": "ReggiesProducts", "password": "Winning2"},
            {"usuario": "RVTDCDistro", "password": "RVTDCDishggsdjt5azys123!#", "grupo": "Tierlock"},
            {"usuario": "CASHriverTAPsweeps1", "password": "DTTG+Riv12456", "grupo": "TAP"},
            {"usuario": "TokenT26", "password": "Resetme1234", "grupo": "Token Tiger"},
            {"usuario": "Pandagod26", "password": 'PMAdmin567!"', "grupo": "Pandagod"},
            {"usuario": "Wysaro26", "password": "Auto1989", "grupo": "Wysaro"},
        ],
    },
    "100 PLUS": {
        "url": "https://888.100plus.me",
        "accounts": [
            {"usuario": "USAutoside26", "password": "Auto1989", "password2": "198989", "grupo": "Wise Gang"},
        ],
    },
    "CASH FRENZY": {
        "url": "https://agentserver.cashfrenzy777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "whatever", "password": "Mkingdom7@", "grupo": "Mushroom Kingdom"},
            {"usuario": "CFTaCaSt0", "password": "CashNo34zsq!", "grupo": "TAP"},
        ],
    },
    "BLUE DRAGON": {
        "url": "https://agent.bluedragon777.com/Login.aspx",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
            # {"usuario": "ReggiesProducts", "password": "Winning1857"},
        ],
    },
    "EASY STREET": {
        "url": "https://agent.easystreet777.com:8088/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
        ],
    },
    "FISH GLORY": {
        "url": "https://dxr.fishglory.games/#/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
        ],
    },
    "GEMINI": {
        "url": "http://admin.gemini777.io/",
        "accounts": [
            {"usuario": "NBGamesBot", "password": "Focus100@@123", "grupo": "Wise Gang"},
            {"usuario": "ReggiesProducts", "password": "Winning7367", "grupo": "Players Club"},
        ],
    },
    "GLAMOUR SPIN": {
        "url": "https://acwwf.glamourspin.mobi/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
        ],
    },
    "HIGHROLLER": {
        "url": "https://highroller.cc//",
        "accounts": [
            {"usuario": "NEWBGamesBot", "password": "Focus100_123", "grupo": "Wise Gang"},
        ],
    },
    "JACKPOT FRENZY": {
        "url": "https://admin.spinfindo.com/#/login",
        "accounts": [
            {"usuario": "NBGamesBot01", "password": "Auto1989!@", "grupo": "Wise Gang"},
        ],
    },
    "JOKER": {
        "url": "https://agent.joker777.win/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "Jok3rCashQ", "password": "NoTacA!jOK1!", "grupo": "TAP"},
        ],
    },
    "KING OF POP": {
        "url": "http://agentserver.slots88888.com:8003/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            # {"usuario": "oakcreek", "password": "gAmES4Uo@K"},
            # {"usuario": "a5games", "password": "H4!leys8888"},
        ],
    },
    "KRAKEN": {
        "url": "https://krakenbackend.com:8781/default.aspx",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
        ],
    },
    "LEGEND FIRE": {
        "url": "https://yadsz.legendfire.xyz/#/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
        ],
    },
    "LOOT": {
        "url": "https://client.lootgame777.com/login",
        "accounts": [
            {"usuario": "NEWBGamesC", "password": "Focus@@123", "grupo": "Wise Gang"},
        ],
    },
    "MOOLAH": {
        "url": "https://moolah.vip:8781/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989", "grupo": "Wise Gang"},
        ],
    },
    "RIVER MONSTER": {
        "url": "https://www.rm-pay.com:8888/",
        "accounts": [
            {"usuario": "Autoside", "password": "Auto1989", "grupo": "Wise Gang"},
        ],
    },
    "SIRIUS": {
        "url": "https://agent.gamesirius999.com/login/",
        "accounts": [
            {"usuario": "NEWBGamesCashier", "password": "Focus100@@123", "grupo": "Wise Gang"},
        ],
    },
    "SUPER DRAGON": {
        "url": "https://dailyug.com/gmpc/login",

        "accounts": [
            # {"usuario": "oakcreek", "password": "OaKcR3ekD4ve"},
            # {"usuario": "hailey", "password": "HaiLey8888"},
        ],

    },
    "VEGAS ROLL": {
        "url": "https://backend.vegas-roll.com/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "TapStoas689", "password": "TapAsSor33!q", "grupo": "TAP"},
        ],
    },
    "WINNERS CLUB": {
        "url": "http://agent.winnersclub777.com:8003/admin/login/",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
        ],
    },
    "YOLO": {
        "url": "https://agent.yolo777.top/",
        "accounts": [
            {"usuario": "Autostore1", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "ReggiesProducts01", "password": "Winning7172", "grupo": "Players Club"},
        ],
    },
    "LUCKY PARADISE": {
        "url": "https://agent.luckyparadise777.com/admin/login",
        "accounts": [
            {"usuario": "Autostore", "password": "Auto1989!@", "grupo": "Wise Gang"},
            {"usuario": "playerstore1", "password": "Monchie21!", "grupo": "Players Club"},
        ],
    },
    "Fire Phoenix": {
        "url": "http://pos.fpc-mob.com/",
        "accounts": [
            {"usuario": "Autostoree2026", "password": "Auto1989!", "grupo": "Wise Gang"},
        ]
    }
}

# Grupos definidos con sus compañías
GRUPOS_COMPANIAS = {
    "Wysaro": [
        "Lucky Duck Lounge", "Simply Unmatched", "Lucky Shamrock", "Paper Route", "Crazy Coins", "Dragons Den", "Club Vpower",
    ],
    "Tierlock": [
        "The Fun Room", "Slots Gone Wild", "JJsreelsadventures", "Lucky Luxe", "Snarcade", "Lucky Buddy", "Devine Slots", "BordersWay", "The Players Lounge",
    ],
    "TAP": [
        "JLEnt"
    ],
    "PPP": [
        "Play Play Play", "Lucky Lady", "The Cash Cove"
    ],
    "Wise Gang": [
        "Wise Gang", "Innercore Games", "Fast Fortunes"
    ],
    "Ballerz": [
        "Ballerz World of Gamez"
    ],
    # "Slap It": [
    #     "Slap It"
    # ],
    # "Oak Creek": [
    #     "Play OakCreek"
    # ],
    # "Slap It y Oak Creek": [
    #     "Slap It", "Play OakCreek"
    # ],
    "Mushroom Kingdom": [
        "Mushroom Kingdom"
    ],
    "Ocean Sluggerz": [
        "Ocean Sluggerz"
    ],
    "Lucky Room": [
        "Lucky Room"
    ],
    # "Hailey Games": [
    #     "Hailey Games"
    # ],
    "Players Club": [
        "The Players Club"
    ],
    "Token Tiger": [
        "Token Tiger"
    ],
    "Pandagod": [
        "Pandagod"
    ],

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
        "GALAXY WORLD",
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
        bulk_docs.append({
            "website": website,
            "username": acc["usuario"],
            "password": acc["password"],
            "grupo": acc.get("grupo")
})

def obtener_grupo(username, website=None):
    """Busca el grupo de un usuario en WEBSITES"""
    for site, info in WEBSITES.items():
        if website and site.upper() != website.upper():
            continue
        for acc in info["accounts"]:
            if acc["usuario"] == username:
                return acc.get("grupo")
    return None

# ✅ SOLO ejecutar cuando se corre directamente, NO al importar
if __name__ == "__main__":
    client = pymongo.MongoClient(os.getenv('MONGO_URI'))
    db = client["plataforma_finanzas"]
    collection = db["cuentas_companias"]
    
    # Opcional: borrar duplicados antes de insertar
    print("Limpiando duplicados existentes...")
    collection.delete_many({})  # O usa el script de mongosh que te di
    
    collection.insert_many(bulk_docs)
    print(f"✓ Insertados {len(bulk_docs)} documentos en cuentas_companias")
