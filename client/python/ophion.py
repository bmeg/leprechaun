
import sys
import json
import requests
import traceback

from functools import reduce


class Ophion:
    """
    Examples
    --------
    -- find samples with a mutation in BRAF:
        O.query().match([
            O.mark("gene").has("symbol", "BRAF"),
            O.mark("gene").incoming("variantInGene")
                .outgoing("variantInBiosample").mark("sample")
            ]).select(["gene", "sample"])

    -- (sample, expression) matrix:
        O.query().has("gid", "cohort:CCLE")
        .outgoing("hasSample").mark("sample").incoming("expressionForSample")
        .mark("expression").select(["sample", "expression"]).count().execute()

    -- (sample, drug-response) matrix:
        O.query().has("gid", "cohort:CCLE")
        .outgoing("hasSample").mark("sample").outEdge("responseToCompound")
        .mark("response").select(["sample", "response"]).count().execute()

    -- find all (sample, expression, response) triplets for the CCLE cohort:
        O.query().has("gid", "cohort:CCLE").outgoing("hasSample").match([
            O.mark("sample").incoming("expressionForSample")
                .values(['serializedExpresion']).mark("expression"),
            O.mark("sample").outEdge("responseToCompound").mark("response")
            ]).select(["sample", "expression", "response"]).limit(1)
    """

    def __init__(self, host):
        self.host = host
        self.url = host + "/vertex/query"

    # entry point
    def query(self):
        return OphionQuery(self)

    # conditions
    def eq(self, v):
        return {'eq': v}

    def neq(self, v):
        return {'neq': v}

    def gt(self, v):
        return {'gt': v}

    def gte(self, v):
        return {'gte': v}

    def lt(self, v):
        return {'lt': v}

    def lte(self, v):
        return {'lte': v}

    def between(self, lower, upper):
        return {'between': {'lower': lower, 'upper': upper}}

    def inside(self, lower, upper):
        return {'inside': {'lower': lower, 'upper': upper}}

    def outside(self, lower, upper):
        return {'outside': {'lower': lower, 'upper': upper}}

    def within(self, values):
        return {'within': values}
        # return {'within': {'values': values}}

    def without(self, values):
        return {'without': values}
        # return {'without': {'values': values}}

    # for match subqueries
    def mark(self, label):
        return self.query().mark(label)

    # remote calls
    def vertex(self, gid):
        url = self.host + "/vertex/find/" + gid
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        return requests.post(url, headers=headers).json()

    def execute(self, query):
        def loadJson(s):
            if len(s) > 0:
                return s.json()
            else:
                return {}

        try:
            payload = query.render()
            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}
            resp = requests.post(self.url,
                                 data=payload, headers=headers)

            return resp.text.rstrip().split("\n")

        except Exception as e:
            traceback.print_exc()
            return {
                'error': {
                    'system': sys.exc_info()[0],
                    'exception': e
                }
            }

def wrapValue(value):
    v = value
    if isinstance(value, int):
        v = {'n': value}
    elif isinstance(value, float):
        v = {'r': value}
    elif isinstance(value, str):
        v = {'s': value}
    elif isinstance(value, list):
        v = list(map(wrapValue, value))
    elif isinstance(value, dict):
        v = {k: wrapValue(v) for k, v in value.items()}
    return v

class OphionQuery:
    def __init__(self, parent=None):
        self.query = []
        self.parent = parent

    # traversals
    def incoming(self, *args):
        if len(args) == 0:
            self.query.append({'in': []})
        elif len(args) == 1:
            labels = args[0]
            if not isinstance(labels, list):
                labels = [labels]
            self.query.append({'in': {'labels': labels}})
        return self

    def outgoing(self, *args):
        if len(args) == 0:
            self.query.append({'out': []})
        elif len(args) == 1:
            labels = args[0]
            if not isinstance(labels, list):
                labels = [labels]
            self.query.append({'out': {'labels': labels}})
        return self

    def inEdge(self, *args):
        if len(args) == 0:
            self.query.append({'inEdge': []})
        elif len(args) == 1:
            labels = args[0]
            if not isinstance(labels, list):
                labels = [labels]
            self.query.append({'inEdge': {'labels': labels}})
        return self

    def outEdge(self, *args):
        if len(args) == 0:
            self.query.append({'outEdge': []})
        elif len(args) == 1:
            labels = args[0]
            if not isinstance(labels, list):
                labels = [labels]
            self.query.append({'outEdge': {'labels': labels}})
        return self

    def inVertex(self):
        self.query.append({'inVertex': True})
        return self

    def outVertex(self):
        self.query.append({'outVertex': True})
        return self

    # traversal manipulation
    def mark(self, label):
        if not isinstance(label, list):
            label = [label]
        self.query.append({'as': {'labels': label}})
        return self

    def select(self, labels):
        if not isinstance(labels, list):
            labels = [labels]
        self.query.append({'select' : {'labels': labels}})
        return self

    def by(self, label):
        self.query.append({'by': {'key': label}})
        return self

    def label(self, *args):
        # if len(args) == 0:
        #     self.query.append({'label': })
        # if not isinstance(labels, list):
        #     labels = [labels]
        # self.query.append({'label': {'labels': labels}})
        self.query.append({'label': {}})
        return self

    def values(self, labels):
        if not isinstance(labels, list):
            labels = [labels]
        self.query.append({'values': {'labels': labels}})
        return self

    def limit(self, l):
        self.query.append({'limit': l})
        return self

    def order(self, o, asc):
        self.query.append({'order': {'key': o, 'ascending': asc}})
        return self

    def range(self, begin, end):
        self.query.append({'range': {'lower': begin, 'upper': end}})
        return self

    def count(self):
        self.query.append({'count': True})
        return self

    def dedup(self):
        self.query.append({'dedup': []})
        return self

    def path(self):
        self.query.append({'path': True})
        return self

    def aggregate(self, label):
        self.query.append({'aggregate': label})
        return self

    def group(self, bys):
        self.query.append({'group': {'bys': map(lambda by: {'key': by})}})
        return self

    def groupCount(self, *args):
        if len(args) == 0:
            self.query.append({'groupCount': {}})
        else:
            label = args[0]
            self.query.append({'groupCount': {'key': label}})
        return self

    def satisfies(self, condition):
        self.query.append({'is': wrapValue(condition)})
        return self

    def has(self, key, *args):
        outer = {'key': key}
        if len(args) > 0:
            value = args[0]
            v = wrapValue(value)
            outer = {'key': key}
            if isinstance(value, dict):
                outer['condition'] = v
                # elif: isinstance(value, OphionQuery);
            else:
                outer['value'] = v
        self.query.append({'has': outer})
        return self

    def hasNot(self, key):
        self.query.append({'hasNot': key})
        return self

    def match(self, queries):
        self.query.append({'match': {'queries': queries}})
        return self

    def searchArgs(self, args):
        out = {}

        if len(args) > 1:
            out['term'] = args[0]
            out['search'] = args[1]
        else:
            out['search'] = args[0]

        return out

    def searchVertex(self, *args):
        opts = self.searchArgs(args)
        self.query.append({'searchVertex': opts})
        return self

    def searchEdge(self, *args):
        opts = self.searchArgs(args)
        self.query.append({'searchEdge': opts})
        return self

    # output
    def render(self):
        # output = {'query': self.query}
        def subsubrender(step):
            if isinstance(step, list) or isinstance(step, dict):
                if 'queries' in step:
                    return {'queries': [v.query for v in step['queries']]}
                else:
                    return step
            else:
                return step

        def subrender(step):
            return {k: subsubrender(v) for k, v in step.items()}

        outquery = [subrender(q) for q in self.query]
        return json.dumps(outquery)


    def execute(self):
        return self.parent.execute(self)

