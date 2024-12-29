**Simulation**

// Opzione A/B
// Distribuzione Uniforme/Lognormale

-Factors:
N = (100, 250, 500) //FEDE P.
Interval rate = (1/0.1, 1/0.5) //Uno estremo, un caso medio //FEDE C.
Size rate = (10^4, 10^3) //Uno estremo, un caso medio //LORE

Caso medio: N=250, I=1/0.5, S=1/10^3


PARAMETRI FISSI:
M fisso = 9
height, Width fissi = 1800x1800
Service rate = 10^5
delay = 50 ms
Grandezza coda = 50 
media, std dev = (log(1800/2), 0,4)

simulation time = 1000s
warmup time = 100s
