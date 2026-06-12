# -*- coding: utf-8 -*-

import json,random

from java.net import URL
from java.util import Scanner

from org.bukkit import Bukkit,ChatColor

from net.md_5.bungee.api.chat import TextComponent
from net.md_5.bungee.api.chat import HoverEvent
from net.md_5.bungee.api.chat import ClickEvent

from net.md_5.bungee.api.chat.hover.content import Text

URL_DATA="https://raw.githubusercontent.com/mohaali250/purseWash-Mc/refs/heads/main/data/random_tips.json"

def fetch_data():
        return json.loads(response)
    except Exception as ex:
        Bukkit.getLogger().severe(
            "[RandomTips] {}".format(ex)
        )
        return None

def cc(msg):
    return ChatColor.translateAlternateColorCodes('&',msg)

def randomtip():
    try:
        tip=random.choice(data["tips"])
        msg=TextComponent(
            cc(tip["content"])
        )
        if len(tip["tooltip"]) != 0:
            msg.setHoverEvent(
                HoverEvent(
                    HoverEvent.Action.SHOW_TEXT,
                    [Text(cc(tip["tooltip"]))]
                )
            )
        if len(tip["do"].keys()) != 0:
            action=list(tip["do"].keys())[0]
            value=tip["do"][action]
            click_action={
                "run_command":ClickEvent.Action.RUN_COMMAND,
                "suggest_command":ClickEvent.Action.SUGGEST_COMMAND,
                "open_url":ClickEvent.Action.OPEN_URL
            }.get(action)
            if click_action is not None:
                msg.setClickEvent(
                    ClickEvent(
                        click_action,
                        value
                    )
                )
        for p in Bukkit.getOnlinePlayers():
            p.spigot().sendMessage(msg)
    except Exception as ex:
        Bukkit.getLogger().severe(
            "[RandomTips] {}".format(ex)
        )

plugin=Bukkit.getPluginManager().getPlugin("PySpigot")


# add these imports

from org.bukkit.command import CommandExecutor

# -------------------------
# COMMAND
# -------------------------

class RefreshTip(CommandExecutor):
    def onCommand(self,sender,command,label,args):
        randomtip()
        return True


# -------------------------
# REGISTER
# -------------------------

refresh=RefreshTip()

cmd=Bukkit.getPluginCommand("refreshtip")


if cmd:
    cmd.setExecutor(refresh)

data=fetch_data()
if data is not None:
    Bukkit.getScheduler().runTaskTimer(
        plugin,
        randomtip,
        0,
        20*300
    )
    print("[RandomTips] Loaded.")
else:
    print("[RandomTips] Failed to load data.")
