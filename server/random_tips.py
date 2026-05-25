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


def randomtip():

    try:

        tip = random.choice(data["tips"])

        parts = []

        parts.append(
            "\"text\":\"" + tip["content"].replace("\"","\\\"") + "\""
        )

        if len(tip["tooltip"]) != 0:

            parts.append(
                "\"hoverEvent\":{\"action\":\"show_text\",\"contents\":\"" +
                tip["tooltip"].replace("\"","\\\"") +
                "\"}"
            )

        if len(tip["do"].keys()) != 0:

            action = list(tip["do"].keys())[0]
            value = tip["do"][action]

            parts.append(
                "\"clickEvent\":{\"action\":\"" +
                action +
                "\",\"value\":\"" +
                value.replace("\"","\\\"") +
                "\"}"
            )

        cmd = "/tellraw @a {" + ",".join(parts) + "}"

        print(cmd)

        Bukkit.dispatchCommand(
            Bukkit.getConsoleSender(),
            cmd
        )

    except Exception as ex:

        Bukkit.getLogger().severe(
            "[RandomTips] {}".format(ex)
        )

plugin = Bukkit.getPluginManager().getPlugin("PySpigot")
data = fetch_data()

# Run

if data is None:
    print("Nothing returned")
else:
    Bukkit.getScheduler().runTaskTimer(
        plugin,
        randomtip,
        0,
        20 * 300
    )
