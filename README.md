# ERP pour le BTP - Second Œuvre

Refactor minimal d'une application de gestion de devis basée sur NiceGUI.

Structure:

- `devis/models.py` : dataclasses du domaine
- `devis/data_manager.py` : chargement / sauvegarde JSON + données de démonstration
- `devis/ui_app.py` : UI NiceGUI (class `DevisApp`)
- `main.py` : point d'entrée pour lancer l'application

Usage rapide (PowerShell):

```powershell
python .\main.py
```

Notes:
- Les données sont sauvegardées dans le dossier `data/` à la racine du projet.
- Pour ajouter l'export PDF, intégrer une librairie (reportlab, WeasyPrint, wkhtmltopdf, ...).
