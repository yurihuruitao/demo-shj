# Shan Hai Jing Knowledge Elements - Flask Web Application

A Flask-based web application for browsing and exploring the Classic of Mountains and Seas (山海经) knowledge base.

## Features

✨ **Expandable Navigation Sidebar**
- Hierarchical category structure
- Auto-expand current category
- Smooth transitions

📚 **Paginated Content Lists**
- 20 items per page
- Grid view with images
- Quick navigation

🖼️ **Detailed Item Views**
- English prompt translations
- Original Chinese descriptions
- High-quality images
- Complete metadata

## Quick Start

### Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python app.py
```

The application will start at: **http://localhost:5000**

## Project Structure

```
demo/
├── app.py                          # Flask application
├── data_loader.py                  # CSV data loading utilities
├── requirements.txt                # Python dependencies
├── templates/                      # HTML templates
│   ├── base.html                  # Base template with navigation
│   ├── index.html                 # Home page
│   ├── category_list.html         # Paginated item list
│   └── detail.html                # Item detail view
├── static/
│   └── css/
│       └── style.css              # Application styles
├── csv_by_category_English/       # Data source (English)
│   ├── Animal（动物）/
│   ├── Toponym（地名）/
│   └── ...
└── images/                        # Generated images
    ├── 地名/
    ├── 动物/
    └── ...
```

## Data Structure

The application reads CSV files from `csv_by_category_English/` with the following structure:

- **Categories**: Top-level folders (e.g., Animal, Toponym)
- **Subcategories**: CSV files within categories
- **Required Columns**:
  - First column: Item name (used as identifier)
  - `prompt翻译`: English description
  - `prompt`: Original Chinese prompt
  - `image_path`: Relative path to image
  - `显示名字`: Romanized display name

## Features in Detail

### Navigation
- Click category names to expand/collapse
- Current selection is highlighted
- Automatically opens category of current page

### List View
- Grid layout with thumbnails
- Displays item names and romanization
- Pagination at bottom
- Shows total item count

### Detail View
- Full-size image
- English translated description
- Original Chinese prompt
- All metadata in table format
- Back to list button

## Customization

### Change Items Per Page
Edit `per_page` in `app.py`:
```python
per_page = 20  # Change to desired number
```

### Modify Styles
Edit `static/css/style.css` to customize:
- Color scheme
- Layout
- Fonts
- Spacing

## Browser Compatibility

✅ Chrome/Edge (recommended)
✅ Firefox
✅ Safari

## Notes

- Images are loaded from the `images/` directory
- Missing images show a placeholder
- All UI text is in English
- Supports responsive design for mobile devices

## License

This project is part of the Shan Hai Jing research initiative.
