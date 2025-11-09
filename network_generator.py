"""
Network graph generator for knowledge elements relationships
"""
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
from typing import Dict, List, Tuple
import json
import os
import tempfile


def load_cooccurrence_data(csv_path: str = 'shanhaijing_cooccurrence_expanded_result.csv') -> pd.DataFrame:
    """Load the cooccurrence data"""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        return df
    except Exception as e:
        print(f"Error loading cooccurrence data: {e}")
        return None


def get_item_relationships(item_name: str, df: pd.DataFrame) -> Dict:
    """
    Get relationships for a specific item from the cooccurrence data
    Returns dict with original text, chapter, and relationships
    """
    # Find the row for this item
    item_rows = df[df['名字'] == item_name]
    
    if item_rows.empty:
        return None
    
    # Get the first occurrence (or we could aggregate if there are multiple)
    item_row = item_rows.iloc[0]
    
    # Parse related entities and relationships
    related_entities = str(item_row['相关人物']).split(',') if pd.notna(item_row['相关人物']) else []
    related_entities_pinyin = str(item_row['相关人物（拼音）']).split(',') if pd.notna(item_row['相关人物（拼音）']) else []
    relationships = str(item_row['关系']).split(',') if pd.notna(item_row['关系']) else []
    
    # Get main item pinyin name
    main_item_pinyin = item_row['名字（拼音）'] if pd.notna(item_row['名字（拼音）']) else item_name
    
    # Filter out "无关" (irrelevant) relationships
    valid_relationships = []
    for entity, entity_pinyin, relation in zip(related_entities, related_entities_pinyin, relationships):
        if relation.strip() != '无关' and relation.strip() != '':
            valid_relationships.append({
                'target': entity.strip(),
                'target_pinyin': entity_pinyin.strip(),
                'relation': relation.strip()
            })
    
    return {
        'name': item_name,
        'name_pinyin': main_item_pinyin,
        'original_text': item_row['原文行'] if pd.notna(item_row['原文行']) else '',
        'chapter': item_row['章节'] if pd.notna(item_row['章节']) else '',
        'relationships': valid_relationships
    }


def create_network_graph(item_name: str, relationships_data: Dict, width: int = 800, height: int = 600) -> str:
    """
    Create an interactive network graph using Plotly
    Returns HTML string for embedding
    """
    if not relationships_data or not relationships_data['relationships']:
        return "<div class='no-network'>No relationship data available</div>"
    
    # Create networkx graph
    G = nx.Graph()
    
    # Get pinyin name for center node
    center_name_pinyin = relationships_data.get('name_pinyin', item_name)
    
    # Add center node (the main item) - use pinyin name
    G.add_node(center_name_pinyin, node_type='center', original_name=item_name)
    
    # Add related nodes and edges - use pinyin names
    edge_labels = {}
    for rel in relationships_data['relationships']:
        target_pinyin = rel['target_pinyin']
        relation = rel['relation']
        G.add_node(target_pinyin, node_type='related', original_name=rel['target'])
        G.add_edge(center_name_pinyin, target_pinyin, relation=relation)
        edge_labels[(center_name_pinyin, target_pinyin)] = relation
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create edge traces
    edge_trace = []
    edge_text_trace = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Edge line
        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Edge label (relationship type)
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        relation_label = G[edge[0]][edge[1]]['relation']
        
        edge_text_trace.append(go.Scatter(
            x=[mid_x],
            y=[mid_y],
            mode='text',
            text=[relation_label],
            textposition='middle center',
            textfont=dict(size=10, color='#666'),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Create node traces
    center_nodes_x = []
    center_nodes_y = []
    center_nodes_text = []
    center_nodes_hover = []
    
    related_nodes_x = []
    related_nodes_y = []
    related_nodes_text = []
    related_nodes_hover = []
    
    for node in G.nodes():
        x, y = pos[node]
        original_name = G.nodes[node].get('original_name', node)
        hover_text = f"{node}<br>原名: {original_name}"
        
        if G.nodes[node]['node_type'] == 'center':
            center_nodes_x.append(x)
            center_nodes_y.append(y)
            center_nodes_text.append(node)
            center_nodes_hover.append(hover_text)
        else:
            related_nodes_x.append(x)
            related_nodes_y.append(y)
            related_nodes_text.append(node)
            related_nodes_hover.append(hover_text)
    
    # Center node trace (main item)
    center_trace = go.Scatter(
        x=center_nodes_x,
        y=center_nodes_y,
        mode='markers+text',
        text=center_nodes_text,
        textposition='top center',
        textfont=dict(size=14, color='#fff', family='Arial Black'),
        marker=dict(
            size=30,
            color='#e74c3c',
            line=dict(width=2, color='#c0392b')
        ),
        hoverinfo='text',
        hovertext=center_nodes_hover,
        name='Main Entity',
        showlegend=True
    )
    
    # Related nodes trace
    related_trace = go.Scatter(
        x=related_nodes_x,
        y=related_nodes_y,
        mode='markers+text',
        text=related_nodes_text,
        textposition='top center',
        textfont=dict(size=11, color='#333'),
        marker=dict(
            size=20,
            color='#3498db',
            line=dict(width=2, color='#2980b9')
        ),
        hoverinfo='text',
        hovertext=related_nodes_hover,
        name='Related Entities',
        showlegend=True
    )
    
    # Combine all traces
    data = edge_trace + edge_text_trace + [center_trace, related_trace]
    
    # Create figure
    fig = go.Figure(data=data)
    
    # Update layout for better appearance
    center_name_display = relationships_data.get('name_pinyin', item_name)
    fig.update_layout(
        title=dict(
            text=f'Knowledge Network: {center_name_display}',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=60),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#fff',
        width=width,
        height=height,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#ddd',
            borderwidth=1
        )
    )
    
    # Return HTML div string
    return fig.to_html(include_plotlyjs='cdn', div_id='network-graph', config={'responsive': True})


def get_all_occurrences(item_name: str, df: pd.DataFrame) -> List[Dict]:
    """
    Get all occurrences of an item across different chapters
    Handles merged rows where original_text and chapter are separated by '|'
    """
    item_rows = df[df['名字'] == item_name]
    
    occurrences = []
    for _, row in item_rows.iterrows():
        original_text = row['原文行'] if pd.notna(row['原文行']) else ''
        chapter = row['章节'] if pd.notna(row['章节']) else ''
        
        # Split by '|' to handle merged rows
        original_texts = [text.strip() for text in str(original_text).split('|')]
        chapters = [ch.strip() for ch in str(chapter).split(';')]
        
        # Ensure both lists have the same length
        # If chapters are fewer, repeat the last chapter
        if len(chapters) < len(original_texts):
            if chapters:
                chapters.extend([chapters[-1]] * (len(original_texts) - len(chapters)))
            else:
                chapters = [''] * len(original_texts)
        
        # Create separate occurrences for each split
        for text, ch in zip(original_texts, chapters):
            if text and text != 'nan':  # Skip empty or 'nan' strings
                occurrences.append({
                    'original_text': text,
                    'chapter': ch
                })
    
    return occurrences


def create_interactive_network_graph(item_name: str, relationships_data: Dict, width: str = "100%", height: str = "600px") -> str:
    """
    Create a fully interactive draggable network graph using pyvis
    Returns HTML string for embedding
    """
    if not relationships_data or not relationships_data['relationships']:
        return "<div class='no-network'>No relationship data available</div>"
    
    # Create pyvis network
    net = Network(
        height=height,
        width=width,
        bgcolor='#f8f9fa',
        font_color='#2c3e50',
        notebook=False
    )
    
    # Configure physics for better interaction
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.1
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "barnesHut",
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 25
            }
        },
        "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true,
            "hover": true,
            "navigationButtons": true,
            "keyboard": {
                "enabled": true
            }
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "Arial"
            },
            "borderWidth": 2,
            "borderWidthSelected": 3
        },
        "edges": {
            "color": {
                "inherit": false,
                "color": "#888888",
                "highlight": "#e74c3c",
                "hover": "#3498db"
            },
            "smooth": {
                "enabled": true,
                "type": "continuous"
            },
            "arrows": {
                "to": {
                    "enabled": false
                }
            },
            "font": {
                "size": 11,
                "color": "#666666",
                "strokeWidth": 0,
                "align": "middle"
            }
        }
    }
    """)
    
    # Get pinyin name for center node
    center_name_pinyin = relationships_data.get('name_pinyin', item_name)
    
    # Add center node (main item)
    net.add_node(
        center_name_pinyin,
        label=center_name_pinyin,
        title=f"<b>主实体</b><br>{center_name_pinyin}<br>原名: {item_name}",
        color='#e74c3c',
        size=30,
        font={'size': 16, 'color': '#ffffff', 'face': 'Arial Black'}
    )
    
    # Add related nodes and edges
    for rel in relationships_data['relationships']:
        target_pinyin = rel['target_pinyin']
        relation = rel['relation']
        original_target = rel['target']
        
        # Add related node
        net.add_node(
            target_pinyin,
            label=target_pinyin,
            title=f"<b>相关实体</b><br>{target_pinyin}<br>原名: {original_target}",
            color='#3498db',
            size=20,
            font={'size': 12, 'color': '#333333'}
        )
        
        # Add edge with relationship label
        net.add_edge(
            center_name_pinyin,
            target_pinyin,
            label=relation,
            title=relation,
            width=2
        )
    
    # Generate HTML
    html = net.generate_html()
    
    # Customize the HTML output
    custom_html = f"""
    <div class="pyvis-network-container">
        <div class="network-instructions">
            <p><strong>💡 交互提示:</strong> 拖动节点调整位置 | 滚轮缩放 | 拖动背景平移视图 | 悬停查看详情</p>
        </div>
        {html}
    </div>
    <style>
        .pyvis-network-container {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .network-instructions {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.8rem 1.2rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            text-align: center;
        }}
        .network-instructions p {{
            margin: 0;
            font-size: 0.9rem;
        }}
        .pyvis-network-container > div {{
            border-radius: 6px;
            overflow: hidden;
        }}
    </style>
    """
    
    return custom_html


def create_global_network_graph(df: pd.DataFrame, width: str = "100%", height: str = "800px", max_nodes: int = 500) -> str:
    """
    Create a global network graph showing all entities and their relationships
    
    Args:
        df: DataFrame with cooccurrence data
        width: Width of the network graph
        height: Height of the network graph
        max_nodes: Maximum number of nodes to display (to prevent performance issues)
    
    Returns:
        HTML string for embedding
    """
    if df is None or df.empty:
        return "<div class='no-network'>No data available for global network</div>"
    
    # Create pyvis network with optimized settings for large graphs
    net = Network(
        height=height,
        width=width,
        bgcolor='#1a1a2e',
        font_color='#eee',
        notebook=False,
        select_menu=True,
        filter_menu=True
    )
    
    # Configure physics for large graphs - stable layout with larger spacing
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {
                "enabled": true,
                "iterations": 500,
                "updateInterval": 50,
                "fit": true
            },
            "barnesHut": {
                "gravitationalConstant": -50000,
                "centralGravity": 0.01,
                "springLength": 350,
                "springConstant": 0.005,
                "damping": 0.5,
                "avoidOverlap": 1
            },
            "maxVelocity": 20,
            "minVelocity": 0.5,
            "solver": "barnesHut",
            "timestep": 0.3,
            "adaptiveTimestep": true
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
        },
        "nodes": {
            "shape": "dot",
            "scaling": {
                "min": 4,
                "max": 45,
                "label": {
                    "enabled": true,
                    "min": 8,
                    "max": 14
                }
            },
            "font": {
                "size": 11,
                "face": "Arial",
                "strokeWidth": 0,
                "strokeColor": "#000000"
            },
            "borderWidth": 1.5,
            "borderWidthSelected": 3
        },
        "edges": {
            "smooth": {
                "enabled": true,
                "type": "continuous",
                "roundness": 0.5
            },
            "color": {
                "color": "rgba(200, 200, 200, 0.25)",
                "highlight": "rgba(66, 135, 245, 0.8)",
                "hover": "rgba(200, 200, 200, 0.5)"
            },
            "width": 1,
            "selectionWidth": 2.5
        },
        "layout": {
            "improvedLayout": true,
            "clusterThreshold": 150
        }
    }
    """)
    
    # Track nodes and their connections
    node_connections = {}
    unique_nodes = set()
    
    # First pass: collect all unique nodes and count connections
    for _, row in df.iterrows():
        main_entity = row['名字']
        main_entity_pinyin = row['名字（拼音）'] if pd.notna(row['名字（拼音）']) else main_entity
        
        if main_entity not in node_connections:
            node_connections[main_entity] = {
                'pinyin': main_entity_pinyin,
                'count': 0
            }
        
        # Parse related entities
        related_entities = str(row['相关人物']).split(',') if pd.notna(row['相关人物']) else []
        related_pinyin = str(row['相关人物（拼音）']).split(',') if pd.notna(row['相关人物（拼音）']) else []
        relationships = str(row['关系']).split(',') if pd.notna(row['关系']) else []
        
        for entity, entity_pinyin, relation in zip(related_entities, related_pinyin, relationships):
            entity = entity.strip()
            if entity and relation.strip() != '无关':
                if entity not in node_connections:
                    node_connections[entity] = {
                        'pinyin': entity_pinyin.strip(),
                        'count': 0
                    }
                node_connections[main_entity]['count'] += 1
                node_connections[entity]['count'] += 1
    
    # Sort nodes by connection count and limit to max_nodes
    sorted_nodes = sorted(node_connections.items(), key=lambda x: x[1]['count'], reverse=True)
    limited_nodes = dict(sorted_nodes[:max_nodes])
    
    # Add nodes with size based on connection count
    for node_name, node_info in limited_nodes.items():
        # Calculate node size based on connections (more connections = bigger node)
        # Even smaller base sizes for cleaner visualization
        connection_count = node_info['count']
        if connection_count > 20:
            size = 20 + min(connection_count * 0.5, 25)  # Very large for highly connected
            color = '#e74c3c'  # Red for highly connected
        elif connection_count > 10:
            size = 14 + connection_count * 0.4  # Large for moderately connected
            color = '#f39c12'  # Orange
        elif connection_count > 5:
            size = 9 + connection_count * 0.3  # Medium
            color = '#3498db'  # Blue
        else:
            size = 4 + connection_count * 0.3  # Very small for less connected
            color = '#95a5a6'  # Gray for less connected
        
        # Create label with pinyin and Chinese
        label = node_info['pinyin']
        title = f"{node_name}\nConnections: {connection_count}"
        
        net.add_node(
            node_name,
            label=label,
            title=title,
            size=size,
            color=color,
            font={'size': 9, 'color': '#fff'}
        )
    
    # Add edges between nodes (only for nodes in limited_nodes)
    added_edges = set()
    for _, row in df.iterrows():
        main_entity = row['名字']
        
        if main_entity not in limited_nodes:
            continue
        
        related_entities = str(row['相关人物']).split(',') if pd.notna(row['相关人物']) else []
        relationships = str(row['关系']).split(',') if pd.notna(row['关系']) else []
        
        for entity, relation in zip(related_entities, relationships):
            entity = entity.strip()
            relation = relation.strip()
            
            if entity in limited_nodes and relation != '无关':
                # Avoid duplicate edges
                edge_key = tuple(sorted([main_entity, entity]))
                if edge_key not in added_edges:
                    net.add_edge(
                        main_entity,
                        entity,
                        title=relation,
                        color='rgba(200, 200, 200, 0.3)'
                    )
                    added_edges.add(edge_key)
    
    # Get HTML directly from pyvis without saving to file
    # This avoids encoding issues with Chinese characters
    import re
    
    # Generate HTML in memory
    try:
        # Get the nodes and edges data as JSON
        nodes_data = []
        edges_data = []
        
        # Extract nodes
        for node in net.nodes:
            nodes_data.append({
                'id': node['id'],
                'label': node.get('label', ''),
                'title': node.get('title', ''),
                'size': node.get('size', 10),
                'color': node.get('color', '#97c2fc'),
                'font': node.get('font', {})
            })
        
        # Extract edges
        edge_id = 0
        for edge in net.edges:
            edges_data.append({
                'id': edge_id,
                'from': edge['from'],
                'to': edge['to'],
                'title': edge.get('title', ''),
                'color': edge.get('color', '#848484')
            })
            edge_id += 1
        
        # Convert to JSON
        import json
        nodes_json = json.dumps(nodes_data, ensure_ascii=False)
        edges_json = json.dumps(edges_data, ensure_ascii=False)
        options_json = json.dumps(net.options, ensure_ascii=False)
        
    except Exception as e:
        return f"<div class='no-network'>Error generating network: {str(e)}</div>"
    
    # Create the network div and script manually
    network_div = f'<div id="globalnetwork" style="width: {width}; height: {height}; background: #1a1a2e;"></div>'
    
    network_script = f"""
    <script type="text/javascript">
        // Create network data
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        var container = document.getElementById('globalnetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {options_json};
        var network = new vis.Network(container, data, options);
        
        // Store original colors for reset
        var originalNodeColors = {{}};
        var originalEdgeColors = {{}};
        nodes.forEach(function(node) {{
            originalNodeColors[node.id] = node.color;
        }});
        edges.forEach(function(edge) {{
            originalEdgeColors[edge.id] = edge.color;
        }});
        
        // Variable to track if a node is selected
        var selectedNodeId = null;
        
        // Click event: highlight connected nodes and edges
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var clickedNodeId = params.nodes[0];
                
                // If clicking the same node again, deselect it
                if (selectedNodeId === clickedNodeId) {{
                    resetAllColors();
                    selectedNodeId = null;
                    return;
                }}
                
                selectedNodeId = clickedNodeId;
                
                // Get all connected nodes
                var connectedNodes = network.getConnectedNodes(clickedNodeId);
                var connectedEdges = network.getConnectedEdges(clickedNodeId);
                
                // Dim all nodes first
                nodes.forEach(function(node) {{
                    if (node.id === clickedNodeId) {{
                        // Highlight clicked node
                        nodes.update({{
                            id: node.id,
                            color: {{
                                background: node.color,
                                border: '#FFD700',
                                highlight: {{
                                    background: node.color,
                                    border: '#FFD700'
                                }}
                            }},
                            borderWidth: 5,
                            font: {{ size: 14, color: '#fff' }}
                        }});
                    }} else if (connectedNodes.indexOf(node.id) !== -1) {{
                        // Highlight connected nodes
                        nodes.update({{
                            id: node.id,
                            color: {{
                                background: node.color,
                                border: '#00FF00',
                                highlight: {{
                                    background: node.color,
                                    border: '#00FF00'
                                }}
                            }},
                            borderWidth: 3,
                            font: {{ size: 12, color: '#fff' }}
                        }});
                    }} else {{
                        // Dim unconnected nodes
                        nodes.update({{
                            id: node.id,
                            color: {{
                                background: 'rgba(150, 150, 150, 0.3)',
                                border: 'rgba(150, 150, 150, 0.5)'
                            }},
                            font: {{ size: 8, color: 'rgba(200, 200, 200, 0.5)' }}
                        }});
                    }}
                }});
                
                // Highlight connected edges
                edges.forEach(function(edge) {{
                    if (connectedEdges.indexOf(edge.id) !== -1) {{
                        edges.update({{
                            id: edge.id,
                            color: {{ color: '#FFD700', highlight: '#FFD700' }},
                            width: 3
                        }});
                    }} else {{
                        edges.update({{
                            id: edge.id,
                            color: {{ color: 'rgba(200, 200, 200, 0.1)' }},
                            width: 0.5
                        }});
                    }}
                }});
            }} else {{
                // Clicked on empty space - reset all
                resetAllColors();
                selectedNodeId = null;
            }}
        }});
        
        // Function to reset all colors
        function resetAllColors() {{
            nodes.forEach(function(node) {{
                nodes.update({{
                    id: node.id,
                    color: originalNodeColors[node.id],
                    borderWidth: 1.5,
                    font: {{ size: 9, color: '#fff' }}
                }});
            }});
            edges.forEach(function(edge) {{
                edges.update({{
                    id: edge.id,
                    color: originalEdgeColors[edge.id] || {{ color: 'rgba(200, 200, 200, 0.25)' }},
                    width: 1
                }});
            }});
        }}
    </script>
    """
    
    # Add custom styling and wrap the network
    custom_html = f"""
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
    <style>
        .global-network-container {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .network-legend {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .network-legend h4 {{
            margin: 0 0 0.75rem 0;
            color: #2c3e50;
            font-size: 1.1rem;
        }}
        .legend-items {{
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
        }}
        .legend-label {{
            font-size: 0.9rem;
            color: #555;
        }}
        .network-stats {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }}
        .network-stats h4 {{
            margin: 0 0 0.5rem 0;
            color: #2c3e50;
        }}
        .stats-grid {{
            display: flex;
            gap: 2rem;
            justify-content: center;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
        }}
        .global-network-instructions {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }}
        .global-network-instructions p {{
            margin: 0;
            font-size: 0.95rem;
        }}
    </style>
    <div class="global-network-container">
        <div class="network-stats">
            <h4>📊 Network Statistics</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{len(limited_nodes)}</div>
                    <div class="stat-label">Nodes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len(added_edges)}</div>
                    <div class="stat-label">Connections</div>
                </div>
            </div>
        </div>
        <div class="network-legend">
            <h4>🎨 Node Colors Legend</h4>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #e74c3c;"></div>
                    <span class="legend-label">Highly Connected (20+ connections)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f39c12;"></div>
                    <span class="legend-label">Well Connected (10-20 connections)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #3498db;"></div>
                    <span class="legend-label">Connected (5-10 connections)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #95a5a6;"></div>
                    <span class="legend-label">Less Connected (< 5 connections)</span>
                </div>
            </div>
        </div>
        <div class="global-network-instructions">
            <p>🔍 Interactive Global Knowledge Network | 💡 Click a node to highlight its connections | Drag nodes to reposition | Scroll to zoom | Click empty space to reset | Use navigation buttons for control</p>
        </div>
        {network_div}
    </div>
    {network_script}
    """
    
    return custom_html
