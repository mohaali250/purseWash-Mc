# -*- coding: utf-8 -*-

import json,random,datetime,time,re,os

import pyspigot as ps

from java.net import URL
from java.util import Scanner

from org.bukkit import Bukkit

from org.bukkit.command import TabExecutor
from java.util import Arrays

from org.bukkit.configuration.file import YamlConfiguration
from java.io import File

from org.bukkit.event import Listener, EventHandler
from org.bukkit.event.player import PlayerJoinEvent
from org.bukkit.event.player import PlayerQuitEvent
from org.bukkit.event.player import PlayerKickEvent


from net.md_5.bungee.api.chat import TextComponent
from net.md_5.bungee.api.chat import ClickEvent
from net.md_5.bungee.api.chat import HoverEvent
from net.md_5.bungee.api.chat.hover.content import Text

# functions

def fetch_data():

    try:
        stream=URL(URL_DATA).openStream()
        scanner=Scanner(stream).useDelimiter("\\A")
        response=scanner.next() if scanner.hasNext() else None
        scanner.close()
        if response is None:
            return None

        return json.loads(response)
    except Exception as ex:
        Bukkit.getLogger().severe(
            "[Player Manager] {}".format(ex)
        )
        return None


def save():
    tmp = File(FILE + ".tmp")
    with open(tmp.getPath(), "w") as f:
        json.dump(data, f, indent=4)

    File(FILE).delete()
    tmp.renameTo(File(FILE))

def now():
    return int(time.time()) 

def uuid(p):
    return str(p.getUniqueId())

def ensure(u):
    if u not in data:
        data[u]={
            "staff":"",
            "staff_playtime":0,
            "locked":-1,
            "banned":0,
            "punishments":[],
            "notify":[]
        }

def parse(t):
    if t=="perm":
        return -1
    total=0
    for n,u in re.findall(r"(\d+)(s|min|h|d|wk)",t.lower()):
        n=int(n)
        if u=="s": total+=n
        elif u=="min": total+=n*60
        elif u=="h": total+=n*3600
        elif u=="d": total+=n*86400
        elif u=="wk": total+=n*604800
    return total if total>0 else None

def lp(cmd):
    Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"lp "+cmd)

def add_staff(name,rank):
    lp("user %s parent add %s"%(name,rank))

def remove_staff(name,rank):
    lp("user %s parent remove %s"%(name,rank))

def eligible(d):
    if d["staff"] == "":return False
    return not any([
        d["banned"] >= time.time() or d["banned"] == -1,
        d["locked"] != 0,
        parse(gdata["ranks"][d["staff"]]["required_playtime"]) > d["staff_playtime"]
    ])


def get_mute_info(player_name):
    player = Bukkit.getOfflinePlayer(player_name)
    if player is None:
        return None
    _uuid = str(player.getUniqueId())
    file = File("plugins/Essentials/userdata/%s.yml" % _uuid)
    if not file.exists():
        return None
    cfg = YamlConfiguration.loadConfiguration(file)
    data = {
        "muted": cfg.getBoolean("muted", False),
        "unmute_timestamp": cfg.getLong("timestamps.mute", 0),
        "reason": None
    }
    try:
        ess = Bukkit.getPluginManager().getPlugin("Essentials")
        user = ess.getUser(player)
        if user:
            mute = user.getMute()
            if mute:
                data["reason"] = mute.getReason()
    except:
        pass
    return data


def onCommand(sender,label,args):
    if gdata is None:
        print("[Staff] Failed to load remote config")
        return
    cmd=label.split(" ")[0]
    if hasattr(sender, "getUniqueId"):
        u=uuid(sender)
        ensure(u)
        f=data[u]
    allowed = ["owner","manager"]
    if cmd=="promote":
        if not sender.hasPermission("staffmanager.promote"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not permitted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if len(args)!=2:
            sender.sendMessage("§c[Staff Manager] [ERROR] ParameterError : Command \"/promote\" requires exactely 2 arguments (%s were given)" % (str(len(args))))
            return True
        if d["staff"] == "" and d["banned"] > time.time():
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Target is staff banned")
            return True
        if d["staff"] == "" and d["locked"] == -1:
            sender.sendMessage("§b[Staff Manager] [INFO] STDOUT : Target will need to agree to the rules first before having staff perms")

        
        sender.sendMessage(u"§a[Staff Manager] [INFO] Sucess : Promoted player §b%s§a for §b%s§a." % (args[0], args[1]))
        target.sendMessage(u"§b[Staff Manager] [INFO] STDOUT : You are promoted for §a%s§b." % (args[1]))
        # Run start
        if len(d["staff"]) != "": remove_staff(target.getName(),d["staff"])
        d["staff"]=args[1]
        # Run end
        if not eligible(d):
            target.sendMessage("§b[Staff Manager] [INFO] STDOUT : You didnt yet complete the requirements, once you do you'll be notified")
            sender.sendMessage("§a[Staff Manager] [INFO] STDOUT : When the target completes their requirements they'll get notified")
        else:
            session_notify(target)
    elif cmd=="suspend":
        if not sender.hasPermission("staffmanager.suspend"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not permitted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if d["staff"] == "":
            sender.sendMessage("§6[Staff Manager] [INFO] STDOUT : Cannot suspend non-staff players, nothing has changed")
            return True
        if len(args)<2:
            sender.sendMessage("§c[Staff Manager] [ERROR] ParameterError : Command \"/suspend\" requires atleast 2 arguments (%s were given)" % (str(len(args))))
            return True
        if len(args)<3:
            sender.sendMessage("§c[Staff Manager] [WARN] STDOUT : You must provide a reason")
            return True
        dur=parse(args[1])
        if dur is None:
            sender.sendMessage("§c[Staff Manager] [ERROR] TypeError : Argument 2 cannot be parsed as a valid timedelta")
            return True
        
        #Run start
        d["locked"]=now()+dur
        remove_staff(target.getName(),d["staff"])
        #Run end
        sender.sendMessage("§e[Staff Manager] STDOUT : Suspended §b%s§e for §b%s§e expiring in §b%s" % (args[0],",".join(args[2:]),str(datetime.timedelta(seconds=dur) if dur != -1 else "Never")))
        target.sendMessage("§cAccount Suspension of Staff")
        target.sendMessage("§cYour account lost its Staff permissions due to a violation of our staff rules")
        target.sendMessage("§cSuspension expires in §b%s" % (str(datetime.timedelta(seconds=dur) if dur != -1 else "Never")))
        for i in args[2:]:
            target.sendMessage("§cReason: %s" % (i))
        target.sendMessage("If you believe this was a misunderstanding, appeal at discord")
    elif cmd=="demote":
        if not sender.hasPermission("staffmanager.demote"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not permitted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if d["staff"] == "":
            sender.sendMessage("§6[Staff Manager] [INFO] STDOUT : Target wasn't staff, nothing has changed")
            return True
        
        #Run start
        d["staff_playtime"]=0
        remove_staff(target.getName(),d["staff"])
        d["staff"]=""
        d["locked"]=-2
        #Run end
        sender.sendMessage("§e[Staff Manager] STDOUT : Demoted §b%s§e for §b%s" % (args[0]," ".join(args[1:])))
        target.sendMessage("§cAccount Demotion of Staff")
        target.sendMessage("§cYour account lost its Staff permissions due to a violation of our staff rules")
        target.sendMessage("§cYou must reapply to get your rank back and redo the required playtime")
        for i in args[2:]:
            target.sendMessage("§cReason: %s" % (i))
        target.sendMessage("If you believe this was a misunderstanding, appeal at discord")
    elif cmd=="staff_ban":
        if not sender.hasPermission("staffmanager.staffban"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not permitted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        
        if d["staff"] == "":
            sender.sendMessage("§6[Staff Manager] [INFO] STDOUT : Target wasn't staff, nothing has changed")
            return True
        if len(args)<2:
            sender.sendMessage("§c[Staff Manager] [ERROR] ParameterError : Command \"/staff_ban\" requires atleast 2 arguments (%s were given)" % (str(len(args))))
            return True
        if len(args)<3:
            sender.sendMessage("§c[Staff Manager] [WARN] STDOUT : You must provide a reason")
            return True
        dur=parse(args[1])
        if dur is None:
            sender.sendMessage("§c[Staff Manager] [ERROR] TypeError : Argument 2 cannot be parsed as a valid timedelta")
            return True
        #Run start
        d["banned"]= -1 if dur == -1 else now()+dur
        remove_staff(target.getName(),d["staff"])
        d["staff"]=""
        #Run end
        sender.sendMessage("§e[Staff Manager] STDOUT : Staff Banned §b%s§e for §b\"%s\"§e expiring in §b%s" % (args[0],"§e,§b".join(args[2:]),str(datetime.timedelta(seconds=dur) if dur != -1 else "Never")))
        target.sendMessage("§cAccount Ban of Staff")
        target.sendMessage("Your account lost its Staff permissions due to a violation of our staff rules")
        target.sendMessage("You must wait out your ban, reapply to get your rank back and redo the required playtime")
        for i in args[2:]:
            target.sendMessage("Reason: "+i)
        target.sendMessage("If you believe this was a misunderstanding, appeal at discord")
    elif cmd=="staff_unban":
        if not sender.hasPermission("staffmanager.staffunban"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not whitelisted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        #Run start
        d["banned"]=now()
        d["staff_playtime"] = 0
        #Run end
        sender.sendMessage("§e[Staff Manager] STDOUT : Lifted Staff Ban of §b%s§e." % (args[0]))
        target.sendMessage("§cAccount Ban of Staff")
        target.sendMessage("Your account recently lost its Staff permissions due to a violation of our staff rules")
        target.sendMessage("Please review the staff rules and click below to agree")
        msg = TextComponent("§a[Reactivate my Account]")
        msg.setClickEvent(ClickEvent(ClickEvent.Action.RUN_COMMAND,
                "/activate staff"
            ))
        msg.setHoverEvent(HoverEvent(HoverEvent.Action.SHOW_TEXT,
                [Text("By clicking this you agree to the staff rules")]
            ))
        target.spigot().sendMessage(msg)
    elif cmd=="activate":
        if len(args)<1:
            sender.sendMessage("§6[Pyspigot / player_manager.py] [WARN] ParameterError : Well what are you gonna activate? (No changes were made)")
            return True
        if args[0] == "staff":
            if not hasattr(sender, "getUniqueId"):
                sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not whitelisted to use this command")
                return True
            if f["banned"] >= time.time() or f["banned"] == -1:
                sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is staff banned")
                return True
            if f["locked"] >= time.time():
                sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is suspended")
                return True
            if f["staff"] == "":
                sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not a pending staff member, perhaps you forgot to apply")
                return True
            if parse(gdata["ranks"][f["staff"]]["required_playtime"]) > f["staff_playtime"]:
                sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is didnt complete their required playtime yet")
                return True
            for p in Bukkit.getOnlinePlayers():
                if p.isOp():
                    p.sendMessage("§e[Staff Manager] STDOUT : §b%s§e claimed staff and verified their account to have staff perms §b" % (sender.getName()))
            
            #Run start
            f["banned"] = 0
            f["locked"] = 0
            if parse(gdata["ranks"][f["staff"]]["required_playtime"]) < f["staff_playtime"]:
                add_staff(sender.getName(),f["staff"])
            
            f["notify"] = 0
            #Run end
            sender.sendMessage("§e[Staff Manager] STDOUT : §bYou§e just claimed staff and verified their account to have staff perms §b")
            return True
    elif cmd=="punish":
        if not sender.hasPermission("staffmanager.punish"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not whitelisted to use this command")
            return True
        
        if len(args)<1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : Expected String for argument 1, got None")
            return True
        
        target=Bukkit.getPlayer(args[0])
        if target is None:
            sender.sendMessage("§6[Staff Manager] [WARN] Exception : Target returned none when parsed as a player, perphaps the player is offline?")
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        
        if len(args)<=1:
            sender.sendMessage("§6[Staff Manager] [WARN] ParameterError : What are you gonna punish them for? (Expected at least 2 arguments, got "+str(len(args))+")")
            return True
        
        # Run Start
        # Calculate
        reason_stack = []
        proof_stack = []
        bn = 0
        st_bn = 0
        st_susp = 0
        mute = 0 
        kick = False
        clear = False
        demote = False
        for v in args[1:]:
            i = v.split(":")[0]
            if len(v.split(":")) == 2:
                g = v.split(":")[1]
                proof = g.split(";")
            else:
                proof = []
            try:
                lt_pn = gdata["punishments"][i]
            except KeyError:
                continue
            for k in lt_pn.keys():
                if k=="ban":
                    if isinstance(lt_pn[k],bool) or bn==-1:
                        bn = -1
                    else:
                        bn += parse(lt_pn[k])
                elif k=="staff_ban":
                    if isinstance(lt_pn[k],bool) or st_bn == -1:
                        st_bn = -1
                    else:
                        st_bn += parse(lt_pn[k])
                elif k=="suspend_staff":
                    st_susp += parse(lt_pn[k])
                elif k=="mute":
                    if isinstance(lt_pn[k],bool) or mute == -1:
                        mute = -1
                    else:
                        mute += parse(lt_pn[k])
                elif k=="kick":
                    kick = True
                elif k=="clear":
                    clear = True
                elif k=="demote":
                    demote = True
                else:
                    continue    
            reason_stack.append(lt_pn["reason"])
            reason_stack.append(proof)
        # Optimizing actions and apply
        d["punishments"] = {i: v for i,v in zip(reason_stack,proof_stack)}
        if clear:
            target.getInventory().clear()
        if demote:
            d["staff_playtime"]=0
            remove_staff(target.getName(),d["staff"])
            d["staff"]=""
        if mute != 0:
            if mute == -1:
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"mute "+args[0]+" perm")
            else:
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"mute "+args[0]+" "+str(mute)+"s")
        if st_susp != 0:
            d["locked"]=now()+st_susp
            if len(d["staff"]) != 0: remove_staff(target.getName(),d["staff"])
        if st_bn != 0:
            d["banned"]= -1 if st_bn == -1 else max(now()+st_bn,now()+st_susp)
            if len(d["staff"]) != 0: remove_staff(target.getName(),d["staff"])
            d["staff"]=""
            d["locked"] = 0
        if bn != 0:
            if bn == -1:
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"ban %s \"Stack Start; %s\"; Stack End; If you believe you were punished unfairly appeal in discord" % (args[0],str(bn), "\\\""+"\\\", \\\"".join(reason_stack)+"\\\""))
            else:
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"tempban %s %ss \"Stack Start; %s\"; Stack End; If you believe you were punished unfairly appeal in discord" % (args[0],str(bn), "\\\""+"\\\", \\\"".join(reason_stack)+"\\\""))
        
        
        sender.sendMessage()
        return True
    elif cmd=="status":
        
        if not hasattr(sender, "getUniqueId"):
            sender.sendMessage("§6[Staff Manager] [WARN] PermissoinDenied : Sender is not whitelisted to use this command")
            return True
        
        d = f
        # banned?
        # .value
        #   -1 : Perm Ban
        #   0  : Not Banned
        #   0<now()<value : Temp Ban
        #   0<value<now() : Ban Expired (User must reactivate staff be reagreeing to the rules)
        # .behaviour
        #   - Ignores suspension if ban is in effect
        # .function
        #   .on_use
        #       - remove staff
        #       - set banned to now()+parse(time)
        #       - remove lp permissions
        #   .on_expire
        #       - notify user to use /status and to reagree to rules
        # locked?
        # .value
        #   -1 : First time, must agree to rules to claim staff
        #   0  : Agreed to rules and not currently suspended
        #   0<now()<value : Currently Suspended
        #   0<value<now() : Suspension Expired (User must reactivate staff be reagreeing to the rules to reclaim staff)
        # .behavior
        #   - null
        # .function
        #   .on_use
        #       - set locked to now()+parse(time)
        #       - remove lp permissions
        #   .on_expire
        #       - notify user to use /status and to reagree to rules
        # staff?
        # .value
        #   "" : Not a staff member (didnt yet apply, got banned or got demoted)
        #   String:Value != "" : Staff (Applied acepted, can be suspended to preserve rank)
        section_show = 0
        if len(args) == 0:
            section_show = 0
        elif args[0] == "staff":
            section_show = 1
        elif args[0] == "punishments":
            section_show = 2
        
        if section_show == 1 or section_show == 0:
            status_text = "Null"
            check_punishments_tab_suggestion = False
            staff_bar_value = 0
            if d["banned"] == -1:
                status_text = "Staff Perm Banned"
                staff_bar_value = 0
            elif 0<d["banned"]<now():
                status_text = "Staff Ban Expired"
                check_punishments_tab_suggestion = True
                staff_bar_value = 1
            elif d["banned"] != 0:
                status_text = "Staff Banned"
                check_punishments_tab_suggestion = True
                staff_bar_value = 0
            elif 0<d["locked"]<now():
                status_text = "Suspension Expired"
                check_punishments_tab_suggestion = True
                staff_bar_value = 2
            elif 0<now()<d["locked"]:
                status_text = "Suspended"
                check_punishments_tab_suggestion = True
                staff_bar_value = 2
            elif d["staff"] == "":
                status_text = "Non-Staff"
                staff_bar_value = 1
            elif d["locked"] == -1:
                status_text = "Needs to agree to rules"
                staff_bar_value = 1
            else:
                status_text = "Active Staff"
                staff_bar_value = 3
            sender.sendMessage("§6Your current staff status:")
            staff_bar = "[" + "\u2588"*staff_bar_value + " "*(3-staff_bar_value)  + "]"
            sender.sendMessage("§6{} {}".format(staff_bar, status_text))
            if check_punishments_tab_suggestion: sender.sendMessage("(Check Punishments tab for more info)")
        if section_show == 2 or section_show == 0:
            sender.sendMessage("Punishments Tab:")
            sender.sendMessage("")
            _any = False
            if d["banned"] != 0 or 0<d["locked"]:
                _any = True
                sender.sendMessage(", ".join([i for i,v in zip(["Staff Ban","Suspended"],[d["banned"] != 0,0<d["locked"]]) if v]))
                sender.sendMessage("")
                sender.sendMessage("Time until "+", ".join([i for i,v in zip(["Staff Ban","Suspended"],[d["banned"] != 0,0<d["locked"]]) if v])+"expires: "+str(datetime.timedelta(seconds=now()-max(d["locked"],d["banned"]))))
            mute_info = get_mute_info(sender.getName())
            if mute_info:
                if mute_info["muted"]:
                    _any = True
                    sender.sendMessage("")
                    sender.sendMessage("Muted")
                    sender.sendMessage("Time until mute expires: %s" % (str(datetime.timedelta(seconds=now()-mute_info["unmute_timestamp"]))))
            else:
                sender.sendMessage("No Data (mute_info returned None)")
            if not _any:
                sender.sendMessage("No Punishments")
            else:
                sender.sendMessage("")
                sender.sendMessage("Reason for punishments:")
                sender.sendMessage("")
                for i, v in d["punishments"]:
                    sender.sendMessage("")
                    sender.sendMessage("Reason: "+i)
                    if len(v) != 0:
                        for n in v:
                            sender.sendMessage("Rule Breaking Item: %s" % (n))
                sender.sendMessage("")
                sender.sendMessage("If you believe you were punished unfairly join discord (/trigger discord) and apeal your ban in tickets")
    for p in Bukkit.getOnlinePlayers():
        session_notify(p) 
    save()
    return True
def onTabComplete(sender,alias,args):
    cmd=alias.split(" ")[0]
    if len(args)==1:
        if cmd=="activate":
            return ["staff"]
        if cmd=="status":
            return ["staff","punishments"]
        return [p.getName() for p in Bukkit.getOnlinePlayers()]
    if len(args)==2:
        if any([i==cmd for i in ["suspend","staff_ban"]]):
            return [args[1] + i for i in ["s","min","h","d","wk"]]
        if cmd=="punish":
            return list(gdata["punishments"].keys())
        if cmd=="promote":
            return list(gdata["ranks"].keys())
    if len(args)>=3:
        if any([i==cmd for i in ["suspend","staff_ban","demote"]]):
            return ["\"" + args[-1] + "\""]
        if cmd=="punish":
            return  list(gdata["punishments"].keys())
    return []


def tick():
    for p in Bukkit.getOnlinePlayers():
        u=uuid(p)
        ensure(u)
        d=data[u]
        if d["banned"] == 0:
            d["staff_playtime"]+=60
        session_notify(p)
    save()


def session_notify(p):
    local_session_notify.setdefault(uuid(p), 0)
    u=uuid(p)
    ensure(u)
    d=data[u]
    if d["staff"] != "" and eligible(d) and not _bit.read(local_session_notify[uuid(p)],0):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : You are now elegible to activate staff see /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],0,True)
    if 0<d["banned"]<=now() and not _bit.read(local_session_notify[uuid(p)],1):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : Your staff ban expired. See /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],1,True)
    if 0<d["locked"]<now() and not _bit.read(local_session_notify[uuid(p)],2):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : Your staff suspension expired. See /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],2,True)
    if 0<now()<=d["banned"] and not _bit.read(d["notify"],3):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : You are Staff banned. See /status for more")
        d["notify"] = _bit.write(d["notify"],3,True)
    if 0<now()<=d["locked"] and not _bit.read(d["notify"],4):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : You are Suspended for staff. See /status for more")
        d["notify"] = _bit.write(d["notify"],4,True)
    if d["locked"]==-2 and not _bit.read(d["notify"],5):
        p.sendMessage("§a[Staff Manager] [INFO] STDOUT : You are Demoted from staff. See /status for more")
        d["notify"] = _bit.write(d["notify"],5,True)




class _bit:
    def read(integer,n):
        return (integer >> n) & 1
    def write(integer,n,value):
        if value is None:
            integer ^= (1 << n)
        elif value:
            integer |= (1 << n)
        else:
            integer &= ~(1 << n)
        return integer


def handle_join(event):
    global local_session_notify
    p = event.getPlayer()
    u=uuid(p)
    ensure(u)
    d=data[u]
    local_session_notify[uuid(p)] = d["notify"]
    session_notify(p)

def handle_disconnect(event):
    player = event.getPlayer()
    local_session_notify.pop(uuid(player), None)
    pass



def onJoin(self, event):
    handle_join(event)

def onQuit(self, event):
    handle_disconnect(event)


def onKick(self, event):
    handle_disconnect(event)

# starter variables

FILE="plugins/PySpigot/staff.json"
URL_DATA="https://raw.githubusercontent.com/mohaali250/purseWash-Mc/refs/heads/main/data/player_manager.json"
local_session_notify = {i: y for i, y in zip([uuid(k) for k in Bukkit.getOnlinePlayers()],[0]*len(Bukkit.getOnlinePlayers()))}


if not os.path.exists(FILE):
    with open(FILE,"w") as f:
        json.dump({},f) 

with open(FILE,"r") as f:
    data=json.load(f)

# Debug

print(onCommand)
print(onCommand.__class__)
print(onTabComplete)
print(onTabComplete.__class__)

# Run  
    
for c in ["promote","suspend","demote","staff_ban","staff_unban","punish","activate","status"]:
    ps.command.registerCommand(onCommand, onTabComplete, c)


gdata = fetch_data()

ps.listener.registerListener(onJoin, PlayerJoinEvent)
ps.listener.registerListener(onQuit, PlayerQuitEvent)
ps.listener.registerListener(onKick, PlayerKickEvent)

ps.scheduler.scheduleRepeatingTask(tick, 1200, 1200)

print("[Staff] Loaded.")
