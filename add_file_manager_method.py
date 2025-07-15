#!/usr/bin/env python
import os
import re
import datetime

def add_file_manager_method(file_path):
    """
    Ajoute la méthode extract_period_from_filename à la classe FileManager
    """
    print(f"Modification du fichier: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Méthode à ajouter
    method_code = """
    def extract_period_from_filename(self, file_path: str) -> str:
        \"\"\"
        Extrait la période (mois/année) à partir d'un nom de fichier MP3
        Si pas trouvé, utilise le mois courant
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Période au format YYYY-MM
        \"\"\"
        filename = os.path.basename(file_path)
        
        # Essayer de trouver une date au format YYYY-MM dans le nom
        date_match = re.search(r'(\d{4}-\d{2})', filename)
        if date_match:
            return date_match.group(1)
        
        # Si pas trouvé, utiliser la date courante
        now = datetime.datetime.now()
        return f"{now.year}-{now.month:02d}"
    """
    
    # Vérifie si la méthode existe déjà
    if "def extract_period_from_filename" in content:
        print("La méthode extract_period_from_filename existe déjà.")
        return
    
    # Trouve la fin de la classe FileManager pour y ajouter la méthode
    if "class FileManager:" in content:
        # Assure-toi d'importer datetime s'il n'est pas déjà importé
        if "import datetime" not in content:
            content = content.replace("import os", "import os\nimport datetime")
        
        # Trouve la dernière méthode de la classe
        last_method_pattern = r"([ ]{4}def [^(]+\([^)]*\)[^:]*:.*?)(?=\n\n[^ ])"
        match = re.search(last_method_pattern, content, re.DOTALL)
        
        if match:
            # Ajoute la nouvelle méthode après la dernière méthode existante
            last_method = match.group(0)
            content = content.replace(last_method, last_method + "\n" + method_code)
        else:
            print("Structure de classe non reconnue, impossible d'ajouter la méthode.")
            return
    else:
        print("Classe FileManager non trouvée.")
        return
    
    # Écrit le contenu modifié
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("FileManager.py modifié avec succès.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_manager_path = os.path.join(base_dir, 'core', 'file_manager.py')
    
    if os.path.exists(file_manager_path):
        add_file_manager_method(file_manager_path)
    else:
        print(f"Fichier file_manager.py non trouvé à l'emplacement: {file_manager_path}")
