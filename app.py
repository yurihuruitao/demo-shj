"""
Flask web application for Shan Hai Jing Knowledge Elements
"""
from flask import Flask, render_template, request, abort, send_from_directory
from data_loader import get_category_structure, load_csv_data, get_paginated_data, get_item_detail
from network_generator import load_cooccurrence_data, get_item_relationships, create_interactive_network_graph, get_all_occurrences, create_global_network_graph
from pathlib import Path
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shan-hai-jing-knowledge-elements'

# Set up images directory
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

# Load cooccurrence data once at startup
COOCCURRENCE_DF = load_cooccurrence_data()


def calculate_top_connected_nodes(df, top_n=10):
    """
    Calculate the top N most connected nodes from the cooccurrence data
    
    Args:
        df: DataFrame with cooccurrence data
        top_n: Number of top nodes to return
        
    Returns:
        List of dictionaries with node info (name, pinyin, connection_count, csv_path)
    """
    import pandas as pd
    import os
    from pathlib import Path
    
    if df is None or df.empty:
        return []
    
    # Track nodes and their connections
    node_connections = {}
    
    # Count connections for each node (excluding '无关' relationships)
    for _, row in df.iterrows():
        main_entity = row['名字']
        main_entity_pinyin = row['名字（拼音）'] if pd.notna(row['名字（拼音）']) else main_entity
        
        if main_entity not in node_connections:
            node_connections[main_entity] = {
                'name': main_entity,
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
                        'name': entity,
                        'pinyin': entity_pinyin.strip(),
                        'count': 0
                    }
                node_connections[main_entity]['count'] += 1
                node_connections[entity]['count'] += 1
    
    # Sort by connection count and get top N
    sorted_nodes = sorted(node_connections.values(), key=lambda x: x['count'], reverse=True)
    top_nodes = sorted_nodes[:top_n]
    
    # Find CSV path for each top node
    csv_base_dir = Path(__file__).parent / 'csv_by_category_English'
    for node in top_nodes:
        node['csv_path'] = find_entity_csv_path(node['name'], csv_base_dir)
    
    return top_nodes


def find_entity_csv_path(entity_name, csv_base_dir):
    """
    Find the CSV file path for a given entity
    
    Args:
        entity_name: Name of the entity to find
        csv_base_dir: Base directory containing CSV files
        
    Returns:
        Relative CSV path or None if not found
    """
    import pandas as pd
    
    # Search through all CSV files
    for csv_file in csv_base_dir.rglob('*.csv'):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # Check if entity exists in '名字' column
            if '名字' in df.columns:
                if entity_name in df['名字'].values:
                    # Return relative path from csv_by_category_English
                    rel_path = csv_file.relative_to(csv_base_dir)
                    return str(rel_path).replace('\\', '/')
        except Exception:
            continue
    
    return None


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/')
def index():
    """Home page with global network visualization"""
    categories = get_category_structure()
    
    # Get max_nodes from query parameter, default to 100
    max_nodes = request.args.get('max_nodes', 100, type=int)
    
    # Limit to reasonable range (10 to 5000)
    max_nodes = max(10, min(max_nodes, 5000))
    
    # Calculate top 10 most connected nodes
    top_nodes = []
    if COOCCURRENCE_DF is not None:
        top_nodes = calculate_top_connected_nodes(COOCCURRENCE_DF, top_n=10)
    
    # Generate global network graph
    global_network_html = None
    if COOCCURRENCE_DF is not None:
        global_network_html = create_global_network_graph(
            COOCCURRENCE_DF, 
            width="100%", 
            height="800px",
            max_nodes=max_nodes
        )
    
    return render_template('index.html', 
                         categories=categories,
                         global_network_html=global_network_html,
                         current_max_nodes=max_nodes,
                         top_nodes=top_nodes)


@app.route('/category/<path:csv_path>')
def category_list(csv_path):
    """Show paginated list of items in a CSV file"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Load CSV data
    df = load_csv_data(csv_path)
    if df is None:
        abort(404)
    
    # Get paginated data
    paginated = get_paginated_data(df, page, per_page)
    
    # Extract category and subcategory from path
    path_parts = csv_path.replace('.csv', '').split('/')
    category = path_parts[0] if len(path_parts) > 0 else 'Unknown'
    subcategory = path_parts[1] if len(path_parts) > 1 else 'Unknown'
    
    categories = get_category_structure()
    
    return render_template('category_list.html',
                         categories=categories,
                         category=category,
                         subcategory=subcategory,
                         csv_path=csv_path,
                         paginated=paginated,
                         columns=df.columns.tolist())


@app.route('/detail/<path:csv_path>/<item_name>')
def item_detail(csv_path, item_name):
    """Show detailed information for a specific item"""
    item = get_item_detail(csv_path, item_name)
    if item is None:
        abort(404)
    
    # Extract category and subcategory from path
    path_parts = csv_path.replace('.csv', '').split('/')
    category = path_parts[0] if len(path_parts) > 0 else 'Unknown'
    subcategory = path_parts[1] if len(path_parts) > 1 else 'Unknown'
    
    categories = get_category_structure()
    
    # Get image path if exists
    image_path = None
    if 'image_path' in item and item['image_path']:
        # Construct proper image path - replace backslashes with forward slashes for web
        image_path = str(item['image_path']).replace('\\', '/')
    
    # Get relationship data and generate network graph
    network_html = None
    original_text = None
    chapter = None
    all_occurrences = []
    
    if COOCCURRENCE_DF is not None:
        # Get relationship data
        rel_data = get_item_relationships(item_name, COOCCURRENCE_DF)
        
        if rel_data:
            # Generate interactive draggable network graph HTML
            network_html = create_interactive_network_graph(item_name, rel_data, width="100%", height="600px")
            
            # Extract only the first original text (before the first '|')
            full_original_text = rel_data['original_text']
            if full_original_text and '|' in full_original_text:
                original_text = full_original_text.split('|')[0].strip()
            else:
                original_text = full_original_text
            
            # Extract only the first chapter (before the first ';')
            full_chapter = rel_data['chapter']
            if full_chapter and ';' in full_chapter:
                chapter = full_chapter.split(';')[0].strip()
            else:
                chapter = full_chapter
        
        # Get all occurrences across chapters
        all_occurrences = get_all_occurrences(item_name, COOCCURRENCE_DF)
    
    return render_template('detail.html',
                         categories=categories,
                         category=category,
                         subcategory=subcategory,
                         csv_path=csv_path,
                         item=item,
                         image_path=image_path,
                         network_html=network_html,
                         original_text=original_text,
                         chapter=chapter,
                         all_occurrences=all_occurrences)


@app.template_filter('get_display_name')
def get_display_name(path_or_name):
    """Extract display name from path or filename"""
    return Path(path_or_name).stem


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
