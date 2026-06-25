import slbcom as slb

s=int(input('entrer le numero de port:'))
if slb.opencom(s,9600,'N',1,1):
        r0=0
        slb.decalers(s,[r0])
while 1:
        bouton=input('enter un nombre:')
        r0=int(bouton)
        if r0<256:
                slb.decalers(s,[r0])
        else:
                break
        
#print(DCD(s))
slb.closecom(s)
