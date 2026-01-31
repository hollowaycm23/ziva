
import networkx as nx
import os
import json
import logging

class GraphStore:
    """
    Local Graph Store using NetworkX.
    Persists graph to a GML or JSON file.
    """
    
    def __init__(self, storage_path="knowledge_graph.gml"):
        self.storage_path = storage_path
        self.graph = nx.MultiDiGraph() # Directed graph with possible multiple edges
        self._load_graph()

    def _load_graph(self):
        if os.path.exists(self.storage_path):
            try:
                self.graph = nx.read_gml(self.storage_path)
                logging.info(f"Loaded Knowledge Graph with {self.graph.number_of_nodes()} nodes.")
            except Exception as e:
                logging.error(f"Failed to load graph: {e}. Starting fresh.")
                self.graph = nx.MultiDiGraph()
        else:
            self.graph = nx.MultiDiGraph()

    def save_graph(self):
        try:
            # GML doesn't support None values easily, ensure data is string/int
            nx.write_gml(self.graph, self.storage_path)
        except Exception as e:
            logging.error(f"Failed to save graph: {e}")

    def add_triplet(self, subject: str, predicate: str, object_: str, source_id: str = None):
        """
        Adds a relationship: (Subject) --[Predicate]--> (Object)
        """
        # Normalize keys
        subj = subject.strip()
        obj = object_.strip()
        pred = predicate.strip()
        
        if not subj or not obj or not pred:
            return

        self.graph.add_node(subj, label=subj)
        self.graph.add_node(obj, label=obj)
        
        # Add edge with metadata
        self.graph.add_edge(subj, obj, relation=pred, source=source_id)
        
        # Save occasionally or handle externally? For prototype, save immediately for safety
        self.save_graph()

    def get_related_concepts(self, entity: str, depth=1) -> list[str]:
        """
        Returns text descriptions of related concepts up to 'depth' hops.
        Format: "Entity --relation--> Neighbor"
        """
        if entity not in self.graph:
            return []

        concepts = []
        
        # 1-Hop Neighbors
        # Outgoing
        for neighbor in self.graph.neighbors(entity):
             edges = self.graph.get_edge_data(entity, neighbor)
             for _, data in edges.items():
                 relation = data.get("relation", "related_to")
                 concepts.append(f"{entity} {relation} {neighbor}")
        
        # Incoming
        for predecessor in self.graph.predecessors(entity):
             edges = self.graph.get_edge_data(predecessor, entity)
             for _, data in edges.items():
                 relation = data.get("relation", "related_to")
                 concepts.append(f"{predecessor} {relation} {entity}")

        return concepts[:10] # Limit to avoid context explosion

    def get_stats(self):
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges()
        }
