#!/usr/bin/env python3
"""
Interface Graphique Moderne - WhatsApp Extractor v2
Design 2025 avec UX exceptionnelle et workflow complet
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import du système moderne
from src.gui.modern_ui import (
    ModernThemeManager, ModernButton, ModernCard, 
    ModernProgressBar, ModernToast, ModernInput
)

# Imports backend
try:
    from src.config.config_manager import ConfigManager
    from src.config.schemas import AppConfig
    from src.core.database import CacheDatabase, DatabaseManager
    from src.core.extraction_pipeline import ExtractionPipeline
    from src.parsers.html_parser import WhatsAppHTMLParser
    HAS_BACKEND = True
except ImportError as e:
    print(f"Modules backend non disponibles: {e}")
    HAS_BACKEND = False
    ConfigManager = None
    AppConfig = None
    CacheDatabase = None
    DatabaseManager = None
    ExtractionPipeline = None
    WhatsAppHTMLParser = None

from src.gui.threading_manager import ThreadingManager
from src.utils.logger import setup_logger


class ModernWhatsAppExtractor:
    """Interface graphique moderne pour WhatsApp Extractor v2"""
    
    def __init__(self):
        # Configuration principale
        self.root = tk.Tk()
        self.root.title("WhatsApp Extractor v2 - Edition Moderne")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Système de thème moderne
        self.theme = ModernThemeManager()
        
        # Variables d'état
        self.config_manager = None
        self.extraction_pipeline = None
        self.threading_manager = ThreadingManager(max_workers=4)
        self.current_step = 0
        self.total_steps = 5
        self.is_processing = False
        
        # Données de workflow
        self.workflow_data = {
            'source_path': '',
            'output_path': '',
            'selected_contacts': [],
            'filter_settings': {},
            'processing_options': {},
            'results': {}
        }
        
        # État de validation des étapes
        self.step_validation = {
            0: False,  # Configuration
            1: False,  # Sélection
            2: False,  # Filtres
            3: False,  # Options
            4: False,  # Traitement
        }
        
        # Interface utilisateur
        self.setup_ui()
        self.load_initial_config()
        
        # Logger
        self.logger = setup_logger(self.log_message)
        self.logger.info("WhatsApp Extractor v2 - Interface moderne initialisée")
        
        # Timer pour les tâches
        self.check_tasks_timer()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur moderne"""
        # Configuration du thème
        self.setup_theme()
        
        # Layout principal
        self.create_main_layout()
        
        # Navigation sidebar
        self.create_navigation()
        
        # Zone de contenu principale
        self.create_content_area()
        
        # Barre de progression globale
        self.create_progress_bar()
        
        # Zone de statut moderne
        self.create_status_area()
        
        # Raccourcis clavier
        self.setup_keyboard_shortcuts()
    
    def setup_theme(self):
        """Configuration du thème moderne"""
        # Appliquer le thème aux widgets ttk
        style = ttk.Style()
        self.theme.apply_theme_to_ttk(style)
        
        # Configuration de la fenêtre principale
        self.root.configure(bg=self.theme.get_color('bg_primary'))
        
        # Configuration des couleurs
        self.colors = {
            'primary': self.theme.get_color('primary'),
            'secondary': self.theme.get_color('secondary'),
            'success': self.theme.get_color('success'),
            'warning': self.theme.get_color('warning'),
            'error': self.theme.get_color('error'),
            'bg_primary': self.theme.get_color('bg_primary'),
            'bg_secondary': self.theme.get_color('bg_secondary'),
            'bg_elevated': self.theme.get_color('bg_elevated'),
            'text_primary': self.theme.get_color('text_primary'),
            'text_secondary': self.theme.get_color('text_secondary'),
            'text_tertiary': self.theme.get_color('text_tertiary'),
        }
    
    def create_main_layout(self):
        """Création du layout principal"""
        # Container principal avec glassmorphisme
        self.main_container = tk.Frame(
            self.root,
            bg=self.colors['bg_primary']
        )
        self.main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Layout en grille moderne
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
    
    def create_navigation(self):
        """Création de la navigation sidebar moderne"""
        # Sidebar avec glassmorphisme
        self.sidebar = ModernCard(
            self.main_container,
            theme_manager=self.theme,
            glass=True,
            width=280
        )
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky='nsew', padx=(20, 10), pady=20)
        self.sidebar.grid_propagate(False)
        
        # Header du sidebar
        self.create_sidebar_header()
        
        # Steps de navigation
        self.create_navigation_steps()
        
        # Actions rapides
        self.create_quick_actions()
    
    def create_sidebar_header(self):
        """Création du header du sidebar"""
        header_frame = tk.Frame(
            self.sidebar,
            bg=self.theme.get_color('bg_glass')
        )
        header_frame.pack(fill='x', padx=20, pady=(20, 30))
        
        # Logo/Titre
        title_label = tk.Label(
            header_frame,
            text="WhatsApp\\nExtractor v2",
            font=self.theme.get_font('h3'),
            fg=self.colors['primary'],
            bg=self.theme.get_color('bg_glass'),
            justify='center'
        )
        title_label.pack()
        
        # Sous-titre
        subtitle_label = tk.Label(
            header_frame,
            text="Extraction moderne et intelligente",
            font=self.theme.get_font('caption'),
            fg=self.colors['text_secondary'],
            bg=self.theme.get_color('bg_glass'),
            justify='center'
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Toggle theme button
        theme_btn = ModernButton(
            header_frame,
            text="🌙" if self.theme.current_theme == 'light' else "☀️",
            command=self.toggle_theme,
            style="outline",
            theme_manager=self.theme
        )
        theme_btn.pack(pady=(15, 0))
        theme_btn.configure(width=40, height=40)
    
    def create_navigation_steps(self):
        """Création des étapes de navigation"""
        self.nav_frame = tk.Frame(
            self.sidebar,
            bg=self.theme.get_color('bg_glass')
        )
        self.nav_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.nav_buttons = []
        steps = [
            {"title": "Configuration", "icon": "⚙️", "desc": "Chemins et paramètres"},
            {"title": "Sélection", "icon": "📁", "desc": "Fichiers WhatsApp"},
            {"title": "Filtres", "icon": "🔍", "desc": "Critères d'extraction"},
            {"title": "Options", "icon": "🎛️", "desc": "Transcription & Export"},
            {"title": "Traitement", "icon": "🚀", "desc": "Extraction et résultats"},
        ]
        
        for i, step in enumerate(steps):
            self.create_nav_step(i, step)
    
    def create_nav_step(self, index: int, step: Dict[str, str]):
        """Création d'une étape de navigation"""
        # Container pour l'étape
        step_frame = tk.Frame(
            self.nav_frame,
            bg=self.theme.get_color('bg_glass')
        )
        step_frame.pack(fill='x', pady=(0, 12))
        
        # Button principal
        step_button = tk.Button(
            step_frame,
            text=f"{step['icon']}  {step['title']}",
            font=self.theme.get_font('body'),
            bg=self.colors['bg_elevated'] if index == self.current_step else self.colors['bg_secondary'],
            fg=self.colors['primary'] if index == self.current_step else self.colors['text_primary'],
            relief='flat',
            bd=0,
            pady=12,
            padx=16,
            anchor='w',
            cursor='hand2',
            command=lambda i=index: self.navigate_to_step(i)
        )
        step_button.pack(fill='x')
        
        # Description
        desc_label = tk.Label(
            step_frame,
            text=step['desc'],
            font=self.theme.get_font('caption'),
            fg=self.colors['text_secondary'],
            bg=self.theme.get_color('bg_glass'),
            anchor='w'
        )
        desc_label.pack(fill='x', padx=16, pady=(0, 4))
        
        # Indicateur de validation
        validation_indicator = tk.Label(
            step_button,
            text="✓" if self.step_validation.get(index, False) else "○",
            font=self.theme.get_font('body'),
            fg=self.colors['success'] if self.step_validation.get(index, False) else self.colors['text_tertiary'],
            bg=step_button['bg']
        )
        validation_indicator.place(relx=0.9, rely=0.5, anchor='center')
        
        self.nav_buttons.append({
            'frame': step_frame,
            'button': step_button,
            'indicator': validation_indicator,
            'desc': desc_label
        })
    
    def create_quick_actions(self):
        """Création des actions rapides"""
        actions_frame = tk.Frame(
            self.sidebar,
            bg=self.theme.get_color('bg_glass')
        )
        actions_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        
        # Titre
        title_label = tk.Label(
            actions_frame,
            text="Actions Rapides",
            font=self.theme.get_font('h5'),
            fg=self.colors['text_primary'],
            bg=self.theme.get_color('bg_glass')
        )
        title_label.pack(anchor='w', pady=(0, 12))
        
        # Boutons d'action
        actions = [
            {"text": "📂 Ouvrir dossier", "command": self.open_output_folder},
            {"text": "📊 Voir résultats", "command": self.view_results},
            {"text": "🔄 Réinitialiser", "command": self.reset_workflow},
            {"text": "💾 Sauvegarder config", "command": self.save_config},
        ]
        
        for action in actions:
            btn = ModernButton(
                actions_frame,
                text=action['text'],
                command=action['command'],
                style="outline",
                theme_manager=self.theme
            )
            btn.pack(fill='x', pady=2)
            btn.configure(height=35)
    
    def create_content_area(self):
        """Création de la zone de contenu principale"""
        # Container principal avec glassmorphisme
        self.content_container = ModernCard(
            self.main_container,
            theme_manager=self.theme,
            glass=False,
            elevation=2
        )
        self.content_container.grid(row=0, column=1, sticky='nsew', padx=(10, 20), pady=(20, 10))
        
        # Header de contenu
        self.create_content_header()
        
        # Zone de contenu scrollable
        self.create_scrollable_content()
        
        # Navigation entre étapes
        self.create_step_navigation()
    
    def create_content_header(self):
        """Création du header de contenu"""
        self.header_frame = tk.Frame(
            self.content_container,
            bg=self.colors['bg_elevated'],
            height=80
        )
        self.header_frame.pack(fill='x', padx=30, pady=(30, 20))
        self.header_frame.pack_propagate(False)
        
        # Titre dynamique
        self.step_title = tk.Label(
            self.header_frame,
            text="Configuration",
            font=self.theme.get_font('h2'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        self.step_title.pack(side='left', anchor='w')
        
        # Indicateur d'étape
        self.step_indicator = tk.Label(
            self.header_frame,
            text="Étape 1 sur 5",
            font=self.theme.get_font('body'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        self.step_indicator.pack(side='right', anchor='e')
    
    def create_scrollable_content(self):
        """Création de la zone de contenu scrollable"""
        # Canvas pour le scroll
        self.content_canvas = tk.Canvas(
            self.content_container,
            bg=self.colors['bg_elevated'],
            highlightthickness=0
        )
        
        # Scrollbar moderne
        scrollbar = ttk.Scrollbar(
            self.content_container,
            orient='vertical',
            command=self.content_canvas.yview,
            style='Modern.Vertical.TScrollbar'
        )
        
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame scrollable
        self.scrollable_frame = tk.Frame(
            self.content_canvas,
            bg=self.colors['bg_elevated']
        )
        
        self.content_canvas.pack(side='left', fill='both', expand=True, padx=(30, 0), pady=(0, 20))
        scrollbar.pack(side='right', fill='y', padx=(0, 30), pady=(0, 20))
        
        # Configuration du scroll
        self.canvas_window = self.content_canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor='nw'
        )
        
        self.scrollable_frame.bind('<Configure>', self.on_frame_configure)
        self.content_canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind mousewheel
        self.content_canvas.bind('<MouseWheel>', self.on_mousewheel)
        
        # Créer les contenus des étapes
        self.create_step_contents()
    
    def create_step_contents(self):
        """Création des contenus des différentes étapes"""
        # Masquer tous les contenus initialement
        self.step_frames = []
        
        # Étape 0: Configuration
        self.create_configuration_step()
        
        # Étape 1: Sélection
        self.create_selection_step()
        
        # Étape 2: Filtres
        self.create_filters_step()
        
        # Étape 3: Options
        self.create_options_step()
        
        # Étape 4: Traitement
        self.create_processing_step()
        
        # Afficher la première étape
        self.show_step(0)
    
    def create_configuration_step(self):
        """Étape 1: Configuration des chemins"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_elevated'])
        self.step_frames.append(frame)
        
        # Description
        desc_label = tk.Label(
            frame,
            text="Configurez les chemins d'entrée et de sortie pour commencer l'extraction.",
            font=self.theme.get_font('body_large'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated'],
            wraplength=800,
            justify='left'
        )
        desc_label.pack(anchor='w', pady=(0, 30))
        
        # Configuration auto-détection
        self.create_auto_detection_section(frame)
        
        # Configuration manuelle
        self.create_manual_config_section(frame)
        
        # Validation de la configuration
        self.create_config_validation_section(frame)
    
    def create_auto_detection_section(self, parent):
        """Section d'auto-détection"""
        section = ModernCard(parent, theme_manager=self.theme, elevation=1)
        section.pack(fill='x', pady=(0, 20))
        
        section_content = tk.Frame(section, bg=self.colors['bg_elevated'])
        section_content.pack(fill='both', expand=True, padx=30, pady=25)
        
        # Titre
        title = tk.Label(
            section_content,
            text="🤖 Détection Automatique",
            font=self.theme.get_font('h4'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        title.pack(anchor='w', pady=(0, 15))
        
        # Description
        desc = tk.Label(
            section_content,
            text="Laissez l'application détecter automatiquement vos exports WhatsApp.",
            font=self.theme.get_font('body'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        desc.pack(anchor='w', pady=(0, 20))
        
        # Bouton de détection
        self.auto_detect_btn = ModernButton(
            section_content,
            text="🔍 Détecter automatiquement",
            command=self.auto_detect_whatsapp,
            style="primary",
            theme_manager=self.theme
        )
        self.auto_detect_btn.pack(anchor='w')
        self.auto_detect_btn.configure(width=250, height=45)
        
        # Résultats de détection
        self.detection_results_frame = tk.Frame(
            section_content,
            bg=self.colors['bg_elevated']
        )
        self.detection_results_frame.pack(fill='x', pady=(20, 0))
    
    def create_manual_config_section(self, parent):
        """Section de configuration manuelle"""
        section = ModernCard(parent, theme_manager=self.theme, elevation=1)
        section.pack(fill='x', pady=(0, 20))
        
        section_content = tk.Frame(section, bg=self.colors['bg_elevated'])
        section_content.pack(fill='both', expand=True, padx=30, pady=25)
        
        # Titre
        title = tk.Label(
            section_content,
            text="⚙️ Configuration Manuelle",
            font=self.theme.get_font('h4'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        title.pack(anchor='w', pady=(0, 15))
        
        # Dossier source
        self.source_input = self.create_path_input(
            section_content,
            "📁 Dossier des exports WhatsApp",
            "Sélectionnez le dossier contenant les fichiers HTML de WhatsApp",
            self.browse_source_folder
        )
        
        # Dossier de sortie
        self.output_input = self.create_path_input(
            section_content,
            "📂 Dossier de sortie",
            "Sélectionnez où sauvegarder les résultats",
            self.browse_output_folder
        )
    
    def create_path_input(self, parent, label: str, placeholder: str, browse_command):
        """Créer un input de chemin avec bouton de navigation"""
        input_frame = tk.Frame(parent, bg=self.colors['bg_elevated'])
        input_frame.pack(fill='x', pady=(0, 20))
        
        # Label
        label_widget = tk.Label(
            input_frame,
            text=label,
            font=self.theme.get_font('h5'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        label_widget.pack(anchor='w', pady=(0, 8))
        
        # Input avec bouton
        input_container = tk.Frame(input_frame, bg=self.colors['bg_elevated'])
        input_container.pack(fill='x')
        
        # Entry moderne
        entry = ModernInput(
            input_container,
            placeholder=placeholder,
            theme_manager=self.theme
        )
        entry.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # Bouton parcourir
        browse_btn = ModernButton(
            input_container,
            text="📂 Parcourir",
            command=browse_command,
            style="secondary",
            theme_manager=self.theme
        )
        browse_btn.pack(side='right')
        browse_btn.configure(width=120, height=45)
        
        return entry
    
    def create_config_validation_section(self, parent):
        """Section de validation de la configuration"""
        section = ModernCard(parent, theme_manager=self.theme, elevation=1)
        section.pack(fill='x', pady=(0, 20))
        
        section_content = tk.Frame(section, bg=self.colors['bg_elevated'])
        section_content.pack(fill='both', expand=True, padx=30, pady=25)
        
        # Titre
        title = tk.Label(
            section_content,
            text="✅ Validation de la Configuration",
            font=self.theme.get_font('h4'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        title.pack(anchor='w', pady=(0, 15))
        
        # Tests de validation
        self.validation_frame = tk.Frame(
            section_content,
            bg=self.colors['bg_elevated']
        )
        self.validation_frame.pack(fill='x', pady=(0, 20))
        
        # Bouton de test
        self.test_config_btn = ModernButton(
            section_content,
            text="🧪 Tester la Configuration",
            command=self.test_configuration,
            style="secondary",
            theme_manager=self.theme
        )
        self.test_config_btn.pack(anchor='w')
        self.test_config_btn.configure(width=200, height=45)
    
    def create_selection_step(self):
        """Étape 2: Sélection des fichiers"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_elevated'])
        self.step_frames.append(frame)
        
        # Description
        desc_label = tk.Label(
            frame,
            text="Sélectionnez les conversations WhatsApp à traiter.",
            font=self.theme.get_font('body_large'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        desc_label.pack(anchor='w', pady=(0, 30))
        
        # TODO: Implémenter sélection des fichiers
        placeholder = tk.Label(
            frame,
            text="[Étape Sélection - À implémenter]",
            font=self.theme.get_font('h3'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        placeholder.pack(expand=True)
    
    def create_filters_step(self):
        """Étape 3: Configuration des filtres"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_elevated'])
        self.step_frames.append(frame)
        
        # Description
        desc_label = tk.Label(
            frame,
            text="Configurez les filtres pour affiner l'extraction.",
            font=self.theme.get_font('body_large'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        desc_label.pack(anchor='w', pady=(0, 30))
        
        # TODO: Implémenter filtres
        placeholder = tk.Label(
            frame,
            text="[Étape Filtres - À implémenter]",
            font=self.theme.get_font('h3'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        placeholder.pack(expand=True)
    
    def create_options_step(self):
        """Étape 4: Options de traitement"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_elevated'])
        self.step_frames.append(frame)
        
        # Description
        desc_label = tk.Label(
            frame,
            text="Configurez les options de transcription et d'export.",
            font=self.theme.get_font('body_large'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        desc_label.pack(anchor='w', pady=(0, 30))
        
        # TODO: Implémenter options
        placeholder = tk.Label(
            frame,
            text="[Étape Options - À implémenter]",
            font=self.theme.get_font('h3'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        placeholder.pack(expand=True)
    
    def create_processing_step(self):
        """Étape 5: Traitement et résultats"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_elevated'])
        self.step_frames.append(frame)
        
        # Description
        desc_label = tk.Label(
            frame,
            text="Lancez l'extraction et suivez le progress en temps réel.",
            font=self.theme.get_font('body_large'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        desc_label.pack(anchor='w', pady=(0, 30))
        
        # TODO: Implémenter traitement
        placeholder = tk.Label(
            frame,
            text="[Étape Traitement - À implémenter]",
            font=self.theme.get_font('h3'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_elevated']
        )
        placeholder.pack(expand=True)
    
    def create_step_navigation(self):
        """Création de la navigation entre étapes"""
        self.nav_bottom_frame = tk.Frame(
            self.content_container,
            bg=self.colors['bg_elevated'],
            height=80
        )
        self.nav_bottom_frame.pack(fill='x', side='bottom', padx=30, pady=(0, 30))
        self.nav_bottom_frame.pack_propagate(False)
        
        # Bouton précédent
        self.prev_btn = ModernButton(
            self.nav_bottom_frame,
            text="← Précédent",
            command=self.previous_step,
            style="outline",
            theme_manager=self.theme
        )
        self.prev_btn.pack(side='left', anchor='w', pady=20)
        self.prev_btn.configure(width=120, height=45)
        
        # Bouton suivant
        self.next_btn = ModernButton(
            self.nav_bottom_frame,
            text="Suivant →",
            command=self.next_step,
            style="primary",
            theme_manager=self.theme
        )
        self.next_btn.pack(side='right', anchor='e', pady=20)
        self.next_btn.configure(width=120, height=45)
        
        # Bouton de lancement (visible uniquement à la dernière étape)
        self.launch_btn = ModernButton(
            self.nav_bottom_frame,
            text="🚀 Lancer l'Extraction",
            command=self.start_extraction,
            style="primary",
            theme_manager=self.theme
        )
        self.launch_btn.configure(width=200, height=45)
        
        self.update_navigation_buttons()
    
    def create_progress_bar(self):
        """Création de la barre de progression globale"""
        self.progress_container = tk.Frame(
            self.main_container,
            bg=self.colors['bg_primary'],
            height=60
        )
        self.progress_container.grid(row=1, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 10))
        self.progress_container.grid_propagate(False)
        
        # Progress bar moderne
        self.global_progress = ModernProgressBar(
            self.progress_container,
            theme_manager=self.theme
        )
        self.global_progress.pack(fill='x', padx=20, pady=15)
        
        # Label de progression
        self.progress_label = tk.Label(
            self.progress_container,
            text="Prêt à commencer",
            font=self.theme.get_font('body'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        )
        self.progress_label.pack(pady=(0, 5))
    
    def create_status_area(self):
        """Création de la zone de statut moderne"""
        self.status_container = ModernCard(
            self.main_container,
            theme_manager=self.theme,
            glass=True
        )
        self.status_container.grid(row=2, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 20))
        
        status_content = tk.Frame(
            self.status_container,
            bg=self.theme.get_color('bg_glass')
        )
        status_content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Indicateurs de statut
        self.create_status_indicators(status_content)
        
        # Logs en temps réel
        self.create_live_logs(status_content)
    
    def create_status_indicators(self, parent):
        """Création des indicateurs de statut"""
        indicators_frame = tk.Frame(parent, bg=self.theme.get_color('bg_glass'))
        indicators_frame.pack(fill='x', pady=(0, 15))
        
        # Indicateurs
        self.status_indicators = {}
        indicators = [
            {"key": "backend", "label": "Backend", "icon": "🔧"},
            {"key": "config", "label": "Config", "icon": "⚙️"},
            {"key": "files", "label": "Fichiers", "icon": "📁"},
            {"key": "processing", "label": "Traitement", "icon": "🚀"},
        ]
        
        for i, indicator in enumerate(indicators):
            self.create_status_indicator(indicators_frame, indicator, i)
    
    def create_status_indicator(self, parent, indicator: Dict[str, str], index: int):
        """Création d'un indicateur de statut"""
        indicator_frame = tk.Frame(parent, bg=self.theme.get_color('bg_glass'))
        indicator_frame.pack(side='left', fill='x', expand=True, padx=(0, 15 if index < 3 else 0))
        
        # Icône et statut
        status_frame = tk.Frame(indicator_frame, bg=self.theme.get_color('bg_glass'))
        status_frame.pack()
        
        # Icône
        icon_label = tk.Label(
            status_frame,
            text=indicator['icon'],
            font=self.theme.get_font('body_large'),
            bg=self.theme.get_color('bg_glass')
        )
        icon_label.pack(side='left', padx=(0, 8))
        
        # Texte
        text_label = tk.Label(
            status_frame,
            text=indicator['label'],
            font=self.theme.get_font('body'),
            fg=self.colors['text_primary'],
            bg=self.theme.get_color('bg_glass')
        )
        text_label.pack(side='left')
        
        # Indicateur d'état
        state_label = tk.Label(
            status_frame,
            text="●",
            font=self.theme.get_font('body'),
            fg=self.colors['text_secondary'],
            bg=self.theme.get_color('bg_glass')
        )
        state_label.pack(side='right', padx=(10, 0))
        
        self.status_indicators[indicator['key']] = {
            'frame': indicator_frame,
            'state': state_label,
            'text': text_label
        }
    
    def create_live_logs(self, parent):
        """Création des logs en temps réel"""
        logs_frame = tk.Frame(parent, bg=self.theme.get_color('bg_glass'))
        logs_frame.pack(fill='both', expand=True)
        
        # Titre
        logs_title = tk.Label(
            logs_frame,
            text="📋 Logs en Temps Réel",
            font=self.theme.get_font('h5'),
            fg=self.colors['text_primary'],
            bg=self.theme.get_color('bg_glass')
        )
        logs_title.pack(anchor='w', pady=(0, 10))
        
        # Zone de logs
        logs_container = tk.Frame(logs_frame, bg=self.theme.get_color('bg_glass'))
        logs_container.pack(fill='both', expand=True)
        
        # Text widget pour les logs
        self.logs_text = tk.Text(
            logs_container,
            height=4,
            font=('Consolas', 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief='flat',
            bd=0,
            wrap='word',
            state='disabled'
        )
        
        # Scrollbar pour les logs
        logs_scrollbar = ttk.Scrollbar(
            logs_container,
            orient='vertical',
            command=self.logs_text.yview,
            style='Modern.Vertical.TScrollbar'
        )
        
        self.logs_text.configure(yscrollcommand=logs_scrollbar.set)
        
        self.logs_text.pack(side='left', fill='both', expand=True)
        logs_scrollbar.pack(side='right', fill='y')
    
    def setup_keyboard_shortcuts(self):
        """Configuration des raccourcis clavier"""
        self.root.bind('<Control-n>', lambda e: self.next_step())
        self.root.bind('<Control-p>', lambda e: self.previous_step())
        self.root.bind('<Control-r>', lambda e: self.reset_workflow())
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.refresh_ui())
    
    # === Méthodes de navigation ===
    
    def navigate_to_step(self, step_index: int):
        """Navigation vers une étape spécifique"""
        if 0 <= step_index < len(self.step_frames):
            self.current_step = step_index
            self.show_step(step_index)
            self.update_navigation_buttons()
            self.update_navigation_ui()
    
    def show_step(self, step_index: int):
        """Affichage d'une étape spécifique"""
        # Masquer tous les frames
        for frame in self.step_frames:
            frame.pack_forget()
        
        # Afficher le frame de l'étape courante
        if 0 <= step_index < len(self.step_frames):
            self.step_frames[step_index].pack(fill='both', expand=True)
    
    def next_step(self):
        """Aller à l'étape suivante"""
        if self.current_step < len(self.step_frames) - 1:
            if self.validate_current_step():
                self.navigate_to_step(self.current_step + 1)
            else:
                self.show_toast("Veuillez compléter cette étape avant de continuer.", "warning")
    
    def previous_step(self):
        """Aller à l'étape précédente"""
        if self.current_step > 0:
            self.navigate_to_step(self.current_step - 1)
    
    def update_navigation_buttons(self):
        """Mise à jour des boutons de navigation"""
        # Bouton précédent
        if self.current_step == 0:
            self.prev_btn.pack_forget()
        else:
            self.prev_btn.pack(side='left', anchor='w', pady=20)
        
        # Boutons suivant/lancement
        if self.current_step == len(self.step_frames) - 1:
            self.next_btn.pack_forget()
            self.launch_btn.pack(side='right', anchor='e', pady=20)
        else:
            self.launch_btn.pack_forget()
            self.next_btn.pack(side='right', anchor='e', pady=20)
    
    def update_navigation_ui(self):
        """Mise à jour de l'interface de navigation"""
        # Mettre à jour le titre et l'indicateur
        steps = ["Configuration", "Sélection", "Filtres", "Options", "Traitement"]
        if 0 <= self.current_step < len(steps):
            self.step_title.configure(text=steps[self.current_step])
            self.step_indicator.configure(text=f"Étape {self.current_step + 1} sur {len(steps)}")
        
        # Mettre à jour la navigation sidebar
        for i, nav_item in enumerate(self.nav_buttons):
            if i == self.current_step:
                nav_item['button'].configure(
                    bg=self.colors['bg_elevated'],
                    fg=self.colors['primary']
                )
            else:
                nav_item['button'].configure(
                    bg=self.colors['bg_secondary'],
                    fg=self.colors['text_primary']
                )
    
    def validate_current_step(self) -> bool:
        """Validation de l'étape courante"""
        if self.current_step == 0:  # Configuration
            # Vérifier que les chemins sont configurés
            source_path = self.source_input.get() if hasattr(self, 'source_input') else ""
            output_path = self.output_input.get() if hasattr(self, 'output_input') else ""
            
            valid = bool(source_path and output_path)
            self.step_validation[0] = valid
            
            if valid:
                self.workflow_data['source_path'] = source_path
                self.workflow_data['output_path'] = output_path
            
            return valid
        
        # Pour les autres étapes, validation simplifiée pour l'instant
        return True
    
    # === Méthodes d'action ===
    
    def auto_detect_whatsapp(self):
        """Auto-détection des exports WhatsApp"""
        self.show_toast("Recherche des exports WhatsApp...", "info")
        
        # TODO: Implémenter la détection automatique
        # Pour l'instant, simulation
        def detect_task():
            import time
            time.sleep(2)  # Simulation
            
            # Résultats simulés
            self.root.after(0, lambda: self.on_detection_complete([
                {"path": "C:/Users/Demo/WhatsApp/Chat 1.html", "contacts": 5, "messages": 150},
                {"path": "C:/Users/Demo/WhatsApp/Chat 2.html", "contacts": 3, "messages": 87},
            ]))
        
        threading.Thread(target=detect_task, daemon=True).start()
    
    def on_detection_complete(self, results: List[Dict[str, Any]]):
        """Callback de fin de détection"""
        if results:
            self.show_detection_results(results)
            self.show_toast(f"Trouvé {len(results)} exports WhatsApp!", "success")
        else:
            self.show_toast("Aucun export WhatsApp trouvé.", "warning")
    
    def show_detection_results(self, results: List[Dict[str, Any]]):
        """Affichage des résultats de détection"""
        # Nettoyer les résultats précédents
        for widget in self.detection_results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            return
        
        # Titre
        title = tk.Label(
            self.detection_results_frame,
            text="📋 Exports Détectés",
            font=self.theme.get_font('h5'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated']
        )
        title.pack(anchor='w', pady=(0, 15))
        
        # Liste des résultats
        for i, result in enumerate(results):
            self.create_detection_result_item(self.detection_results_frame, result, i)
    
    def create_detection_result_item(self, parent, result: Dict[str, Any], index: int):
        """Création d'un item de résultat de détection"""
        item_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        item_frame.pack(fill='x', pady=(0, 8))
        
        content = tk.Frame(item_frame, bg=self.colors['bg_secondary'])
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Chemin
        path_label = tk.Label(
            content,
            text=f"📁 {result['path']}",
            font=self.theme.get_font('body'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            anchor='w'
        )
        path_label.pack(fill='x')
        
        # Statistiques
        stats_label = tk.Label(
            content,
            text=f"👥 {result['contacts']} contacts • 💬 {result['messages']} messages",
            font=self.theme.get_font('caption'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary'],
            anchor='w'
        )
        stats_label.pack(fill='x', pady=(5, 0))
    
    def browse_source_folder(self):
        """Navigation pour le dossier source"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier des exports WhatsApp")
        if folder:
            self.source_input.set(folder)
            self.show_toast("Dossier source configuré!", "success")
    
    def browse_output_folder(self):
        """Navigation pour le dossier de sortie"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if folder:
            self.output_input.set(folder)
            self.show_toast("Dossier de sortie configuré!", "success")
    
    def test_configuration(self):
        """Test de la configuration"""
        self.show_toast("Test de la configuration en cours...", "info")
        
        def test_task():
            if not HAS_BACKEND:
                self.root.after(0, lambda: self.on_config_test_complete({
                    'backend': False,
                    'config': False,
                    'source_path': False,
                    'output_path': False,
                    'api_key': False
                }))
                return
            
            try:
                # Initialiser le backend si pas encore fait
                if not self.config_manager:
                    self.config_manager = ConfigManager()
                
                if not self.extraction_pipeline:
                    self.extraction_pipeline = ExtractionPipeline(self.config_manager)
                
                # Tester la configuration
                test_results = self.extraction_pipeline.test_configuration()
                self.root.after(0, lambda: self.on_config_test_complete(test_results))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_config_test_error(str(e)))
        
        threading.Thread(target=test_task, daemon=True).start()
    
    def on_config_test_complete(self, results: Dict[str, bool]):
        """Callback de fin de test de configuration"""
        # Effacer les résultats précédents
        for widget in self.validation_frame.winfo_children():
            widget.destroy()
        
        # Afficher les résultats
        tests = [
            {"key": "backend", "label": "Backend disponible", "icon": "🔧"},
            {"key": "config_valid", "label": "Configuration valide", "icon": "⚙️"},
            {"key": "source_path_exists", "label": "Dossier source accessible", "icon": "📁"},
            {"key": "output_dir_writable", "label": "Dossier sortie accessible", "icon": "📂"},
            {"key": "api_key_valid", "label": "Clé API valide", "icon": "🔑"},
        ]
        
        all_passed = True
        for test in tests:
            result = results.get(test['key'], False)
            if not result:
                all_passed = False
            
            self.create_validation_result(self.validation_frame, test, result)
        
        # Message de résumé
        if all_passed:
            self.show_toast("Configuration valide! ✅", "success")
            self.step_validation[0] = True
        else:
            self.show_toast("Problèmes détectés dans la configuration", "warning")
        
        self.update_validation_indicator(0)
    
    def on_config_test_error(self, error: str):
        """Callback d'erreur de test de configuration"""
        self.show_toast(f"Erreur lors du test: {error}", "error")
    
    def create_validation_result(self, parent, test: Dict[str, str], result: bool):
        """Création d'un résultat de validation"""
        result_frame = tk.Frame(parent, bg=self.colors['bg_elevated'])
        result_frame.pack(fill='x', pady=2)
        
        # Icône de statut
        status_icon = "✅" if result else "❌"
        status_color = self.colors['success'] if result else self.colors['error']
        
        status_label = tk.Label(
            result_frame,
            text=status_icon,
            font=self.theme.get_font('body'),
            fg=status_color,
            bg=self.colors['bg_elevated']
        )
        status_label.pack(side='left', padx=(0, 10))
        
        # Label du test
        test_label = tk.Label(
            result_frame,
            text=f"{test['icon']} {test['label']}",
            font=self.theme.get_font('body'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_elevated'],
            anchor='w'
        )
        test_label.pack(side='left', fill='x', expand=True)
    
    def update_validation_indicator(self, step_index: int):
        """Mise à jour de l'indicateur de validation d'une étape"""
        if 0 <= step_index < len(self.nav_buttons):
            nav_item = self.nav_buttons[step_index]
            is_valid = self.step_validation.get(step_index, False)
            
            nav_item['indicator'].configure(
                text="✓" if is_valid else "○",
                fg=self.colors['success'] if is_valid else self.colors['text_tertiary']
            )
    
    def start_extraction(self):
        """Démarrage de l'extraction"""
        if not self.validate_current_step():
            self.show_toast("Veuillez compléter toutes les étapes avant de lancer l'extraction.", "warning")
            return
        
        self.show_toast("Démarrage de l'extraction...", "info")
        self.is_processing = True
        
        # TODO: Implémenter l'extraction réelle
        def extraction_task():
            import time
            for i in range(101):
                progress = i / 100.0
                task_name = f"Traitement en cours... {i}%"
                
                self.root.after(0, lambda p=progress, t=task_name: self.update_extraction_progress(p, t))
                time.sleep(0.05)  # Simulation
                
                if not self.is_processing:  # Arrêt demandé
                    break
            
            if self.is_processing:
                self.root.after(0, lambda: self.on_extraction_complete({"status": "success"}))
        
        threading.Thread(target=extraction_task, daemon=True).start()
    
    def update_extraction_progress(self, progress: float, task_name: str):
        """Mise à jour du progrès d'extraction"""
        self.global_progress.set_progress(progress)
        self.progress_label.configure(text=task_name)
    
    def on_extraction_complete(self, results: Dict[str, Any]):
        """Callback de fin d'extraction"""
        self.is_processing = False
        
        if results.get('status') == 'success':
            self.show_toast("Extraction terminée avec succès! 🎉", "success")
            self.update_status_indicator('processing', True)
        else:
            self.show_toast("Erreur lors de l'extraction", "error")
            self.update_status_indicator('processing', False)
    
    # === Méthodes utilitaires ===
    
    def toggle_theme(self):
        """Basculer entre thème clair/sombre"""
        self.theme.toggle_theme()
        self.refresh_ui()
        self.show_toast(f"Thème {self.theme.current_theme} activé", "info")
    
    def refresh_ui(self):
        """Actualisation de l'interface"""
        # Réappliquer le thème
        self.setup_theme()
        
        # Actualiser les widgets
        self.root.update_idletasks()
    
    def show_toast(self, message: str, type: str = "info"):
        """Affichage d'une notification toast"""
        ModernToast(self.root, message, type, theme_manager=self.theme)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Ajout d'un message aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\\n"
        
        self.logs_text.configure(state='normal')
        self.logs_text.insert('end', formatted_message)
        self.logs_text.configure(state='disabled')
        self.logs_text.see('end')
    
    def update_status_indicator(self, key: str, status: bool):
        """Mise à jour d'un indicateur de statut"""
        if key in self.status_indicators:
            indicator = self.status_indicators[key]
            color = self.colors['success'] if status else self.colors['error']
            indicator['state'].configure(fg=color)
    
    def load_initial_config(self):
        """Chargement de la configuration initiale"""
        try:
            if HAS_BACKEND:
                self.config_manager = ConfigManager()
                # Ne pas charger automatiquement pour éviter les erreurs
                self.update_status_indicator('backend', True)
                self.update_status_indicator('config', True)
            else:
                self.update_status_indicator('backend', False)
                self.update_status_indicator('config', False)
        except Exception as e:
            self.log_message(f"Erreur lors du chargement de la configuration: {e}", "ERROR")
            self.update_status_indicator('config', False)
    
    def check_tasks_timer(self):
        """Vérification périodique des tâches"""
        try:
            results = self.threading_manager.get_pending_results()
            
            for result in results:
                self.log_message(f"Tâche terminée: {result.task_id}")
                
        except Exception as e:
            self.log_message(f"Erreur check_tasks_timer: {e}", "DEBUG")
        
        # Programmer la prochaine vérification
        self.root.after(1000, self.check_tasks_timer)
    
    # === Méthodes de callback pour les scrolls ===
    
    def on_frame_configure(self, event=None):
        """Callback de redimensionnement du frame scrollable"""
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """Callback de redimensionnement du canvas"""
        canvas_width = event.width
        self.content_canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        """Callback de la molette de souris"""
        self.content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    # === Actions rapides ===
    
    def open_output_folder(self):
        """Ouvrir le dossier de sortie"""
        output_path = self.workflow_data.get('output_path')
        if output_path and Path(output_path).exists():
            os.startfile(output_path)
        else:
            self.show_toast("Dossier de sortie non configuré", "warning")
    
    def view_results(self):
        """Voir les résultats"""
        self.show_toast("Fonctionnalité en cours de développement", "info")
    
    def reset_workflow(self):
        """Réinitialiser le workflow"""
        result = messagebox.askyesno(
            "Réinitialiser",
            "Êtes-vous sûr de vouloir réinitialiser le workflow?\\nTous les paramètres seront perdus."
        )
        
        if result:
            self.workflow_data = {
                'source_path': '',
                'output_path': '',
                'selected_contacts': [],
                'filter_settings': {},
                'processing_options': {},
                'results': {}
            }
            
            self.step_validation = {i: False for i in range(5)}
            self.current_step = 0
            self.navigate_to_step(0)
            
            # Réinitialiser les inputs
            if hasattr(self, 'source_input'):
                self.source_input.set("")
            if hasattr(self, 'output_input'):
                self.output_input.set("")
            
            self.show_toast("Workflow réinitialisé", "success")
    
    def save_config(self):
        """Sauvegarder la configuration"""
        try:
            config_data = {
                'workflow_data': self.workflow_data,
                'step_validation': self.step_validation,
                'current_step': self.current_step,
                'theme': self.theme.current_theme,
                'timestamp': datetime.now().isoformat()
            }
            
            with open('workflow_config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.show_toast("Configuration sauvegardée", "success")
            
        except Exception as e:
            self.show_toast(f"Erreur de sauvegarde: {e}", "error")
    
    def show_help(self):
        """Afficher l'aide"""
        help_text = """
        🚀 WhatsApp Extractor v2 - Guide Rapide
        
        📋 Raccourcis Clavier:
        • Ctrl+N : Étape suivante
        • Ctrl+P : Étape précédente  
        • Ctrl+R : Réinitialiser
        • Ctrl+S : Sauvegarder
        • F1 : Aide
        • F5 : Actualiser
        
        🔄 Workflow:
        1. Configuration : Définir les chemins
        2. Sélection : Choisir les conversations
        3. Filtres : Affiner l'extraction
        4. Options : Paramétrer transcription/export
        5. Traitement : Lancer et suivre
        """
        
        messagebox.showinfo("Aide - WhatsApp Extractor v2", help_text)
    
    def run(self):
        """Lancement de l'application"""
        self.root.mainloop()


def main():
    """Point d'entrée principal"""
    try:
        app = ModernWhatsAppExtractor()
        app.run()
    except Exception as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()