import datetime, json

from java.net import URL
from java.io import BufferedReader, InputStreamReader

from org.bukkit import Bukkit
from java.lang import Runnable

# CONFIG
URL_DATA = "https://raw.githubusercontent.com/mohaali250/server_plan_predicter_pack/main/calibration.json"

RQ = 400
GETD = 10

# ------------------------
# HTTP FETCH (Java way)
# ------------------------
def fetch_data():
    url = URL(URL_DATA)
    conn = url.openConnection()
    conn.setRequestMethod("GET")

    reader = BufferedReader(InputStreamReader(conn.getInputStream()))
    response = ""

    line = reader.readLine()
    while line:
        response += line
        line = reader.readLine()

    reader.close()
    return json.loads(response)

# ------------------------
# CORE LOGIC (NO LOOP)
# ------------------------
def is_server_open(data):
    now = datetime.datetime.utcnow()

    oldcrt = data["Credits"]
    olddslp = data["Days_Since_last_pay"]
    lupd = datetime.datetime(*data["Last_Updated"])

    days_passed = (now - lupd).days

    crt = (oldcrt + days_passed * GETD) % RQ
    dslp = (olddslp + days_passed) % (RQ // GETD)

    # decision logic
    if dslp > 30 and crt < RQ:
        return False
    return True

# ------------------------
# APPLY SERVER STATE
# ------------------------
def apply_state():
    try:
        data = fetch_data()
    except:
        print("Failed to fetch data")
        return

    allowed = is_server_open(data)

    now = datetime.datetime.utcnow().time()
    time_allowed = datetime.time(9, 0) <= now <= datetime.time(20, 15)

    should_open = allowed if allowed else not time_allowed

    if should_open:
        Bukkit.setWhitelist(False)
        print("Server OPEN")
    else:
        Bukkit.setWhitelist(True)
        print("Server CLOSED")

        # kick non-whitelisted players
        for p in Bukkit.getOnlinePlayers():
            if not p.isWhitelisted():
                p.kickPlayer("Server is closed right now.")

        # optional: shutdown if empty
        if len(Bukkit.getOnlinePlayers()) == 0:
            Bukkit.shutdown()

# ------------------------
# SCHEDULER (runs every 60s)
# ------------------------
class Loop(Runnable):
    def run(self):
        apply_state()

from org.bukkit import Bukkit

plugin = Bukkit.getPluginManager().getPlugin("PySpigot")

# run every 60 seconds
Bukkit.getScheduler().runTaskTimer(plugin, Loop(), 0, 20 * 60)
