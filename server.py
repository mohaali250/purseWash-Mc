# -*- coding: utf-8 -*-
import datetime, json, random

from java.net import URL
from java.io import BufferedReader, InputStreamReader
from java.util import Scanner

from org.bukkit import Bukkit
from java.lang import Runnable

# CONFIG
URL_DATA = "https://raw.githubusercontent.com/mohaali250/server_plan_predicter_pack/main/calibration.json"


# ------------------------
# HTTP FETCH (Java way)
# ------------------------
def fetch_data():
    try:
        stream = URL(URL_DATA).openStream()
        scanner = Scanner(stream).useDelimiter("\\A")
        response = scanner.next() if scanner.hasNext() else None
        scanner.close()

        if response is None or response.strip() == "":
            print("Empty response from URL")
            return None

        print("RAW RESPONSE:", response[:200])
        return json.loads(response)

    except Exception as e:
        print("fetch_data error:", e)
        return None
# ------------------------
# CORE LOGIC (NO LOOP)
# ------------------------
def is_server_open(data):
    now = datetime.datetime.utcnow()

    crt = data["Credits"]
    dslp = data["Days_Since_last_pay"]
    lupd = datetime.datetime(*data["Last_Updated"])
    rq = data["required_credits"]
    getd = data["daily_credits"]
    data_type = data["load_type"]

    days_passed = (now - lupd).days

    if data_type != "absolute":
        Bukkit.getLogger().warning(
            '[37412][24/7 Plan Script] Data type ("{}") is invalid. Assuming data type is "absolute"'
            .format(data_type)
        )
    if days_passed < 0:
        Bukkit.getLogger().severe(
            '[37412][24/7 Plan Script] Variable days_passed returns an unhandelable value ({}), Please review and reset the calibration.json file'
            .format(days_passed)
        )
    if dslp < 0:
        Bukkit.getLogger().warning(
            '[37412][24/7 Plan Script] Variable dslp returns an unhandelable value ({}), Consider checking the calibration.json file. Setting value to the default (30)'
            .format(dslp)
        )
        dslp = 30
    cur = lupd
    cron = False

    for i in range(days_passed):
        cron = False
        dslp += 1
        crt += getd
        cur = cur + datetime.timedelta(days=1)
        if dslp > 30:
            if crt >= rq:
                crt -= rq
                dslp = 0
                cron = True
            else:
                cron = False
        else:
            cron = True
    if days_passed < 1:
        cron = False
        if dslp > 30:
            if crt >= rq:
                crt -= rq
                dslp = 0
                cron = True
            else:
                cron = False
        else:
            cron = True
    return cron
    """
    if dslp > 30 and crt < rq:
        return False
    return True"""

# ------------------------
# APPLY SERVER STATE
# ------------------------
def apply_state():
    data = fetch_data()
    if data is None:
        return
    allowed = is_server_open(data)

    now = datetime.datetime.utcnow()

    start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end = now.replace(hour=14, minute=0, second=0, microsecond=0)
    
    time_deny = not (start <= now <= end)
    
    should_open = allowed if allowed else time_deny

    print(now)

    if should_open:
        print("Server OPEN : ",allowed, time_deny)
    else:
        print("Server CLOSED : ",allowed, time_deny)
        # kick non-whitelisted players
        for p in Bukkit.getOnlinePlayers():
            p.kickPlayer("Ops... The server isnt on a 24/7 plan right now. Come back at 15:00 UTC+0. To check the predicted schedule, go to our discord server and download the schedule prediction script. Or alternatively use the link to check the web version")

        # optional: shutdown if empty
        if len(Bukkit.getOnlinePlayers()) == 0:
            Bukkit.shutdown()

# ------------------------
# SCHEDULER (runs every 60s)
# ------------------------
def Loop(task):
    try:
        apply_state()
    except Exception as ex:
        Bukkit.getLogger().severe(
            '[37412][24/7 Plan Script] Exception :'
            .format(days_passed)
        )

tips = [
    "Use /trigger ping set <Rank of ping: 1 to 5> to ping afk staff",
    "Cheating will result in a temporary ban with no chance of appeal",
    "Join our Discord by typing /trigger discord",
    "Talismans grant more Health and mining speed",
    "Thank you for playing, Player",
    "Boosting the discord server or this server, is highly apreciated",
    "Use Knockback sticks to buy time to regenerate in a pvp",
    "Dont spawn kill",
    "Check the community chests for free loot",
    "Smelt items in the super smelter",
    "Spamming the mine reset button, ping and flooding chat is not allowed",
    "Be nice",
    "The higher rank staff are always open to suggestions",
    "Report a player in discord /trigger discord",
    "If you a stuck somewhere do /trigger spawn",
    "Favouriting the server helps it grow /fav",
    "Talking about NSFW Topics results in a permanent ban wiith no chance of appeal",
    "Be creative at the free build arena",
    "Keep Inventory is on",
    "If you ask something from a staff member, you wont be given anything",
    "Friendly reminder: Put your unwanted loot in the community chests",
    "Theres something odd about wind charges",
    "The bank-like structure at the corner was the old tokens shop, and remains untouched to this day",
    "purseWash was the name minehut randomly generated for this server"
]

def chcol(msg):
    return ChatColor.translateAlternateColorCodes('&', msg)


def randomtip(task):
    try:
    	tip = random.choice(tips)
    	Bukkit.broadcastMessage(chcol("&6FUN FACT - &f") + tip)
    except Exception as ex:
    	Bukkit.getLogger().severe(
        	'[37412][24/7 Plan Script] Exception : {}'
            .format(ex)
     )


plugin = Bukkit.getPluginManager().getPlugin("PySpigot")

# run every 60 seconds
Bukkit.getScheduler().runTaskTimer(plugin, Loop, 0, 20 * 60)

Bukkit.getScheduler().runTaskTimer(plugin, randomtip, 0, 20 * 300)
