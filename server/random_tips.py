# -*- coding: utf-8 -*-
import datetime, json, random, time

from java.net import URL
from java.io import BufferedReader, InputStreamReader
from java.util import Scanner

from org.bukkit import Bukkit
from org.bukkit import ChatColor
from java.lang import Runnable

URL_DATA = "https://raw.githubusercontent.com/mohaali250/purseWash-Mc/refs/heads/main/data/random_tips.json"

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

def chcol(msg):
    return ChatColor.translateAlternateColorCodes('&', msg)


def randomtip(task):
    try:
        tip = random.choice(data["tips"])
        
        start = "/tellraw @a "
        click = "\"click_event\":{\"action\":\"" + list(tip["do"].keys())[0] + "\",\"command\":\"" + tip["do"][list(tip["do"].keys())[0]] + "\"" if len(list(tip["do"].keys())) != 0 else ""
        hover = "\"hover_event\":{\"action\":\"show_text\",\"value\":\"" + tip["tooltip"] + "\"" if len(tip["tooltip"]) != 0 else ""
        content = "\"text\":\"" + chcol(tip["content"]) + "\""
        end = ""
        
        cmd = start + "{" + ",".join([i for i in [click,hover,content] if i != ""]) + "}" + end
        
    	Bukkit.dispatchCommand(
            Bukkit.getConsoleSender(),
            cmd
        )
    except Exception as ex:
    	Bukkit.getLogger().severe(
        	'[37412][24/7 Plan Script] Exception : {}'
            .format(ex)
     )


plugin = Bukkit.getPluginManager().getPlugin("PySpigot")

if __name__ == "__main__":
    data = fetch_data()
    if data is None:
        print("Nothing returned")
    Bukkit.getScheduler().runTaskTimer(plugin, randomtip, 0, 20 * 300)
