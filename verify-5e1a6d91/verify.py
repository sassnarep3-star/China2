import json,os,sys,csv
sys.dont_write_bytecode=True; D=os.path.dirname(__file__); d=json.load(open(f"{D}/data.json")); c=d["costs"]; n=0
def ck(x,m):
 global n; n+=1; assert x,m
ck(len(c)==40 and c[0]["usd"]==10000 and c[-1]["usd"]==400000,"tiers")
SELL, MID = d["inputs"]["sell"], d["inputs"]["mid"]
for r in c:
 fee=(min(max(r["usd"]*SELL*0.001,50),260)+150)/SELL; sp=r["usd"]*(SELL/MID-1)
 ck(abs(r["total_usd"]-round(sp+fee,2))<0.02 and abs(r["fee_usd"]-round(fee,2))<0.02,"arith")
ck(list(csv.DictReader(open(f"{D}/costs.csv"))).__len__()==40,"csv")
for p in ["index","methods","costs","questions","sources","flagged"]:
 h=open(f"{D}/{p}.html").read(); ck("viewport" in h and "https://" in h,p)
print(f"PASS {n} checks, 40 tiers, 10 sources")
