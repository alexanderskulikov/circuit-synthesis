# Finding Efficient Circuits Using SAT-solvers

## Usage
<pre>
python3 circuit2sat.py n r truthtable1 ... truthtablem
</pre>
Here, n is the number of inputs of the function,
r is the number of gates, m is the number of outputs 
(hence, truthtablei is a bit-string of length 2^n).

The script uses the minisat SAT-solver 
and assumes that there is an executable 
file minisat_static in the same folder.

For using other SAT-solvers, either adjust
the line
<pre>
os.system("./minisat_static tmp.cnf tmp.sat")
</pre>
of the script or simply run your favourite 
SAT-solver on the CNF-formula tmp.cnf generated
by the script.

## Reduction
The reduction to CNF-SAT is described in [Kojevnikov, Kulikov, Yaroslavtsev.
Finding Efficient Circuits Using SAT-Solvers. SAT 2009.
(<a href="http://dx.doi.org/10.1007/978-3-642-02777-2_5">DOI</a>)]. See also [D. E. Knuth, The Art of Computer Programming, Volume 4, Fascicle 6: Satisfiability, 1st ed. Addison-Wesley Professional, 2015. (Solution to exercise 477)]
An implementation of the reduction by Knuth is available at <http://www-cs-faculty.stanford.edu/∼knuth/programs.html> (sat-chains.w file in SATexamples archive).