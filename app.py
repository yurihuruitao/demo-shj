"""
Flask web application for Shan Hai Jing Knowledge Elements
"""
from flask import Flask, render_template, request, abort, send_from_directory
from data_loader import get_category_structure, load_csv_data, get_paginated_data, get_item_detail
from network_generator import load_cooccurrence_data, get_item_relationships, create_interactive_network_graph, get_all_occurrences
from pathlib import Path
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shan-hai-jing-knowledge-elements'

# Set up images directory
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

# Load cooccurrence data once at startup
COOCCURRENCE_DF = load_cooccurrence_data()


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/')
def index():
    """Home page with navigation"""
    categories = get_category_structure()
    return render_template('index.html', categories=categories)


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
