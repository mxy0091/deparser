#!/bin/python
from jsonParser import jsonP4Parser
from GraphGen import deparserGraph, deparserStateMachines
import os
import sys
import getopt
from math import factorial
from gen_vivado import gen_vivado, export_sim
from debug_util import exportParserGraph
from debug_util import exportDeparserSt, exportDepGraphs


def comp(codeName, outputFolder,
         busWidth=64, exportGraph=False):
    projectParam = {"projectName": codeName,
                    "busWidth": busWidth,
                    "deparserName": "deparser",
                    "boardDir": os.path.join(os.getcwd(), "board", "base")}
    deparserName = projectParam["deparserName"]
    print("processing : {}".format(codeName))
    P4Code = jsonP4Parser("../p4/{}.json".format(codeName))

    headers = P4Code.getDeparserHeaderList()
    parsed = P4Code.getParserGraph()
    depG = deparserGraph(P4Code.graphInit, headers)
    print("generating deparser optimized")
    deparser = deparserStateMachines(depG, P4Code.getParserTuples(), busWidth)
    rtlDir = os.path.join(outputFolder, "rtl")
    depVHDL = deparser.exportToVHDL(rtlDir, deparserName,
                                    parsed.getHeadersAssoc())
    depParam = depVHDL.getVHDLParam()
    projectParam["phvBusWidth"] = depParam["phvBusWidth"]
    projectParam["phvValidityWidth"] = depParam["phvValidityWidth"]
    projectParam["phvValidityDep"] = depParam["phvValidity"]
    projectParam["phvBusDep"] = depParam["phvBus"]

    gen_vivado(projectParam, rtlDir, os.path.join(outputFolder, "vivado_Opt"))
    export_sim(deparserName, rtlDir, os.path.join(outputFolder, "sim_opt"))
    print("end deparser Generation")

    if exportGraph:
        print("exporting Graphs")
        exportParserGraph(parsed, outputFolder)
        exportDepGraphs(P4Code, depG, outputFolder)
        # deparser Graph generation for state Machine
        print("exporting deparser stateMachines optimized")
        exportDeparserSt(deparser, outputFolder, "opt")
        print("nb headers : {}".format(len(P4Code.getDeparserHeaderList())))

    if len(P4Code.getDeparserHeaderList()) < 10:
        print("generating deparser Not optimized")
        deparser = deparserStateMachines(depG, P4Code.getDeparserTuples(),
                                         busWidth)
        print("end generation not optimized")
        deparser.exportToVHDL(os.path.join(outputFolder, "rtlNoOpt"),
                              deparserName, parsed.getHeadersAssoc())
        gen_vivado(projectParam, os.path.join(outputFolder, "rtlNoOpt"),
                   os.path.join(outputFolder, "vivado_noOpt"))
        export_sim(deparserName, rtlDir,
                   os.path.join(outputFolder, "sim_no_opt"))

        if exportGraph:
            print("exporting deparser stateMachines not optimized Graph")
            exportDeparserSt(deparser, outputFolder, "no_opt")
    else:
        print("skip exporting deparser state machine not optimized, "
              "too many possible path : {}"
              .format(factorial(len(P4Code.getDeparserHeaderList()))))


def main(argv):
    codeNames = argv
    exportGraph = False
    output = os.path.join(os.getcwd(), "output")
    busWidth = 64
    try:
        opts, codeNames = getopt.getopt(argv, "ho:w:",
                                        ["exportGraph", "outputDir",
                                         "busWidth", "help"])
    except getopt.GetoptError:
        print("main.py [-o outputDir] [--exportGraph] jsons")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("main.py [-o outputDir] [--exportGraph] jsons")
            sys.exit(0)
        elif opt in ("-o", "--outputDir"):
            output = os.path.join(os.getcwd(), arg)
        elif opt == "--exportGraph":
            exportGraph = True
        elif opt in ("-w", "--busWidth"):
            busWidth = int(arg)
    if len(codeNames) == 0:
        print("please give json Name")
        print("main.py [-o outputDir] [--exportGraph] jsons")
        sys.exit(1)
        
    if not os.path.exists(output):
        os.mkdir(output)

    for codeName in codeNames:
        outputFolder = os.path.join(output, codeName)
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)
        comp(codeName, outputFolder, busWidth, exportGraph)


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
    exit()
