# ERP BTP - Context for AI Agents

## Quick Reference

### Stack
- Python 3.12 + NiceGUI + JSON storage
- Desktop app (Windows build via PyInstaller)
- PDF generation via ReportLab

### Key Files
- `erp/core/data_manager.py` - Central data CRUD
- `erp/core/models.py` - All dataclasses
- `erp/ui/app.py` - Main application
- `erp/ui/panels/` - UI screens (modular)
- `erp/ui/components.py` - Reusable UI components

### Current Features
✅ Auth, Clients, Suppliers
✅ Articles catalog (with hierarchical categories)
✅ Ouvrages (multi-article assemblies)
✅ Quotes with chapters, discounts
✅ PDF generation
✅ Projects, Organization info

### Code Patterns

**Panel structure:**
```python
def create_xxx_panel(app_instance):
    with ui.card().classes('w-full shadow-sm').style('padding: 24px;'):
        container = ui.column()
        def refresh():
            container.clear()
            with container:
                # Display data from app_instance.dm
                pass
        refresh()
```

**Data access:**
```python
app_instance.dm.articles  # List[Article]
app_instance.dm.save_data()  # Persist to JSON
app_instance.dm.load_data()  # Reload from JSON
```

**Notifications:**
```python
from erp.ui.utils import notify_success, notify_error, notify_info
notify_success('Done!')
```

**Edit dialogs:**
```python
from erp.ui.components import create_edit_dialog
dialog = create_edit_dialog(title, fields=[...], on_save=callback)
dialog.open()
```

### UI Classes
- `themed-button` - Primary buttons
- `text-2xl font-bold mb-6` - Titles
- `w-full shadow-sm` - Cards
- `font-semibold text-base` - Labels

### Recent Changes (Dec 2025)
- Added hierarchical categories (2 levels max)
- Subcategories for articles/ouvrages
- Subcategory filtering for articles
- Menu order: "Liste" before "Devis"
- Organisation dates (exercise start/end)
- Full organisation data persistence

### Important Notes
- Categories: parent → children (max 2 levels)
- Articles/Ouvrages store final category ID (parent or child)
- Filtering: category includes children, subcategory = exact match
- All IDs are integers (auto-incremented)
- All models are @dataclass
- JSON files in `data/` directory

### Next Priorities
- Database migration (JSON → SQLite) when data grows
- Stock management
- Modification history
- Better authentication

### When Starting New Work
1. Check `erp/ui/panels/` for existing patterns
2. Use `components.py` helpers
3. Follow snake_case naming
4. Always call `app_instance.dm.save_data()` after changes
5. Use notifications for user feedback
6. Test with real data in `data/` directory

### File Naming
- Panels: `liste_xxx.py` for lists, `xxx.py` for create/edit forms
- Functions: `create_xxx_panel(app_instance)` for panels
- Refresh: `refresh_xxx_list()` or `refresh_display()` for dynamic updates
