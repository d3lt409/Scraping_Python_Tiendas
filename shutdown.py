import numpy as np
import random as r
import scipy.stats as st

ga=0
pa=0
ts=360 #1 hora

gll = [ts+1]
pll = [ts+1]

ta=[]
tll=[0]
tpll=[0]

gs=[0]
ps=[0]
ncs=[0]

tps=[ts+1]

def Nor(u,dv):
  return st.norm.ppf(r.random(),loc=u,scale=dv)
def exp(media):
  return -media*np.log(r.random())

while min(tpll[-1], tps[-1],ts) != ts:
  if tpll[-1]<tps[-1]: #LLega
    ncs=np.append(ncs, ncs[-1]+1)     
    print(gs[-1],ps[-1]) 
    if min(gs[-1],ps[-1])==gs[-1]: #Llega grande      
      if ncs[-1]==1:
        ta=np.append(ta, exp(20))
        gs=np.append(gs, gs[-1]+ta[-1])         
        tps[-1]=tpll[-1]+ta[-1]
      tll=np.append(tll, Nor(30,10)) 
      tpll=np.append(tpll, tpll[-1]+tll[-1])   
    else: #Llega pequeño
      if ncs[-1]==1:
        ta=np.append(ta, exp(20))
        ms=np.append(ps, ps[-1]+ta[-1])
        tps[-1]=tpll[-1]+ta[-1]
      tll=np.append(tll, exp(60))
      tpll=np.append(tpll, tpll[-1]+tll[-1])

  else: #Ocurre una salida
    ncs=np.append(ncs, ncs[-1]-1)
    if ncs[-1]>0:
      if min(gs[-1],ps[-1])==gs[-1]: #Sale grande
        ta=np.append(ta, exp(30))
        gs=np.append(gs, gs[-1]+ta[-1])         
        tps[-1]=np.append(tps,tps[-1]+ta[-1]) 
      else: #Sale pequeño
        ta=np.append(ta, (30+(45-30)*r.random()))
        ps=np.append(ps, ps[-1]+ta[-1])
        tps[-1]=tpll[-1]+ta[-1]
    else:
      tps.append(ts+1)