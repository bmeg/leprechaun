# ophion

Language for making graph queries from data

![OPHION](https://github.com/bmeg/ophion/blob/master/resources/public/img/ophion.png)

## usage

Ophion queries are an array of graph operations. Each element of this array is itself an array, with the first element being the name of the operation and the rest of the elements parameters to this operation.

### example

Here is an example query that starts from Individual vertexes from BRCA and traverses to all associated Variants called from MUTECT, and returns every Individual/Variant pair:

    [["where",{"disease_code":"BRCA"}],
     ["mark","individual"],
     ["from","sampleOf","Biosample"],
     ["from","callSetOf","CallSet"],
     ["where",{"method":"MUTECT"}],
     ["fromUnique","variantCall","Variant"],
     ["mark","variant"],
     ["select",["individual","variant"]]]

This is the actual json payload. You can deliver this through any http method you wish to use. Here is an example query through curl that gets all Biosamples for a given Individual:

    curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '[["mark","individual"],["from","sampleOf","Biosample"],["mark","biosample"],["select",["individual","biosample"]]]' \
    http://10.96.11.144/query/Individual

If you notice, the starting vertex label is in the url, while the query is posted as json.

## operations

The operations currently supported are:

### traversals

Traversal operations help you navigate the graph:

* from
* to
* fromEdge
* toEdge
* fromVertex
* toVertex
* fromUnique
* toUnique

### control

Mark and select work together to keep track of state during traversals:

* mark
* select

### filters

Filter operations help you cull or craft the results:

* where
* dedup
* limit
* order
* offset
* match
* values

### aggregates

Aggregate operations assemble metrics from a set of results:

* count
* gather
* aggregate
* groupCount

Each of these operations is explained in more detail below.

## traversals

The two main traversal operations are `from` and `to`. Because Ophion works with directed graphs, there is a distinction between traversing across an edge in either direction. Either requires two additional pieces of information, an edge label and the ultimate destination label.

One upshot of this is that in order to craft traversals, you need to know the schema of the graph you are querying. The raw schema is defined in a `protograph` file, for BMEG the [protograph file is here](https://github.com/biostream/bmeg-etl/blob/master/bmeg.protograph.yaml). This will show you all vertex labels and all edges they have to other labels.

If you want a visual representation then you can use the [BMEG website code](https://github.com/bmeg/bmeg) to generate a schema in cytoscape. Here is the current BMEG schema as an example:

![SCHEMA](https://github.com/bmeg/ophion/blob/master/resources/public/bmeg-schema-march-2018.png)

Either way, once you have your schema you know a few key things:

* vertex labels
* edge labels
* edge directions

These are the things you need to know to successfully traverse the graph.

### to

The `to` operation travels across outgoing edges. It requires two pieces of information: the edge label, and the destination label:

    ["to", $edgeLabel, $destinationLabel]

As an example say we are on a Variant vertex and want to see what Gene the Variant is in. The query would look like this:

    ["to", "variantIn", "Gene"]

### from

The `from` operation is the same as `to` but going in the other direction. To demonstrate this, let's reverse the previous query and find every Variant that is in a given Gene (assuming we are already on a Gene vertex):

    ["from", "variantIn", "Variant"]

### toUnique/fromUnique

Say you are going from Variants to Genes. Every Gene has many associated Variants, so if you go this direction you will end up with a lot of the same Genes in your traversal. Sometimes this is what you want, but sometimes you don't care where they came from, you just want to know which Genes were implicated in your given set of Variants.

The `toUnique` and `fromUnique` operations work exactly the same as their non-unique counterparts, but the outcome will merge all identical vertexes.

### toEdge/fromEdge, toVertex/fromVertex

The *Edge and *Vertex traversals are for navigating to and from the actual edge records between vertexes.