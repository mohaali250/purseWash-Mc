import datetime

cur = datetime.datetime.today()

url="https://raw.githubusercontent.com/mohaali250/server_plan_predicter_pack/main/calibration.json"
data = json.loads(requests.get(url).text)

oldcrt = data["Credits"]
olddslp = data["Days_Since_last_pay"]
lupd = datetime.datetime(*data["Last_Updated"])

rq = 400
getd = 10


def is_ok():
    crt = (oldcrt + ((cur-lupd)*getd).days)%(rq)
    dslp = (((cur-lupd).days)+olddslp)%(rq//getd)
    while True:
        dslp += 1
        crt += getd
        cur = cur + datetime.timedelta(days=1)
        if dslp > 30 and crt < rq:
            cron = False
        elif dslp > 30 and crt >= rq:
            cron = True
            crt -= rq
            dslp = 0
        elif dslp <= 30 :
            cron = True
        if datetime.datetime.today() == cur:
            return not cron

@EventHandler
def on_join(event):
    now = datetime.datetime.now(datetime.timezone.utc).time()
    if is_ok() and (datetime.time(9,0) <= now <= datetime.time(15,0)):
        event.disallow("Ops... The server isnt on a 24/7 plan right now. Come back at 15:00 UTC+0. To check the predicted schedule, go to our discord server and download the schedule prediction script.")
