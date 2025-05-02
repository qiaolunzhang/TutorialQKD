set N ordered; #set of physical nodes
set E within {i in N, j in N: i<j}; #set of physical links
set Nl ordered; #set of logical nodes 
set El within Nl cross Nl; #set of logical links
#set El within N cross N; #Used for mapping 

# Is the following lines used to make the link bidirectional?
set A within {N,N} := E union setof{(i,j) in E} (j,i);
#set B within {N,N} := El union setof{(s,t) in El} (t,s); #Used for VNM
set B within {Nl,Nl} := El union setof{(s,t) in El} (t,s); #Used for VNE
#set B within Nl cross Nl;

set nVN;
set GEO{Nl} within N; 
set Nlog{nVN} within Nl;

# the following two lines are not used now
#param timeIN2 default 0;
#param timeOUT2 default 0;
set L := 1..30;
param m:= card(Nl);

#Next 5 lines are for  Survivability, no need to worry about them 
set POWERSET2 := 0 .. (2**m -1);
set S2{k in POWERSET2} := {i in Nl : (k div 2**(ord(i)-1)) mod 2 = 1};

#CUTSET della topologia logica
set SUBE{k in POWERSET2} := {s in S2[k], t in Nl diff S2[k]: (s,t) in El or (t,s) in El};
set SUBE2{k in POWERSET2} := {(s,t) in El: (s,t) in SUBE[k] or (t,s) in SUBE[k]};

param M := 70;

var xN{N,Nl} binary; #node assignment/mapping
var q{A,B} binary; #link assignment/mapping
var qa{E,El} binary;
var wj{A,B,L} binary;
var w{A,B,L} binary;
var y{E,El,El} binary;

#var z{El,El} binary;

var x{B,L} binary ;
var xj{B,L} binary ;

#var p >=0 integer;

var p{L} binary;



minimize Ninterfaces:
	
	# TOTAL WAVELENGTHS CONSUMPTION
	sum{(i,j) in A, (s,t) in B} q[i,j,s,t];
	

# node mapping

s.t. atMostOnePhysicNode {i in N, vn in nVN}:
	sum{j in Nlog[vn]} xN[i,j] <= 1;

s.t. LogicNodeMapping {j in Nl}:
	sum{i in GEO[j]} xN[i,j] = 1;



# Flow constraints

s.t. flow {(s,t) in B, i in N}:
	sum{(i,j) in A} q[i,j,s,t] - sum{(j,i) in A} q[j,i,s,t] = xN[i,s]-xN[i,t];
	

s.t. bidirectionality {(s,t) in B, (i,j) in A}:
#s.t. bidirectionality {(s,t) in B, (i,j) in A: i in N}:
	q[i,j,s,t]-q[j,i,t,s]=0;

s.t. biderectionality2 {(s,t) in B, (i,j) in A}:
	q[i,j,s,t]+q[j,i,s,t]<=1;
	


# wavelength assignment

s.t. continuity1 {(i,j) in A, (s,t) in B, l in L}:
	w[i,j,s,t,l] <= x[s,t,l];

s.t. continuity2 {(i,j) in A, (s,t) in B, l in L}:
	w[i,j,s,t,l] <= q[i,j,s,t];
	
s.t. continuity3 {(i,j) in A, (s,t) in B, l in L}:
	w[i,j,s,t,l] >= x[s,t,l] + q[i,j,s,t] -1;
	
s.t. continuity4 {(s,t) in B}:
	sum{l in L} x[s,t,l]=1;




# wavelength contiguity
s.t. continuity5 {(i,j) in A, (s,t) in B, (u,r) in B diff{(s,t)}, l in L}:#:r<>t or u<>s}:
	w[i,j,s,t,l]+w[i,j,u,r,l]<=1;


s.t. wavelengthNUM{l in L}:
	p[l]>= sum{(s,t) in B} x[s,t,l]/M;
