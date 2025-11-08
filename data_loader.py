"""
Data loader module for reading CSV files from csv_by_category_English
"""
import os
import pandas as pd
from pathlib import Path


def get_category_structure(base_path="csv_by_category_English"):
    """
    Scan the csv_by_category_English folder and return a hierarchical structure.
    Returns: dict with structure {category: [csv_files]}
    """
    structure = {}
    base = Path(base_path)
    
    if not base.exists():
        return structure
    
    # Iterate through first-level directories (categories)
    for category_dir in sorted(base.iterdir()):
        if category_dir.is_dir():
            csv_files = []
            # Find all CSV files in this category
            for csv_file in sorted(category_dir.glob("*.csv")):
                csv_files.append({
                    'name': csv_file.stem,
                    'path': str(csv_file.relative_to(base))
                })
            if csv_files:
                structure[category_dir.name] = csv_files
    
    return structure


def load_csv_data(csv_path, base_path="csv_by_category_English"):
    """
    Load a specific CSV file and return as DataFrame.
    """
    full_path = Path(base_path) / csv_path
    if not full_path.exists():
        return None
    
    try:
        df = pd.read_csv(full_path)
        return df
    except Exception as e:
        print(f"Error loading {full_path}: {e}")
        return None


def get_paginated_data(df, page=1, per_page=20):
    """
    Paginate DataFrame and return page data with metadata.
    """
    if df is None or df.empty:
        return {
            'data': [],
            'page': 1,
            'total_pages': 0,
            'total_items': 0,
            'has_prev': False,
            'has_next': False
        }
    
    total_items = len(df)
    total_pages = (total_items + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    page_data = df.iloc[start_idx:end_idx].to_dict('records')
    
    return {
        'data': page_data,
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }


def get_item_detail(csv_path, item_name, base_path="csv_by_category_English"):
    """
    Get detailed information for a specific item by name.
    """
    df = load_csv_data(csv_path, base_path)
    if df is None:
        return None
    
    # Try to find by the first column (usually '名字' or similar)
    name_col = df.columns[0]
    item = df[df[name_col] == item_name]
    
    if item.empty:
        return None
    
    return item.iloc[0].to_dict()
