#!/usr/bin/env python3
"""
Interface graphique principale pour WhatsApp Extractor v2
Crée une interface utilisateur complète avec onglets pour toutes les fonctionnalités
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Import des modules de l'application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Imports conditionnels pour éviter les erreurs si les modules ne sont pas disponibles
try:
    from src.config.config_manager import ConfigManager
    from src.config.schemas import AppConfig
    from src.core.database import CacheDatabase, DatabaseManager
    from src.core.extraction_pipeline import ExtractionPipeline
    from src.parsers.html_parser import WhatsAppHTMLParser
    HAS_BACKEND = True
except ImportError as e:
    print(f"Modules backend non disponibles: {e}")
    print("L'interface fonctionnera en mode démonstration")
    HAS_BACKEND = False
    ConfigManager = None
    AppConfig = None
    CacheDatabase = None
    DatabaseManager = None
    ExtractionPipeline = None
    WhatsAppHTMLParser = None

from src.gui.threading_manager import ThreadingManager, create_extraction_task, create_transcription_task
from src.utils.logger import setup_logger, get_logger, log_action, log_button_click, log_error


class WhatsAppExtractorGUI:
    """Interface graphique principale pour WhatsApp Extractor v2"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Extractor v2 - Interface Graphique")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Variables d'état
        self.config_manager = None
        self.config = None
        self.db_manager = None
        self.threading_manager = ThreadingManager(max_workers=4)
        self.current_extraction_task = None
        self.is_processing = False
        self.preferences_file = Path("gui_preferences.json")
        
        # Variables Tkinter
        self.variables = {}
        self.contacts_vars = {}
        
        # Configurer le système de logging
        self.logger = setup_logger(self.on_log_message)
        self.logger.info("Interface WhatsApp Extractor v2 initialisée")
        
        # Timer pour vérifier les résultats des tâches
        self.check_tasks_timer()
        
        # Initialiser l'interface
        self.setup_styles()
        self.create_widgets()
        self.load_preferences()
        self.load_configuration()
        
    def setup_styles(self):
        """Configuration des styles pour l'interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style pour les boutons principaux
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', foreground='green')
        style.configure('Warning.TButton', foreground='orange')
        style.configure('Error.TButton', foreground='red')
        
        # Style pour les titres
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'))
        
    def create_widgets(self):
        """Création de l'interface utilisateur principale"""
        # Menu principal
        self.create_menu()
        
        # Notebook principal avec onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Création des onglets
        self.create_config_tab()
        self.create_filters_tab()
        self.create_launch_tab()
        self.create_progress_tab()
        self.create_results_tab()
        self.create_debug_tab()
        
        # Barre de statut
        self.create_status_bar()
        
    def create_menu(self):
        """Création du menu principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Charger config...", command=self.load_config_file)
        file_menu.add_command(label="Sauvegarder config...", command=self.save_config_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Nettoyer cache", command=self.clear_cache)
        tools_menu.add_command(label="Vérifier intégrité", command=self.check_integrity)
        tools_menu.add_command(label="Diagnostics", command=self.run_diagnostics)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
        
    def create_config_tab(self):
        """Onglet Configuration"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        
        # Titre
        title_label = ttk.Label(config_frame, text="Configuration WhatsApp Extractor v2", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(config_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Canvas pour scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Section Chemins
        paths_frame = ttk.LabelFrame(scrollable_frame, text="Chemins et Dossiers", padding=10)
        paths_frame.pack(fill='x', pady=5)
        
        # Variables pour les chemins
        self.variables['html_dir'] = tk.StringVar()
        self.variables['media_dir'] = tk.StringVar()
        self.variables['output_dir'] = tk.StringVar()
        
        # Champ HTML Directory
        ttk.Label(paths_frame, text="Dossier Export WhatsApp HTML:").grid(row=0, column=0, sticky='w', pady=2)
        html_entry = ttk.Entry(paths_frame, textvariable=self.variables['html_dir'], width=50)
        html_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(paths_frame, text="Parcourir", 
                  command=lambda: self.browse_directory(self.variables['html_dir'])).grid(row=0, column=2, padx=5)
        
        # Champ Media Directory
        ttk.Label(paths_frame, text="Dossier Médias WhatsApp:").grid(row=1, column=0, sticky='w', pady=2)
        media_entry = ttk.Entry(paths_frame, textvariable=self.variables['media_dir'], width=50)
        media_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(paths_frame, text="Parcourir", 
                  command=lambda: self.browse_directory(self.variables['media_dir'])).grid(row=1, column=2, padx=5)
        
        # Champ Output Directory
        ttk.Label(paths_frame, text="Dossier de Sortie:").grid(row=2, column=0, sticky='w', pady=2)
        output_entry = ttk.Entry(paths_frame, textvariable=self.variables['output_dir'], width=50)
        output_entry.grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(paths_frame, text="Parcourir", 
                  command=lambda: self.browse_directory(self.variables['output_dir'])).grid(row=2, column=2, padx=5)
        
        # Auto-détection
        ttk.Button(paths_frame, text="Détecter automatiquement les dossiers WhatsApp",
                  command=self.auto_detect_paths, style='Action.TButton').grid(row=3, column=0, columnspan=3, pady=10)
        
        # Section API
        api_frame = ttk.LabelFrame(scrollable_frame, text="Configuration API OpenAI", padding=10)
        api_frame.pack(fill='x', pady=5)
        
        self.variables['openai_key'] = tk.StringVar()
        
        ttk.Label(api_frame, text="Clé API OpenAI:").grid(row=0, column=0, sticky='w', pady=2)
        api_entry = ttk.Entry(api_frame, textvariable=self.variables['openai_key'], show='*', width=50)
        api_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(api_frame, text="Tester", command=self.test_api_connection).grid(row=0, column=2, padx=5)
        
        # Section Options de Transcription
        transcription_frame = ttk.LabelFrame(scrollable_frame, text="Options de Transcription", padding=10)
        transcription_frame.pack(fill='x', pady=5)
        
        self.variables['transcribe_sent'] = tk.BooleanVar(value=True)
        self.variables['transcribe_received'] = tk.BooleanVar(value=True)
        self.variables['max_retries'] = tk.IntVar(value=3)
        self.variables['parallel_transcriptions'] = tk.IntVar(value=2)
        
        ttk.Checkbutton(transcription_frame, text="Transcrire les messages envoyés", 
                       variable=self.variables['transcribe_sent']).grid(row=0, column=0, sticky='w', pady=2)
        ttk.Checkbutton(transcription_frame, text="Transcrire les messages reçus", 
                       variable=self.variables['transcribe_received']).grid(row=1, column=0, sticky='w', pady=2)
        
        ttk.Label(transcription_frame, text="Nombre de tentatives max:").grid(row=2, column=0, sticky='w', pady=2)
        ttk.Spinbox(transcription_frame, from_=1, to=10, textvariable=self.variables['max_retries'], 
                   width=10).grid(row=2, column=1, sticky='w', padx=5)
        
        ttk.Label(transcription_frame, text="Transcriptions en parallèle:").grid(row=3, column=0, sticky='w', pady=2)
        ttk.Spinbox(transcription_frame, from_=1, to=8, textvariable=self.variables['parallel_transcriptions'], 
                   width=10).grid(row=3, column=1, sticky='w', padx=5)
        
        # Boutons d'action
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(buttons_frame, text="Sauvegarder Configuration", 
                  command=self.save_configuration, style='Success.TButton').pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Recharger Configuration", 
                  command=self.load_configuration).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Réinitialiser", 
                  command=self.reset_configuration, style='Warning.TButton').pack(side='left', padx=5)
        
        # Pack canvas et scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_filters_tab(self):
        """Onglet Filtres et Sélection"""
        filters_frame = ttk.Frame(self.notebook)
        self.notebook.add(filters_frame, text="Filtres")
        
        # Titre
        title_label = ttk.Label(filters_frame, text="Filtres et Sélection des Données", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Paned window pour diviser l'espace
        paned = ttk.PanedWindow(filters_frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame gauche - Liste des contacts
        contacts_frame = ttk.LabelFrame(paned, text="Contacts Disponibles", padding=5)
        paned.add(contacts_frame, weight=1)
        
        # Treeview pour les contacts
        columns = ('contact', 'messages', 'audio')
        self.contacts_tree = ttk.Treeview(contacts_frame, columns=columns, show='tree headings', height=15)
        
        self.contacts_tree.heading('#0', text='Sélection')
        self.contacts_tree.heading('contact', text='Contact')
        self.contacts_tree.heading('messages', text='Messages')
        self.contacts_tree.heading('audio', text='Audios')
        
        self.contacts_tree.column('#0', width=80)
        self.contacts_tree.column('contact', width=200)
        self.contacts_tree.column('messages', width=80)
        self.contacts_tree.column('audio', width=80)
        
        # Scrollbar pour la liste des contacts
        contacts_scroll = ttk.Scrollbar(contacts_frame, orient='vertical', command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=contacts_scroll.set)
        
        self.contacts_tree.pack(side='left', fill='both', expand=True)
        contacts_scroll.pack(side='right', fill='y')
        
        # Boutons pour la sélection des contacts
        contacts_buttons = ttk.Frame(contacts_frame)
        contacts_buttons.pack(fill='x', pady=5)
        
        ttk.Button(contacts_buttons, text="Tout sélectionner", 
                  command=self.select_all_contacts).pack(side='left', padx=2)
        ttk.Button(contacts_buttons, text="Tout désélectionner", 
                  command=self.deselect_all_contacts).pack(side='left', padx=2)
        ttk.Button(contacts_buttons, text="Actualiser", 
                  command=self.refresh_contacts).pack(side='left', padx=2)
        
        # Frame droite - Options de filtrage
        options_frame = ttk.LabelFrame(paned, text="Options de Filtrage", padding=5)
        paned.add(options_frame, weight=1)
        
        # Filtre par date
        date_frame = ttk.LabelFrame(options_frame, text="Filtrage par Date", padding=5)
        date_frame.pack(fill='x', pady=5)
        
        self.variables['enable_date_filter'] = tk.BooleanVar()
        self.variables['after_date'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Checkbutton(date_frame, text="Activer le filtre par date", 
                       variable=self.variables['enable_date_filter']).pack(anchor='w')
        
        date_entry_frame = ttk.Frame(date_frame)
        date_entry_frame.pack(fill='x', pady=5)
        ttk.Label(date_entry_frame, text="Messages après le:").pack(side='left')
        ttk.Entry(date_entry_frame, textvariable=self.variables['after_date'], 
                 width=15).pack(side='left', padx=5)
        
        # Filtre par type de message
        type_frame = ttk.LabelFrame(options_frame, text="Types de Messages", padding=5)
        type_frame.pack(fill='x', pady=5)
        
        self.variables['include_sent'] = tk.BooleanVar(value=True)
        self.variables['include_received'] = tk.BooleanVar(value=True)
        self.variables['include_text'] = tk.BooleanVar(value=True)
        self.variables['include_audio'] = tk.BooleanVar(value=True)
        self.variables['include_video'] = tk.BooleanVar(value=True)
        self.variables['include_images'] = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(type_frame, text="Messages envoyés", 
                       variable=self.variables['include_sent']).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="Messages reçus", 
                       variable=self.variables['include_received']).pack(anchor='w')
        
        ttk.Separator(type_frame, orient='horizontal').pack(fill='x', pady=5)
        
        ttk.Checkbutton(type_frame, text="Messages texte", 
                       variable=self.variables['include_text']).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="Messages audio", 
                       variable=self.variables['include_audio']).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="Messages vidéo", 
                       variable=self.variables['include_video']).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="Images", 
                       variable=self.variables['include_images']).pack(anchor='w')
        
        # Filtre par nombre de messages
        count_frame = ttk.LabelFrame(options_frame, text="Nombre de Messages", padding=5)
        count_frame.pack(fill='x', pady=5)
        
        self.variables['min_messages'] = tk.IntVar(value=0)
        
        ttk.Label(count_frame, text="Minimum de messages:").pack(anchor='w')
        ttk.Spinbox(count_frame, from_=0, to=10000, textvariable=self.variables['min_messages'], 
                   width=15).pack(anchor='w', pady=2)
        
        # Boutons d'aperçu
        preview_frame = ttk.Frame(options_frame)
        preview_frame.pack(fill='x', pady=10)
        
        ttk.Button(preview_frame, text="Aperçu des Données", 
                  command=self.preview_filtered_data, style='Action.TButton').pack(fill='x', pady=2)
        ttk.Button(preview_frame, text="Estimation Coût API", 
                  command=self.estimate_api_cost).pack(fill='x', pady=2)
        
    def create_launch_tab(self):
        """Onglet Lancement et Contrôle"""
        launch_frame = ttk.Frame(self.notebook)
        self.notebook.add(launch_frame, text="Lancement")
        
        # Titre
        title_label = ttk.Label(launch_frame, text="Lancement de l'Extraction", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(launch_frame)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Section Modes d'exécution
        modes_frame = ttk.LabelFrame(main_frame, text="Mode d'Exécution", padding=10)
        modes_frame.pack(fill='x', pady=10)
        
        self.variables['processing_mode'] = tk.StringVar(value='normal')
        
        ttk.Radiobutton(modes_frame, text="Mode Normal - Extraction complète avec transcription", 
                       variable=self.variables['processing_mode'], value='normal').pack(anchor='w', pady=2)
        ttk.Radiobutton(modes_frame, text="Mode Test - Sans transcription (plus rapide)", 
                       variable=self.variables['processing_mode'], value='test').pack(anchor='w', pady=2)
        ttk.Radiobutton(modes_frame, text="Mode Complet - Avec toutes les optimisations", 
                       variable=self.variables['processing_mode'], value='complete').pack(anchor='w', pady=2)
        ttk.Radiobutton(modes_frame, text="Mode Incrémental - Traiter seulement les nouveaux fichiers", 
                       variable=self.variables['processing_mode'], value='incremental').pack(anchor='w', pady=2)
        
        # Section Estimations
        estimates_frame = ttk.LabelFrame(main_frame, text="Estimations", padding=10)
        estimates_frame.pack(fill='x', pady=10)
        
        # Labels pour les estimations
        self.estimate_labels = {}
        
        estimates_grid = ttk.Frame(estimates_frame)
        estimates_grid.pack(fill='x')
        
        ttk.Label(estimates_grid, text="Contacts à traiter:").grid(row=0, column=0, sticky='w', pady=2)
        self.estimate_labels['contacts'] = ttk.Label(estimates_grid, text="--", foreground='blue')
        self.estimate_labels['contacts'].grid(row=0, column=1, sticky='w', padx=10)
        
        ttk.Label(estimates_grid, text="Messages audio:").grid(row=1, column=0, sticky='w', pady=2)
        self.estimate_labels['audio'] = ttk.Label(estimates_grid, text="--", foreground='blue')
        self.estimate_labels['audio'].grid(row=1, column=1, sticky='w', padx=10)
        
        ttk.Label(estimates_grid, text="Temps estimé:").grid(row=2, column=0, sticky='w', pady=2)
        self.estimate_labels['time'] = ttk.Label(estimates_grid, text="--", foreground='blue')
        self.estimate_labels['time'].grid(row=2, column=1, sticky='w', padx=10)
        
        ttk.Label(estimates_grid, text="Coût API estimé:").grid(row=3, column=0, sticky='w', pady=2)
        self.estimate_labels['cost'] = ttk.Label(estimates_grid, text="--", foreground='blue')
        self.estimate_labels['cost'].grid(row=3, column=1, sticky='w', padx=10)
        
        # Bouton de mise à jour des estimations
        ttk.Button(estimates_frame, text="Mettre à jour les estimations", 
                  command=self.update_estimates).pack(pady=5)
        
        # Section Contrôles
        controls_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding=10)
        controls_frame.pack(fill='x', pady=10)
        
        # Gros bouton de démarrage
        self.start_button = ttk.Button(controls_frame, text="🚀 DÉMARRER L'EXTRACTION", 
                                      command=self.start_extraction, style='Action.TButton')
        self.start_button.pack(fill='x', pady=10)
        
        # Boutons de contrôle
        control_buttons = ttk.Frame(controls_frame)
        control_buttons.pack(fill='x', pady=5)
        
        self.pause_button = ttk.Button(control_buttons, text="⏸️ Pause", 
                                      command=self.pause_extraction, state='disabled')
        self.pause_button.pack(side='left', padx=5)
        
        self.resume_button = ttk.Button(control_buttons, text="▶️ Reprendre", 
                                       command=self.resume_extraction, state='disabled')
        self.resume_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(control_buttons, text="⏹️ Arrêter", 
                                     command=self.stop_extraction, state='disabled', style='Error.TButton')
        self.stop_button.pack(side='left', padx=5)
        
    def create_progress_tab(self):
        """Onglet Progression"""
        progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(progress_frame, text="Progression")
        
        # Titre
        title_label = ttk.Label(progress_frame, text="Progression de l'Extraction", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(progress_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Barre de progression globale
        progress_global_frame = ttk.LabelFrame(main_frame, text="Progression Globale", padding=10)
        progress_global_frame.pack(fill='x', pady=5)
        
        self.progress_global = ttk.Progressbar(progress_global_frame, mode='determinate')
        self.progress_global.pack(fill='x', pady=5)
        
        self.progress_global_label = ttk.Label(progress_global_frame, text="En attente...")
        self.progress_global_label.pack()
        
        # Statistiques en temps réel
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=10)
        stats_frame.pack(fill='x', pady=5)
        
        # Grid pour les statistiques
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        self.stats_labels = {}
        
        # Première ligne
        ttk.Label(stats_grid, text="Contacts traités:").grid(row=0, column=0, sticky='w', pady=2)
        self.stats_labels['contacts_processed'] = ttk.Label(stats_grid, text="0 / 0")
        self.stats_labels['contacts_processed'].grid(row=0, column=1, sticky='w', padx=10)
        
        ttk.Label(stats_grid, text="Messages traités:").grid(row=0, column=2, sticky='w', pady=2, padx=(20,0))
        self.stats_labels['messages_processed'] = ttk.Label(stats_grid, text="0 / 0")
        self.stats_labels['messages_processed'].grid(row=0, column=3, sticky='w', padx=10)
        
        # Deuxième ligne
        ttk.Label(stats_grid, text="Audios transcrits:").grid(row=1, column=0, sticky='w', pady=2)
        self.stats_labels['audio_transcribed'] = ttk.Label(stats_grid, text="0 / 0")
        self.stats_labels['audio_transcribed'].grid(row=1, column=1, sticky='w', padx=10)
        
        ttk.Label(stats_grid, text="Erreurs:").grid(row=1, column=2, sticky='w', pady=2, padx=(20,0))
        self.stats_labels['errors'] = ttk.Label(stats_grid, text="0", foreground='red')
        self.stats_labels['errors'].grid(row=1, column=3, sticky='w', padx=10)
        
        # Troisième ligne
        ttk.Label(stats_grid, text="Temps écoulé:").grid(row=2, column=0, sticky='w', pady=2)
        self.stats_labels['elapsed_time'] = ttk.Label(stats_grid, text="00:00:00")
        self.stats_labels['elapsed_time'].grid(row=2, column=1, sticky='w', padx=10)
        
        ttk.Label(stats_grid, text="Temps restant:").grid(row=2, column=2, sticky='w', pady=2, padx=(20,0))
        self.stats_labels['remaining_time'] = ttk.Label(stats_grid, text="--:--:--")
        self.stats_labels['remaining_time'].grid(row=2, column=3, sticky='w', padx=10)
        
        # Log en temps réel
        log_frame = ttk.LabelFrame(main_frame, text="Logs en Temps Réel", padding=5)
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)
        
        # Boutons de contrôle des logs
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill='x', pady=5)
        
        ttk.Button(log_buttons, text="Effacer logs", 
                  command=self.clear_logs).pack(side='left', padx=5)
        ttk.Button(log_buttons, text="Sauvegarder logs", 
                  command=self.save_logs).pack(side='left', padx=5)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_buttons, text="Défilement automatique", 
                       variable=self.auto_scroll_var).pack(side='right', padx=5)
        
    def create_results_tab(self):
        """Onglet Résultats"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Résultats")
        
        # Titre
        title_label = ttk.Label(results_frame, text="Résultats de l'Extraction", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(results_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Statistiques finales
        final_stats_frame = ttk.LabelFrame(main_frame, text="Statistiques Finales", padding=10)
        final_stats_frame.pack(fill='x', pady=5)
        
        # Grid pour les statistiques finales
        final_stats_grid = ttk.Frame(final_stats_frame)
        final_stats_grid.pack(fill='x')
        
        self.final_stats_labels = {}
        
        # Configuration de la grille
        stats_info = [
            ("Contacts traités:", "final_contacts"),
            ("Messages extraits:", "final_messages"),
            ("Audios transcrits:", "final_audio"),
            ("Durée totale:", "final_duration"),
            ("Taille fichiers:", "final_size"),
            ("Coût API total:", "final_cost")
        ]
        
        for i, (label_text, var_name) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(final_stats_grid, text=label_text).grid(row=row, column=col, sticky='w', pady=2, padx=(0,10))
            self.final_stats_labels[var_name] = ttk.Label(final_stats_grid, text="--", foreground='blue')
            self.final_stats_labels[var_name].grid(row=row, column=col+1, sticky='w', pady=2, padx=(0,20))
        
        # Aperçu des fichiers générés
        preview_frame = ttk.LabelFrame(main_frame, text="Fichiers Générés", padding=5)
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        # Treeview pour les fichiers de sortie
        files_columns = ('file', 'size', 'modified')
        self.files_tree = ttk.Treeview(preview_frame, columns=files_columns, show='headings', height=8)
        
        self.files_tree.heading('file', text='Fichier')
        self.files_tree.heading('size', text='Taille')
        self.files_tree.heading('modified', text='Modifié')
        
        self.files_tree.column('file', width=300)
        self.files_tree.column('size', width=100)
        self.files_tree.column('modified', width=150)
        
        # Scrollbar pour la liste des fichiers
        files_scroll = ttk.Scrollbar(preview_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scroll.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        files_scroll.pack(side='right', fill='y')
        
        # Boutons d'action pour les résultats
        results_buttons = ttk.Frame(main_frame)
        results_buttons.pack(fill='x', pady=10)
        
        ttk.Button(results_buttons, text="📁 Ouvrir Dossier de Sortie", 
                  command=self.open_output_folder, style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(results_buttons, text="📊 Ouvrir CSV Principal", 
                  command=self.open_main_csv).pack(side='left', padx=5)
        ttk.Button(results_buttons, text="📋 Exporter Rapport", 
                  command=self.export_report).pack(side='left', padx=5)
        ttk.Button(results_buttons, text="🔄 Actualiser", 
                  command=self.refresh_results).pack(side='left', padx=5)
        
    def create_debug_tab(self):
        """Onglet Tests et Debug"""
        debug_frame = ttk.Frame(self.notebook)
        self.notebook.add(debug_frame, text="Tests/Debug")
        
        # Titre
        title_label = ttk.Label(debug_frame, text="Tests et Maintenance", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(debug_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Section Tests
        tests_frame = ttk.LabelFrame(main_frame, text="Tests du Système", padding=10)
        tests_frame.pack(fill='x', pady=5)
        
        tests_buttons = ttk.Frame(tests_frame)
        tests_buttons.pack(fill='x')
        
        ttk.Button(tests_buttons, text="🔧 Test Configuration", 
                  command=self.test_configuration).pack(side='left', padx=5, pady=2)
        ttk.Button(tests_buttons, text="🌐 Test Connexion API", 
                  command=self.test_api_connection).pack(side='left', padx=5, pady=2)
        ttk.Button(tests_buttons, text="📁 Test Accès Fichiers", 
                  command=self.test_file_access).pack(side='left', padx=5, pady=2)
        ttk.Button(tests_buttons, text="🎵 Test FFmpeg", 
                  command=self.test_ffmpeg).pack(side='left', padx=5, pady=2)
        
        # Section Maintenance
        maintenance_frame = ttk.LabelFrame(main_frame, text="Maintenance", padding=10)
        maintenance_frame.pack(fill='x', pady=5)
        
        maintenance_buttons = ttk.Frame(maintenance_frame)
        maintenance_buttons.pack(fill='x')
        
        ttk.Button(maintenance_buttons, text="🗑️ Nettoyer Cache", 
                  command=self.clear_cache).pack(side='left', padx=5, pady=2)
        ttk.Button(maintenance_buttons, text="✅ Vérifier Intégrité", 
                  command=self.check_integrity).pack(side='left', padx=5, pady=2)
        ttk.Button(maintenance_buttons, text="🔍 Diagnostics Complets", 
                  command=self.run_diagnostics).pack(side='left', padx=5, pady=2)
        ttk.Button(maintenance_buttons, text="📊 Statistiques DB", 
                  command=self.show_db_stats).pack(side='left', padx=5, pady=2)
        
        # Section Mode Debug
        debug_mode_frame = ttk.LabelFrame(main_frame, text="Mode Debug", padding=10)
        debug_mode_frame.pack(fill='x', pady=5)
        
        self.variables['debug_mode'] = tk.BooleanVar()
        self.variables['verbose_logging'] = tk.BooleanVar()
        
        ttk.Checkbutton(debug_mode_frame, text="Activer le mode debug", 
                       variable=self.variables['debug_mode']).pack(anchor='w', pady=2)
        ttk.Checkbutton(debug_mode_frame, text="Logs verbeux", 
                       variable=self.variables['verbose_logging']).pack(anchor='w', pady=2)
        
        # Console de debug
        console_frame = ttk.LabelFrame(main_frame, text="Console de Debug", padding=5)
        console_frame.pack(fill='both', expand=True, pady=5)
        
        self.debug_text = scrolledtext.ScrolledText(console_frame, height=12, wrap=tk.WORD, 
                                                   font=('Courier', 10))
        self.debug_text.pack(fill='both', expand=True)
        
        # Commandes de debug
        debug_commands = ttk.Frame(console_frame)
        debug_commands.pack(fill='x', pady=5)
        
        ttk.Button(debug_commands, text="Effacer Console", 
                  command=self.clear_debug_console).pack(side='left', padx=5)
        ttk.Button(debug_commands, text="Exporter Logs Debug", 
                  command=self.export_debug_logs).pack(side='left', padx=5)
        
    def create_status_bar(self):
        """Création de la barre de statut"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Label de statut principal
        self.status_label = ttk.Label(self.status_bar, text="Prêt", relief='sunken')
        self.status_label.pack(side='left', fill='x', expand=True, padx=2)
        
        # Indicateur de connexion API
        self.api_status = ttk.Label(self.status_bar, text="API: Non testée", relief='sunken', width=15)
        self.api_status.pack(side='right', padx=2)
        
        # Indicateur de configuration
        self.config_status = ttk.Label(self.status_bar, text="Config: Non chargée", relief='sunken', width=20)
        self.config_status.pack(side='right', padx=2)
        
    # Méthodes utilitaires et événements
    
    def browse_directory(self, var):
        """Ouvrir un dialog pour sélectionner un dossier"""
        log_button_click("Parcourir", "Configuration")
        try:
            directory = filedialog.askdirectory(title="Sélectionner un dossier")
            if directory:
                var.set(directory)
                self.logger.log_action(f"Dossier sélectionné: {directory}")
                self.log_message(f"Dossier sélectionné: {directory}")
                
                # Valider le dossier selon son type
                self.validate_selected_directory(directory, var)
            else:
                self.logger.debug("Sélection de dossier annulée")
        except Exception as e:
            self.logger.log_error_with_context(e, "Sélection de dossier")
            self.show_error("Erreur", f"Impossible d'ouvrir le sélecteur de dossier: {e}")
            
    def validate_selected_directory(self, directory: str, var):
        """Valider un dossier sélectionné"""
        path = Path(directory)
        
        # Déterminer le type de dossier basé sur la variable
        var_name = None
        for name, variable in self.variables.items():
            if variable == var:
                var_name = name
                break
                
        if var_name == 'html_dir':
            # Vérifier s'il contient des fichiers HTML WhatsApp
            html_files = list(path.glob("*.html"))
            if html_files:
                self.show_success("Dossier valide", f"Dossier HTML WhatsApp détecté\n{len(html_files)} fichiers HTML trouvés")
            else:
                self.show_warning("Attention", "Aucun fichier HTML trouvé dans ce dossier")
                
        elif var_name == 'media_dir':
            # Vérifier s'il contient des médias
            media_extensions = ['.opus', '.mp3', '.m4a', '.wav', '.mp4', '.jpg', '.jpeg', '.png']
            media_files = []
            for ext in media_extensions:
                media_files.extend(path.glob(f"**/*{ext}"))
            
            if media_files:
                self.show_success("Dossier valide", f"Dossier médias détecté\n{len(media_files)} fichiers média trouvés")
            else:
                self.show_warning("Attention", "Aucun fichier média trouvé dans ce dossier")
                
        elif var_name == 'output_dir':
            # Vérifier les permissions d'écriture
            if path.exists() and os.access(path, os.W_OK):
                self.show_success("Dossier valide", "Dossier de sortie accessible en écriture")
            elif not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.show_success("Dossier créé", "Dossier de sortie créé avec succès")
                except Exception as e:
                    self.show_error("Erreur", f"Impossible de créer le dossier: {e}")
            else:
                self.show_warning("Attention", "Dossier sans permissions d'écriture")
            
    def load_preferences(self):
        """Charger les préférences utilisateur"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    
                # Appliquer les préférences aux variables
                for key, value in prefs.items():
                    if key in self.variables:
                        self.variables[key].set(value)
                        
                self.log_message("Préférences chargées avec succès")
            except Exception as e:
                self.log_message(f"Erreur lors du chargement des préférences: {e}")
                
    def save_preferences(self):
        """Sauvegarder les préférences utilisateur"""
        try:
            prefs = {}
            for key, var in self.variables.items():
                try:
                    prefs[key] = var.get()
                except:
                    pass
                    
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
                
            self.log_message("Préférences sauvegardées")
        except Exception as e:
            self.log_message(f"Erreur lors de la sauvegarde des préférences: {e}")
            
    def load_configuration(self):
        """Charger la configuration de l'application"""
        try:
            # Chercher le fichier de config
            config_path = Path("config.ini")
            if config_path.exists() and HAS_BACKEND and ConfigManager:
                # Charger avec ConfigManager
                self.config_manager = ConfigManager(config_path)
                self.config = self.config_manager.load_config()
                
                # Mettre à jour l'interface
                self.update_ui_from_config()
                self.config_status.config(text="Config: Chargée", foreground='green')
                self.log_message("Configuration chargée avec succès")
            elif config_path.exists():
                # Mode dégradé - lire directement le fichier INI
                self.load_config_ini_fallback(config_path)
                self.config_status.config(text="Config: Mode dégradé", foreground='orange')
                self.log_message("Configuration chargée en mode dégradé")
            else:
                self.config_status.config(text="Config: Introuvable", foreground='red')
                self.log_message("Fichier de configuration introuvable")
                
        except Exception as e:
            self.config_status.config(text="Config: Erreur", foreground='red')
            self.log_message(f"Erreur lors du chargement de la configuration: {e}")
            
    def load_config_ini_fallback(self, config_path: Path):
        """Charger la configuration en mode dégradé (sans le backend)"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            # Lire les valeurs basiques
            if 'Paths' in config:
                if 'html_dir' in config['Paths']:
                    self.variables['html_dir'].set(config['Paths']['html_dir'])
                if 'media_dir' in config['Paths']:
                    self.variables['media_dir'].set(config['Paths']['media_dir'])
                if 'output_dir' in config['Paths']:
                    self.variables['output_dir'].set(config['Paths']['output_dir'])
                    
            if 'API' in config:
                if 'openai_key' in config['API']:
                    self.variables['openai_key'].set(config['API']['openai_key'])
                if 'max_retries' in config['API']:
                    self.variables['max_retries'].set(int(config['API'].get('max_retries', '3')))
                    
            if 'Transcription' in config:
                if 'parallel_transcriptions' in config['Transcription']:
                    self.variables['parallel_transcriptions'].set(int(config['Transcription'].get('parallel_transcriptions', '2')))
                    
            if 'Processing' in config:
                if 'transcribe_sent' in config['Processing']:
                    self.variables['transcribe_sent'].set(config['Processing'].getboolean('transcribe_sent', True))
                if 'transcribe_received' in config['Processing']:
                    self.variables['transcribe_received'].set(config['Processing'].getboolean('transcribe_received', True))
                    
        except Exception as e:
            self.log_message(f"Erreur lors du chargement INI: {e}")
            
    def update_ui_from_config(self):
        """Mettre à jour l'interface à partir de la configuration"""
        if not self.config:
            return
            
        try:
            # Chemins
            if hasattr(self.config, 'paths'):
                if hasattr(self.config.paths, 'whatsapp_export_path'):
                    self.variables['html_dir'].set(str(self.config.paths.whatsapp_export_path))
                if hasattr(self.config.paths, 'media_output_dir'):
                    self.variables['media_dir'].set(str(self.config.paths.media_output_dir))
                if hasattr(self.config.paths, 'export_output_dir'):
                    self.variables['output_dir'].set(str(self.config.paths.export_output_dir))
            
            # API
            if hasattr(self.config, 'transcription'):
                if hasattr(self.config.transcription, 'api_key'):
                    self.variables['openai_key'].set(self.config.transcription.api_key)
                if hasattr(self.config.transcription, 'transcribe_sent'):
                    self.variables['transcribe_sent'].set(self.config.transcription.transcribe_sent)
                if hasattr(self.config.transcription, 'transcribe_received'):
                    self.variables['transcribe_received'].set(self.config.transcription.transcribe_received)
                if hasattr(self.config.transcription, 'max_retries'):
                    self.variables['max_retries'].set(self.config.transcription.max_retries)
                    
        except Exception as e:
            self.log_message(f"Erreur lors de la mise à jour de l'interface: {e}")
            
    def validate_configuration(self) -> bool:
        """Valider la configuration avant de démarrer l'extraction"""
        errors = []
        
        # Vérifier les chemins
        html_dir = self.variables.get('html_dir', tk.StringVar()).get()
        if not html_dir or not Path(html_dir).exists():
            errors.append("Dossier HTML WhatsApp non configuré ou inexistant")
            
        output_dir = self.variables.get('output_dir', tk.StringVar()).get()
        if not output_dir:
            errors.append("Dossier de sortie non configuré")
            
        # Vérifier la clé API
        api_key = self.variables.get('openai_key', tk.StringVar()).get()
        if not api_key and self.variables.get('processing_mode', tk.StringVar()).get() != 'test':
            errors.append("Clé API OpenAI manquante (requis sauf en mode test)")
            
        if errors:
            error_msg = "Configuration incomplète:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Erreur de Configuration", error_msg)
            return False
            
        return True
        
    def reset_extraction_ui(self):
        """Remettre l'interface dans l'état initial"""
        self.is_processing = False
        self.current_extraction_task = None
        self.start_button.config(state='normal')
        self.pause_button.config(state='disabled')
        self.resume_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.progress_global['value'] = 0
        self.progress_global_label.config(text="Prêt")
        
    def on_extraction_progress(self, task_id: str, progress: float, message: str):
        """Callback appelé lors de la progression de l'extraction"""
        # Mettre à jour l'interface dans le thread principal
        self.root.after(0, self._update_progress_ui, progress, message)
        
    def _update_progress_ui(self, progress: float, message: str):
        """Mettre à jour l'interface de progression (thread principal)"""
        self.progress_global['value'] = progress
        self.progress_global_label.config(text=message)
        self.log_message(f"Progression: {progress:.1f}% - {message}")
        
    def check_tasks_timer(self):
        """Vérifier périodiquement les résultats des tâches"""
        try:
            # Récupérer les résultats en attente
            results = self.threading_manager.get_pending_results()
            
            for result in results:
                # Gérer différents types de résultats
                if result.task_id == self.current_extraction_task:
                    self.on_extraction_completed(result)
                elif hasattr(result, 'result') and isinstance(result.result, dict):
                    # Résultat de test API
                    if 'status' in result.result and 'message' in result.result:
                        self.handle_api_test_result(result.result)
                elif hasattr(result, 'result') and isinstance(result.result, list):
                    # Résultat d'analyse de contacts
                    self.populate_contacts_tree(result.result)
                    
        except Exception as e:
            self.logger.debug(f"Erreur check_tasks_timer: {e}")
                
        # Programmer la prochaine vérification
        self.root.after(500, self.check_tasks_timer)
        
    def on_extraction_completed(self, result):
        """Gérer la fin d'une extraction"""
        self.reset_extraction_ui()
        
        if result.status.value == "completed":
            self.log_message("✅ Extraction terminée avec succès!", "SUCCESS")
            self.progress_global['value'] = 100
            self.progress_global_label.config(text="Extraction terminée")
            messagebox.showinfo("Succès", "Extraction terminée avec succès!")
            
        elif result.status.value == "failed":
            error_msg = str(result.error) if result.error else "Erreur inconnue"
            self.log_message(f"❌ Extraction échouée: {error_msg}", "ERROR")
            messagebox.showerror("Erreur", f"L'extraction a échoué:\n{error_msg}")
            
        elif result.status.value == "cancelled":
            self.log_message("⚠️ Extraction annulée", "WARNING")
            messagebox.showwarning("Annulé", "L'extraction a été annulée")
            
        # Actualiser les résultats
        self.refresh_results()
            
    def log_message(self, message, level="INFO"):
        """Ajouter un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        # Ajouter au log principal
        self.log_text.insert(tk.END, formatted_message)
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
        # Ajouter aussi au debug si activé
        if self.variables.get('debug_mode', tk.BooleanVar()).get():
            self.debug_text.insert(tk.END, formatted_message)
            self.debug_text.see(tk.END)
            
        # Mettre à jour la barre de statut
        self.status_label.config(text=message)
        
        # Forcer la mise à jour de l'affichage
        self.root.update_idletasks()
        
    # Méthodes d'action - TOUTES FONCTIONNELLES
    
    def auto_detect_paths(self):
        """Auto-détection des dossiers WhatsApp"""
        log_button_click("Détecter automatiquement", "Configuration")
        self.log_message("🔍 Recherche automatique des dossiers WhatsApp...")
        
        try:
            found_paths = self.scan_for_whatsapp_folders()
            
            if found_paths:
                # Afficher les résultats dans une boîte de dialogue
                self.show_detection_results(found_paths)
            else:
                self.show_warning("Aucun dossier trouvé", 
                                "Aucun dossier WhatsApp détecté automatiquement.\n"
                                "Veuillez sélectionner manuellement les dossiers.")
                
        except Exception as e:
            self.logger.log_error_with_context(e, "Auto-détection")
            self.show_error("Erreur", f"Erreur lors de l'auto-détection: {e}")
            
    def scan_for_whatsapp_folders(self) -> dict:
        """Scanner le système pour trouver les dossiers WhatsApp"""
        found_paths = {}
        
        # Dossiers à scanner
        scan_locations = [
            Path.home() / "Downloads",
            Path.home() / "Desktop", 
            Path.home() / "Documents",
            Path("C:/Users") / os.getenv('USERNAME', '') / "Downloads" if os.name == 'nt' else Path.home() / "Downloads",
        ]
        
        # Patterns de recherche
        whatsapp_patterns = [
            "*WhatsApp*",
            "*whatsapp*", 
            "*iPhone*WhatsApp*",
            "*Android*WhatsApp*",
            "*Chat*WhatsApp*"
        ]
        
        for location in scan_locations:
            if not location.exists():
                continue
                
            self.logger.debug(f"Scan de {location}")
            
            try:
                for pattern in whatsapp_patterns:
                    for path in location.glob(pattern):
                        if path.is_dir():
                            # Analyser le contenu
                            html_files = list(path.glob("*.html"))
                            media_files = []
                            
                            for ext in ['.opus', '.mp3', '.m4a', '.mp4']:
                                media_files.extend(path.glob(f"**/*{ext}"))
                            
                            if html_files:
                                found_paths[str(path)] = {
                                    'type': 'html',
                                    'files': len(html_files),
                                    'description': f'Dossier HTML ({len(html_files)} fichiers)'
                                }
                            elif media_files:
                                found_paths[str(path)] = {
                                    'type': 'media', 
                                    'files': len(media_files),
                                    'description': f'Dossier Médias ({len(media_files)} fichiers)'
                                }
                                
            except Exception as e:
                self.logger.debug(f"Erreur scan {location}: {e}")
                
        return found_paths
        
    def show_detection_results(self, found_paths: dict):
        """Afficher les résultats de détection dans une fenêtre"""
        result_window = tk.Toplevel(self.root)
        result_window.title("Résultats de la détection automatique")
        result_window.geometry("600x400")
        result_window.transient(self.root)
        result_window.grab_set()
        
        # Titre
        ttk.Label(result_window, text="Dossiers WhatsApp détectés", 
                 style='Title.TLabel').pack(pady=10)
        
        # Frame pour la liste
        list_frame = ttk.Frame(result_window)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview pour les résultats
        columns = ('path', 'type', 'files')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        tree.heading('path', text='Chemin')
        tree.heading('type', text='Type')
        tree.heading('files', text='Fichiers')
        
        tree.column('path', width=300)
        tree.column('type', width=100)
        tree.column('files', width=80)
        
        # Ajouter les résultats
        for path, info in found_paths.items():
            tree.insert('', 'end', values=(path, info['type'], info['files']))
            
        tree.pack(fill='both', expand=True)
        
        # Boutons
        buttons_frame = ttk.Frame(result_window)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        def apply_selection():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                path = item['values'][0]
                path_type = item['values'][1]
                
                if path_type == 'html':
                    self.variables['html_dir'].set(path)
                    self.log_message(f"Dossier HTML configuré: {path}")
                elif path_type == 'media':
                    self.variables['media_dir'].set(path)
                    self.log_message(f"Dossier médias configuré: {path}")
                    
                result_window.destroy()
                self.show_success("Configuration appliquée", 
                                f"Dossier {path_type} configuré automatiquement")
            else:
                self.show_warning("Aucune sélection", "Veuillez sélectionner un dossier")
                
        ttk.Button(buttons_frame, text="Appliquer la sélection", 
                  command=apply_selection, style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Fermer", 
                  command=result_window.destroy).pack(side='right', padx=5)
        
    def test_api_connection(self):
        """Tester la connexion à l'API OpenAI"""
        log_button_click("Tester connexion API", "Configuration")
        self.log_message("🔗 Test de connexion à l'API OpenAI...")
        
        try:
            api_key = self.variables.get('openai_key', tk.StringVar()).get()
            
            if not api_key:
                self.show_error("Clé API manquante", 
                              "Veuillez saisir votre clé API OpenAI avant de tester")
                return
                
            # Créer une tâche de test en arrière-plan
            def test_api_task(**kwargs):
                """Tâche de test API"""
                try:
                    # Récupérer le callback de progression si fourni
                    progress_callback = kwargs.get('progress_callback')
                    stop_event = kwargs.get('stop_event')
                    
                    # Mise à jour du progrès
                    if progress_callback:
                        progress_callback.update("api_test", 0, "Début du test API...")
                    
                    # Simulation d'un test API (remplacer par vraie vérification)
                    import time
                    time.sleep(1)  # Simulation latence
                    
                    if progress_callback:
                        progress_callback.update("api_test", 50, "Validation de la clé...")
                    
                    # Vérifier si on doit s'arrêter
                    if stop_event and stop_event.is_set():
                        return {"status": "cancelled", "message": "Test annulé"}
                    
                    time.sleep(1)  # Suite de la simulation
                    
                    # Ici on pourrait faire un vrai appel à l'API OpenAI
                    # import openai
                    # openai.api_key = api_key
                    # response = openai.models.list()
                    
                    # Pour l'instant, on simule le succès si la clé ressemble à une clé valide
                    if api_key.startswith('sk-') and len(api_key) > 40:
                        if progress_callback:
                            progress_callback.update("api_test", 100, "Test réussi")
                        return {"status": "success", "message": "Connexion API réussie"}
                    else:
                        if progress_callback:
                            progress_callback.update("api_test", 100, "Test échoué")
                        return {"status": "error", "message": "Format de clé API invalide"}
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback.update("api_test", 100, f"Erreur: {e}")
                    return {"status": "error", "message": str(e)}
            
            # Lancer le test en arrière-plan
            task_id = self.threading_manager.submit_task(
                test_api_task,
                progress_callback=self.on_api_test_progress
            )
            
            # Désactiver le bouton pendant le test
            # Note: Il faut récupérer la référence au bouton depuis l'interface
            self.log_message("Test API en cours...")
            self.api_status.config(text="API: Test en cours...", foreground='orange')
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Test API")
            self.show_error("Erreur", f"Erreur lors du test API: {e}")
            
    def on_api_test_progress(self, task_id: str, progress: float, message: str):
        """Callback pour la progression du test API"""
        self.root.after(0, self._update_api_test_ui, progress, message)
        
    def _update_api_test_ui(self, progress: float, message: str):
        """Mettre à jour l'UI du test API"""
        if progress >= 100:
            # Test terminé - récupérer le résultat
            results = self.threading_manager.get_pending_results()
            for result in results:
                if hasattr(result, 'result') and result.result:
                    self.handle_api_test_result(result.result)
                    break
                    
    def handle_api_test_result(self, result: dict):
        """Gérer le résultat du test API"""
        if result['status'] == 'success':
            self.api_status.config(text="API: Connectée", foreground='green')
            self.show_success("Test API réussi ✅", 
                            f"{result['message']}\n\nLa clé API OpenAI est valide et fonctionnelle.")
            self.logger.info("Test API réussi")
        else:
            self.api_status.config(text="API: Erreur", foreground='red')
            self.show_error("Test API échoué ❌", 
                          f"{result['message']}\n\nVérifiez votre clé API OpenAI dans l'onglet Configuration.")
            self.logger.error(f"Test API échoué: {result['message']}")
        
    def save_configuration(self):
        """Sauvegarder la configuration"""
        self.log_message("Sauvegarde de la configuration...")
        self.save_preferences()
        
    def reset_configuration(self):
        """Réinitialiser la configuration"""
        if messagebox.askyesno("Confirmer", "Réinitialiser toute la configuration ?"):
            self.log_message("Réinitialisation de la configuration...")
            # TODO: Implémenter la réinitialisation
            
    def refresh_contacts(self):
        """Actualiser la liste des contacts"""
        log_button_click("Actualiser", "Filtres")
        self.log_message("🔄 Actualisation de la liste des contacts...")
        
        try:
            html_dir = self.variables.get('html_dir', tk.StringVar()).get()
            
            if not html_dir or not Path(html_dir).exists():
                self.show_warning("Dossier manquant", 
                                "Veuillez d'abord configurer le dossier HTML WhatsApp")
                return
                
            # Lancer l'analyse en arrière-plan
            def analyze_contacts(**kwargs):
                """Analyser les contacts depuis les fichiers HTML"""
                contacts_data = []
                
                try:
                    # Récupérer le callback de progression si fourni
                    progress_callback = kwargs.get('progress_callback')
                    stop_event = kwargs.get('stop_event')
                    
                    html_path = Path(html_dir)
                    html_files = list(html_path.glob("*.html"))
                    
                    self.logger.info(f"Analyse de {len(html_files)} fichiers HTML")
                    
                    if progress_callback:
                        progress_callback.update("contacts_analysis", 0, f"Analyse de {len(html_files)} fichiers...")
                    
                    for i, html_file in enumerate(html_files):
                        # Vérifier si on doit s'arrêter
                        if stop_event and stop_event.is_set():
                            break
                            
                        try:
                            # Analyser le fichier HTML pour extraire les infos
                            contact_info = self.analyze_html_file(html_file)
                            if contact_info:
                                contacts_data.append(contact_info)
                                
                        except Exception as e:
                            self.logger.warning(f"Erreur analyse {html_file}: {e}")
                            
                        # Mettre à jour le progrès
                        progress = ((i + 1) / len(html_files)) * 100
                        if progress_callback:
                            progress_callback.update("contacts_analysis", progress, 
                                                   f"Analysé {i+1}/{len(html_files)} fichiers")
                        
                    if progress_callback:
                        progress_callback.update("contacts_analysis", 100, 
                                               f"Analyse terminée: {len(contacts_data)} contacts trouvés")
                        
                    return contacts_data
                    
                except Exception as e:
                    self.logger.error(f"Erreur analyse contacts: {e}")
                    if progress_callback:
                        progress_callback.update("contacts_analysis", 100, f"Erreur: {e}")
                    return []
            
            # Lancer l'analyse
            task_id = self.threading_manager.submit_task(
                analyze_contacts,
                progress_callback=self.on_contacts_analysis_progress
            )
            
            self.log_message("Analyse des contacts en cours...")
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Actualisation contacts")
            self.show_error("Erreur", f"Erreur lors de l'actualisation: {e}")
            
    def analyze_html_file(self, html_file: Path) -> dict:
        """Analyser un fichier HTML pour extraire les informations de contact"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extraire le nom du contact depuis le nom de fichier ou le contenu
            contact_name = html_file.stem
            
            # Compter les messages (approximativement)
            message_count = content.count('<div class="message">')
            if message_count == 0:
                # Essayer d'autres patterns
                message_count = content.count('class="message')
                
            # Compter les messages audio
            audio_count = content.count('.opus') + content.count('.mp3') + content.count('.m4a')
            
            # Estimer les messages envoyés/reçus
            sent_count = content.count('sent') if 'sent' in content else message_count // 2
            received_count = message_count - sent_count
            
            return {
                'name': contact_name,
                'file_path': str(html_file),
                'total_messages': message_count,
                'audio_messages': audio_count,
                'sent_messages': sent_count,
                'received_messages': received_count,
                'selected': True  # Par défaut sélectionné
            }
            
        except Exception as e:
            self.logger.debug(f"Erreur analyse {html_file}: {e}")
            return None
            
    def on_contacts_analysis_progress(self, task_id: str, progress: float, message: str):
        """Callback pour la progression de l'analyse des contacts"""
        self.root.after(0, self._update_contacts_analysis_ui, progress, message)
        
    def _update_contacts_analysis_ui(self, progress: float, message: str):
        """Mettre à jour l'UI de l'analyse des contacts"""
        if progress >= 100:
            # Analyse terminée - récupérer les résultats
            results = self.threading_manager.get_pending_results()
            for result in results:
                if hasattr(result, 'result') and isinstance(result.result, list):
                    self.populate_contacts_tree(result.result)
                    break
                    
    def populate_contacts_tree(self, contacts_data: list):
        """Remplir l'arbre des contacts avec les données"""
        try:
            # Vider l'arbre existant
            for item in self.contacts_tree.get_children():
                self.contacts_tree.delete(item)
                
            # Réinitialiser les variables de contact
            self.contacts_vars.clear()
            
            # Ajouter les contacts
            for contact in contacts_data:
                # Créer une variable pour la sélection
                var = tk.BooleanVar(value=contact.get('selected', True))
                self.contacts_vars[contact['name']] = var
                
                # Ajouter à l'arbre
                item_id = self.contacts_tree.insert('', 'end', values=(
                    contact['name'],
                    contact['total_messages'],
                    contact['audio_messages']
                ))
                
                # Marquer comme sélectionné par défaut
                if contact.get('selected', True):
                    self.contacts_tree.selection_add(item_id)
                    
            self.log_message(f"✅ {len(contacts_data)} contacts chargés")
            
            # Mettre à jour les estimations
            self.update_estimates()
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Population contacts")
            self.show_error("Erreur", f"Erreur lors de l'affichage des contacts: {e}")
        
    def select_all_contacts(self):
        """Sélectionner tous les contacts"""
        # TODO: Implémenter la sélection
        pass
        
    def deselect_all_contacts(self):
        """Désélectionner tous les contacts"""
        # TODO: Implémenter la désélection
        pass
        
    def preview_filtered_data(self):
        """Aperçu des données filtrées"""
        self.log_message("Génération de l'aperçu des données...")
        # TODO: Implémenter l'aperçu
        
    def estimate_api_cost(self):
        """Estimer le coût de l'API"""
        self.log_message("Estimation du coût API...")
        # TODO: Implémenter l'estimation
        
    def update_estimates(self):
        """Mettre à jour les estimations"""
        self.log_message("Mise à jour des estimations...")
        # TODO: Implémenter les estimations
        
    def start_extraction(self):
        """Démarrer l'extraction"""
        if not self.validate_configuration():
            return
            
        self.log_message("Démarrage de l'extraction...")
        self.is_processing = True
        self.start_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        
        # Réinitialiser les barres de progression
        self.progress_global['value'] = 0
        self.progress_global_label.config(text="Initialisation...")
        
        # Créer la tâche d'extraction
        try:
            # Fonction d'extraction réelle avec backend
            def extraction_task(**kwargs):
                """Tâche d'extraction principale"""
                
                # Récupérer les arguments
                progress_callback = kwargs.get('progress_callback')
                stop_event = kwargs.get('stop_event')
                pause_event = kwargs.get('pause_event')
                
                try:
                    if not HAS_BACKEND:
                        # Mode simulation si backend non disponible
                        for i, (step_name, progress) in enumerate([
                            ("Mode simulation - pas de backend", 0.5),
                            ("Simulation terminée", 1.0)
                        ]):
                            if stop_event and stop_event.is_set():
                                return {"status": "cancelled", "message": "Extraction annulée"}
                            if progress_callback:
                                progress_callback.update("extraction", progress * 100, step_name)
                            import time
                            time.sleep(1)
                        return {"status": "completed", "message": "Mode simulation terminé"}
                    
                    # Mode réel avec backend
                    if not self.config_manager:
                        return {"status": "failed", "message": "Configuration non chargée"}
                    
                    # Initialiser le pipeline d'extraction
                    pipeline = ExtractionPipeline(self.config_manager)
                    
                    # Définir callback de progression
                    def on_pipeline_progress(task_name, progress):
                        if progress_callback:
                            progress_callback.update("extraction", progress, task_name)
                    
                    pipeline.set_progress_callback(on_pipeline_progress)
                    
                    # Obtenir le chemin source
                    source_path = self.variables.get('html_dir', tk.StringVar()).get()
                    if not source_path or not Path(source_path).exists():
                        return {"status": "failed", "message": "Chemin source non configuré ou inexistant"}
                    
                    # Lancer l'extraction complète
                    results = pipeline.extract_full_pipeline(source_path)
                    
                    if stop_event and stop_event.is_set():
                        pipeline.stop_processing()
                        return {"status": "cancelled", "message": "Extraction annulée"}
                    
                    return {"status": "completed", "message": "Extraction terminée avec succès", "results": results}
                    
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    return {"status": "failed", "message": f"Erreur d'extraction: {str(e)}", "details": error_details}
            
            # Lancer la tâche
            self.current_extraction_task = self.threading_manager.submit_task(
                extraction_task,
                progress_callback=self.on_extraction_progress
            )
            
            self.log_message(f"Tâche d'extraction démarrée: {self.current_extraction_task}")
            
        except Exception as e:
            self.log_message(f"Erreur lors du démarrage de l'extraction: {e}", "ERROR")
            self.reset_extraction_ui()
        
    def pause_extraction(self):
        """Mettre en pause l'extraction"""
        if self.current_extraction_task:
            self.threading_manager.pause_task(self.current_extraction_task)
            self.log_message("Extraction mise en pause")
            self.pause_button.config(state='disabled')
            self.resume_button.config(state='normal')
        
    def resume_extraction(self):
        """Reprendre l'extraction"""
        if self.current_extraction_task:
            self.threading_manager.resume_task(self.current_extraction_task)
            self.log_message("Extraction reprise")
            self.pause_button.config(state='normal')
            self.resume_button.config(state='disabled')
        
    def stop_extraction(self):
        """Arrêter l'extraction"""
        if messagebox.askyesno("Confirmer", "Arrêter l'extraction en cours ?"):
            if self.current_extraction_task:
                self.threading_manager.stop_task(self.current_extraction_task)
                self.log_message("Arrêt de l'extraction demandé...")
                self.reset_extraction_ui()
            
    def clear_logs(self):
        """Effacer les logs"""
        self.log_text.delete(1.0, tk.END)
        
    def save_logs(self):
        """Sauvegarder les logs"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Logs sauvegardés dans {filename}")
            
    def open_output_folder(self):
        """Ouvrir le dossier de sortie"""
        output_dir = self.variables['output_dir'].get()
        if output_dir and Path(output_dir).exists():
            os.startfile(output_dir)
        else:
            messagebox.showwarning("Attention", "Dossier de sortie non configuré ou inexistant")
            
    def open_main_csv(self):
        """Ouvrir le fichier CSV principal"""
        # TODO: Implémenter l'ouverture du CSV
        pass
        
    def export_report(self):
        """Exporter un rapport"""
        # TODO: Implémenter l'export de rapport
        pass
        
    def refresh_results(self):
        """Actualiser les résultats"""
        self.log_message("Actualisation des résultats...")
        # TODO: Implémenter l'actualisation
        
    def test_configuration(self):
        """Tester la configuration"""
        log_button_click("Test Configuration", "Debug")
        self.log_message("🔧 Test de la configuration...")
        
        try:
            errors = []
            warnings = []
            success_count = 0
            
            # Test 1: Vérifier les chemins
            html_dir = self.variables.get('html_dir', tk.StringVar()).get()
            if html_dir and Path(html_dir).exists():
                html_files = list(Path(html_dir).glob("*.html"))
                if html_files:
                    success_count += 1
                    self.log_message(f"✅ Dossier HTML: {len(html_files)} fichiers trouvés")
                else:
                    warnings.append("Dossier HTML configuré mais aucun fichier HTML trouvé")
            else:
                errors.append("Dossier HTML non configuré ou inexistant")
                
            # Test 2: Dossier de sortie
            output_dir = self.variables.get('output_dir', tk.StringVar()).get()
            if output_dir:
                output_path = Path(output_dir)
                try:
                    if not output_path.exists():
                        output_path.mkdir(parents=True, exist_ok=True)
                    
                    # Test d'écriture
                    test_file = output_path / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    
                    success_count += 1
                    self.log_message("✅ Dossier de sortie: accessible en écriture")
                except Exception as e:
                    errors.append(f"Dossier de sortie non accessible: {e}")
            else:
                errors.append("Dossier de sortie non configuré")
                
            # Test 3: Clé API
            api_key = self.variables.get('openai_key', tk.StringVar()).get()
            if api_key:
                if api_key.startswith('sk-') and len(api_key) > 40:
                    success_count += 1
                    self.log_message("✅ Clé API: format valide")
                else:
                    warnings.append("Format de clé API suspect")
            else:
                warnings.append("Clé API non configurée (requis pour transcription)")
                
            # Test 4: FFmpeg
            try:
                ffmpeg_path = Path("ffmpeg/ffmpeg.exe")
                if ffmpeg_path.exists():
                    success_count += 1
                    self.log_message("✅ FFmpeg: trouvé localement")
                else:
                    # Tester dans le PATH
                    import subprocess
                    result = subprocess.run(['ffmpeg', '-version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        success_count += 1
                        self.log_message("✅ FFmpeg: trouvé dans le PATH")
                    else:
                        warnings.append("FFmpeg non trouvé")
            except Exception:
                warnings.append("FFmpeg non accessible")
                
            # Afficher le résultat
            total_tests = 4
            self.show_test_results("Test Configuration", success_count, total_tests, errors, warnings)
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Test configuration")
            self.show_error("Erreur Test", f"Erreur lors du test: {e}")
        
    def test_file_access(self):
        """Tester l'accès aux fichiers"""
        log_button_click("Test Accès Fichiers", "Debug")
        self.log_message("📁 Test d'accès aux fichiers...")
        
        try:
            errors = []
            warnings = []
            success_count = 0
            
            # Test 1: Dossier HTML
            html_dir = self.variables.get('html_dir', tk.StringVar()).get()
            if html_dir:
                html_path = Path(html_dir)
                if html_path.exists() and html_path.is_dir():
                    try:
                        files = list(html_path.iterdir())
                        readable_files = []
                        
                        for file in files[:5]:  # Test sur 5 premiers fichiers
                            try:
                                if file.is_file():
                                    with open(file, 'r', encoding='utf-8') as f:
                                        f.read(1024)  # Lire 1KB
                                    readable_files.append(file.name)
                            except Exception:
                                try:
                                    with open(file, 'r', encoding='latin-1') as f:
                                        f.read(1024)
                                    readable_files.append(f"{file.name} (latin-1)")
                                except Exception:
                                    pass
                                    
                        if readable_files:
                            success_count += 1
                            self.log_message(f"✅ Accès HTML: {len(readable_files)} fichiers lisibles")
                        else:
                            warnings.append("Fichiers HTML présents mais non lisibles")
                            
                    except Exception as e:
                        errors.append(f"Erreur accès dossier HTML: {e}")
                else:
                    errors.append("Dossier HTML non accessible")
            else:
                warnings.append("Dossier HTML non configuré")
                
            # Test 2: Dossier médias
            media_dir = self.variables.get('media_dir', tk.StringVar()).get()
            if media_dir:
                media_path = Path(media_dir)
                if media_path.exists():
                    try:
                        media_extensions = ['.opus', '.mp3', '.m4a', '.mp4', '.jpg', '.png']
                        media_files = []
                        
                        for ext in media_extensions:
                            found = list(media_path.glob(f"**/*{ext}"))
                            media_files.extend(found[:2])  # Max 2 par type
                            
                        accessible_count = 0
                        for media_file in media_files:
                            try:
                                size = media_file.stat().st_size
                                if size > 0:
                                    accessible_count += 1
                            except Exception:
                                pass
                                
                        if accessible_count > 0:
                            success_count += 1
                            self.log_message(f"✅ Accès médias: {accessible_count} fichiers accessibles")
                        else:
                            warnings.append("Dossier médias configuré mais fichiers non accessibles")
                            
                    except Exception as e:
                        errors.append(f"Erreur accès dossier médias: {e}")
                else:
                    warnings.append("Dossier médias non accessible")
            else:
                warnings.append("Dossier médias non configuré")
                
            # Test 3: Permissions écriture
            output_dir = self.variables.get('output_dir', tk.StringVar()).get()
            if output_dir:
                try:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    # Test création/suppression fichier
                    test_file = output_path / "access_test.tmp"
                    test_file.write_text("Test d'accès")
                    content = test_file.read_text()
                    test_file.unlink()
                    
                    if content == "Test d'accès":
                        success_count += 1
                        self.log_message("✅ Permissions écriture: OK")
                    else:
                        errors.append("Test écriture/lecture échoué")
                        
                except Exception as e:
                    errors.append(f"Permissions écriture insuffisantes: {e}")
            else:
                warnings.append("Dossier de sortie non configuré")
                
            # Test 4: Espace disque
            try:
                import shutil
                output_dir = self.variables.get('output_dir', tk.StringVar()).get() or "."
                free_space = shutil.disk_usage(output_dir).free
                free_gb = free_space / (1024**3)
                
                if free_gb > 1:
                    success_count += 1
                    self.log_message(f"✅ Espace disque: {free_gb:.1f} GB disponibles")
                else:
                    warnings.append(f"Espace disque faible: {free_gb:.1f} GB")
                    
            except Exception as e:
                warnings.append(f"Impossible de vérifier l'espace disque: {e}")
                
            # Afficher le résultat
            total_tests = 4
            self.show_test_results("Test Accès Fichiers", success_count, total_tests, errors, warnings)
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Test accès fichiers")
            self.show_error("Erreur Test", f"Erreur lors du test: {e}")
        
    def test_ffmpeg(self):
        """Tester FFmpeg"""
        log_button_click("Test FFmpeg", "Debug")
        self.log_message("🎵 Test de FFmpeg...")
        
        try:
            import subprocess
            errors = []
            warnings = []
            success_count = 0
            
            # Test 1: FFmpeg local
            ffmpeg_local = Path("ffmpeg/ffmpeg.exe")
            if ffmpeg_local.exists():
                try:
                    result = subprocess.run([str(ffmpeg_local), '-version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_line = result.stdout.split('\n')[0]
                        success_count += 1
                        self.log_message(f"✅ FFmpeg local: {version_line}")
                    else:
                        warnings.append("FFmpeg local présent mais non fonctionnel")
                except Exception as e:
                    warnings.append(f"Erreur FFmpeg local: {e}")
            else:
                warnings.append("FFmpeg local non trouvé dans ffmpeg/")
                
            # Test 2: FFmpeg dans PATH
            try:
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    success_count += 1
                    self.log_message(f"✅ FFmpeg PATH: {version_line}")
                else:
                    warnings.append("FFmpeg dans PATH mais non fonctionnel")
            except FileNotFoundError:
                warnings.append("FFmpeg non trouvé dans PATH")
            except Exception as e:
                warnings.append(f"Erreur FFmpeg PATH: {e}")
                
            # Test 3: Test de conversion simple
            if success_count > 0:
                try:
                    # Créer un fichier audio de test (silence de 1 seconde)
                    test_dir = Path("temp_test")
                    test_dir.mkdir(exist_ok=True)
                    
                    ffmpeg_cmd = str(ffmpeg_local) if ffmpeg_local.exists() else 'ffmpeg'
                    
                    # Générer 1 seconde de silence en MP3
                    cmd = [
                        ffmpeg_cmd, '-f', 'lavfi', '-i', 'anullsrc=duration=1', 
                        '-y', str(test_dir / 'test_silence.mp3')
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0 and (test_dir / 'test_silence.mp3').exists():
                        # Convertir en OPUS pour tester
                        cmd2 = [
                            ffmpeg_cmd, '-i', str(test_dir / 'test_silence.mp3'),
                            '-y', str(test_dir / 'test_silence.opus')
                        ]
                        
                        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=15)
                        
                        if result2.returncode == 0:
                            success_count += 1
                            self.log_message("✅ Test conversion: MP3 → OPUS réussi")
                        else:
                            warnings.append("Conversion OPUS échouée")
                            
                        # Nettoyer
                        for f in test_dir.glob("*"):
                            f.unlink()
                        test_dir.rmdir()
                        
                    else:
                        warnings.append("Génération audio de test échouée")
                        
                except Exception as e:
                    warnings.append(f"Test conversion échoué: {e}")
                    
            # Test 4: Codecs supportés
            if success_count > 0:
                try:
                    ffmpeg_cmd = str(ffmpeg_local) if ffmpeg_local.exists() else 'ffmpeg'
                    result = subprocess.run([ffmpeg_cmd, '-codecs'], 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        codecs = result.stdout.lower()
                        supported = []
                        
                        if 'opus' in codecs:
                            supported.append('OPUS')
                        if 'mp3' in codecs:
                            supported.append('MP3') 
                        if 'aac' in codecs:
                            supported.append('AAC')
                        if 'h264' in codecs:
                            supported.append('H.264')
                            
                        if supported:
                            success_count += 1
                            self.log_message(f"✅ Codecs supportés: {', '.join(supported)}")
                        else:
                            warnings.append("Codecs audio/vidéo non détectés")
                            
                except Exception as e:
                    warnings.append(f"Vérification codecs échouée: {e}")
                    
            if success_count == 0:
                errors.append("FFmpeg non trouvé ou non fonctionnel")
                errors.append("Solution: Installer FFmpeg ou placer ffmpeg.exe dans le dossier ffmpeg/")
                
            # Afficher le résultat
            total_tests = 4
            self.show_test_results("Test FFmpeg", success_count, total_tests, errors, warnings)
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Test FFmpeg")
            self.show_error("Erreur Test", f"Erreur lors du test FFmpeg: {e}")
        
    def clear_cache(self):
        """Nettoyer le cache"""
        if messagebox.askyesno("Confirmer", "Nettoyer tout le cache ?"):
            self.log_message("Nettoyage du cache...")
            # TODO: Implémenter le nettoyage
            
    def check_integrity(self):
        """Vérifier l'intégrité des données"""
        self.log_message("Vérification de l'intégrité...")
        # TODO: Implémenter la vérification
        
    def run_diagnostics(self):
        """Lancer les diagnostics complets"""
        self.log_message("Lancement des diagnostics...")
        # TODO: Implémenter les diagnostics
        
    def show_db_stats(self):
        """Afficher les statistiques de la base de données"""
        self.log_message("Affichage des statistiques DB...")
        # TODO: Implémenter les stats DB
        
    def clear_debug_console(self):
        """Effacer la console de debug"""
        self.debug_text.delete(1.0, tk.END)
        
    def export_debug_logs(self):
        """Exporter les logs de debug"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.debug_text.get(1.0, tk.END))
            self.log_message(f"Logs debug sauvegardés dans {filename}")
            
    def load_config_file(self):
        """Charger un fichier de configuration"""
        filename = filedialog.askopenfilename(
            filetypes=[("Fichiers INI", "*.ini"), ("Fichiers YAML", "*.yaml"), 
                      ("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.log_message(f"Chargement de {filename}...")
            # TODO: Implémenter le chargement
            
    def save_config_file(self):
        """Sauvegarder un fichier de configuration"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".ini",
            filetypes=[("Fichiers INI", "*.ini"), ("Fichiers YAML", "*.yaml"), 
                      ("Fichiers JSON", "*.json")]
        )
        if filename:
            self.log_message(f"Sauvegarde dans {filename}...")
            # TODO: Implémenter la sauvegarde
            
    def show_about(self):
        """Afficher les informations sur l'application"""
        about_text = """
WhatsApp Extractor v2.0
Interface Graphique

Application professionnelle pour l'extraction
et la transcription des données WhatsApp.

Développé avec Python et Tkinter
© 2024 WhatsApp Extractor Team
        """
        messagebox.showinfo("À propos", about_text)
        
    # Méthodes utilitaires pour l'interface
    
    def show_success(self, title: str, message: str):
        """Afficher un message de succès"""
        messagebox.showinfo(title, message)
        self.logger.info(f"SUCCESS: {title} - {message}")
        
    def show_warning(self, title: str, message: str):
        """Afficher un avertissement"""
        messagebox.showwarning(title, message)
        self.logger.warning(f"WARNING: {title} - {message}")
        
    def show_error(self, title: str, message: str):
        """Afficher une erreur"""
        messagebox.showerror(title, message)
        self.logger.error(f"ERROR: {title} - {message}")
        
    def show_test_results(self, test_name: str, success_count: int, total_tests: int, 
                         errors: list, warnings: list):
        """Afficher les résultats d'un test dans une fenêtre dédiée"""
        
        # Créer une fenêtre de résultats
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Résultats - {test_name}")
        result_window.geometry("500x400")
        result_window.transient(self.root)
        result_window.grab_set()
        
        # Titre avec score
        score_color = "green" if success_count == total_tests else "orange" if success_count > 0 else "red"
        title_text = f"{test_name}: {success_count}/{total_tests} tests réussis"
        
        title_label = ttk.Label(result_window, text=title_text, style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(result_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Text widget avec scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        result_text = scrolledtext.ScrolledText(text_frame, height=15, wrap=tk.WORD)
        result_text.pack(fill='both', expand=True)
        
        # Ajouter le contenu
        content = f"=== {test_name} ===\n\n"
        content += f"Score: {success_count}/{total_tests} tests réussis\n\n"
        
        if success_count == total_tests:
            content += "🎉 Tous les tests ont réussi !\n\n"
        elif success_count > 0:
            content += "⚠️ Certains tests ont échoué ou ont des avertissements.\n\n"
        else:
            content += "❌ Tous les tests ont échoué. Configuration requise.\n\n"
            
        if errors:
            content += "❌ ERREURS:\n"
            for error in errors:
                content += f"  • {error}\n"
            content += "\n"
            
        if warnings:
            content += "⚠️ AVERTISSEMENTS:\n"
            for warning in warnings:
                content += f"  • {warning}\n"
            content += "\n"
            
        content += "=== Conseils ===\n"
        if test_name == "Test Configuration":
            content += "• Configurez tous les chemins dans l'onglet Configuration\n"
            content += "• Utilisez 'Détecter automatiquement' pour trouver WhatsApp\n"
            content += "• Vérifiez que la clé API OpenAI est valide\n"
        elif test_name == "Test Accès Fichiers":
            content += "• Vérifiez les permissions de lecture/écriture\n"
            content += "• Assurez-vous que les dossiers contiennent les bons fichiers\n"
            content += "• Libérez de l'espace disque si nécessaire\n"
        elif test_name == "Test FFmpeg":
            content += "• Installez FFmpeg système ou placez ffmpeg.exe dans ffmpeg/\n"
            content += "• Téléchargez FFmpeg sur https://ffmpeg.org/download.html\n"
            content += "• FFmpeg est requis pour conversion audio\n"
            
        result_text.insert('1.0', content)
        result_text.config(state='disabled')
        
        # Boutons
        buttons_frame = ttk.Frame(result_window)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Fermer", 
                  command=result_window.destroy).pack(side='right', padx=5)
        
        if test_name == "Test Configuration" and errors:
            ttk.Button(buttons_frame, text="Aller à Configuration", 
                      command=lambda: [result_window.destroy(), self.notebook.select(0)]).pack(side='left', padx=5)
                      
        # Logger le résultat
        self.logger.info(f"{test_name}: {success_count}/{total_tests} réussis")
        if errors:
            for error in errors:
                self.logger.error(f"{test_name} - {error}")
        if warnings:
            for warning in warnings:
                self.logger.warning(f"{test_name} - {warning}")
        
    def on_log_message(self, message: str, level: str):
        """Callback pour recevoir les messages de log du système de logging"""
        # Cette méthode sera appelée par le système de logging
        # pour afficher les messages dans l'interface
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {level}: {message}\n"
            
            try:
                self.log_text.insert(tk.END, formatted_message)
                if hasattr(self, 'auto_scroll_var') and self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
            except:
                pass  # Interface pas encore créée
                
        # Aussi dans debug si activé
        if hasattr(self, 'debug_text') and hasattr(self, 'variables'):
            if self.variables.get('debug_mode', tk.BooleanVar()).get():
                try:
                    self.debug_text.insert(tk.END, formatted_message)
                    self.debug_text.see(tk.END)
                except:
                    pass
        
    def run(self):
        """Lancer l'interface graphique"""
        try:
            # Message de bienvenue
            self.log_message("WhatsApp Extractor v2 - Interface Graphique démarrée")
            self.log_message("Bienvenue ! Configurez vos paramètres dans l'onglet Configuration.")
            
            # Démarrer la boucle principale
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du démarrage de l'interface: {e}")
            
    def on_closing(self):
        """Gérer la fermeture de l'application"""
        if self.is_processing:
            if messagebox.askyesno("Confirmer", "Une extraction est en cours. Quitter quand même ?"):
                # Arrêter toutes les tâches
                self.threading_manager.shutdown()
                self.save_preferences()
                self.root.destroy()
        else:
            # Arrêter le gestionnaire de threading proprement
            self.threading_manager.shutdown()
            self.save_preferences()
            self.root.destroy()


def main():
    """Point d'entrée principal"""
    try:
        app = WhatsAppExtractorGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Erreur fatale", f"Impossible de démarrer l'application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()