#!/usr/bin/env python3
"""
Gestionnaire de threading pour l'interface graphique
Permet l'exécution non-bloquante des opérations longues
"""

import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """États possibles d'une tâche"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class TaskResult:
    """Résultat d'une tâche"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    progress: float = 0.0
    message: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ProgressCallback:
    """Callback pour le suivi de progression"""
    
    def __init__(self, gui_callback: Callable[[str, float, str], None]):
        self.gui_callback = gui_callback
        
    def update(self, task_id: str, progress: float, message: str = ""):
        """Mettre à jour la progression"""
        try:
            self.gui_callback(task_id, progress, message)
        except Exception as e:
            logger.error(f"Erreur dans le callback de progression: {e}")


class BackgroundTask:
    """Représente une tâche en arrière-plan"""
    
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0.0
        self.message = ""
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.should_stop = threading.Event()
        self.is_paused = threading.Event()
        
    def run(self, progress_callback: Optional[ProgressCallback] = None):
        """Exécuter la tâche"""
        try:
            self.status = TaskStatus.RUNNING
            self.start_time = time.time()
            
            # Ajouter le callback de progression aux kwargs si nécessaire
            if progress_callback and 'progress_callback' not in self.kwargs:
                self.kwargs['progress_callback'] = progress_callback
                
            # Ajouter l'événement d'arrêt aux kwargs si nécessaire
            if 'stop_event' not in self.kwargs:
                self.kwargs['stop_event'] = self.should_stop
                
            # Ajouter l'événement de pause aux kwargs si nécessaire
            if 'pause_event' not in self.kwargs:
                self.kwargs['pause_event'] = self.is_paused
                
            # Exécuter la fonction
            self.result = self.func(*self.args, **self.kwargs)
            
            if self.should_stop.is_set():
                self.status = TaskStatus.CANCELLED
            else:
                self.status = TaskStatus.COMPLETED
                self.progress = 100.0
                
        except Exception as e:
            self.error = e
            self.status = TaskStatus.FAILED
            logger.error(f"Erreur dans la tâche {self.task_id}: {e}")
            
        finally:
            self.end_time = time.time()
            
    def stop(self):
        """Arrêter la tâche"""
        self.should_stop.set()
        
    def pause(self):
        """Mettre en pause la tâche"""
        self.is_paused.set()
        self.status = TaskStatus.PAUSED
        
    def resume(self):
        """Reprendre la tâche"""
        self.is_paused.clear()
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            
    def get_result(self) -> TaskResult:
        """Obtenir le résultat de la tâche"""
        return TaskResult(
            task_id=self.task_id,
            status=self.status,
            result=self.result,
            error=self.error,
            progress=self.progress,
            message=self.message,
            start_time=self.start_time,
            end_time=self.end_time
        )


class ThreadingManager:
    """Gestionnaire de tâches en arrière-plan pour l'interface graphique"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.active_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.result_queue = queue.Queue()
        self.progress_callbacks: Dict[str, ProgressCallback] = {}
        self.lock = threading.Lock()
        self._next_task_id = 1
        
    def generate_task_id(self) -> str:
        """Générer un ID unique pour une tâche"""
        with self.lock:
            task_id = f"task_{self._next_task_id}"
            self._next_task_id += 1
            return task_id
            
    def submit_task(self, 
                    func: Callable, 
                    args: tuple = (), 
                    kwargs: dict = None,
                    task_id: Optional[str] = None,
                    progress_callback: Optional[Callable[[str, float, str], None]] = None) -> str:
        """Soumettre une tâche pour exécution en arrière-plan"""
        
        if task_id is None:
            task_id = self.generate_task_id()
            
        # Vérifier qu'il n'y a pas trop de tâches actives
        with self.lock:
            if len(self.active_tasks) >= self.max_workers:
                raise RuntimeError(f"Trop de tâches actives ({len(self.active_tasks)}/{self.max_workers})")
                
            task = BackgroundTask(task_id, func, args, kwargs or {})
            self.active_tasks[task_id] = task
            
        # Créer le callback de progression si fourni
        if progress_callback:
            self.progress_callbacks[task_id] = ProgressCallback(progress_callback)
            
        # Démarrer la tâche dans un thread
        def task_wrapper():
            try:
                progress_cb = self.progress_callbacks.get(task_id)
                task.run(progress_cb)
            finally:
                # Déplacer la tâche vers les tâches complétées
                with self.lock:
                    if task_id in self.active_tasks:
                        completed_task = self.active_tasks.pop(task_id)
                        self.completed_tasks[task_id] = completed_task
                        
                # Mettre le résultat dans la queue
                self.result_queue.put(task.get_result())
                
                # Nettoyer le callback
                if task_id in self.progress_callbacks:
                    del self.progress_callbacks[task_id]
                    
        task.thread = threading.Thread(target=task_wrapper, daemon=True)
        task.thread.start()
        
        logger.info(f"Tâche {task_id} démarrée")
        return task_id
        
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Obtenir le statut d'une tâche"""
        with self.lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].status
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].status
            else:
                return None
                
    def get_task_progress(self, task_id: str) -> float:
        """Obtenir la progression d'une tâche"""
        with self.lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].progress
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].progress
            else:
                return 0.0
                
    def stop_task(self, task_id: str) -> bool:
        """Arrêter une tâche"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.stop()
                logger.info(f"Arrêt demandé pour la tâche {task_id}")
                return True
            else:
                return False
                
    def pause_task(self, task_id: str) -> bool:
        """Mettre en pause une tâche"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.pause()
                logger.info(f"Pause demandée pour la tâche {task_id}")
                return True
            else:
                return False
                
    def resume_task(self, task_id: str) -> bool:
        """Reprendre une tâche"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.resume()
                logger.info(f"Reprise demandée pour la tâche {task_id}")
                return True
            else:
                return False
                
    def stop_all_tasks(self):
        """Arrêter toutes les tâches actives"""
        with self.lock:
            task_ids = list(self.active_tasks.keys())
            
        for task_id in task_ids:
            self.stop_task(task_id)
            
        logger.info(f"Arrêt demandé pour {len(task_ids)} tâches")
        
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Attendre qu'une tâche se termine"""
        start_time = time.time()
        
        while True:
            status = self.get_task_status(task_id)
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                with self.lock:
                    if task_id in self.completed_tasks:
                        return self.completed_tasks[task_id].get_result()
                break
                
            if timeout and (time.time() - start_time) > timeout:
                return None
                
            time.sleep(0.1)
            
        return None
        
    def get_pending_results(self) -> list[TaskResult]:
        """Récupérer tous les résultats en attente"""
        results = []
        
        try:
            while True:
                result = self.result_queue.get_nowait()
                results.append(result)
        except queue.Empty:
            pass
            
        return results
        
    def get_active_task_count(self) -> int:
        """Obtenir le nombre de tâches actives"""
        with self.lock:
            return len(self.active_tasks)
            
    def get_completed_task_count(self) -> int:
        """Obtenir le nombre de tâches complétées"""
        with self.lock:
            return len(self.completed_tasks)
            
    def clear_completed_tasks(self):
        """Nettoyer les tâches complétées"""
        with self.lock:
            self.completed_tasks.clear()
            
        logger.info("Tâches complétées nettoyées")
        
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtenir les informations détaillées d'une tâche"""
        with self.lock:
            task = None
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
            elif task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                
            if task:
                duration = None
                if task.start_time:
                    end_time = task.end_time or time.time()
                    duration = end_time - task.start_time
                    
                return {
                    'task_id': task.task_id,
                    'status': task.status.value,
                    'progress': task.progress,
                    'message': task.message,
                    'start_time': task.start_time,
                    'end_time': task.end_time,
                    'duration': duration,
                    'has_error': task.error is not None,
                    'error_message': str(task.error) if task.error else None
                }
                
        return None
        
    def shutdown(self):
        """Arrêter le gestionnaire et toutes les tâches"""
        logger.info("Arrêt du gestionnaire de threading...")
        self.stop_all_tasks()
        
        # Attendre que toutes les tâches se terminent
        with self.lock:
            active_tasks = list(self.active_tasks.values())
            
        for task in active_tasks:
            if task.thread and task.thread.is_alive():
                task.thread.join(timeout=5.0)
                
        self.clear_completed_tasks()
        logger.info("Gestionnaire de threading arrêté")


# Fonctions utilitaires pour créer des tâches courantes

def create_extraction_task(extraction_func: Callable, 
                          config: Any,
                          progress_callback: Optional[Callable] = None) -> Callable:
    """Créer une tâche d'extraction adaptée au threading"""
    
    def extraction_wrapper(progress_callback=None, stop_event=None, pause_event=None):
        """Wrapper pour la fonction d'extraction"""
        
        def progress_updater(current: int, total: int, message: str = ""):
            if progress_callback:
                progress = (current / total) * 100 if total > 0 else 0
                progress_callback.update("extraction", progress, message)
                
        def should_continue():
            """Vérifier si on doit continuer l'exécution"""
            if stop_event and stop_event.is_set():
                return False
                
            # Gérer la pause
            if pause_event and pause_event.is_set():
                while pause_event.is_set() and not (stop_event and stop_event.is_set()):
                    time.sleep(0.1)
                    
            return not (stop_event and stop_event.is_set())
            
        # Ajouter les callbacks à la config si possible
        if hasattr(config, 'progress_callback'):
            config.progress_callback = progress_updater
        if hasattr(config, 'should_continue'):
            config.should_continue = should_continue
            
        return extraction_func(config)
        
    return extraction_wrapper


def create_transcription_task(transcription_func: Callable,
                             audio_files: list,
                             progress_callback: Optional[Callable] = None) -> Callable:
    """Créer une tâche de transcription adaptée au threading"""
    
    def transcription_wrapper(progress_callback=None, stop_event=None, pause_event=None):
        """Wrapper pour la fonction de transcription"""
        
        results = []
        total_files = len(audio_files)
        
        for i, audio_file in enumerate(audio_files):
            # Vérifier si on doit s'arrêter
            if stop_event and stop_event.is_set():
                break
                
            # Gérer la pause
            if pause_event and pause_event.is_set():
                while pause_event.is_set() and not (stop_event and stop_event.is_set()):
                    time.sleep(0.1)
                    
            try:
                # Mettre à jour la progression
                if progress_callback:
                    progress = (i / total_files) * 100
                    message = f"Transcription de {audio_file.name}..."
                    progress_callback.update("transcription", progress, message)
                    
                # Transcrire le fichier
                result = transcription_func(audio_file)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Erreur lors de la transcription de {audio_file}: {e}")
                
        # Progression finale
        if progress_callback:
            progress_callback.update("transcription", 100.0, "Transcription terminée")
            
        return results
        
    return transcription_wrapper