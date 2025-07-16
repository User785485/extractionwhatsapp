"""
Onglet d'extraction amélioré avec intégration complète du workflow Claude Tools
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import List, Optional
import json

from .workflow_integration import WorkflowIntegration

class EnhancedExtractionTab:
    """Onglet d'extraction avec workflow complet"""
    
    def __init__(self, parent):
        self.parent = parent
        self.workflow = None
        self.selected_files = []
        
        # Variables UI
        self.transcribe_var = tk.BooleanVar(value=True)
        self.parallel_var = tk.BooleanVar(value=True)
        self.csv_var = tk.BooleanVar(value=True)
        self.txt_var = tk.BooleanVar(value=True)
        self.markdown_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configuration de l'interface"""
        
        # Frame principale avec padding
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configuration grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)  # Zone de log extensible
        
        # Section 1: Sélection des fichiers
        self._create_file_section(main_frame)
        
        # Section 2: Options de traitement
        self._create_options_section(main_frame)
        
        # Section 3: Contrôles
        self._create_controls_section(main_frame)
        
        # Section 4: Progression et logs
        self._create_progress_section(main_frame)
        
    def _create_file_section(self, parent):
        """Section de sélection des fichiers"""
        
        # Frame pour la sélection
        file_frame = ttk.LabelFrame(parent, text="Sélection des fichiers", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Boutons de sélection
        ttk.Button(
            file_frame,
            text="Sélectionner fichiers HTML",
            command=self.select_files
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            file_frame,
            text="Sélectionner dossier",
            command=self.select_folder
        ).grid(row=0, column=1, padx=5)
        
        # Label pour afficher la sélection
        self.selection_label = ttk.Label(file_frame, text="Aucun fichier sélectionné")
        self.selection_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Chemin des médias
        ttk.Label(file_frame, text="Dossier médias:").grid(row=2, column=0, sticky="e", padx=5)
        
        self.media_path_var = tk.StringVar(
            value=r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519"
        )
        
        media_entry = ttk.Entry(file_frame, textvariable=self.media_path_var, width=50)
        media_entry.grid(row=2, column=1, padx=5)
        
        ttk.Button(
            file_frame,
            text="Parcourir",
            command=self.browse_media_folder
        ).grid(row=2, column=2, padx=5)
        
    def _create_options_section(self, parent):
        """Section des options de traitement"""
        
        options_frame = ttk.LabelFrame(parent, text="Options de traitement", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Options principales
        ttk.Checkbutton(
            options_frame,
            text="Transcrire les messages audio (Whisper API)",
            variable=self.transcribe_var
        ).grid(row=0, column=0, sticky="w", pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Traitement parallèle (plus rapide)",
            variable=self.parallel_var
        ).grid(row=1, column=0, sticky="w", pady=2)
        
        # Formats d'export
        export_label = ttk.Label(options_frame, text="Formats d'export:")
        export_label.grid(row=2, column=0, sticky="w", pady=(10, 2))
        
        formats_frame = ttk.Frame(options_frame)
        formats_frame.grid(row=3, column=0, sticky="w", padx=(20, 0))
        
        ttk.Checkbutton(
            formats_frame,
            text="CSV",
            variable=self.csv_var
        ).grid(row=0, column=0, padx=5)
        
        ttk.Checkbutton(
            formats_frame,
            text="TXT",
            variable=self.txt_var
        ).grid(row=0, column=1, padx=5)
        
        ttk.Checkbutton(
            formats_frame,
            text="Markdown",
            variable=self.markdown_var
        ).grid(row=0, column=2, padx=5)
        
        # Langue pour transcription
        ttk.Label(options_frame, text="Langue transcription:").grid(row=4, column=0, sticky="w", pady=(10, 2))
        
        self.language_var = tk.StringVar(value="fr")
        language_combo = ttk.Combobox(
            options_frame,
            textvariable=self.language_var,
            values=["fr", "en", "es", "ar", "auto"],
            width=10,
            state="readonly"
        )
        language_combo.grid(row=4, column=0, sticky="w", padx=(140, 0))
        
    def _create_controls_section(self, parent):
        """Section des boutons de contrôle"""
        
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Boutons principaux
        self.start_button = ttk.Button(
            controls_frame,
            text="Démarrer le traitement",
            command=self.start_processing,
            style="Primary.TButton"
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            controls_frame,
            text="Arrêter",
            command=self.stop_processing,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            controls_frame,
            text="Ouvrir dossier résultats",
            command=self.open_output_folder
        ).grid(row=0, column=2, padx=5)
        
    def _create_progress_section(self, parent):
        """Section de progression et logs"""
        
        # Progress bar
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1)
        
        # Zone de logs
        log_frame = ttk.LabelFrame(parent, text="Journal d'exécution", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
        
        # Text widget avec scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            log_container,
            wrap="word",
            height=10,
            font=("Consolas", 9)
        )
        
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tags pour couleurs
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("info", foreground="blue")
        
    def select_files(self):
        """Sélectionner des fichiers HTML"""
        files = filedialog.askopenfilenames(
            title="Sélectionner fichiers WhatsApp HTML",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if files:
            self.selected_files = list(files)
            self.selection_label.config(
                text=f"{len(self.selected_files)} fichier(s) sélectionné(s)"
            )
            
    def select_folder(self):
        """Sélectionner un dossier"""
        folder = filedialog.askdirectory(
            title="Sélectionner dossier WhatsApp"
        )
        
        if folder:
            self.selected_files = [folder]
            # Compter les HTML dans le dossier
            html_count = len(list(Path(folder).glob("*.html")))
            self.selection_label.config(
                text=f"Dossier: {Path(folder).name} ({html_count} fichiers HTML)"
            )
            
    def browse_media_folder(self):
        """Parcourir pour sélectionner le dossier média"""
        folder = filedialog.askdirectory(
            title="Sélectionner dossier des médias WhatsApp"
        )
        
        if folder:
            self.media_path_var.set(folder)
            
    def start_processing(self):
        """Démarrer le traitement"""
        
        if not self.selected_files:
            messagebox.showwarning(
                "Sélection requise",
                "Veuillez sélectionner des fichiers ou un dossier à traiter."
            )
            return
            
        # Préparer les options
        export_formats = []
        if self.csv_var.get():
            export_formats.append("csv")
        if self.txt_var.get():
            export_formats.append("text")
        if self.markdown_var.get():
            export_formats.append("markdown")
            
        if not export_formats:
            messagebox.showwarning(
                "Format requis",
                "Veuillez sélectionner au moins un format d'export."
            )
            return
            
        options = {
            'transcribe': self.transcribe_var.get(),
            'export_formats': export_formats,
            'language': self.language_var.get(),
            'parallel': self.parallel_var.get(),
            'media_path': self.media_path_var.get()
        }
        
        # Vérifier la clé API si transcription demandée
        if options['transcribe']:
            import os
            if not os.getenv('OPENAI_API_KEY'):
                messagebox.showwarning(
                    "Clé API requise",
                    "Pour la transcription, définissez OPENAI_API_KEY dans les variables d'environnement."
                )
                return
                
        # UI: désactiver boutons
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Effacer logs
        self.log_text.delete("1.0", tk.END)
        self.log("Démarrage du traitement...", "info")
        
        # Créer workflow
        self.workflow = WorkflowIntegration(
            progress_callback=self.update_progress,
            log_callback=self.log
        )
        
        # Lancer dans un thread
        self.processing_thread = threading.Thread(
            target=self._run_processing,
            args=(self.selected_files, options),
            daemon=True
        )
        self.processing_thread.start()
        
    def _run_processing(self, files: List[str], options: Dict):
        """Exécuter le traitement (dans un thread)"""
        
        try:
            result = self.workflow.process_files(files, options)
            
            if result['success']:
                self.log(f"\n[SUCCESS] Traitement terminé!", "success")
                self.log(f"Fichiers traités: {result['stats']['processed']}", "success")
                self.log(f"Avec audio: {result['stats']['with_audio']}", "success")
                self.log(f"Transcrits: {result['stats']['transcribed']}", "success")
                self.log(f"Résultats dans: {result['output_dir']}", "info")
                
                # Afficher notification
                self.parent.after(0, lambda: messagebox.showinfo(
                    "Traitement terminé",
                    f"Traitement réussi!\n\n"
                    f"Fichiers traités: {result['stats']['processed']}\n"
                    f"Transcriptions: {result['stats']['transcribed']}\n\n"
                    f"Résultats dans: {result['output_dir']}"
                ))
            else:
                self.log(f"\n[ERROR] Échec du traitement: {result.get('error')}", "error")
                
        except Exception as e:
            self.log(f"\n[ERROR] Exception: {str(e)}", "error")
            
        finally:
            # Réactiver UI
            self.parent.after(0, self._processing_complete)
            
    def _processing_complete(self):
        """Actions après fin du traitement"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_var.set(100)
        self.progress_label.config(text="100%")
        
    def stop_processing(self):
        """Arrêter le traitement"""
        if self.workflow:
            self.workflow.cancel_processing()
            self.log("Annulation en cours...", "info")
            
    def update_progress(self, value: int):
        """Mettre à jour la progression"""
        self.parent.after(0, lambda: self._update_progress_ui(value))
        
    def _update_progress_ui(self, value: int):
        """MAJ UI progression (thread principal)"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value}%")
        
    def log(self, message: str, tag: Optional[str] = None):
        """Ajouter un message au log"""
        self.parent.after(0, lambda: self._log_ui(message, tag))
        
    def _log_ui(self, message: str, tag: Optional[str] = None):
        """MAJ UI log (thread principal)"""
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        
    def open_output_folder(self):
        """Ouvrir le dossier de résultats"""
        output_dir = Path(__file__).parent.parent.parent / "claude_tools" / "output"
        output_dir.mkdir(exist_ok=True)
        
        import os
        import platform
        
        if platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{output_dir}'")
        else:  # Linux
            os.system(f"xdg-open '{output_dir}'")