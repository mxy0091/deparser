import json
from collections import OrderedDict
from GraphGen import deparserGraph, parserGraph


class jsonP4Parser(object):
    def __init__(self, jsonFile):
        with open(jsonFile, 'r') as f:
            self.graph = json.load(f)
        self._header_types = False
        self._headers = False
        self.Gd = None
        self.Gp = None
        self._deparserTuples = False
        self._parserTuples = False
        self.graphInit = self.graph["parsers"][0]["init_state"]

    def getHeaders(self):
        if not self._headers:
            self._genHeaderList()
        return self._headers

    def getDeparserComb(self, opt=False):
        if opt:
            return self.getOptimizeDeparserTuples()
        return self.getDeparserTuples()

    def getOptimizeDeparserTuples(self):
        tuples = self.getParserTuples()
        return tuples

    def getDeparserTuples(self):
        if not self._deparserTuples:
            self._genDeparserTuples()
        return self._deparserTuples

    def getParserTuples(self):
        if self.Gp is None:
            self.genParserGraph()
        return self.Gp.getAllHeaderPath()

    def getHeaderTypes(self):
        if not self._header_types:
            self._genHeaderTypes()
        return self._header_types

    def _genHeaderTypes(self):
        self._header_types = {}
        for i in self.graph["header_types"]:
            h_len = 0
            for j in i['fields']:
                h_len += j[1]
            self._header_types[i['name']] = h_len

    def _genHeaderList(self):
        self._headers = OrderedDict()
        header_types = self.getHeaderTypes()
        for i in self.graph["headers"]:
            self._headers[i['name']] = header_types[i['header_type']]

    def getDeparserHeaderList(self):
        """ Generate ordered dict of all
        deparser headers.
        """
        headers = OrderedDict()
        for i in self._getDeparserProtocols():
            headers[i] = self.getHeaders()[i]
        return headers

    def _getDeparserProtocols(self):
        return self.graph['deparsers'][0]['order']

    def extract_states(self, stateList, state):
        """ Extract active states
        """
        stateTuple = []
        curState = stateList[state]
        ActivatedProtocolList = []
        for i in curState[0]:
            if i['op'] == 'extract':
                for j in i['parameters']:
                    ActivatedProtocolList.append(j['value'])
        stateTuple.append(tuple(ActivatedProtocolList))
        for i in curState[1]:
            curList = []
            if i['next_state'] is not None:
                curList.extend(self.extract_states(stateList, i['next_state']))
            for j in curList:
                tmp = ActivatedProtocolList.copy()
                tmp.extend(j)
                stateTuple.append(tuple(tmp))
        return stateTuple

    def getParserGraph(self):
        if self.Gp is None:
            self.genParserGraph()
        return self.Gp

    def genParserGraph(self):
        parser = self.graph["parsers"][0]
        self.Gp = parserGraph(self.getHeaders(), self.graphInit)
        GpTmp = self.Gp
        lastState = GpTmp.lastState
        GpTmp.add_state_assoc_graph(lastState, [lastState])
        for i in parser["parse_states"]:
            tmp = []
            # gen list of extracted headers
            for e in i["parser_ops"]:
                if e["op"] == "extract":
                    tmp.append(e["parameters"][0]["value"])
            GpTmp.add_state_assoc_graph(i["name"], tmp)
            # associate next states
            for j in i["transitions"]:
                if j["next_state"] is None:
                    GpTmp.append_edge(i["name"], lastState)
                else:
                    GpTmp.append_edge(i["name"], j["next_state"])

    def _genDeparserTuples(self):
        """
        Gen all possible Deparser Tuples
        This list contains all possibilities
        """
        self._deparserTuples = []
        self.Gd = deparserGraph(self.graphInit, self.getDeparserHeaderList())
        self._deparserTuples = self.Gd.getAllPathClosed()
