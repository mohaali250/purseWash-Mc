# -*- coding: utf-8 -*-
import json,random,datetime,time,re,os,__builtin__  # Python 2.7
import pyspigot as ps
from java.net import URL
from java.util import Scanner
from java.util import UUID
from org.bukkit import Bukkit
from org.bukkit import Statistic
from org.bukkit.command import TabExecutor
from java.util import Arrays
from org.bukkit.configuration.file import YamlConfiguration
from java.io import File
from org.bukkit.event import Listener, EventHandler
from org.bukkit.event.player import PlayerJoinEvent
from org.bukkit.event.player import PlayerQuitEvent
from org.bukkit.event.player import PlayerKickEvent
from org.bukkit import ChatColor
from net.md_5.bungee.api.chat import TextComponent
from net.md_5.bungee.api.chat import ClickEvent
from net.md_5.bungee.api.chat import HoverEvent
from net.md_5.bungee.api.chat.hover.content import Text
# functions
def fetch_data():
    try:
        print("Fetching:", URL_DATA)
        stream = URL(URL_DATA).openStream()
        scanner = Scanner(stream).useDelimiter("\\A")
        response = scanner.next() if scanner.hasNext() else None
        scanner.close()
        print("Response:")
        print(response)
        if response is None:
            print("Response was None")
            return None
        obj = json.loads(response)
        print("Parsed:")
        print(obj)
        return obj
    except Exception as ex:
        print("EXCEPTION:", ex)
        import traceback
        traceback.print_exc()
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
def get_total_playtime_seconds(u):
    player = Bukkit.getPlayer(UUID.fromString(u))
    return player.getStatistic(Statistic.PLAY_ONE_MINUTE) / 20

class exception_type:
    PERMISSION_ERROR = "Permission Error"
    PARAMETER_ERROR = "Paremeter Error"
    PARSE_ERROR = "Parse Error"
    SUCCESS = "Success"
def chat_log(target,state,string,variables=(),_type="PRINT"):
    if target is None: return False
    states = {
        0: {
            "contents": "INFO",
            "default_color": "&3",
            "highlight":"&a"
        },
        1: {
            "contents": "WARN",
            "default_color": "&6",
            "highlight":"&a"
        },
        2: {
            "contents": "ERROR",
            "default_color": "&4",
            "highlight":"&a"
        },
        3: {
            "contents": "SUCCESS",
            "default_color": "&2",
            "highlight":"&a"
        },
        4: {
            "contents": "NOTIFY",
            "default_color": "&e",
            "highlight":"&b"
        }
    }
    message_color = states[state]["default_color"]
    text = message_color+string.replace("%s", states[state]["highlight"]+"%s"+message_color) % variables
    if _type != "PRINT":
        target.sendMessage(ChatColor.translateAlternateColorCodes('&', states[state]["default_color"]+"[Pyspigot/player_manager.py] [%s] %s : %s" % (states[state]["contents"],_type,text)))
    else:
        target.sendMessage(ChatColor.translateAlternateColorCodes('&', states[state]["default_color"]+"[Pyspigot/player_manager.py] [%s] %s" % (states[state]["contents"],text)))

def ensure(u):
    print("ENSURE CALLED FOR", u)
    defaults = {
        "staff": "",
        "staff_playtime": get_total_playtime_seconds(u),
        "locked": -1,
        "banned": 0,
        "punishments": {},
        "notify": 0
    }
    if u not in data:
        print("CREATING ENTRY")
        data[u] = defaults.copy()
    else:
        print("BEFORE ENSURE:", data[u])
        for k, default in defaults.items():
            if k not in data[u]:
                data[u][k] = default
        print("AFTER ENSURE:", data[u])
def pretty_timedelta(timeinterval):
    if not isinstance(timeinterval,int):
        return None
    days = timeinterval // 86400
    hours = (timeinterval % 86400) // 3600
    minutes = (timeinterval % 3600) // 60
    seconds = timeinterval % 60
    text = ""
    if days != 0:
        if days == 1:
            text += "%d day " % (days)
        else:
            text += "%d days " % (days)
    if hours != 0:
        if hours == 1:
            text += "%d hr " % (hours)
        else:
            text += "%d hrs " % (hours)
    if minutes != 0:
        if minutes == 1:
            text += "%d minute " % (minutes)
        else:
            text += "%d minutes " % (minutes)
    if seconds != 0:
        if seconds == 1:
            text += "%d second " % (seconds)
        else:
            text += "%d seconds " % (seconds)
    return text[:-1]
def extended_staff_rank(string):
    if string == "": return "Default"
    return gdata["ranks"][string]["extended_name"]
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
    lp("user %s parent set %s"%(name,rank))
def remove_staff(name,rank=""):
    lp("user %s parent clear"%(name))
def eligible(d):
    if d["staff"] == "":return False
    return not any([
        d["banned"] >= time.time() or d["banned"] == -1,
        d["locked"] != 0,
        parse(gdata["ranks"][d["staff"]]["required_playtime"]) > d["staff_playtime"]
    ])
def eligible_to_activate(d):
    if d["staff"] == "":return False
    return not any([
        d["banned"] >= time.time() or d["banned"] == -1,
        d["locked"] <= 0,
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
def chatcolor(msg):
    return ChatColor.translateAlternateColorCodes('&', msg)
def onCommand(sender,label,args):
    if gdata is None:
        print("[Staff] Failed to load remote config")
        return
    cmd=label.split(" ")[0].split(":")[-1]
    if hasattr(sender, "getUniqueId"):
        u=uuid(sender)
        ensure(u)
        f=data[u]
    allowed = ["owner","manager"]
    if cmd=="promote":
        if not sender.hasPermission("staffmanager.promote"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if len(args)!=2:
            chat_log(sender,2,"Command \"/promote\" requires exactely 2 arguments (%s were given)",variables=(str(len(args))),_type=exception_type.PARAMETER_ERROR)
            return True
        if d["staff"] == "" and (d["banned"] > time.time() or d["banned"]==-1):
            chat_log(sender,1,"Target %s is staff banned",variables=(args[0]))
            return True
        
        chat_log(sender,3,"Promoted player %s for %s.",variables=(args[0],extended_staff_rank(args[1])))
        chat_log(target,0,"%s are promoted for %s. Check [/status] for more info!",variables=("You",extended_staff_rank(args[1])))
        # Run start
        add_staff(target.getName(),"trainee")
        d["staff"]=args[1]
        if d["locked"] < 0: d["locked"] = -3
        # Run end
    elif cmd=="suspend":
        if not sender.hasPermission("staffmanager.suspend"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if d["staff"] == "":
            chat_log(sender,1,"Cannot suspend %s because they arent a staff member",variables=(args[0]))
            return True
        if len(args)<2:
            chat_log(sender,2,"Command \"/suspend\" requires atleast 2 arguments (%s were given)",variables=(str(len(args))),_type=exception_type.PARAMETER_ERROR)
            return True
        if len(args)<3:
            chat_log(sender,1,"You must provide a reason")
            return True
        dur=parse(args[1])
        if dur is None:
            chat_log(sender,1,"%s returned none when parsed as a timedelta",variables=(args[1]),_type=exception_type.PARSE_ERROR)
            return True
        
        #Run start
        d["locked"]=now()+dur
        remove_staff(target.getName(),d["staff"])
        #Run end
        chat_log(sender,3,"Suspended %s for &a"+"&2,&a".join(args[2:])+"&2 expiring in %s.",variables=(args[0],str(pretty_timedelta(dur) if dur != -1 else "Never")))
        chat_log(target,0,"%s are now suspended from staff. More info on [/status]",variables=("You"))
    elif cmd=="demote":
        if not sender.hasPermission("staffmanager.demote"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        if d["staff"] == "":
            chat_log(sender,1,"Cannot demote %s because they arent a staff member",variables=(args[0]))
            return True
        
        #Run start
        d["staff_playtime"]=0
        remove_staff(target.getName(),d["staff"])
        d["staff"]=""
        d["locked"]=-2
        #Run end
        chat_log(sender,3,"Demoted %s for &a"+"&2,&a".join(args[1:])+"&2.",variables=(args[0]))
        chat_log(target,0,"%s are now demoted from staff. More info on [/status]",variables=("You"))
    elif cmd=="staff_ban":
        if not sender.hasPermission("staffmanager.staffban"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        
        if d["staff"] == "":
            chat_log(sender,1,"Cannot staff ban %s because they arent a staff member",variables=(args[0]))
            return True
        if len(args)<2:
            chat_log(sender,2,"Command \"/staff_ban\" requires atleast 2 arguments (%s were given)",variables=(str(len(args))),_type=exception_type.PARAMETER_ERROR)
            return True
        if len(args)<3:
            chat_log(sender,1,"You must provide a reason")
            return True
        dur=parse(args[1])
        if dur is None:
            chat_log(sender,1,"%s returned none when parsed as a timedelta",variables=(args[1]),_type=exception_type.PARSE_ERROR)
            return True
        #Run start
        d["banned"]= -1 if dur == -1 else now()+dur
        remove_staff(target.getName(),d["staff"])
        d["staff"]=""
        #Run end
        chat_log(sender,3,"Staff banned %s for &a"+"&2,&a".join(args[2:])+"&2 expiring in %s.",variables=(args[0],str(pretty_timedelta(dur) if dur != -1 else "Never")))
        chat_log(target,0,"%s are now banned from staff. More info on [/status]",variables=("You"))
    elif cmd=="staff_unban":
        if not sender.hasPermission("staffmanager.staffunban"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]

        #Run start
        if d["banned"] != 0:
            dur = now() - d["banned"]
            chat_log(sender,3,"Lifted staff ban of %s which left %s to finish.",variables=(args[0],str(pretty_timedelta(dur) if dur != -1 else "Never")))
            chat_log(target,4,"%s ban from staff is now lifted. Reagree to rules by typing [/activate staff]. More info on [/status]",variables=("Your"))
            d["staff_playtime"] = 0
            d["banned"]=now()
        elif 0 < d["locked"]:
            dur = now() - d["banned"]
            chat_log(sender,3,"Lifted staff suspension of %s which left %s to finish.",variables=(args[0],str(pretty_timedelta(dur) if dur != -1 else "Never")))
            chat_log(target,4,"%s staff suspension is now lifted. Reagree to rules by typing [/activate staff]. More info on [/status]",variables=("Your"))
            d["locked"] = -2
        else:
            chat_log(sender,3,"%s doesnt have a punishment to remove",variables=(args[0]))

        local_session_notify[uuid(sender)]=0
        #Run end
    elif cmd=="activate":
        if len(args)<1:
            chat_log(sender,1,"Well, what are you gonna activate? (Expected String at argument 1, got None)",_type=exception_type.PARAMETER_ERROR)
            return True
        if args[0] == "staff":
            if not hasattr(sender, "getUniqueId"):
                print("You cant run this command as CONSOLE")
                return True
            if f["banned"] >= time.time() or f["banned"] == -1:
                chat_log(sender,1,"%s are staff banned, you cant activate staff. More info on [/status]",variables=("You"),_type=exception_type.PERMISSION_ERROR)
                return True
            if f["locked"] >= time.time():
                chat_log(sender,1,"%s are suspended, you cant activate staff. More info on [/status]",variables=("You"),_type=exception_type.PERMISSION_ERROR)
                return True
            
            if f["staff"] != "" and parse(gdata["ranks"][f["staff"]]["required_playtime"]) > f["staff_playtime"]:
                chat_log(sender,0,"%s dont have the required playtime yet. Check [/status] for how much playtime left",variables=("You"))
                return True
            elif f["staff"] != "":
                chat_log(sender,0,"%s agreed to staff rules and are now a staff member (%s). You have now gained perms for this rank. Check [/status] for more info",variables=("You",extended_staff_rank(f["staff"])))
            else:
                f["banned"] = 0
                f["locked"] = 0
                f["punishments"] = {}
                chat_log(sender,3,"%s reagreed to rules ",variables=("You"))
                return True
            
            for p in Bukkit.getOnlinePlayers():
                if f["staff"] != "" and parse(gdata["ranks"][f["staff"]]["required_playtime"]) < f["staff_playtime"]:
                    chat_log(p,0,"%s agreed to staff rules and now is a staff member. Congradulate our new %s!",variables=(sender.getName(),extended_staff_rank(f["staff"])))
            
            #Run start
            f["banned"] = 0
            f["locked"] = 0
            f["punishments"] = {}
            if f["staff"] != "" and parse(gdata["ranks"][f["staff"]]["required_playtime"]) <     f["staff_playtime"]:
                add_staff(sender.getName(),f["staff"])
                local_session_notify[uuid(sender)] = 0
            #Run end
    elif cmd=="punish":
        if not sender.hasPermission("staffmanager.punish"):
            chat_log(sender,1,"%s are not permitted to use this command",variables=("You"),_type=exception_type.PERMISSION_ERROR)
            return True
        
        if len(args)<1:
            chat_log(sender,1,"Expected String for argument 1, got None",_type=exception_type.PARAMETER_ERROR)
            return True
        
        target=Bukkit.getOfflinePlayer(args[0])
        if not target.hasPlayedBefore() and not target.isOnline():
            chat_log(sender,1,"Target %s has never joined or is an invalid username",variables=(args[0]),_type=exception_type.PARSE_ERROR)
            return True
        u=uuid(target)
        ensure(u)
        d=data[u]
        
        if len(args)<=1:
            chat_log(sender,1,"ParameterError : What are you gonna punish them for? (Expected at least 2 arguments, got %s)",variables=(str(len(args))),_type=exception_type.PARAMETER_ERROR)
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
            proof_stack.append(proof)
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
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"ban %s Stack Start | %s | Stack End; If you believe you were punished unfairly appeal in discord" % (args[0], " | ".join(reason_stack)))
            else:
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"tempban %s %ss Stack Start | %s | Stack End; If you believe you were punished unfairly appeal in discord" % (args[0], str(bn), " | ".join(reason_stack)))
        if kick:
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"kick %s Stack Start | %s | Stack End; Rejoin with that in mind" % (args[0], " | ".join(reason_stack))) 
        
        chat_log(sender,3,"Punished &a%s&2 for &a%s&2." % (args[0],"&2,&a".join(args[1:])))
    elif cmd=="status":
        
        if not hasattr(sender, "getUniqueId"):
            print("You cant run this command as CONSOLE")
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
        elif args[0] == "raw_data":
            section_show = 3
        elif args[0] == "set":
            section_show = 4
        elif args[0] == "get":
            section_show = 5
        
        if section_show == 1 or section_show == 0:
            sender.sendMessage(chatcolor("&8:=====================< &6STATUS &8>======================:"))
            sender.sendMessage("")
            status_text = "Unknown"
            status_bar = 0
            if d["banned"] == -1:
                status_text = "&4Staff Permanently Banned"
                status_bar = 0
            elif 0 < now() < d["banned"]:
                status_text = "&6Staff Banned"
                status_bar = 1
            elif 0 < d["banned"] < now():
                status_text = "&6Staff Ban expired (do /activate staff)"
                status_bar = 2
            elif 0 < now() < d["locked"]:
                status_text = "&6Suspended"
                status_bar = 1
            elif 0 < d["locked"] < now():
                status_text = "&eSuspension Expired"
                status_bar = 2
            elif d["staff"] == "":
                status_text = "&7Non-Staff"
                status_bar = 2
            elif parse(gdata["ranks"][d["staff"]]["required_playtime"]) > d["staff_playtime"]:
                status_text = "&ePending Staff"
                status_bar = 3
            elif d["locked"] in [-1, -2, -3]:
                status_text = "&eNeeds Rule Agreement"
                status_bar = 3
            else:
                status_text = "&aActive Staff"
                status_bar = 4
            sender.sendMessage(
                chatcolor("[&a%s&8%s&f] %s" % (
                    "#" * status_bar,
                    "-" * (4 - status_bar),
                    status_text
                ))
            )
            sender.sendMessage(
                chatcolor("&7Rank: &b%s" % extended_staff_rank(d["staff"]))
            )
            sender.sendMessage("")
            if d["staff"] != "" and d["locked"] < 0:
                required = parse(
                    gdata["ranks"][d["staff"]]["required_playtime"]
                )
                current = d["staff_playtime"]
                progress = min(
                    1.0,
                    float(current) / max(required, 1)
                )
                filled = int(progress * 100)
                if max(required - current, 0) != 0:
                    sender.sendMessage(
                        chatcolor(
                            "&7Time left: &f %s &7out of &f%s &7to get &b%s"
                            % (
                                pretty_timedelta(max(required - current, 0)),
                                pretty_timedelta(required),
                                extended_staff_rank(d["staff"])
                            )
                        )
                    )
                else:
                    sender.sendMessage(
                        chatcolor(
                            "&7You completed the&f%s&7 to claim get &b%s&7. Do &f/activate staff"
                            % (
                                pretty_timedelta(required),
                                extended_staff_rank(d["staff"])
                            )
                        )
                    )
                sender.sendMessage(
                    chatcolor(
                        "[&a%s&8%s&f]"
                        % (
                            "|" * filled,
                            "|" * (100 - filled)
                        )
                    )
                )
            sender.sendMessage("")
            #status_text = "Null"
            #check_punishments_tab_suggestion = False
            #staff_bar_value = 0
            #if d["banned"] == -1:
            #    status_text = "Staff Perm Banned"
            #    staff_bar_value = 0
            #elif 0<d["banned"]<now():
            #    status_text = "Staff Ban Expired"
            #    check_punishments_tab_suggestion = True
            #    staff_bar_value = 1
            #elif d["banned"] != 0:
            #    status_text = "Staff Banned"
            #    check_punishments_tab_suggestion = True
            #    staff_bar_value = 0
            #elif 0<d["locked"]<now():
            #    status_text = "Suspension Expired"
            #    check_punishments_tab_suggestion = True
            #    staff_bar_value = 2
            #elif 0<now()<d["locked"]:
            #    status_text = "Suspended"
            #    check_punishments_tab_suggestion = True
            #    staff_bar_value = 2
            #elif d["staff"] == "":
            #    status_text = "Non-Staff"
            #    staff_bar_value = 1
            #elif parse(gdata["ranks"][d["staff"]]["required_playtime"]) > d["staff_playtime"]:
            #    status_text = "Pending staff (%s left) - Applying for %s" % (str(pretty_timedelta(parse(gdata["ranks"][d["staff"]]["required_playtime"])-d["staff_playtime"])),extended_staff_rank(d["staff"]))
            #    staff_bar_value = 1
            #elif d["locked"] == -1:
            #    status_text = "Needs to agree to rules"
            #    staff_bar_value = 2
            #elif d["locked"] == -3:
            #    status_text = "Upgraded Rank (Reagree to rules)"
            #    staff_bar_value = 2
            #else:
            #    status_text = "Active Staff"
            #    staff_bar_value = 3
            #sender.sendMessage(chatcolor("&6Your current staff status:"))
            #staff_bar = "[" + "#"*staff_bar_value + "-"*(3-staff_bar_value)  + "]"
            #sender.sendMessage(chatcolor("&6{} {}".format(staff_bar, status_text)))
            #sender.sendMessage(chatcolor("&a    Staff rank: %s" % (extended_staff_rank(d["staff"]))))
            #if check_punishments_tab_suggestion: sender.sendMessage("(Check Punishments tab for more info)")
        if section_show == 2 or section_show == 0:
            sender.sendMessage(chatcolor("&8:===================< &6PUNISHMENTS &8>===================:"))
            sender.sendMessage("")
            active = []
            if d["banned"] == -1:
                active.append("Staff Ban (Permanent)")
            elif d["banned"] > now():
                active.append(
                    "Staff Ban (%s left)"
                    % pretty_timedelta(d["banned"] - now())
                )
            if d["locked"] > now():
                active.append(
                    "Suspension (%s left)"
                    % pretty_timedelta(d["locked"] - now())
                )
            mute_info = get_mute_info(sender.getName())
            if mute_info and mute_info["muted"]:
                if mute_info["unmute_timestamp"] == -1:
                    active.append("Mute (Permanent)")
                else:
                    active.append(
                        "Mute (%s left)"
                        % pretty_timedelta(
                            mute_info["unmute_timestamp"] - now()
                        )
                    )
            if len(active) == 0:
                sender.sendMessage(chatcolor("&aStatus: Clean"))
            else:
                sender.sendMessage(chatcolor("&cStatus: %s" % ", ".join(active)))
                if len(d["punishments"]) != 0:
                    sender.sendMessage("")
                    sender.sendMessage(chatcolor("&6Reason:"))
                    for reason, items in d["punishments"].items():
                        sender.sendMessage("")
                        sender.sendMessage(chatcolor("&e- %s" % reason))
                        for item in items:
                            sender.sendMessage(
                                chatcolor("&7  - %s" % item)
                            )
            sender.sendMessage("")
            sender.sendMessage(chatcolor("&8:====================================================:"))
                    #sender.sendMessage("Punishments Tab:")
                    #sender.sendMessage("")
                    #_any = False
                    #if d["banned"] != 0 or 0<d["locked"]:
                    #    _any = True
                    #    sender.sendMessage(", ".join([i for i,v in zip(["Staff Ban","Suspended"],[d["banned"] != 0,0<d["locked"]]) if v]))
                    #    sender.sendMessage("")
                    #    
                    #    if max(d["locked"],d["banned"])-now() > 0:
                    #        expires_time_text = str(pretty_timedelta(max(d["locked"],d["banned"])-now()))
                    #    elif d["banned"] == -1:
                    #        expires_time_text = "Never"
                    #    else:
                    #        expires_time_text = "Reagree to rules to lift ban"
                    #    sender.sendMessage("Time until %s expires: %s" % (", ".join([i for i,v in zip(["Staff Ban","Suspended"],[d["banned"] != 0,0<d["locked"]]) if v]),expires_time_text))
                    #mute_info = get_mute_info(sender.getName())
                    #if mute_info:
                    #    if mute_info["muted"]:
                    #        _any = True
                    #        sender.sendMessage("")
                    #        sender.sendMessage("Muted")
                    #        sender.sendMessage("Time until mute expires: %s" % (str(pretty_timedelta(mute_info["unmute_timestamp"]-now()) if mute_info["unmute_timestamp"] != -1 else "Never")))
                    #else:
                    #    sender.sendMessage("No Data (mute_info returned None)")
                    #if not _any:
                    #    sender.sendMessage("No Punishments")
                    #else:
                    #    sender.sendMessage("")
                    #    sender.sendMessage("Reason for punishments:")
                    #    for i, v in d["punishments"].items():
                    #        sender.sendMessage("")
                    #        sender.sendMessage("Reason: "+i)
                    #        if len(v) != 0:
                    #            for n in v:
                    #                sender.sendMessage("Rule Breaking Item: %s" % (n))
                    #    sender.sendMessage("")
                    #    sender.sendMessage("If you believe you were punished unfairly join discord (/trigger discord) and apeal your ban in tickets")
        if section_show == 3:
            sender.sendMessage("Raw staff data:")
            for i, v in d.items():
                sender.sendMessage("")
                sender.sendMessage("Key: %s" % (i))
                sender.sendMessage("Value: %s" % (v))
        if section_show == 4:
            if hasattr(sender, "getUniqueId") and not uuid(sender)==OWNERUUID:
                chat_log(sender,1,"%s are not permitted to use this command. Use console to run this instead",variables=("You"),_type=exception_type.PERMISSION_ERROR)
                return True
            ensure(uuid(Bukkit.getPlayer(args[1])))
            player_uuid = uuid(Bukkit.getPlayer(args[1]))
            converter = getattr(__builtin__, args[3])
            data[player_uuid][args[2]] = converter(" ".join(args[4:]))
        if section_show == 5:
            if hasattr(sender, "getUniqueId") and not uuid(sender)==OWNERUUID:
                chat_log(sender,1,"%s are not permitted to use this command. Use console to run this instead",variables=("You"),_type=exception_type.PERMISSION_ERROR)
                return True
            ensure(uuid(Bukkit.getPlayer(args[1])))
            d = data[uuid(Bukkit.getPlayer(args[1]))]
            sender.sendMessage("Raw data of %s:" % (args[1]))
            for i, v in d.items():
                sender.sendMessage("Key: %s; Type: %s; Value: %s; | " % (i, str(type(v)),str(v)))
    elif cmd=="apply":
        sender.sendMessage(chatcolor("&8:===================< &6APPLY &8>===================:"))
        sender.sendMessage("")

        sender.sendMessage(chatcolor("&eRequirements"))
        sender.sendMessage(chatcolor("&71. &fMust be &e13+ years old"))
        sender.sendMessage(chatcolor("&72. &fJoin our Discord &7(/trigger discord)"))
        sender.sendMessage(chatcolor("&73. &fAnswer all questions honestly"))
        sender.sendMessage(chatcolor("&74. &fMeet the playtime requirement"))
        sender.sendMessage("")

        sender.sendMessage(chatcolor("&eRank Requirements"))

        sorted_ranks = sorted(
            gdata["ranks"].items(),
            key=lambda item: parse(item[1]["required_playtime"])
        )

        for rank, info in sorted_ranks:
            sender.sendMessage(
                chatcolor(
                    "&8» &b%s &7- &f%s"
                    % (
                        extended_staff_rank(rank),
                        pretty_timedelta(
                            parse(info["required_playtime"])
                        )
                    )
                )
            )

        sender.sendMessage("")
        sender.sendMessage(chatcolor("&eNotes"))
        sender.sendMessage(chatcolor("&8» &7You may apply before reaching the required playtime"))
        sender.sendMessage(chatcolor("&8» &7Denied applications may be submitted again"))
        sender.sendMessage(chatcolor("&8» &7Use &f/status &7to view staff status"))
        sender.sendMessage("")
        sender.sendMessage(chatcolor("&8:====================================================:"))
        #sender.sendMessage("How to apply")
        #sender.sendMessage("")
        #sender.sendMessage("Requirements")
        #sender.sendMessage("1. Must be 13 or older")
        #sender.sendMessage("2. Must join our discord (/trigger discord)")
        #sender.sendMessage("3. Must respond and elaborate on all questions, this step will determine if you are accepted or not")
        #sender.sendMessage("4. Must have the required playtime (but you can apply before), but depends on what rank are you going for:")
        #sorted_ranks = sorted(
        #    gdata["ranks"].items(),
        #    key=lambda item: parse(item[1]["required_playtime"])
        #)
        #for rank, info in sorted_ranks:
        #    sender.sendMessage(
        #        "    %s: %s" % (
        #            extended_staff_rank(rank),
        #            str(pretty_timedelta(
        #                parse(info["required_playtime"])
        #                ))
        #        )
        #    )
        #sender.sendMessage("If your application gets denied you can always apply again, same for upgrading ranks. Also check your playtime with [/playtime] and your staff status with [/status]")
    save()  
    for p in Bukkit.getOnlinePlayers():
        session_notify(p) 
    return True
def typing_filter(arg, options):
    return [c for c in options if c.lower().startswith(arg.lower())]
def onTabComplete(sender,alias,args):
    online = list(Bukkit.getOnlinePlayers())
    offline = [
        p for p in Bukkit.getOfflinePlayers()
        if not p.isOnline()
    ]
    all_players = online + offline

    cmd=alias.split(" ")[0].split(":")[-1]
    if cmd=="apply":
        return []
    if len(args)==1:
        if cmd=="activate":
            return typing_filter(args[0],["staff"])
        if cmd=="status":
            return typing_filter(args[0],["staff","punishments","set","get","raw_data"])
        return typing_filter(args[0],all_players)
    if len(args)==2:
        if any([i==cmd for i in ["suspend","staff_ban"]]):
            try:
                num = int(args[1])
            except Exception:
                try:
                    num = parse(args[1])
                    if num is None:
                        return []
                except Exception:
                    return [args[1]+c for c in ["s","min","h","d","wk"] if (args[1]+c).lower().startswith(args[1].lower())]
            return [args[1] + i for i in ["s","min","h","d","wk"]]
        if cmd=="status":
            if args[0] == "set" or args[0] == "get":
                return typing_filter(
                    args[1],
                    all_players
                )
            return typing_filter(args[0],all_players)
        if cmd=="punish":
            return typing_filter(args[1],list(gdata["punishments"].keys()))
        if cmd=="promote":
            return typing_filter(args[1],list(gdata["ranks"].keys()))
    if len(args)>=3:
        if any([i==cmd for i in ["suspend","staff_ban","demote"]]):
            return ["\"" + args[-1] + "\""]
        if cmd=="punish":
            return typing_filter(args[-1],list(gdata["punishments"].keys()))
        if cmd=="status":
            # /status set <player>
            target = Bukkit.getOfflinePlayer(args[1])
            u = uuid(target)
            ensure(u)
            # /status set <player> <key>
            if len(args) == 3:
                return typing_filter(
                    args[2],
                    list(data[u].keys())
                )
            # /status set <player> <key> <type>
            if len(args) == 4:
                types_list = []
                for name in dir(__builtin__):
                    obj = getattr(__builtin__, name)
                    if isinstance(obj, type):
                        types_list.append(name)
                return typing_filter(
                    args[3],
                    types_list
                )
            # /status set <player> <key> <type> <value>
            if len(args) == 5:
                current = data[u].get(args[2])
                if isinstance(current, bool):
                    return typing_filter(args[4], ["True", "False"])
                return [str(current)]
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
    if d["staff"] != "" and eligible_to_activate(d) and not _bit.read(local_session_notify[uuid(p)],0):
        chat_log(p,4,"You are now elegible to activate staff see /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],0,True)
    if 0<d["banned"]<=now() and not _bit.read(local_session_notify[uuid(p)],1):
        chat_log(p,4,"Your staff ban expired. See /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],1,True)
    if 0<d["locked"]<now() and not _bit.read(local_session_notify[uuid(p)],2):
        chat_log(p,4,"Your staff suspension expired. See /status")
        local_session_notify[uuid(p)] = _bit.write(local_session_notify[uuid(p)],2,True)
    if 0<now()<=d["banned"] and not _bit.read(d["notify"],3):
        chat_log(p,4,"You are Staff banned. See /status for more")
        d["notify"] = _bit.write(d["notify"],3,True)
    if 0<now()<=d["locked"] and not _bit.read(d["notify"],4):
        chat_log(p,4,"You are Suspended for staff. See /status for more")
        d["notify"] = _bit.write(d["notify"],4,True)
    if d["locked"]==-2 and not _bit.read(d["notify"],5):
        chat_log(p,4,"You are Demoted from staff. See /status for more")
        d["notify"] = _bit.write(d["notify"],5,True)
class _bit:
    @staticmethod
    def read(integer,n):
        return (integer >> n) & 1
    @staticmethod
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
def onJoin(event):
    handle_join(event)
def onQuit(event):
    handle_disconnect(event)
def onKick(event):
    handle_disconnect(event)
# starter variables
FILE="plugins/PySpigot/staff.json"
URL_DATA="https://raw.githubusercontent.com/mohaali250/purseWash-Mc/refs/heads/main/data/player_manager.json"
OWNERUUID = "ce120874-48ad-45e8-a4c5-a70790a56934"
local_session_notify = {i: y for i, y in zip([uuid(k) for k in Bukkit.getOnlinePlayers()],[0]*len(Bukkit.getOnlinePlayers()))}
if not os.path.exists(FILE):
    with open(FILE,"w") as f:
        json.dump({},f) 
with open(FILE,"r") as f:
    data=json.load(f)
# Run  
    
for c in ["promote","suspend","demote","staff_ban","staff_unban","punish","activate","status","apply"]:
    ps.command.registerCommand(onCommand, onTabComplete, c)
gdata = fetch_data()
ps.listener.registerListener(onJoin, PlayerJoinEvent)
ps.listener.registerListener(onQuit, PlayerQuitEvent)
ps.listener.registerListener(onKick, PlayerKickEvent)
ps.scheduler.scheduleRepeatingTask(tick, 1200, 1200)
print("[Staff] Loaded.")
