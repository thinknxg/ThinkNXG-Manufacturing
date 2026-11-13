import json,sys,collections
EV=json.load(open(sys.argv[1] if len(sys.argv)>1 else '/home/claude/out/events.json'))
EV.sort(key=lambda e:(e[0],e[1]))
bal=collections.defaultdict(float); bad=0
low=collections.defaultdict(lambda:1e18)
for d,t,l,lines in EV:
    for it,wh,q in lines:
        bal[(it,wh)]+=q
        low[(it,wh)]=min(low[(it,wh)],bal[(it,wh)])
        if bal[(it,wh)]<-1e-6: print("NEGATIVE",d,t,l,it,wh,round(bal[(it,wh)],3)); bad+=1
print("events:",len(EV),"negative:",bad)
print("closing balances (selected):")
for k in sorted(bal):
    if k[0].startswith(("FG-","SA-")): print(" ",k[0],k[1].split(' - ')[0],round(bal[k],2))
print("lowest RM balances:")
for k in sorted(low,key=lambda k:low[k])[:8]: print(" ",k[0],round(low[k],1))
