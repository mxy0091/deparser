from jsonParser import jsonP4Parser
from GraphGen import deparserGraph


P4Code = jsonP4Parser("../p4/t4.json")
headers = P4Code.getDeparserHeaderList()

listeTuple = list(headers.keys())  # conversion de nom
Stmp = [(0, 3, 1), (0, 4, 1), (2, 3), (0, 2, 4)]
S = []
for i in Stmp:
    tmp = []
    for j in i:
        tmp.append(listeTuple[j])
    S.append(tuple(tmp))

depG = deparserGraph(headers)
depG.genOptimizedGraph(S, True)
