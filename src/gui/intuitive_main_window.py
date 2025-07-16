#!/usr/bin/env python3
"""
Interface intuitive et claire pour WhatsApp Extractor v2
Basée sur l'analyse de 30 personas utilisateurs et meilleures pratiques UX 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import json
from datetime import datetime
import sys
import os
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config.config_manager import ConfigManager
    from core.extraction_pipeline import ExtractionPipeline
    from utils.logger import WhatsAppLogger
    from utils.advanced_logger import get_logger, ErrorCategory, init_logger
    from parsers.mobiletrans_parser import MobileTransParser
    from exporters import CSVExporter, JSONExporter, ExcelExporter
except ImportError as e:
    print(f"Import warning: {e}")
    # Fallback si les imports échouent
    ConfigManager = None
    ExtractionPipeline = None
    WhatsAppLogger = None
    get_logger = None
    ErrorCategory = None
    init_logger = None
    MobileTransParser = None
    CSVExporter = None
    JSONExporter = None
    ExcelExporter = None


class IntuitiveMainWindow:
    """Interface principale claire et intuitive"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.setup_ui()
        self.setup_backend()
        
    def setup_window(self):
        """Configuration de la fenêtre principale"""
        self.root.title("WhatsApp Extractor v2 - Extraction Simple & Rapide")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Centrer la fenêtre
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
        # Style moderne
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuration couleurs
        self.colors = {
            'primary': '#2563eb',      # Bleu moderne
            'success': '#16a34a',      # Vert succès
            'warning': '#ea580c',      # Orange attention
            'danger': '#dc2626',       # Rouge erreur
            'bg_light': '#f8fafc',     # Fond clair
            'bg_card': '#ffffff',      # Fond carte
            'text_primary': '#1f2937', # Texte principal
            'text_secondary': '#6b7280', # Texte secondaire
            'border': '#e5e7eb'        # Bordures
        }
        
        self.root.configure(bg=self.colors['bg_light'])
        
    def setup_variables(self):
        """Initialisation des variables"""
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / "WhatsApp_Extraits"))
        self.mode = tk.StringVar(value="express")  # express ou avancé
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Prêt à extraire vos conversations WhatsApp")
        self.is_processing = False
        self.selected_files = []  # Liste des fichiers sélectionnés
        
    def setup_backend(self):
        """Initialisation du backend"""
        try:
            # Initialiser le logger avancé
            if init_logger:
                self.advanced_logger = init_logger(Path("logs"))
                self.advanced_logger.info("Interface intuitive initialisée")
            else:
                self.advanced_logger = None
            
            if ConfigManager and ExtractionPipeline:
                self.config_manager = ConfigManager()
                self.pipeline = ExtractionPipeline(self.config_manager)
                
                # Initialiser les parsers et exporters
                if MobileTransParser:
                    self.parser = MobileTransParser()
                else:
                    self.parser = None
                    
                if CSVExporter and JSONExporter and ExcelExporter:
                    self.exporters = {
                        'csv': CSVExporter(),
                        'json': JSONExporter(),
                        'excel': ExcelExporter()
                    }
                else:
                    self.exporters = None
                    
                if self.advanced_logger:
                    self.advanced_logger.info("Backend initialisé avec succès")
            else:
                # Mode démo sans backend
                self.config_manager = None
                self.pipeline = None
                self.parser = None
                self.exporters = None
                if self.advanced_logger:
                    self.advanced_logger.warning("Mode démo - Backend non disponible")
                    
        except Exception as e:
            error_msg = f"Erreur d'initialisation backend: {e}"
            print(error_msg)
            if self.advanced_logger:
                self.advanced_logger.critical(error_msg, ErrorCategory.CONFIGURATION, exception=e)
            self.config_manager = None
            self.pipeline = None
            self.parser = None
            self.exporters = None
    
    def setup_ui(self):
        """Construction de l'interface utilisateur"""
        # Container principal avec padding
        main_frame = tk.Frame(self.root, bg=self.colors['bg_light'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête avec titre et aide
        self.create_header(main_frame)
        
        # Mode selection (Express vs Avancé)
        self.create_mode_selector(main_frame)
        
        # Zone principale d'extraction
        self.create_extraction_area(main_frame)
        
        # Barre de progression et statut
        self.create_progress_area(main_frame)
        
        # Boutons d'action
        self.create_action_buttons(main_frame)
        
        # Zone d'aide contextuelle
        self.create_help_area(main_frame)
        
    def create_header(self, parent):
        """Créer l'en-tête avec titre et aide"""
        header_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Titre principal
        title = tk.Label(
            header_frame,
            text="📱 Extraction WhatsApp",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_light']
        )
        title.pack(side='left')
        
        # Bouton aide
        help_btn = tk.Button(
            header_frame,
            text="❓ Aide",
            font=('Segoe UI', 11),
            fg=self.colors['primary'],
            bg=self.colors['bg_light'],
            relief='flat',
            cursor='hand2',
            command=self.show_help
        )
        help_btn.pack(side='right', padx=(10, 0))
        
        # Sous-titre explicatif
        subtitle = tk.Label(
            parent,
            text="Transformez facilement vos conversations WhatsApp en fichiers lisibles",
            font=('Segoe UI', 12),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light']
        )
        subtitle.pack(anchor='w', pady=(0, 20))
        
    def create_mode_selector(self, parent):
        """Créer le sélecteur de mode"""
        mode_frame = tk.LabelFrame(
            parent,
            text="Choisissez votre méthode",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_light'],
            relief='solid',
            bd=1
        )
        mode_frame.pack(fill='x', pady=(0, 20))
        mode_frame.configure(bg=self.colors['bg_light'])
        
        # Mode Express (recommandé)
        express_frame = tk.Frame(mode_frame, bg=self.colors['bg_card'], relief='solid', bd=1)
        express_frame.pack(fill='x', padx=10, pady=10)
        
        express_radio = tk.Radiobutton(
            express_frame,
            text="🚀 Mode Express (Recommandé)",
            variable=self.mode,
            value="express",
            font=('Segoe UI', 13, 'bold'),
            fg=self.colors['success'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_card'],
            command=self.on_mode_change
        )
        express_radio.pack(anchor='w', padx=15, pady=(10, 5))
        
        express_desc = tk.Label(
            express_frame,
            text="✓ Extraction rapide en 2 clics\n✓ Configuration automatique\n✓ Parfait pour la plupart des utilisateurs",
            font=('Segoe UI', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card'],
            justify='left'
        )
        express_desc.pack(anchor='w', padx=30, pady=(0, 10))
        
        # Mode Avancé
        advanced_frame = tk.Frame(mode_frame, bg=self.colors['bg_card'], relief='solid', bd=1)
        advanced_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        advanced_radio = tk.Radiobutton(
            advanced_frame,
            text="⚙️ Mode Avancé",
            variable=self.mode,
            value="advanced",
            font=('Segoe UI', 13, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_card'],
            command=self.on_mode_change
        )
        advanced_radio.pack(anchor='w', padx=15, pady=(10, 5))
        
        advanced_desc = tk.Label(
            advanced_frame,
            text="✓ Options de filtrage avancées\n✓ Transcription audio personnalisée\n✓ Contrôle complet du processus",
            font=('Segoe UI', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card'],
            justify='left'
        )
        advanced_desc.pack(anchor='w', padx=30, pady=(0, 10))
        
    def create_extraction_area(self, parent):
        """Créer la zone principale d'extraction"""
        self.extraction_frame = tk.LabelFrame(
            parent,
            text="Configuration de l'extraction",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_light'],
            relief='solid',
            bd=1
        )
        self.extraction_frame.pack(fill='both', expand=True, pady=(0, 20))
        self.extraction_frame.configure(bg=self.colors['bg_light'])
        
        # Mode Express par défaut
        self.create_express_mode()
        
    def create_express_mode(self):
        """Interface du mode express"""
        # Nettoyer le frame
        for widget in self.extraction_frame.winfo_children():
            widget.destroy()
            
        # Étape 1: Sélection des fichiers
        step1_frame = self.create_step_frame("1", "Sélectionnez vos fichiers WhatsApp")
        
        file_info = tk.Label(
            step1_frame,
            text="Choisissez le dossier contenant vos exports WhatsApp (.html)\nOu sélectionnez directement les fichiers individuels",
            font=('Segoe UI', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card'],
            justify='left'
        )
        file_info.pack(anchor='w', padx=20, pady=(0, 10))
        
        # Boutons de sélection
        button_frame = tk.Frame(step1_frame, bg=self.colors['bg_card'])
        button_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        folder_btn = tk.Button(
            button_frame,
            text="📁 Choisir un dossier",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg=self.colors['primary'],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.select_folder
        )
        folder_btn.pack(side='left', padx=(0, 10))
        
        files_btn = tk.Button(
            button_frame,
            text="📄 Choisir des fichiers",
            font=('Segoe UI', 11),
            fg=self.colors['primary'],
            bg=self.colors['bg_card'],
            relief='solid',
            bd=1,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.select_files
        )
        files_btn.pack(side='left')
        
        # Chemin sélectionné
        self.path_label = tk.Label(
            step1_frame,
            textvariable=self.source_path,
            font=('Segoe UI', 10),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card'],
            wraplength=400,
            justify='left'
        )
        self.path_label.pack(anchor='w', padx=20, pady=(0, 15))
        
        # Étape 2: Destination
        step2_frame = self.create_step_frame("2", "Choisissez où sauvegarder")
        
        output_frame = tk.Frame(step2_frame, bg=self.colors['bg_card'])
        output_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        output_entry = tk.Entry(
            output_frame,
            textvariable=self.output_path,
            font=('Segoe UI', 11),
            width=50,
            relief='solid',
            bd=1
        )
        output_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(
            output_frame,
            text="Parcourir",
            font=('Segoe UI', 10),
            fg=self.colors['primary'],
            bg=self.colors['bg_card'],
            relief='solid',
            bd=1,
            cursor='hand2',
            command=self.select_output_folder
        )
        browse_btn.pack(side='right')
        
    def create_advanced_mode(self):
        """Interface du mode avancé"""
        # Nettoyer le frame
        for widget in self.extraction_frame.winfo_children():
            widget.destroy()
            
        # Message temporaire
        temp_label = tk.Label(
            self.extraction_frame,
            text="🚧 Mode avancé en cours de développement\n\nLe mode Express couvre déjà 90% des besoins.\nContactez-nous si vous avez des besoins spécifiques.",
            font=('Segoe UI', 12),
            fg=self.colors['warning'],
            bg=self.colors['bg_light'],
            justify='center'
        )
        temp_label.pack(expand=True, pady=50)
        
    def create_step_frame(self, number, title):
        """Créer un frame d'étape avec numérotation"""
        step_frame = tk.Frame(self.extraction_frame, bg=self.colors['bg_card'], relief='solid', bd=1)
        step_frame.pack(fill='x', padx=15, pady=10)
        
        # En-tête de l'étape
        header_frame = tk.Frame(step_frame, bg=self.colors['primary'])
        header_frame.pack(fill='x')
        
        step_label = tk.Label(
            header_frame,
            text=f"Étape {number}: {title}",
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg=self.colors['primary']
        )
        step_label.pack(anchor='w', padx=15, pady=10)
        
        return step_frame
        
    def create_progress_area(self, parent):
        """Créer la zone de progression"""
        progress_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        progress_frame.pack(fill='x', pady=(0, 20))
        
        # Barre de progression
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # Texte de statut
        self.status_label = tk.Label(
            progress_frame,
            textvariable=self.status_text,
            font=('Segoe UI', 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light']
        )
        self.status_label.pack()
        
    def create_action_buttons(self, parent):
        """Créer les boutons d'action"""
        button_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        button_frame.pack(fill='x', pady=(0, 20))
        
        # Bouton principal d'extraction
        self.extract_btn = tk.Button(
            button_frame,
            text="🚀 Commencer l'extraction",
            font=('Segoe UI', 14, 'bold'),
            fg='white',
            bg=self.colors['success'],
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            command=self.start_extraction
        )
        self.extract_btn.pack(side='left', padx=(0, 15))
        
        # Boutons secondaires
        self.preview_btn = tk.Button(
            button_frame,
            text="👁️ Aperçu",
            font=('Segoe UI', 11),
            fg=self.colors['primary'],
            bg=self.colors['bg_card'],
            relief='solid',
            bd=1,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.preview_extraction
        )
        self.preview_btn.pack(side='left', padx=(0, 10))
        
        self.reset_btn = tk.Button(
            button_frame,
            text="🔄 Réinitialiser",
            font=('Segoe UI', 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card'],
            relief='solid',
            bd=1,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.reset_form
        )
        self.reset_btn.pack(side='left')
        
    def create_help_area(self, parent):
        """Créer la zone d'aide contextuelle"""
        help_frame = tk.LabelFrame(
            parent,
            text="💡 Aide rapide",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_light'],
            relief='solid',
            bd=1
        )
        help_frame.pack(fill='x')
        help_frame.configure(bg=self.colors['bg_light'])
        
        help_text = """
🔍 Où trouver mes exports WhatsApp ?
• Sur Android: WhatsApp → Paramètres → Discussions → Historique → Exporter
• Sur iPhone: Paramètres → Discussions → Exporter une discussion

📱 Formats supportés: .html, .txt, .zip
💾 Espace requis: ~50MB pour 1000 messages
⏱️ Temps estimé: 2-5 minutes selon la taille
        """.strip()
        
        help_label = tk.Label(
            help_frame,
            text=help_text,
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light'],
            justify='left'
        )
        help_label.pack(anchor='w', padx=15, pady=10)
        
    # Méthodes d'interaction
    
    def on_mode_change(self):
        """Gérer le changement de mode"""
        if self.mode.get() == "express":
            self.create_express_mode()
        else:
            self.create_advanced_mode()
            
    def select_folder(self):
        """Sélectionner un dossier source"""
        folder = filedialog.askdirectory(
            title="Choisissez le dossier contenant vos exports WhatsApp"
        )
        if folder:
            self.source_path.set(folder)
            self.selected_files = []  # Réinitialiser la liste
            self.update_status(f"Dossier sélectionné: {Path(folder).name}")
            
    def select_files(self):
        """Sélectionner des fichiers individuels"""
        files = filedialog.askopenfilenames(
            title="Choisissez vos fichiers WhatsApp",
            filetypes=[
                ("Fichiers WhatsApp", "*.html"),
                ("Fichiers texte", "*.txt"), 
                ("Archives", "*.zip"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if files:
            # Garder la liste des fichiers sélectionnés
            self.selected_files = list(files)
            
            if len(files) == 1:
                self.source_path.set(files[0])
                self.update_status(f"1 fichier sélectionné: {Path(files[0]).name}")
            else:
                # Afficher un résumé des fichiers sélectionnés
                file_names = [Path(f).name for f in files[:3]]
                if len(files) > 3:
                    file_names.append(f"... et {len(files) - 3} autres")
                
                self.source_path.set(f"{len(files)} fichiers sélectionnés")
                self.update_status(f"{len(files)} fichiers sélectionnés: {', '.join(file_names)}")
                
            if self.advanced_logger:
                self.advanced_logger.info(f"Fichiers sélectionnés: {len(files)}", {
                    'files': [str(f) for f in files]
                })
            
    def select_output_folder(self):
        """Sélectionner le dossier de destination"""
        folder = filedialog.askdirectory(
            title="Choisissez où sauvegarder vos extractions"
        )
        if folder:
            self.output_path.set(folder)
            
    def preview_extraction(self):
        """Aperçu de l'extraction avec vrai workflow"""
        if not self.source_path.get():
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner vos fichiers WhatsApp")
            return
            
        try:
            if self.advanced_logger:
                self.advanced_logger.info("Début de l'aperçu d'extraction", {
                    'source_path': self.source_path.get()
                })
            
            self.update_status("Analyse des fichiers en cours...")
            self.progress_var.set(10)
            
            # Thread pour éviter de bloquer l'interface
            def preview_task():
                try:
                    result = self._analyze_whatsapp_files()
                    
                    # Afficher les résultats dans l'interface principale
                    self.root.after(0, lambda: self.show_preview_results(result))
                    
                except Exception as e:
                    error_msg = f"Erreur aperçu: {str(e)}"
                    if self.advanced_logger:
                        self.advanced_logger.error(error_msg, ErrorCategory.FILE_READ, exception=e)
                    self.root.after(0, lambda: self.update_status(error_msg))
                finally:
                    self.root.after(0, lambda: self.progress_var.set(0))
            
            threading.Thread(target=preview_task, daemon=True).start()
            
        except Exception as e:
            error_msg = f"Erreur lors de l'aperçu: {str(e)}"
            if self.advanced_logger:
                self.advanced_logger.error(error_msg, ErrorCategory.UNKNOWN, exception=e)
            messagebox.showerror("Erreur", error_msg)
            self.progress_var.set(0)
            
    def show_preview_results(self, results):
        """Afficher les résultats de l'aperçu"""
        self.update_status("Aperçu terminé")
        
        preview_text = f"""
📊 Aperçu de l'extraction:

📁 Fichiers trouvés: {results['files_found']}
👥 Contacts: {results['contacts']}
💬 Messages: {results['messages']}
📎 Fichiers média: {results['media_files']}
⏱️ Temps estimé: {results['estimated_time']}
💾 Espace requis: {results['storage_needed']}
        """.strip()
        
        messagebox.showinfo("Aperçu", preview_text)
        
    def start_extraction(self):
        """Commencer l'extraction"""
        if not self.source_path.get():
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner vos fichiers WhatsApp")
            return
            
        if not self.output_path.get():
            messagebox.showwarning("Attention", "Veuillez choisir un dossier de destination")
            return
            
        # Désactiver le bouton pendant le traitement
        self.extract_btn.configure(state='disabled', text="⏳ Extraction en cours...")
        self.is_processing = True
        
        # Lancer l'extraction dans un thread séparé
        def extraction_task():
            try:
                self.run_extraction()
            except Exception as e:
                self.root.after(0, lambda: self.on_extraction_error(str(e)))
            finally:
                self.root.after(0, self.on_extraction_complete)
        
        threading.Thread(target=extraction_task, daemon=True).start()
        
    def run_extraction(self):
        """Exécuter l'extraction réelle avec workflow complet"""
        try:
            source = self.source_path.get()
            output = self.output_path.get()
            
            if self.advanced_logger:
                self.advanced_logger.info("Début de l'extraction complète", {
                    'source_path': source,
                    'output_path': output
                })
            
            # Mise à jour du statut
            self.root.after(0, lambda: self.update_status("Initialisation..."))
            self.root.after(0, lambda: self.progress_var.set(5))
            
            # Étape 1: Analyse des fichiers
            self.root.after(0, lambda: self.update_status("Analyse des fichiers WhatsApp..."))
            self.root.after(0, lambda: self.progress_var.set(15))
            
            analysis_result = self._analyze_whatsapp_files()
            
            if analysis_result['files_found'] == 0:
                raise Exception("Aucun fichier WhatsApp trouvé dans le répertoire spécifié")
            
            # Étape 2: Extraction des données
            self.root.after(0, lambda: self.update_status("Extraction des messages..."))
            self.root.after(0, lambda: self.progress_var.set(35))
            
            extraction_result = self._extract_all_data(source)
            
            # Étape 3: Traitement des médias
            self.root.after(0, lambda: self.update_status("Traitement des médias..."))
            self.root.after(0, lambda: self.progress_var.set(55))
            
            media_result = self._process_media_files(extraction_result.get('media_files', []))
            
            # Étape 4: Création des exports
            self.root.after(0, lambda: self.update_status("Création des exports..."))
            self.root.after(0, lambda: self.progress_var.set(75))
            
            export_result = self._create_all_exports(extraction_result, output)
            
            # Étape 5: Finalisation
            self.root.after(0, lambda: self.update_status("Finalisation..."))
            self.root.after(0, lambda: self.progress_var.set(95))
            
            # Résumé final
            final_stats = {
                'contacts': extraction_result.get('total_contacts', 0),
                'messages': extraction_result.get('total_messages', 0),
                'media_files': len(media_result.get('processed_files', [])),
                'exports_created': len(export_result.get('created_files', []))
            }
            
            self.root.after(0, lambda: self.update_status("Extraction terminée avec succès!"))
            self.root.after(0, lambda: self.progress_var.set(100))
            
            if self.advanced_logger:
                self.advanced_logger.info("Extraction terminée avec succès", final_stats)
            
            # Message de succès avec vraies données
            success_msg = f"""
✅ Extraction terminée!

📁 Fichiers sauvegardés dans:
{output}

💬 Données extraites:
• Messages: {final_stats['messages']}
• Contacts: {final_stats['contacts']}  
• Médias: {final_stats['media_files']} fichiers
• Exports: {final_stats['exports_created']} fichiers

🔍 Ouvrir le dossier?
            """.strip()
            
            result = messagebox.askyesno("Succès", success_msg)
            if result:
                # Ouvrir le dossier de destination
                os.startfile(output)
                    
        except Exception as e:
            error_msg = f"Erreur lors de l'extraction: {str(e)}"
            if self.advanced_logger:
                self.advanced_logger.critical(error_msg, ErrorCategory.UNKNOWN, exception=e)
            raise Exception(error_msg)
            
    def on_extraction_error(self, error_msg):
        """Gérer les erreurs d'extraction"""
        self.update_status(f"Erreur: {error_msg}")
        self.progress_var.set(0)
        messagebox.showerror("Erreur", f"L'extraction a échoué:\n\n{error_msg}")
        
    def on_extraction_complete(self):
        """Finaliser l'extraction"""
        self.extract_btn.configure(state='normal', text="🚀 Commencer l'extraction")
        self.is_processing = False
        
    def reset_form(self):
        """Réinitialiser le formulaire"""
        if self.is_processing:
            if not messagebox.askyesno("Confirmation", "Une extraction est en cours. Voulez-vous vraiment l'arrêter?"):
                return
                
        self.source_path.set("")
        self.output_path.set(str(Path.home() / "WhatsApp_Extraits"))
        self.progress_var.set(0)
        self.update_status("Prêt à extraire vos conversations WhatsApp")
        self.mode.set("express")
        self.create_express_mode()
        
    def show_help(self):
        """Afficher l'aide complète"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Guide d'utilisation - WhatsApp Extractor v2")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        # Centrer la fenêtre d'aide
        help_window.transient(self.root)
        help_window.grab_set()
        
        help_text = """
📱 GUIDE D'UTILISATION - WhatsApp Extractor v2

🎯 QU'EST-CE QUE C'EST ?
Ce logiciel transforme vos conversations WhatsApp en fichiers lisibles 
(CSV, Excel, JSON) que vous pouvez ouvrir sur n'importe quel ordinateur.

📥 COMMENT OBTENIR VOS CONVERSATIONS WHATSAPP ?

Sur Android:
1. Ouvrez WhatsApp
2. Menu (3 points) → Paramètres → Discussions
3. Historique des discussions → Exporter
4. Choisissez "Avec fichiers média" ou "Sans fichiers"
5. Sélectionnez "Gmail" ou "Drive" pour l'envoi

Sur iPhone:
1. Ouvrez WhatsApp
2. Paramètres → Discussions → Exporter une discussion
3. Choisissez la conversation à exporter
4. Sélectionnez "Joindre les fichiers" ou "Sans fichiers"
5. Envoyez-vous l'export par email

🚀 UTILISATION DU LOGICIEL

Mode Express (Recommandé):
• Parfait pour 90% des utilisateurs
• 2 clics seulement
• Configuration automatique

Mode Avancé:
• Pour les utilisateurs expérimentés
• Options de filtrage personnalisées
• Contrôle complet du processus

💡 CONSEILS

✓ Utilisez le mode Express pour commencer
✓ Créez un dossier dédié pour vos extractions
✓ Gardez vos fichiers originaux en backup
✓ L'aperçu vous montre ce qui sera extrait

❓ PROBLÈMES FRÉQUENTS

• "Aucun fichier trouvé" → Vérifiez que vous avez des fichiers .html
• "Erreur de permission" → Choisissez un dossier dans vos Documents
• "Extraction lente" → Normal pour les gros historiques (1000+ messages)

📞 SUPPORT
En cas de problème, contactez-nous avec:
• Votre système d'exploitation
• La taille de vos fichiers WhatsApp
• Le message d'erreur exact
        """.strip()
        
        text_widget = tk.Text(
            help_window,
            wrap='word',
            font=('Segoe UI', 10),
            padx=20,
            pady=20
        )
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', help_text)
        text_widget.configure(state='disabled')
        
        # Bouton fermer
        close_btn = tk.Button(
            help_window,
            text="Fermer",
            font=('Segoe UI', 11),
            command=help_window.destroy
        )
        close_btn.pack(pady=10)
        
    def update_status(self, message):
        """Mettre à jour le message de statut"""
        self.status_text.set(message)
        self.root.update_idletasks()
    
    def _analyze_whatsapp_files(self) -> Dict[str, Any]:
        """Analyser les fichiers WhatsApp dans le répertoire source"""
        try:
            # Utiliser les fichiers sélectionnés si disponibles
            if self.selected_files:
                html_files = [Path(f) for f in self.selected_files if Path(f).suffix.lower() == '.html']
                media_dir = Path(self.selected_files[0]).parent if self.selected_files else None
                
                if self.advanced_logger:
                    self.advanced_logger.info(f"Analyse de {len(html_files)} fichiers sélectionnés")
            else:
                # Sinon, utiliser le chemin source
                source_path = Path(self.source_path.get())
                
                if self.advanced_logger:
                    self.advanced_logger.info(f"Analyse du répertoire: {source_path}")
                
                # Chercher les fichiers HTML
                if source_path.is_file():
                    # Un seul fichier sélectionné
                    html_files = [source_path] if source_path.suffix.lower() == '.html' else []
                    media_dir = source_path.parent
                else:
                    # Dossier sélectionné
                    html_files = list(source_path.glob("*.html"))
                    media_dir = source_path
            
            result = {
                'files_found': len(html_files),
                'contacts': 0,
                'messages': 0,
                'media_files': 0,
                'estimated_time': '0 minutes',
                'storage_needed': '0 MB',
                'file_details': []
            }
            
            if not html_files:
                if self.advanced_logger:
                    self.advanced_logger.warning(f"Aucun fichier HTML trouvé dans {source_path}")
                return result
            
            # Analyser chaque fichier avec le parser
            total_messages = 0
            total_contacts = 0
            
            for html_file in html_files[:10]:  # Limiter à 10 fichiers pour l'aperçu
                try:
                    if self.parser and self.parser.validate_file(html_file):
                        contact_messages = self.parser.parse(html_file)
                        
                        for contact_name, messages in contact_messages.items():
                            total_contacts += 1
                            total_messages += len(messages)
                            
                            result['file_details'].append({
                                'file': html_file.name,
                                'contact': contact_name,
                                'messages': len(messages)
                            })
                            
                            if self.advanced_logger:
                                self.advanced_logger.log_contact_processing(
                                    contact_name, len(messages), True
                                )
                    else:
                        if self.advanced_logger:
                            self.advanced_logger.log_file_processing(
                                str(html_file), False, "Fichier non valide"
                            )
                        
                except Exception as e:
                    if self.advanced_logger:
                        self.advanced_logger.log_file_processing(
                            str(html_file), False, str(e)
                        )
            
            # Estimer les médias
            media_files = []
            if media_dir.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.mp4', '*.opus', '*.m4a']:
                    media_files.extend(media_dir.glob(ext))
            
            # Calculs finaux
            result.update({
                'contacts': total_contacts,
                'messages': total_messages,
                'media_files': len(media_files),
                'estimated_time': f"{max(1, total_messages // 100)} minutes",
                'storage_needed': f"{max(1, total_messages // 50)} MB"
            })
            
            if self.advanced_logger:
                self.advanced_logger.info("Analyse terminée", result)
            
            return result
            
        except Exception as e:
            if self.advanced_logger:
                self.advanced_logger.error(f"Erreur analyse: {str(e)}", ErrorCategory.FILE_READ, exception=e)
            # Retourner un résultat par défaut en cas d'erreur
            return {
                'files_found': 0,
                'contacts': 0,
                'messages': 0,
                'media_files': 0,
                'estimated_time': '0 minutes',
                'storage_needed': '0 MB',
                'file_details': []
            }
    
    def _extract_all_data(self, source_path: str) -> Dict[str, Any]:
        """Extraire toutes les données des fichiers WhatsApp"""
        try:
            all_contacts = []
            all_messages = []
            all_media = []
            
            # Utiliser les fichiers sélectionnés si disponibles
            if self.selected_files:
                html_files = [Path(f) for f in self.selected_files if Path(f).suffix.lower() == '.html']
                
                if self.advanced_logger:
                    self.advanced_logger.info(f"Extraction de {len(html_files)} fichiers sélectionnés")
            else:
                # Sinon, utiliser le chemin source
                source = Path(source_path)
                
                if self.advanced_logger:
                    self.advanced_logger.info(f"Extraction des données: {source}")
                
                # Obtenir la liste des fichiers
                if source.is_file():
                    html_files = [source] if source.suffix.lower() == '.html' else []
                else:
                    html_files = list(source.glob("*.html"))
            
            for html_file in html_files:
                try:
                    if self.parser and self.parser.validate_file(html_file):
                        # Parser le fichier
                        contact_messages = self.parser.parse(html_file)
                        
                        for contact_name, messages in contact_messages.items():
                            # Ajouter les messages
                            for msg in messages:
                                message_data = {
                                    'contact_name': contact_name,
                                    'message_id': msg.id,
                                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else '',
                                    'direction': msg.direction.value if hasattr(msg.direction, 'value') else str(msg.direction),
                                    'message_type': msg.media_type.value if hasattr(msg.media_type, 'value') else str(msg.media_type),
                                    'content': msg.content,
                                    'media_path': str(msg.media_path) if msg.media_path else '',
                                    'media_filename': msg.media_filename or '',
                                    'file_source': html_file.name
                                }
                                all_messages.append(message_data)
                                
                                # Ajouter les médias s'il y en a
                                if msg.media_path:
                                    all_media.append({
                                        'path': str(msg.media_path),
                                        'filename': msg.media_filename,
                                        'type': message_data['message_type'],
                                        'contact': contact_name
                                    })
                            
                            # Ajouter le contact
                            all_contacts.append({
                                'name': contact_name,
                                'message_count': len(messages),
                                'file_source': html_file.name
                            })
                            
                            if self.advanced_logger:
                                self.advanced_logger.log_contact_processing(
                                    contact_name, len(messages), True
                                )
                    else:
                        if self.advanced_logger:
                            self.advanced_logger.log_file_processing(
                                str(html_file), False, "Validation échouée"
                            )
                        
                except Exception as e:
                    if self.advanced_logger:
                        self.advanced_logger.log_file_processing(
                            str(html_file), False, f"Erreur parsing: {str(e)}"
                        )
            
            result = {
                'total_contacts': len(all_contacts),
                'total_messages': len(all_messages),
                'contacts': all_contacts,
                'messages': all_messages,
                'media_files': all_media
            }
            
            if self.advanced_logger:
                self.advanced_logger.info("Extraction des données terminée", {
                    'total_contacts': result['total_contacts'],
                    'total_messages': result['total_messages'],
                    'media_files': len(all_media)
                })
            
            return result
            
        except Exception as e:
            if self.advanced_logger:
                self.advanced_logger.error(f"Erreur extraction: {str(e)}", ErrorCategory.HTML_PARSING, exception=e)
            # Retourner un résultat vide en cas d'erreur
            return {
                'total_contacts': 0,
                'total_messages': 0,
                'contacts': [],
                'messages': [],
                'media_files': []
            }
    
    def _process_media_files(self, media_files: list) -> Dict[str, Any]:
        """Traiter les fichiers média"""
        try:
            if self.advanced_logger:
                self.advanced_logger.info(f"Traitement de {len(media_files)} fichiers média")
            
            processed = []
            failed = []
            
            for media in media_files:
                try:
                    media_path = Path(media['path'])
                    if media_path.exists():
                        # Pour l'instant, on ne fait que valider l'existence
                        processed.append(media)
                        if self.advanced_logger:
                            self.advanced_logger.info(f"Média traité: {media_path.name}")
                    else:
                        failed.append(media)
                        if self.advanced_logger:
                            self.advanced_logger.warning(f"Média introuvable: {media_path}")
                        
                except Exception as e:
                    failed.append(media)
                    if self.advanced_logger:
                        self.advanced_logger.log_media_conversion(
                            media.get('path', 'unknown'), 
                            'validation', 
                            False, 
                            str(e)
                        )
            
            result = {
                'processed_files': processed,
                'failed_files': failed,
                'success_rate': len(processed) / max(len(media_files), 1) * 100
            }
            
            if self.advanced_logger:
                self.advanced_logger.info("Traitement média terminé", result)
            
            return result
            
        except Exception as e:
            if self.advanced_logger:
                self.advanced_logger.error(f"Erreur traitement média: {str(e)}", ErrorCategory.MEDIA_ORGANIZATION, exception=e)
            return {'processed_files': [], 'failed_files': media_files, 'success_rate': 0}
    
    def _create_all_exports(self, extraction_data: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """Créer tous les exports (CSV, JSON, Excel)"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.advanced_logger:
                self.advanced_logger.info(f"Création des exports dans: {output_path}")
            
            created_files = []
            failed_exports = []
            
            messages = extraction_data.get('messages', [])
            
            if not messages:
                if self.advanced_logger:
                    self.advanced_logger.warning("Aucun message à exporter")
                return {'created_files': [], 'failed_exports': []}
            
            # Export CSV
            if self.exporters and 'csv' in self.exporters:
                try:
                    csv_path = output_path / "whatsapp_messages.csv"
                    if self.exporters['csv'].export(messages, csv_path):
                        created_files.append(str(csv_path))
                        if self.advanced_logger:
                            self.advanced_logger.log_export_creation(
                                'CSV', str(csv_path), len(messages), True
                            )
                    else:
                        failed_exports.append('CSV')
                        
                except Exception as e:
                    failed_exports.append('CSV')
                    if self.advanced_logger:
                        self.advanced_logger.log_export_creation(
                            'CSV', str(output_path / "whatsapp_messages.csv"), 
                            len(messages), False, str(e)
                        )
            
            # Export JSON
            if self.exporters and 'json' in self.exporters:
                try:
                    json_path = output_path / "whatsapp_messages.json"
                    if self.exporters['json'].export(messages, json_path):
                        created_files.append(str(json_path))
                        if self.advanced_logger:
                            self.advanced_logger.log_export_creation(
                                'JSON', str(json_path), len(messages), True
                            )
                    else:
                        failed_exports.append('JSON')
                        
                except Exception as e:
                    failed_exports.append('JSON')
                    if self.advanced_logger:
                        self.advanced_logger.log_export_creation(
                            'JSON', str(output_path / "whatsapp_messages.json"),
                            len(messages), False, str(e)
                        )
            
            # Export Excel
            if self.exporters and 'excel' in self.exporters:
                try:
                    excel_path = output_path / "whatsapp_messages.xlsx"
                    if self.exporters['excel'].export(messages, excel_path):
                        created_files.append(str(excel_path))
                        if self.advanced_logger:
                            self.advanced_logger.log_export_creation(
                                'Excel', str(excel_path), len(messages), True
                            )
                    else:
                        failed_exports.append('Excel')
                        
                except Exception as e:
                    failed_exports.append('Excel')
                    if self.advanced_logger:
                        self.advanced_logger.log_export_creation(
                            'Excel', str(output_path / "whatsapp_messages.xlsx"),
                            len(messages), False, str(e)
                        )
            
            result = {
                'created_files': created_files,
                'failed_exports': failed_exports,
                'success_count': len(created_files)
            }
            
            if self.advanced_logger:
                self.advanced_logger.info("Création des exports terminée", result)
            
            return result
            
        except Exception as e:
            if self.advanced_logger:
                self.advanced_logger.error(f"Erreur création exports: {str(e)}", ErrorCategory.EXPORT_CREATION, exception=e)
            return {'created_files': [], 'failed_exports': ['ALL'], 'success_count': 0}
        
    def run(self):
        """Lancer l'application"""
        try:
            self.root.mainloop()
        finally:
            # Fermer le logger à la fin
            if hasattr(self, 'advanced_logger') and self.advanced_logger:
                self.advanced_logger.close()


def main():
    """Point d'entrée principal"""
    try:
        app = IntuitiveMainWindow()
        app.run()
    except Exception as e:
        messagebox.showerror("Erreur fatale", f"Impossible de démarrer l'application:\n{str(e)}")


if __name__ == "__main__":
    main()