"""
MindWeave - AI-Powered Thought Network System
A machine learning-based knowledge graph that builds semantic connections between ideas
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import networkx as nx
from datetime import datetime
import json
import re
from collections import defaultdict

class ThoughtNode:
    """Represents a single thought/idea in the network"""
    
    def __init__(self, content, tags=None):
        self.id = datetime.now().timestamp()
        self.content = content
        self.timestamp = datetime.now()
        self.tags = tags or self._extract_tags(content)
        self.embedding = None
        self.connections = []
        
    def _extract_tags(self, text):
        """Extract hashtags from text"""
        return re.findall(r'#(\w+)', text)
    
    def __repr__(self):
        return f"ThoughtNode(id={self.id}, content='{self.content[:50]}...')"


class MindWeave:
    """
    Main MindWeave system for building and analyzing thought networks
    Uses ML techniques for semantic similarity and clustering
    """
    
    def __init__(self, similarity_threshold=0.3):
        self.thoughts = []
        self.graph = nx.Graph()
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.similarity_threshold = similarity_threshold
        self.embeddings = None
        
    def add_thought(self, content, tags=None):
        """Add a new thought to the network"""
        thought = ThoughtNode(content, tags)
        self.thoughts.append(thought)
        self.graph.add_node(thought.id, 
                           content=content, 
                           tags=thought.tags,
                           timestamp=thought.timestamp)
        
        # Analyze connections with existing thoughts
        if len(self.thoughts) > 1:
            self._analyze_connections(thought)
        
        print(f"✓ Added thought: '{content[:60]}...'")
        return thought
    
    def _analyze_connections(self, new_thought):
        """Find semantic connections between new thought and existing ones"""
        # Recompute embeddings with new thought
        corpus = [t.content for t in self.thoughts]
        self.embeddings = self.vectorizer.fit_transform(corpus)
        
        # Get similarity scores for new thought
        new_idx = len(self.thoughts) - 1
        new_embedding = self.embeddings[new_idx]
        similarities = cosine_similarity(new_embedding, self.embeddings)[0]
        
        # Create connections for similar thoughts
        for idx, similarity in enumerate(similarities):
            if idx != new_idx and similarity > self.similarity_threshold:
                other_thought = self.thoughts[idx]
                
                # Add edge to graph
                self.graph.add_edge(
                    new_thought.id,
                    other_thought.id,
                    weight=float(similarity),
                    reason=self._generate_connection_reason(new_thought, other_thought)
                )
                
                print(f"  → Connected to: '{other_thought.content[:50]}...' "
                      f"(similarity: {similarity:.3f})")
    
    def _generate_connection_reason(self, thought1, thought2):
        """Generate explanation for why two thoughts are connected"""
        common_tags = set(thought1.tags) & set(thought2.tags)
        if common_tags:
            return f"Shared tags: {', '.join(common_tags)}"
        
        # Extract common important words
        words1 = set(thought1.content.lower().split())
        words2 = set(thought2.content.lower().split())
        common_words = (words1 & words2) - {'the', 'a', 'an', 'and', 'or', 'but'}
        
        if common_words:
            return f"Related concepts: {', '.join(list(common_words)[:3])}"
        
        return "Semantic similarity"
    
    def find_related_thoughts(self, query, top_k=5):
        """Find thoughts most related to a query"""
        if not self.thoughts:
            return []
        
        # Transform query using existing vectorizer
        query_embedding = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k most similar
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    'thought': self.thoughts[idx],
                    'similarity': similarities[idx]
                })
        
        return results
    
    def discover_clusters(self, min_samples=2):
        """Use DBSCAN to discover thematic clusters in thoughts"""
        if len(self.thoughts) < min_samples:
            return {}
        
        # Use embeddings for clustering
        clustering = DBSCAN(
            eps=0.5,
            min_samples=min_samples,
            metric='cosine'
        ).fit(self.embeddings.toarray())
        
        # Group thoughts by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # -1 is noise
                clusters[f"Cluster {label}"].append(self.thoughts[idx])
        
        return dict(clusters)
    
    def get_thought_neighborhood(self, thought_id, depth=1):
        """Get connected thoughts within depth hops"""
        if thought_id not in self.graph:
            return []
        
        neighbors = []
        for node in nx.single_source_shortest_path_length(
            self.graph, thought_id, cutoff=depth
        ):
            if node != thought_id:
                thought = next(t for t in self.thoughts if t.id == node)
                edge_data = self.graph.get_edge_data(thought_id, node)
                neighbors.append({
                    'thought': thought,
                    'distance': nx.shortest_path_length(self.graph, thought_id, node),
                    'connection_strength': edge_data.get('weight', 0) if edge_data else 0
                })
        
        return sorted(neighbors, key=lambda x: x['connection_strength'], reverse=True)
    
    def get_network_stats(self):
        """Get statistics about the thought network"""
        return {
            'total_thoughts': len(self.thoughts),
            'total_connections': self.graph.number_of_edges(),
            'avg_connections_per_thought': (
                self.graph.number_of_edges() * 2 / len(self.thoughts)
                if self.thoughts else 0
            ),
            'unique_tags': len(set(tag for t in self.thoughts for tag in t.tags)),
            'most_connected': self._get_most_connected_thought(),
            'network_density': nx.density(self.graph) if self.thoughts else 0
        }
    
    def _get_most_connected_thought(self):
        """Find the thought with most connections"""
        if not self.graph.nodes():
            return None
        
        degrees = dict(self.graph.degree())
        if not degrees:
            return None
            
        max_node = max(degrees.items(), key=lambda x: x[1])
        thought = next(t for t in self.thoughts if t.id == max_node[0])
        return {
            'content': thought.content,
            'connections': max_node[1]
        }
    
    def suggest_next_thoughts(self, current_thought, n=3):
        """Generate suggestions for what to think about next"""
        related = self.find_related_thoughts(current_thought.content, top_k=5)
        
        suggestions = []
        
        # Suggest exploring connected ideas
        if related:
            top_related = related[0]['thought']
            suggestions.append(
                f"How does '{current_thought.content[:40]}...' relate to '{top_related.content[:40]}...'?"
            )
        
        # Suggest expanding on tags
        if current_thought.tags:
            tag = current_thought.tags[0]
            suggestions.append(
                f"What are other aspects of #{tag} worth exploring?"
            )
        
        # Suggest contrarian thinking
        suggestions.append(
            f"What would be a counterargument to '{current_thought.content[:40]}...'?"
        )
        
        return suggestions[:n]
    
    def export_network(self, filename='mindweave_network.json'):
        """Export the thought network to JSON"""
        data = {
            'thoughts': [
                {
                    'id': t.id,
                    'content': t.content,
                    'tags': t.tags,
                    'timestamp': t.timestamp.isoformat()
                }
                for t in self.thoughts
            ],
            'connections': [
                {
                    'from': u,
                    'to': v,
                    'weight': d['weight'],
                    'reason': d.get('reason', '')
                }
                for u, v, d in self.graph.edges(data=True)
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Network exported to {filename}")


# Demo usage
if __name__ == "__main__":
    print("=== MindWeave: AI-Powered Thought Network ===\n")
    
    # Initialize MindWeave
    mind = MindWeave(similarity_threshold=0.2)
    
    # Add some example thoughts
    thoughts_to_add = [
        "Machine learning can help us understand patterns in data #AI #learning",
        "Neural networks are inspired by the human brain #AI #neuroscience",
        "Deep learning requires large amounts of training data #AI #data",
        "Reading books expands our knowledge and perspective #learning #books",
        "The best way to learn is through practice and iteration #learning #growth",
        "Meditation helps improve focus and mental clarity #mindfulness #health",
        "Regular exercise is important for both physical and mental health #health #fitness",
        "Knowledge graphs can represent complex relationships between concepts #data #networks",
        "The human brain has remarkable plasticity and adaptability #neuroscience #learning",
        "Continuous learning is essential in a rapidly changing world #learning #growth"
    ]
    
    print("Adding thoughts to the network...\n")
    for thought_content in thoughts_to_add:
        mind.add_thought(thought_content)
        print()
    
    # Display network statistics
    print("\n" + "="*60)
    print("NETWORK STATISTICS")
    print("="*60)
    stats = mind.get_network_stats()
    for key, value in stats.items():
        if key != 'most_connected':
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    if stats['most_connected']:
        print(f"\nMost Connected Thought:")
        print(f"  '{stats['most_connected']['content'][:60]}...'")
        print(f"  Connections: {stats['most_connected']['connections']}")
    
    # Find clusters
    print("\n" + "="*60)
    print("DISCOVERED THEMATIC CLUSTERS")
    print("="*60)
    clusters = mind.discover_clusters(min_samples=2)
    for cluster_name, thoughts in clusters.items():
        print(f"\n{cluster_name}:")
        for thought in thoughts:
            print(f"  • {thought.content}")
    
    # Search example
    print("\n" + "="*60)
    print("SEARCH: 'learning and growth'")
    print("="*60)
    results = mind.find_related_thoughts("learning and growth", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['similarity']:.3f}] {result['thought'].content}")
    
    # Explore neighborhood
    if mind.thoughts:
        example_thought = mind.thoughts[0]
        print("\n" + "="*60)
        print(f"NEIGHBORHOOD: '{example_thought.content[:50]}...'")
        print("="*60)
        neighbors = mind.get_thought_neighborhood(example_thought.id, depth=2)
        for neighbor in neighbors[:5]:
            print(f"  → [{neighbor['connection_strength']:.3f}] {neighbor['thought'].content}")
    
    # Get suggestions
    if mind.thoughts:
        print("\n" + "="*60)
        print("AI SUGGESTIONS FOR NEXT THOUGHTS")
        print("="*60)
        suggestions = mind.suggest_next_thoughts(mind.thoughts[0])
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    
    # Export network
    print("\n" + "="*60)
    mind.export_network()
    print("="*60)