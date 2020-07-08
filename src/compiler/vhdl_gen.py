from colorama import Fore, Style
from string import Template
from os import path, mkdir, scandir
from shutil import copyfile
from warnings import warn
import vhdl_util

VERSION = 0.1


class deparserHDL(object):
    def __getlibrary(self):
        """set a dictionnary with library folder
        each folder is the <name> of an entity
        file component.vhdl components instantiation templates
        file entity.vhdl are placement template for components
        file module.vhdl are lib file to copy
        """
        self.lib = {}
        for d in scandir(self.tmplFolder):
            if d.is_dir():
                curPath = path.join(self.tmplFolder, d.name)
                self.lib[d.name] = (path.join(curPath, "module.vhdl"),
                                    path.join(curPath, "component.vhdl"),
                                    path.join(curPath, "entity.vhdl"))

    def __init__(self, deparser, outputDir,
                 templateFolder,
                 phvBus,
                 baseName="deparser",
                 libDirName="lib",
                 clk="clk", reset_n="reset_n"):
        self.clkName = clk
        self.enDep = "en_deparser"
        self.rstName = reset_n
        self.dep = deparser
        self.phvBus = phvBus
        self.headerBus = phvBus[0]["data"]
        self.busValidAssocPos = phvBus[1]["data"]
        self.entityName = baseName
        self.tmplFolder = templateFolder
        self.tmplFile = path.join(templateFolder, "deparser.vhdl")
        self.libDir = path.join(outputDir, libDirName)
        if not path.exists(self.libDir):
            mkdir(self.libDir)
        self.signals = {}
        self.entities = {}
        self.stateMachines = {}
        self.components = {}
        self.muxes = {}
        self.__getlibrary()
        self.dictSub = {'name': baseName,
                        'code': "",
                        'payloadSize': deparser.busSize,
                        'outputSize': deparser.busSize,
                        'nbMuxes': deparser.nbStateMachine}

    def _setSignalStr(self):
        strSignal = ""
        sigTmpl = Template("signal $n : ${t}; \n")
        for n, t in self.signals.items():
            strSignal += sigTmpl.substitute({"n": n, "t": t})
        self.dictSub["signals"] = strSignal

    def __str__(self):
        self.genInputs()
        self._setSignalStr()
        self._setEntitiesImplCode()
        self._setComponentsCode()
        self._setMuxesConnectionCode()
        with open(self.tmplFile, 'r') as myfile:
            tmpl = Template(myfile.read())
        return tmpl.safe_substitute(self.dictSub)

    def _setComponentsCode(self):
        code = ""
        for n, d in self.components.items():
            if n not in self.lib:
                raise NameError("component {} does not exist "
                                "in library".format(n))
            if d is False:
                with open(self.lib[n][1], 'r') as f:
                    code += f.read()
            else:
                with open(self.lib[n][1], 'r') as f:
                    tmpl = Template(f.read())
                for n, dic in d.items():
                    code += tmpl.safe_substitute(dic)
        self.dictSub["components"] = code

    def _setEntitiesImplCode(self):
        """ Gen implementation for a component
        Component : component name
        tmplDict : template dictionnary
        Require a <component>_place.vhdl file in <component> dir
        """
        implCode = ""
        for c, d in self.entities.values():
            if c not in self.lib:
                raise NameError("component {} does not exist "
                                "in library".format(c))
            with open(self.lib[c][2], 'r') as f:
                tData = Template(f.read())
            implCode += tData.safe_substitute(d)
        self.dictSub["entities"] = implCode

    def writeTB(self, fileName):
        Tmpl = {"compVersion": VERSION,
                "name": self.entityName,
                "payloadSize": self.dictSub["payloadSize"],
                "outputSize": self.dictSub["outputSize"],
                "phvBus": self.dictSub["phvBus"],
                "phvValidity": self.dictSub["phvValidity"],
                "phvBusWidth": self.dictSub["phvBusWidth"],
                "phvValidityWidth": self.dictSub["phvValidityWidth"]}
        phvBus = ""
        phvBusIn = ""
        phvBusTmpl = "phvBus({} downto {}) <= {}_bus;\n"
        phvInTmpl = "{}_bus : in std_logic_vector({} downto 0);\n"
        for name, pos in self.headerBus.items():
            phvBusIn += phvInTmpl.format(name, pos[1] - pos[0])
            phvBus += phvBusTmpl.format(pos[1], pos[0], name)
        vBus = ""
        vBusIn = ""
        for name, pos in self.busValidAssocPos.items():
            vBusIn += "{}_valid : in std_logic;\n".format(name)
            vBus += "validityBus({}) <= {}_valid;\n".format(pos, name)
        Tmpl["setPhvBus"] = phvBus
        Tmpl["setValBus"] = vBus
        Tmpl["headerBuses"] = phvBusIn
        Tmpl["validityBits"] = vBusIn
        with open(path.join(self.tmplFolder, "deparser_tb.vhdl")) as inFile:
            TB = Template(inFile.read())
        with open(fileName, 'w') as outFile:
            outFile.write(TB.substitute(Tmpl))

    def writeFiles(self, mainFileName):
        """ export all files.
        mainFile‌ + lib files in libFolder
        """
        for name, d in self.components.items():
            tF = self.lib[name][0]
            if d is False:
                oF = path.join(self.libDir,
                               "{}.vhdl".format(name))  # output lib file
                copyfile(tF, oF)
            else:
                with open(tF, 'r') as tmpl:
                    t = Template(tmpl.read())
                for n, dic in d.items():
                    oF = path.join(self.libDir,
                                   "{}.vhdl".format(n))  # output lib file
                    with open(oF, 'w') as outFile:
                        outFile.write(t.substitute(dic))
        with open(mainFileName, 'w') as outFile:
            outFile.write(str(self))

    def genInputs(self):
        # value assignments
        self.dictSub["phvBus"] = self.phvBus[0]["name"]
        self.dictSub["phvValidity"] = self.getValidBusName()
        self.dictSub["phvBusWidth"] = self.phvBus[0]["width"] - 1
        self.dictSub["phvValidityWidth"] = self.getNbHeaders() - 1

    def getValidBusName(self):
        return self.phvBus[1]["name"]

    def getNbHeaders(self):
        return self.phvBus[1]["width"]

    def appendCode(self, code):
        oldCode = self.dictSub["code"]
        if code in oldCode:
            warn("append code already here : \n"
                 "oldCode : {}\n newCode : {}"
                 "\n".format(oldCode, code))
        oldCode += code
        self.dictSub["code"] = oldCode

    def _addVector(self, name, size):
        self._addSignal(name,
                        "std_logic_vector({} downto 0)".format(size - 1))

    def _addLogic(self, name):
        self._addSignal(name, "std_logic")

    def _addSignal(self, name, t):
        """ name : signal name
        t signal Type
        """
        if name in self.signals:
            raise NameError("signal {} already exist".format(name))
        self.signals[name] = t

    def _addEntity(self, name, tmplDict):
        """Add entity name with template file template
        and tmplDict
        error if name exists
        """
        if name in self.entities:
            raise NameError("entity {} already exist".format(name))
        self.entities[name] = tmplDict

    def getEntity(self, name):
        if name in self.entities:
            return self.entities[name]
        else:
            raise NameError("entity {} does not exist".format(name))

    def _setMuxesConnectionCode(self):
        def getMuxConnectStr(muxNum):
            """ Generate the code to connect a Mux
            """
            code = ""
            _, connections = self.muxes[muxNum]
            entity = self._getMuxEntity(muxNum)
            strTmpl = Template("${dst}(${dMSB} downto ${dLSB}) <= "
                               "${src}(${sMSB} downto ${sLSB});\n")
            dictTmpl = {"dst": entity["input"]}
            width = entity["width"]
            for src, dst in connections.values():
                dictTmpl["dMSB"] = int((dst+1)*width - 1)
                dictTmpl["dLSB"] = int(dst * width)
                dictTmpl["sMSB"] = int(src[1] + width - 1)
                dictTmpl["sLSB"] = int(src[1])
                dictTmpl["src"] = src[0]
                code += strTmpl.substitute(dictTmpl)
            return code

        allMuxStr = ""
        for n in self.muxes:
            allMuxStr += getMuxConnectStr(n)
        self.dictSub["muxes"] = allMuxStr

    def genMuxes(self):
        for i in range(self.dep.nbStateMachine):
            self._genMux(i)
            self._genStateMachine(i)

    def _getStMCompTmpl(self, num, name):
        """Gen template for a state machine
        """
        graph = self.dep.getStateMachine(num)
        stateList = {}
        for u, v, d in graph.edges(data=True):
            if u not in stateList:
                stateList[u] = []
            stateList[u].append((v, d))

        def genStateTransitionCode(listTransition):
            def getStateTransition(name, cond):
                busAssoc = self.busValidAssocPos
                transitionTmpl = "NEXT_STATE <= {}; \n"
                condTmpl = "if headerValid({}) = '1' then \n {} end if;\n"
                tmp = transitionTmpl.format(name)
                if "label" in cond:
                    tmp = condTmpl.format(busAssoc[cond["label"]],
                                          tmp)
                return tmp
            transitionCode = ""
            for n, d in listTransition:
                transitionCode += getStateTransition(n, d)
            return transitionCode

        tmplDict = {"compVersion": VERSION,
                    "name": name,
                    "initState": self.dep.init,
                    "lastState": self.dep.last,
                    "stateList": "({})".format(", "
                                               .join(list(graph.nodes))),
                    "initStateTransition":
                    genStateTransitionCode(stateList.pop(self.dep.init))}
        otherStateTransition = ""
        assocMuxIn = self.muxes[num][1]  # get ctrl val to assign for a state
        for k, struct in stateList.items():
            otherStateTransition += "when {} =>\n".format(k)
            stateMuxConv = vhdl_util.int2vector(assocMuxIn[k][1],
                                                "outputWidth")
            otherStateTransition += "output_reg <= {} ;\n".format(stateMuxConv)
            otherStateTransition += genStateTransitionCode(struct)
        tmplDict["otherStateTransition"] = otherStateTransition
        return tmplDict

    def _getStateMachineEntity(self, num):
        compName = "state_machine_{}".format(num)
        name = "stM_{}".format(num)
        nbInput = self.getNbHeaders()
        outWidth = self._getMuxEntity(num)["wControl"]
        output = self._getMuxEntity(num)["control"]
        if "state_machine" not in self.components:
            self.components["state_machine"] = {}
        if name not in self.entities:
            stComp = self.components["state_machine"]
            if compName not in stComp:
                stComp[compName] = self._getStMCompTmpl(num, compName)
            tmplDict = {"name": name,
                        "componentName": compName,
                        "nbHeader": nbInput,
                        "wControl": outWidth,
                        "clk": self.clkName,
                        "reset_n": self.rstName,
                        "start": "start_deparser",
                        "ready": "deparser_rdy_i({})".format(num),
                        "finish": "endDeparser({})".format(num),
                        "headersValid": self.getValidBusName(),
                        "output": output}
            self._addEntity(name, ("state_machine", tmplDict))
        return self.getEntity(name)[1]

    def _genStateMachine(self, num):
        if num not in self.stateMachines:
            entity = self._getStateMachineEntity(num)
            self.stateMachines[num] = (entity["name"],)
        else:
            warn("trying to regenerate stateMachine {}".format(num))

    def _getMuxEntity(self, muxNum):
        """Function to get a mux entity name with
        nbIn as nb input and width as output size
        The mux name is generated such as being unique for
        a certain type of mux.
        if mux does not exist, add it to entities dictionnary
        """
        graph = self.dep.getStateMachine(muxNum)
        nbInput = len(graph)-2
        outWidth = 8
        muxName = "mux_{}".format(muxNum)
        outputName = "muxes_o({})".format(muxNum)
        inputName = "muxes_{}_in".format(muxNum)
        controlName = "muxes_{}_ctrl".format(muxNum)
        if muxName not in self.entities:
            if "mux" not in self.components:
                self.components["mux"] = False

            dictMux = {"name": muxName,
                       "nbInput": nbInput,
                       "wControl": vhdl_util.getLog2In(nbInput),
                       "clk": self.clkName,
                       "width": outWidth,
                       "input": inputName,
                       "wInput": int(nbInput * outWidth),
                       "output": outputName,
                       "control": controlName}
            self._addEntity(muxName, ("mux", dictMux))
        return self.getEntity(muxName)[1]

    def _genMux(self, muxNum):
        """ Mux is tuple : entityName, stateMachine assignments)
        """
        def genConnections(num):
            """ Connection :
            Dictionnary key =  graph node name
            value : tuple(src, dst)
            src: tuple(signalName, start)
            dst: mux input number
            """
            connections = {}
            graph = self.dep.getStateMachine(num)
            i = 0
            for n, d in graph.nodes(data=True):
                if d != {}:
                    signalName = self.phvBus[0]["name"]
                    startPos = d["pos"][0] + self.headerBus[d["header"]][0]
                    connections[n] = ((signalName, startPos), i)
                    i += 1
            return connections

        if muxNum not in self.muxes:
            entity = self._getMuxEntity(muxNum)
            self._addVector(entity["control"], entity["wControl"])
            self._addVector(entity["input"], entity["wInput"])
            connections = genConnections(muxNum)
            self.muxes[muxNum] = (entity["name"], connections)
        else:
            warn("Trying to regenerate mux {}".format(muxNum))


def _validateInputs(funcIn):
    """ funcIn : list of three tuples :
    (Type got, variable Name, expected type)
    """
    val = True
    # validate input
    for g, n, e in funcIn:
        if g != e:
            print(Fore.YELLOW + "Wrong {} type got {}"
                  ", expected {} {}".format(n, g, e,
                                            Style.RESET_ALL))
            val = False
    return val


def exportDeparserToVHDL(deparser, outputFolder, phvBus, baseName="deparser"):
    """ This function export to VHDL a deparserStateMachines
    If stateMachines are not of type deparserStateMachines exit
    """
    toValidate = [(type(outputFolder), "outputFolder", str),
                  (type(baseName), "baseName", str)]
    if not _validateInputs(toValidate):
        return
    if not path.exists(outputFolder):
        mkdir(outputFolder)

    outputFiles = path.join(outputFolder, baseName + ".vhdl")
    output_tb = path.join(outputFolder, "{}_tb.vhdl".format(baseName))
    vhdlGen = deparserHDL(deparser, outputFolder, 'library', phvBus, baseName)
    vhdlGen.genMuxes()
    vhdlGen.writeFiles(outputFiles)
    vhdlGen.writeTB(output_tb)
