#!/usr/local/bin/python

import itertools as it
import sys
import os

if len(sys.argv) <= 1:
    print("Usage: {} n r truthtable1 ... truthtablem".format(sys.argv[0]))
    print("(n is the number of inputs, r is the number of gates, m is the number of outputs)")
    sys.exit(0)

n = int(sys.argv[1]) # number of inputs
r = int(sys.argv[2]) # number of gates

truthtables = sys.argv[3:]

m = len(truthtables) # number of outputs

#print("c Looking for a circuit with", n, "inputs,", r, "gates and", m, "output(s) computing", truthtables)


assert all(len(table) == 1<<n for table in truthtables), "wrong truth table"
assert all(all(c in "01*" for c in table) for table in truthtables), "wrong symbol in a truth table"
assert all((table[0] == '0' or table[0] == '*') for table in truthtables), "function is not normal"

# print("c n", n, " (number of inputs)")
# print("c r", r, " (number of gates)")
# print("c m", m, " (number of outputs)")

#######
####### declaring cnf variables

vars = {} # dictionary
vars["dummy"] = 0

def isvalidinputnum(i):
    return 1 <= i and i <= n

def isvalidgatenum(i):
    return n+1 <= i and i <= n+r

def isvalidoutputnum(h):
    return 1 <= h and h <= m

def varnum(name):
  if name in vars:
      return vars[name]

  vars[name] = len(vars)+1
  return vars[name]

# output of i-th gate on inputs (p,q)
def gatetypevarnum(i, p, q):
    assert 0 <= p and p <= 1 and 0 <= q and q <= 1
    assert isvalidgatenum(i)
    return varnum("f_"+str(i)+"_"+str(p)+"_"+str(q))

# i-th gate operates on gates j and k
def predecessorsvarnum(i, j, k):
    #print(i)
    assert isvalidgatenum(i)
    assert (isvalidgatenum(j) or isvalidinputnum(j)) and (isvalidgatenum(k) or isvalidinputnum(k))
    assert j < k and k < i
    return varnum("s_"+str(i)+"_"+str(j)+"_"+str(k))

# h-th output is computed at gate i
def outputvarnum(h, i):
    assert isvalidoutputnum(h)
    assert isvalidgatenum(i) or isvalidinputnum(i)
    return varnum("g_"+str(h)+"_"+str(i))

# t-th bit of the truth table of i-th gate
def gatevalue(i, t):
    assert isvalidgatenum(i) or isvalidinputnum(i)
    assert 0 <= t and t < 2**n
    return varnum("x_"+str(i)+"_"+str(t))

# i-th gate has different values on inputs t1 and t2
def differentvalues(i, t1, t2):
    assert isvalidgatenum(i)
    assert 0 <= t1 and t1 < (1 << n) and 0 <= t2 and t2 < (1 << n)
    return varnum("diff_"+str(i)+"_"+str(t1)+"_"+str(t2))



#######
####### writing down clauses
clauses=[]

# given a list of literals writes clauses stating that exactly one of these variables is true
def exactly_one_of(arr):
    longclause = []
    for x in arr:
        longclause.append(x)

    clauses.append(longclause)

    for pair in it.combinations(arr, 2):
        shortclause = []
        for i in pair:
            shortclause.append(-i)

        clauses.append(shortclause)

# each gate i operates on two gates j,k
for i in range(n+1, n+r+1):
    pairs = it.combinations(range(1, i), 2)
    ijk = [predecessorsvarnum(i,j,k) for (j,k) in pairs]
    exactly_one_of(ijk)

# each output h is computed somewhere
for h in range(1, m+1):
    hi = [outputvarnum(h,i) for i in range(n+1, n+r+1)]
    exactly_one_of(hi)

# truth values for inputs
for i in range(1, n+1):
    for t in range(0, 1<<n):
        clause = []
        if ((t >> i-1) & 1):
            clause.append(gatevalue(i,t))
        else:
            clause.append(-gatevalue(i,t))
        clauses.append(clause)

# i-th gate computes the right value
for i in range(n+1, n+r+1):
    for (j,k) in it.combinations(range(1, i), 2):
        for (a,b,c) in it.product(range(0,2), repeat=3):
            for t in range(0, 1<<n):
                # main clause
                clause = []
                clause.append(-predecessorsvarnum(i,j,k))
                clause.append((-1 if a else 1)*gatevalue(i, t))
                clause.append((-1 if b else 1)*gatevalue(j, t))
                clause.append((-1 if c else 1)*gatevalue(k, t))
                clause.append((1 if a else -1)*gatetypevarnum(i, b, c))

                clauses.append(clause)


# each output h computes the right value
for h in range(1, m+1):
    for t in range(0, 1<<n):
        if truthtables[h-1][t] != "*":
            for i in range(n+1, n+r+1):
                clause = []
                clause.append(-outputvarnum(h,i))
                if truthtables[h-1][t] == "1":
                    clause.append(gatevalue(i,t))
                elif truthtables[h-1][t] == "0":
                    clause.append(-gatevalue(i,t))

                clauses.append(clause)



######## now adding additional clauses that are supposed to help a solver to run quicker

# i-th gate is normal
for i in range(n+1, n+r+1):
    clause = []
    clause.append(-gatetypevarnum(i, 0, 0))
    clauses.append(clause)

# i-th gate computes non-degenerate function
for i in range(n+1, n+r+1):
    clauses.append([gatetypevarnum(i, 0, 1), gatetypevarnum(i, 1, 0), gatetypevarnum(i, 1, 1)])
    clauses.append([gatetypevarnum(i, 0, 1), -gatetypevarnum(i, 1, 0), -gatetypevarnum(i, 1, 1)])
    clauses.append([-gatetypevarnum(i, 0, 1), gatetypevarnum(i, 1, 0), -gatetypevarnum(i, 1, 1)])

## i-th gate is used at least once
for i in range(n+1, n+r+1):
    clause = []
    for k in range(1, m+1):
        clause.append(outputvarnum(k, i))
    for k in range(i+1, n+r+1):
        for j in range(1, i):
            clause.append(predecessorsvarnum(k, j, i))
    for k in range(i+1, n+r+1):
        for j in range(i+1, k):
            clause.append(predecessorsvarnum(k, i, j))

    clauses.append(clause)

# avoiding reapplying an operand (not sure that helps)
for j in range(1, i):
    for k in range(j+1, i):
        for q in range(i+1, n+r+1):
            clauses.append([-predecessorsvarnum(i, j, k), -predecessorsvarnum(q, j, i)])
            clauses.append([-predecessorsvarnum(i, j, k), -predecessorsvarnum(q, k, i)])


### NOW COME OPTIONAL CLAUSES:

# if we are looking for a formula: i-th gate is used at most once




######## finally, writing down all the clauses

with open('tmp.cnf', 'w') as f:
  f.write("p cnf {} {}\n".format(len(vars), len(clauses)))
  for c in clauses:
    c.append(0);
    f.write(" ".join(map(str, c)) + "\n")

  for v in vars.keys():
    f.write("c {} {}\n".format(v, vars[v]))


#### running solver
os.system("./minisat_static tmp.cnf tmp.sat")

satass = []

with open("tmp.sat") as satfile:
  for line in satfile:
    # print(line)
    if line.split()[0] == "UNSAT":
      print("\n\nThere is no such circuit, sorry")
      exit(0)
    elif line.split()[0] == "SAT":
      print("\n\nSatisfying assignment found")
    else:
      satass += [int(x) for x in line.split()]

if len(satass) > 0:
  cnffile = open("tmp.cnf", 'r')
  vars = {}

  for line in cnffile:
    if line[0] == 'c':
      tokens = line.split()
      vars[tokens[1]] = int(tokens[2])

  cnffile.close()

for i in range(n+1, n+r+1):
    s = "x" + str(i)+ "("
    left, right = 0, 0
    for (j,k) in it.combinations(range(1, i), 2):
        varnum = vars["s_"+str(i)+"_"+str(j)+"_"+str(k)]
        if varnum in satass:
            s += "x"+str(j)+",x"+str(k)+"): "
            left, right = j, k

    for (a,b) in it.product(range(0,2), repeat=2):
        varnum = vars["f_"+str(i)+"_"+str(a)+"_"+str(b)]
        if varnum in satass:
            s += "1"
        else:
            assert -varnum in satass
            s += "0"

    gatetype = s[-4:]
    if gatetype == "1001":
        s+= " x" + str(left) + "=x" + str(right) + " "
    elif gatetype == "0100":
        s+= " (x" + str(left) + "+1)*x" + str(right) + " "
    elif gatetype == "1000":
        s+= " (x" + str(left) + "+1)*(x" + str(right) + "+1) "
    elif gatetype == "0001":
        s+= " x" + str(left) + "*x" + str(right) + " "
    elif gatetype == "0111":
        s+= " (x" + str(left) + "+1)*(x" + str(right) + "+1)+1 "
    elif gatetype == "1110":
        s+= " (x" + str(left) + "+1)*(x" + str(right) + "+1)+1 "
    elif gatetype == "0010":
        s+= " x" + str(left) + "*(x" + str(right) + "+1) "
    elif gatetype == "1011":
        s+= " (x" + str(left) + "+1)*x" + str(right) + "+1 "
    elif gatetype == "0110":
        s+= " x" + str(left) + "+x" + str(right) + " "


    for h in range(1, m+1):
        varnum = vars["g_"+str(h)+"_"+str(i)]
        if varnum in satass:
            s += " (output" + str(h) + ")"

    print(s)

