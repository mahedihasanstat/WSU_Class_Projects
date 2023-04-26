from py2neo import Graph
import pandas as pd

import matplotlib 
import matplotlib.pyplot as plt

plt.style.use('fivethirtyeight')
pd.set_option('display.float_format', lambda x: '%.3f' % x)
pd.set_option('display.max_colwidth', 100)

#data preprocessing
#remove duplicates
display(graph.run("CREATE CONSTRAINT ON (a:Article) ASSERT a.index IS UNIQUE").stats())
display(graph.run("CREATE CONSTRAINT ON (a:Author) ASSERT a.name IS UNIQUE").stats())
display(graph.run("CREATE CONSTRAINT ON (v:Venue) ASSERT v.name IS UNIQUE").stats())

#load data 
query = """
CALL apoc.periodic.iterate(
  'UNWIND ["dblp-ref-0.json", "dblp-ref-1.json", "dblp-ref-2.json", "dblp-ref-3.json"] AS file
   CALL apoc.load.json("https://github.com/neo4j-contrib/training-v3/raw/master/modules/gds-data-science/supplemental/data/" + file)
   YIELD value WITH value
   return value',
  'MERGE (a:Article {index:value.id})
   SET a += apoc.map.clean(value,["id","authors","references", "venue"],[0])
   WITH a, value.authors as authors, value.references AS citations, value.venue AS venue
   MERGE (v:Venue {name: venue})
   MERGE (a)-[:VENUE]->(v)
   FOREACH(author in authors | 
     MERGE (b:Author{name:author})
     MERGE (a)-[:AUTHOR]->(b))
   FOREACH(citation in citations | 
     MERGE (cited:Article {index:citation})
     MERGE (a)-[:CITED]->(cited))', 
   {batchSize: 1000, iterateList: true});
"""
graph.run(query).to_data_frame()

# removing article with no title
query = """
MATCH (a:Article) WHERE not(exists(a.title))
DETACH DELETE a
"""
graph.run(query).stats()

#EDA:
#overall represntation
graph.run("CALL db.schema.visualization()").data()

#nodes of each label
result = {"label": [], "count": []}
for label in graph.run("CALL db.labels()").to_series():
    query = f"MATCH (:`{label}`) RETURN count(*) as count"
    count = graph.run(query).to_data_frame().iloc[0]['count']
    result["label"].append(label)
    result["count"].append(count)
nodes_df = pd.DataFrame(data=result)
nodes_df.sort_values("count")

 #plot
nodes_df.plot(kind='bar', x='label', y='count', legend=None, title="Node Cardinalities")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

#relation type in graph
result = {"relType": [], "count": []}
for relationship_type in graph.run("CALL db.relationshipTypes()").to_series():
    query = f"MATCH ()-[:`{relationship_type}`]->() RETURN count(*) as count"
    count = graph.run(query).to_data_frame().iloc[0]['count']
    result["relType"].append(relationship_type)
    result["count"].append(count)
rels_df = pd.DataFrame(data=result)
rels_df.sort_values("count")

#plot
rels_df.plot(kind='bar', x='relType', y='count', legend=None, title="Relationship Cardinalities")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


#citation network
exploratory_query = """
MATCH (author:Author)<-[:AUTHOR]-(article:Article)-[:VENUE]->(venue)
RETURN article.title AS article, author.name AS author, venue.name AS venue, 
       size((article)-[:CITED]->()) AS citationsGiven, size((article)<-[:CITED]-()) AS citationsReceived
ORDER BY rand()
LIMIT 25
"""

graph.run(exploratory_query).to_data_frame()


# citation given for article
query = """
MATCH (a:Article)
RETURN size((a)<-[:CITED]-()) AS citations
"""

citation_df = graph.run(query).to_data_frame()
citation_df.describe([.25, .5, .75, .9, .99])

#plot
fig1, ax1 = plt.subplots()
ax1.hist(pd.Series(citation_df['citations'].dropna()), 1250, density=True, facecolor='g', alpha=0.75)
ax1.set_xscale("log")
plt.tight_layout()
plt.show()


# citation received for article
query = """
MATCH (a:Article)
RETURN size((a)-[:CITED]->()) AS cited
"""

cited_df = graph.run(query).to_data_frame()
cited_df.describe([.25, .5, .75, .9, .99])

#plot
fig1, ax1 = plt.subplots()
ax1.hist(pd.Series(cited_df['cited'].dropna()), 50, density=True, facecolor='g', alpha=0.75)
plt.tight_layout()
plt.show()


#published by authors
query = """
MATCH (a:Author)
RETURN size((a)<-[:AUTHOR]-()) AS published
"""

published_df = graph.run(query).to_data_frame()
published_df.describe([.25, .5, .75, .9, .99])
