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
