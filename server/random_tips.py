# -*- coding: utf-8 -*-
import datetime, json, random, time

from java.net import URL
from java.io import BufferedReader, InputStreamReader
from java.util import Scanner

from org.bukkit import Bukkit
from org.bukkit import ChatColor
from java.lang import Runnable

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
