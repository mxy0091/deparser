from jsonParser import jsonP4Parser
from GraphGen import deparserGraph
import networkx as nx

P4Code = jsonP4Parser("../p4/t4.json")
headers = P4Code.getDeparserHeaderList()

listeTuple = list(headers.keys())  # conversion de nom
Stmp = [(0, 3, 1), (0, 4, 1), (2, ), (0, 2, 4)]
S = []
for i in Stmp:
    tmp = []
    for j in i:
        tmp.append(listeTuple[j])
    S.append(tuple(tmp))

depG = deparserGraph(headers)
#depG.getOptimizedGraph(S, True)

depGc = depG.getClosedGraph()

print(depG.getAllPathClosed())
print(P4Code.getDeparserTuples())
equivalent = True
for i in depG.getAllPathClosed():
    if i not in P4Code.getDeparserTuples():
        equivalent = False
print(equivalent)
