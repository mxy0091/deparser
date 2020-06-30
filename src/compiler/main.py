#!/bin/python

from jsonParser import jsonP4Parser
from GraphGen import deparserGraph, deparserStateMachines
import networkx as nx
import os
from math import factorial


def nx_to_png(machine, outputFile):
    tmp = nx.nx_pydot.to_pydot(machine)
    tmp.write_png(outputFile)


codeNames = ["t0"] #, "t4", "open_switch"]
output = os.path.join(os.getcwd(), "output")
if not os.path.exists(output):
    os.mkdir(output)

for codeName in codeNames:
    print("processing : {}".format(codeName))
    P4Code = jsonP4Parser("../p4/{}.json".format(codeName))
    outputFolder = os.path.join(output, codeName)
    if not os.path.exists(outputFolder):
        os.mkdir(outputFolder)

    headers = P4Code.getDeparserHeaderList()
    parsed = P4Code.getParserGraph()
    print("exporting parser state graph")
    parsed.exportToDot(os.path.join(outputFolder, "ParserStates.dot"))
    nx_to_png(parsed.G, os.path.join(outputFolder, "ParserStates.png"))

    parsed = P4Code.getParserHeaderGraph()
    print("exporting parser header graph")
    parsed.exportToDot(os.path.join(outputFolder, "ParserHeader.dot"))
    nx_to_png(parsed.G, os.path.join(outputFolder, "ParserHeader.png"))

    depG = deparserGraph(P4Code.graphInit, headers)
    if len(P4Code.getDeparserHeaderList()) < 10:
        print("exporting deparser closed graph (not optimized)")
        nx.nx_pydot.write_dot(depG.getClosedGraph(),
                              os.path.join(outputFolder,
                                           "./deparserClosed.dot"))
        nx_to_png(depG.getClosedGraph(),
                  os.path.join(outputFolder, "./deparserClosed.png"))
    else:
        print("skip exporting deparser closed graph not optmized")

    print("exporting deparser graph parser optimized")
    nx.nx_pydot.write_dot(depG.getOptimizedGraph(P4Code.getParserTuples()),
                          os.path.join(outputFolder, "./deparserParser.dot"))
    nx_to_png(depG.getOptimizedGraph(P4Code.getParserTuples()),
              os.path.join(outputFolder, "deparserParser.png"))

    # deparser Graph generation for state Machine
    print("exporting deparser stateMachines optimized")
    deparser = deparserStateMachines(depG, P4Code.getParserTuples(), 64)
    for i, st in enumerate(deparser.getStateMachines()):
        nx.nx_pydot.write_dot(st, os.path.join(outputFolder,
                                               "machine{}_opt.dot".format(i)))
        nx_to_png(st, os.path.join(outputFolder,
                                   "machine_mux{}_opt.png".format(i)))
        nb = 0
        for j in nx.all_simple_paths(st, deparser.init, deparser.last):
            nb += 1
        print("state machine {} posseses {} path".format(
            i, nb))

    print("nb headers : {}".format(len(P4Code.getDeparserHeaderList())))

    if len(P4Code.getDeparserHeaderList()) < 10:
        print("exporting deparser stateMachines not optimized")
        P4Code = jsonP4Parser("../p4/{}.json".format(codeName))
        deparser = deparserStateMachines(depG, P4Code.getDeparserTuples(), 64)
        for i, st in enumerate(deparser.getStateMachines()):
            nx.nx_pydot.write_dot(st,
                                  os.path.join(
                                      outputFolder,
                                      "machine{}_no_opt.dot".format(i)))
            nx_to_png(st, os.path.join(outputFolder,
                                       "machine_mux{}_no_opt.png".format(i)))
            nb = 0
            for j in nx.all_simple_paths(st, deparser.init, deparser.last):
                nb += 1
            print("state machine {} posseses {} path".format(
                i, nb))
    else:
        print("skip exporting deparser state machine not optimized, "
              "too many possible path : {}"
              .format(factorial(len(P4Code.getDeparserHeaderList()))))
