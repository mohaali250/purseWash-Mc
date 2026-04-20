import datetime, requests, json

cur = datetime.datetime.today()

url="https://raw.githubusercontent.com/mohaali250/server_plan_predicter_pack/main/calibration.json"
data = json.loads(requests.get(url).text)

oldcrt = data["Credits"]
olddslp = data["Days_Since_last_pay"]
lupd = datetime.datetime(*data["Last_Updated"])

rq = 400
getd = 10

crt = (oldcrt + ((cur-lupd)*getd).days)%(rq)

dslp = (((cur-lupd).days)+olddslp)%(rq//getd)


ws = cur.weekday()
print(" Mon Tue Wed Thu Fri Sat Sun")
print(" "*(ws+1), end="")
pon = True
difmonth = ""

for i in range(1,365,1):
    dslp += 1
    crt += getd
    cur = cur + datetime.timedelta(days=1)
    if i%7==ws: 
        print(" "+str(cur)[:7] if difmonth != str(cur)[:7] else " ")
        print()
        difmonth = str(cur)[:7]
    if dslp > 30 and crt < rq:
        cron = False
    elif dslp > 30 and crt >= rq:
        cron = True
        crt -= rq
        dslp = 0
    elif dslp <= 30 :
        cron = True
    if i%7==ws:    
        pon = not cron    
    print(" " if pon != cron else ("\033[48;2;0;255;0m\033[38;2;0;0;0m " if cron else "\033[48;2;255;0;0m "),end="")    
    print("\033[48;2;0;255;0m\033[38;2;0;0;0m" if cron else "\033[48;2;255;0;0m", end="")  
    print(f"{cur.day:0>2}", end="")
    print("\033[49m\033[39m", end="")
    pon = cron
