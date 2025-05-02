# this model want to solve the time-slot interchange problem
set Np ordered; # set of physical nodes
set Ep_u within {i in Np, j in Np: i<j}; #set of physical links

set Ea_u := {i in Np, j in Np: i<j}; # set of all possible node pairs of request: unidirectional
# make the link bidirectional
set Ep within {Np,Np} := Ep_u union setof{(i,j) in Ep_u} (j,i);
set Ea within {Np,Np} := Ea_u union setof{(i,j) in Ea_u} (j,i);
set Nt within Np; # set of trusted node

set P default Ea_u;

set W;
# set of key distribution time frame
set N;
set T;
# theta
param theta default 1;

# set R within {i in Np, j in Np: i<j}, default Ea_u; # set of all
# set of node pairs with key rate requests in KDTF n
set R within {i in Np, j in Np: i<j}, default Ea_u; # set of all

# the set of paths
set PhiSet{Ea};
set PhiSetAll;

# here we do not use R, because we may change R here
param r{Ea_u} default 0;
# equals to 1 if link e is the path phi
param delta{PhiSetAll, Ep} default 0;

# the key rate of link pair
param h{PhiSetAll} default 5;
# the number of quantum modules
param C{Np} default 2;

param Q0{P} default 0; # the available keys in the QKP in the beginning
param Qm{P} default 1; # the maximum amount of keys in the QKP in the beginning

param alpha1 default 1000;
param alpha2 default 60;

# param M := 12;#130;
param M default 50;
param T_max default 4;

var q{Ea, P, W, T} binary; # q{(i,j), (s,d), w, t}
#var f{Ea, Ea_u, Np, W, T}; # f{(i,j), (s,d), m, w, t}
var f{P, W, T} binary;
var u{Ea, P, W, T} binary; # u{(i,j), (s,d), w, t}
var u_bar{Ea, P, W, T} binary; # u{(i,j), (s,d), w, t}

var x{Ea, PhiSetAll, P, W, T} binary; # x[i,j,s,d,m,n,w,t]


# Key rate provided for the node 
# pair (s,d) on wavelength w at time-slot t
var zeta{P, W, T}, >=0; 
# Key rate provided from the QKP of the node pair (i,j)
# for the trusted relay of node pair (s,d) at time-slot t
var z{Ea, P, W, T}, >=0;
# Key rate provided by the QKD network for node pair (s,d)
var lambda{Ea_u,T}, >=0;
# Used key rate from QKP of node pair (i,j)
# var k{P,T}, >=0;
var k{P, T};

var y{Ea_u} binary; # equals to 1 if the corresponding request is served
var g{P, T}, >=0;

# var kMq{Ea,Ea_u,W,T}, >=0; # kMq[i,j,s,t,w,t]


maximize ObjectiveServedRequest:
	
	# Total number of served request
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in P} alpha2 * g[s,d,T_max]
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in P, t in T} alpha2 * k[s,d,t]
	sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in P, t in T} k[s,d,t] / (T_max + 1)
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j]
;

maximize ObjectiveServedRequestSecond:
	
	# Total number of served request
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in P} alpha2 * g[s,d,T_max]
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in P, t in T} alpha2 * k[s,d,t]
	sum{(i,j) in R} alpha1 * r[i,j] * y[i,j]
	# sum{(i,j) in R} alpha1 * r[i,j] * y[i,j] + sum{(s,d) in R, t in T} k[s,d,t]
;

# 1) eg. flow conservation constraints for quantum keys

s.t. flowQuantum {(s,d) in Ea_u, i in Np, w in W, t in T}:
	sum{(i,j) in Ea} q[i,j,s,d,w,t] 
	- sum{(j,i) in Ea} q[j,i,s,d,w,t] =
			if i = s then f[s,d,w,t]
			else if i = d then -f[s,d,w,t]
			else 0 
;
s.t. flowQuantum2 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	q[i,j,s,d,w,t] <= f[s,d,w,t]
;
s.t. flowQuantum3 {(s,d) in P, i in Np, w in W, t in T}:
	sum{(i,j) in Ea} q[i,j,s,d,w,t] <= 1
;
s.t. flowQuantum4 {(s,d) in P, j in Np, w in W, t in T}:
	sum{(i,j) in Ea} q[i,j,s,d,w,t] <= 1
;
s.t. flowQuantum5 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	q[i,j,s,d,w,t] + q[j,i,s,d,w,t] <= 1
;

# 2) Link formation of QKD path
s.t. flowNoSelfProvision {(s,d) in P, w in W, t in T}:
	u_bar[s,d,s,d,w,t] = 0
;

s.t. flowProvision1 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	u[i,j,s,d,w,t] + u_bar[i,j,s,d,w,t] >= q[i,j,s,d,w,t]
;

s.t. flowProvision2 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	u[i,j,s,d,w,t] <= q[i,j,s,d,w,t]
;

s.t. flowProvision3 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	u_bar[i,j,s,d,w,t] <= q[i,j,s,d,w,t]
;

# 3) Quantum module capacity constriants
s.t. quantumChannelCapacity1 {i in Np, t in T}:
	sum{(s,d) in P, (i,j) in Ea, w in W} (u[i,j,s,d,w,t]  + u[j,i,s,d,w,t])<= C[i]
;

# 4) Trusted relay
s.t. trustedRelay {(s,d) in P, (i,j) in Ea, w in W, t in T: i <> s and j <> d and (i not in Nt) and (j not in Nt)}:
	q[i,j,s,d,w,t] = 0
;

# 5) Routing of quantum channels
#var x{Ea, PhiSetAll, P, W, T} binary; # x[i,j,s,d,m,n,w,t]
s.t. flowQKDLink {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	sum{phi in PhiSet[i,j]} x[i,j,phi,s,d,w,t] = u[i,j,s,d,w,t]
;
s.t. flowQKDLink2 {(i,j) in Ea, phi in PhiSet[i,j], w in W, t in T}:
    sum{(s,d) in P} x[i,j,phi,s,d,w,t] <= 1
;
# param delta{PhiSetAll, Ep} default 0;
s.t. flowQKDLink3 {(i,j) in Ep, w in W, t in T}:
    sum{(s,d) in P, (i2,j2) in Ea, phi in PhiSet[i2,j2]} (x[i2,j2,phi,s,d,w,t] * delta[phi, i, j]) <= 1
;

# 6) Key supply constraint
s.t. keySupply1 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	zeta[s,d,w,t] <= sum{phi in PhiSet[i,j]} x[i,j,phi,s,d,w,t] * h[phi] + z[i,j,s,d,w,t] + M * (1 - q[i,j,s,d,w,t])
;

s.t. keySupply1Add {(s,d) in P, w in W, t in T}:
	zeta[s,d,w,t] <= M * f[s,d,w,t]
;
s.t. keySupply2 {(s,d) in P, (i,j) in Ea, w in W, t in T}:
	z[i,j,s,d,w,t] <= M * u_bar[i,j,s,d,w,t]
;


# 11) key storing, partially serving requests is not possible
s.t. keyStoring1 {(s,d) in P, t in T}:
	k[s,d,t] <= sum{w in W} zeta[s,d,w,t] - sum{(s2,d2) in P, w in W} (z[s,d,s2,d2,w,t] + z[d,s,s2,d2,w,t]) - lambda[s,d,t]
;
s.t. keyStoring2 {(s,d) in R}:
	r[s,d] * y[s,d] <= sum{t in T} (lambda[s,d,t] / (T_max+1))
;

# when storing, we need to shrink it to the whole time-slot frame if g is like the key rate
s.t. keyStoring3 {(s,d) in P, t in 1..T_max}:
	g[s,d,t] <= g[s,d,t-1] + k[s,d,t] * theta / (T_max + 1)
;
s.t. keyStoring3Add {(s,d) in P}:
	g[s,d,0] = Q0[s,d] + k[s,d,0] * theta / (T_max + 1)
;
s.t. keyStoring4 {(s,d) in P, t in T}:
	g[s,d,t] >=0
;
s.t. keyStoring5 {(s,d) in P, t in T}:
	g[s,d,t] <= Qm[s,d]
;

# Poliqi
s.t. NoTrustedRelay {(s,d) in P, (i,j) in Ea, w in W, t in T: i <> s or j <> d}:
    q[i,j,s,d,w,t] = 0
;

s.t. NoOpticalBypass {(s,d) in P, (i,j) in Ea diff Ep, w in W, t in T}:
    u[i,j,s,d,w,t] = 0
;

problem rwtaProblem:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequest,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3,
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5
;

problem rwtaOBProblem:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequest,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoTrustedRelay
;

problem rwtaTRProblem:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequest,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoOpticalBypass
;

problem rwtaNoOBTRProblem:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequest,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoTrustedRelay, NoOpticalBypass
;

problem rwtaProblemSecond:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequestSecond,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3,
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5
;

problem rwtaOBProblemSecond:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequestSecond,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoTrustedRelay
;

problem rwtaTRProblemSecond:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequestSecond,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoOpticalBypass
;

problem rwtaNoOBTRProblemSecond:
q, f, u, u_bar, x, zeta, z, lambda, k, y, g,
ObjectiveServedRequestSecond,
flowQuantum,flowQuantum2,flowQuantum3, flowQuantum4, flowQuantum5,
flowNoSelfProvision,flowProvision1,flowProvision2,flowProvision3, 
#keySupplyLinealization1,keySupplyLinealization2,#keySupplyLinealization3,keySupplyLinealization4,
quantumChannelCapacity1,
# trustedRelay1,trustedRelay2,
trustedRelay,
flowQKDLink,flowQKDLink2,flowQKDLink3,
keySupply1,keySupply1Add,keySupply2,
keyStoring1, keyStoring2, keyStoring3, keyStoring3Add, 
keyStoring4, keyStoring5,
NoTrustedRelay, NoOpticalBypass
;

