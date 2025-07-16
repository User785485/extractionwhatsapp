#!/usr/bin/env python3
"""
Debug complet du workflow - Identifier pourquoi ça ne marche pas
"""

import sys
import os
from pathlib import Path

# Configuration de base
print("=== DEBUG WORKFLOW WHATSAPP EXTRACTOR ===")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Tester tous les imports nécessaires"""
    print("\n1. TEST DES IMPORTS")
    imports_ok = True
    
    try:
        print("  - Testing parsers...")
        from parsers.mobiletrans_parser import MobileTransParser
        print("    [OK] MobileTransParser")
    except Exception as e:
        print(f"    [ERROR] MobileTransParser: {e}")
        imports_ok = False
    
    try:
        print("  - Testing exporters...")
        from exporters.csv_exporter import CSVExporter
        from exporters.json_exporter import JSONExporter
        from exporters.excel_exporter import ExcelExporter
        print("    [OK] All exporters")
    except Exception as e:
        print(f"    [ERROR] Exporters: {e}")
        imports_ok = False
    
    try:
        print("  - Testing logger...")
        from utils.advanced_logger import init_logger
        print("    [OK] Advanced logger")
    except Exception as e:
        print(f"    [ERROR] Logger: {e}")
        imports_ok = False
    
    return imports_ok

def test_file_access():
    """Tester l'accès aux fichiers WhatsApp"""
    print("\n2. TEST D'ACCES AUX FICHIERS")
    
    iphone_dir = Path("C:/Users/Moham/Downloads/iPhone_20250605021808/WhatsApp")
    
    if not iphone_dir.exists():
        print(f"  [ERROR] Repertoire non trouve: {iphone_dir}")
        return False
    
    print(f"  [OK] Repertoire trouve: {iphone_dir}")
    
    # Lister quelques fichiers
    html_files = list(iphone_dir.glob("*.html"))[:5]
    print(f"  [INFO] {len(list(iphone_dir.glob('*.html')))} fichiers HTML trouves")
    
    for f in html_files:
        print(f"    - {f.name} ({f.stat().st_size} bytes)")
    
    return True

def test_parser():
    """Tester le parser sur un vrai fichier"""
    print("\n3. TEST DU PARSER")
    
    try:
        from parsers.mobiletrans_parser import MobileTransParser
        parser = MobileTransParser()
        print("  [OK] Parser cree")
        
        # Fichier de test
        test_file = Path("C:/Users/Moham/Downloads/iPhone_20250605021808/WhatsApp/+1 (418) 550-4053.html")
        
        if not test_file.exists():
            print(f"  [ERROR] Fichier test non trouve: {test_file}")
            return False
        
        print(f"  [TEST] Fichier: {test_file.name}")
        
        # Validation
        is_valid = parser.validate_file(test_file)
        print(f"  [VALIDATION] {is_valid}")
        
        if not is_valid:
            print("  [ERROR] Fichier non valide pour le parser")
            return False
        
        # Parsing
        try:
            contact_messages = parser.parse(test_file)
            print(f"  [PARSING] Succes")
            
            for contact, messages in contact_messages.items():
                print(f"    Contact: {contact}")
                print(f"    Messages: {len(messages)}")
                
                if messages:
                    msg = messages[0]
                    print(f"    Premier message: {msg.content[:50]}...")
                    
        except Exception as e:
            print(f"  [ERROR] Parsing: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"  [ERROR] Parser test: {e}")
        return False
    
    return True

def test_exporters():
    """Tester les exporters"""
    print("\n4. TEST DES EXPORTERS")
    
    try:
        from exporters.csv_exporter import CSVExporter
        from exporters.json_exporter import JSONExporter
        
        # Données de test
        test_data = [{
            'contact_name': 'Test Contact',
            'message_id': '123',
            'timestamp': '2025-07-16T12:00:00',
            'direction': 'sent',
            'message_type': 'text',
            'content': 'Test message',
            'media_path': '',
            'file_source': 'test.html'
        }]
        
        # Test CSV
        csv_exp = CSVExporter()
        csv_file = Path("test_export.csv")
        
        if csv_exp.export(test_data, csv_file):
            print(f"  [OK] CSV export ({csv_file.stat().st_size} bytes)")
            csv_file.unlink()  # Cleanup
        else:
            print("  [ERROR] CSV export failed")
            
        # Test JSON
        json_exp = JSONExporter()
        json_file = Path("test_export.json")
        
        if json_exp.export(test_data, json_file):
            print(f"  [OK] JSON export ({json_file.stat().st_size} bytes)")
            json_file.unlink()  # Cleanup
        else:
            print("  [ERROR] JSON export failed")
            
    except Exception as e:
        print(f"  [ERROR] Exporter test: {e}")
        return False
        
    return True

def test_full_workflow():
    """Tester le workflow complet"""
    print("\n5. TEST DU WORKFLOW COMPLET")
    
    try:
        from parsers.mobiletrans_parser import MobileTransParser
        from exporters.csv_exporter import CSVExporter
        from exporters.json_exporter import JSONExporter
        from utils.advanced_logger import init_logger
        
        # Logger
        logger = init_logger(Path("logs"))
        print("  [OK] Logger initialise")
        
        # Parser
        parser = MobileTransParser()
        
        # Fichiers de test
        test_files = [
            "C:/Users/Moham/Downloads/iPhone_20250605021808/WhatsApp/+1 (418) 550-4053.html",
            "C:/Users/Moham/Downloads/iPhone_20250605021808/WhatsApp/+1 (438) 304-7483.html"
        ]
        
        all_messages = []
        total_parsed = 0
        
        for file_path in test_files:
            file_obj = Path(file_path)
            
            if not file_obj.exists():
                print(f"  [SKIP] Fichier non trouve: {file_obj.name}")
                continue
                
            print(f"  [PARSING] {file_obj.name}")
            
            try:
                if parser.validate_file(file_obj):
                    contact_messages = parser.parse(file_obj)
                    
                    for contact, messages in contact_messages.items():
                        print(f"    -> {contact}: {len(messages)} messages")
                        total_parsed += len(messages)
                        
                        # Ajouter pour export
                        for msg in messages:
                            all_messages.append({
                                'contact_name': contact,
                                'message_id': msg.id,
                                'timestamp': msg.timestamp.isoformat() if msg.timestamp else '',
                                'direction': msg.direction.value if hasattr(msg.direction, 'value') else str(msg.direction),
                                'content': msg.content,
                                'file_source': file_obj.name
                            })
                            
            except Exception as e:
                print(f"    [ERROR] {e}")
                
        print(f"  [TOTAL] {total_parsed} messages parses")
        
        # Export
        if all_messages:
            output_dir = Path("debug_exports")
            output_dir.mkdir(exist_ok=True)
            
            # CSV
            csv_file = output_dir / "debug_workflow.csv"
            csv_exp = CSVExporter()
            if csv_exp.export(all_messages, csv_file):
                print(f"  [EXPORT] CSV: {csv_file} ({csv_file.stat().st_size} bytes)")
            
            # JSON
            json_file = output_dir / "debug_workflow.json"
            json_exp = JSONExporter()
            if json_exp.export(all_messages, json_file):
                print(f"  [EXPORT] JSON: {json_file} ({json_file.stat().st_size} bytes)")
                
            print(f"  [OK] Exports sauvegardes dans: {output_dir}")
        
        logger.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_components():
    """Tester les composants GUI"""
    print("\n6. TEST DES COMPOSANTS GUI")
    
    try:
        import tkinter as tk
        print("  [OK] Tkinter disponible")
        
        # Test création fenêtre
        root = tk.Tk()
        root.withdraw()  # Ne pas afficher
        print("  [OK] Creation fenetre")
        root.destroy()
        
    except Exception as e:
        print(f"  [ERROR] GUI: {e}")
        return False
        
    return True

def main():
    """Exécuter tous les tests"""
    print("\nDEBUG: Execution de tous les tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("File Access", test_file_access),
        ("Parser", test_parser),
        ("Exporters", test_exporters),
        ("Full Workflow", test_full_workflow),
        ("GUI Components", test_gui_components)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            result = test_func()
            results[test_name] = result
            print(f"\n[{'OK' if result else 'FAILED'}] {test_name}")
        except Exception as e:
            print(f"\n[CRASH] {test_name}: {e}")
            results[test_name] = False
    
    # Résumé
    print("\n\n=== RESUME DES TESTS ===")
    for test_name, result in results.items():
        status = "OK" if result else "FAILED"
        print(f"  [{status}] {test_name}")
    
    success_count = sum(1 for r in results.values() if r)
    print(f"\nTotal: {success_count}/{len(tests)} tests passes")
    
    if success_count < len(tests):
        print("\n[ATTENTION] Des problemes ont ete detectes!")
        print("Verifiez les messages d'erreur ci-dessus.")
    else:
        print("\n[SUCCESS] Tous les tests sont passes!")
        print("Le workflow devrait fonctionner correctement.")

if __name__ == "__main__":
    main()
    print("\nAppuyez sur Entree pour terminer...")
    input()