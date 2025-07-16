# Claude Operations Guide
**Boîte à Outils WhatsApp - Guide Opérationnel Complet**

---

## 🎯 Vue d'Ensemble

Cette boîte à outils a été spécialement conçue pour **Claude** par un créateur qui connaît parfaitement ses patterns de travail et ses besoins. Chaque outil est optimisé pour l'efficacité, la simplicité d'usage, et l'autonomie.

### Philosophie
- **Outils spécialisés** : Chaque script fait une chose et la fait bien
- **Chainables** : Les outils peuvent être utilisés ensemble ou séparément
- **Cache intelligent** : Évite les re-calculs coûteux
- **Logs structurés** : Debug autonome avec informations détaillées
- **Formats multiples** : Exports adaptés à différents usages

---

## 📁 Structure des Outils

```
claude_tools/
├── bin/                    # Scripts exécutables
│   ├── parse_received.py   # Parser messages reçus uniquement
│   ├── find_media.py       # Détection et mapping médias
│   ├── convert_audio.py    # Conversion audio universelle
│   ├── transcribe.py       # Interface Whisper optimisée
│   ├── analyze.py          # Analyseur et générateur rapports
│   └── process_all.py      # Pipeline complet automatisé
├── lib/                    # Modules réutilisables
│   └── logger.py          # Système de logs structurés
├── cache/                  # Cache des transcriptions
├── logs/                   # Logs d'exécution
└── output/                # Résultats générés
```

---

## 🚀 Démarrage Rapide

### Prérequis
```bash
# Python packages
pip install beautifulsoup4 openai

# FFmpeg (pour conversion audio)
# Windows: télécharger depuis https://ffmpeg.org/
# Ou: choco install ffmpeg
```

### Variables d'Environnement
```bash
# API OpenAI pour transcription
export OPENAI_API_KEY="sk-proj-..."
# Ou sur Windows:
set OPENAI_API_KEY=sk-proj-...
```

### 📂 Organisation des Fichiers
```
whatsapp_extractor_v2/
├── claude_tools/
│   ├── bin/           # Outils exécutables
│   ├── output/        # 👈 FICHIERS DE SORTIE ICI
│   ├── cache/         # Cache transcriptions
│   └── logs/          # Logs d'exécution
```

⚠️ **IMPORTANT** : Tous les fichiers de sortie doivent être dans `claude_tools/output/`

### Utilisation Simple
```bash
# Se placer dans le bon dossier
cd claude_tools/bin

# Pipeline complet automatique
python process_all.py "/path/to/whatsapp/folder" -o ../output/mon_analyse

# Ou étape par étape
python parse_received.py "contact.html" -o ../output/messages.json
python find_media.py "/path/to/whatsapp" --audio-only --report ../output/media.json
python convert_audio.py audio.opus -o ../output/converted/
python transcribe.py ../output/converted/*.mp3 --output ../output/transcriptions.json
python analyze.py ../output/messages.json -f markdown -o ../output/rapport.md
```

### 🎯 Guide d'Utilisation pour Claude

Quand j'utilise mes propres outils, voici comment je procède :

1. **Toujours me placer dans le bon dossier** :
   ```bash
   cd claude_tools/bin
   ```

2. **Utiliser les chemins relatifs pour output** :
   ```bash
   # ✅ BON
   python parse_received.py fichier.html -o ../output/resultat.json
   
   # ❌ MAUVAIS  
   python parse_received.py fichier.html -o ../../resultat.json
   ```

3. **Pipeline recommandé pour traiter des contacts** :
   ```bash
   # Étape 1: Parser les messages reçus
   python parse_received.py "C:/path/to/*.html" -o ../output/messages_parsed.json
   
   # Étape 2: Trouver les médias audio
   python find_media.py "C:/path/to/WhatsApp" --voice-only --report ../output/voice_files.json
   
   # Étape 3: Convertir en MP3
   python convert_audio.py --whisper -o ../output/whisper_ready < ../output/voice_files.json
   
   # Étape 4: Transcrire
   python transcribe.py ../output/whisper_ready/*.mp3 -o ../output/transcriptions.json
   
   # Étape 5: Analyser
   python analyze.py ../output/messages_parsed.json -f markdown -o ../output/analyse_finale.md
   ```

---

## 🔧 Guide des Outils

### 1. parse_received.py
**Objectif** : Extraire UNIQUEMENT les messages reçus des exports WhatsApp

```bash
# Usage de base
python parse_received.py contact.html

# Batch processing
python parse_received.py /path/to/*.html -o results.json

# Format spécifique
python parse_received.py contact.html --format mobiletrans

# Statistiques rapides
python parse_received.py contact.html --stats-only
```

**Formats supportés** :
- MobileTrans (détection automatique)
- WhatsApp Web exports
- Auto-détection intelligente

**Sortie** : JSON avec messages, métadonnées, stats

### 2. find_media.py
**Objectif** : Détecter et associer fichiers médias aux messages

```bash
# Scan complet dossier
python find_media.py /path/to/whatsapp/folder

# Audio uniquement (messages vocaux)
python find_media.py /path/to/folder --voice-only

# Pour contact spécifique
python find_media.py /path/to/folder --contact "+1 234 567 8900"

# Générer rapport détaillé
python find_media.py /path/to/folder --report media_report.json

# Associer médias aux messages
python find_media.py /path/to/folder --map-messages messages.json
```

**Types détectés** :
- Audio : .opus, .m4a, .mp3, .ogg, .weba, .aac
- Images : .jpg, .png, .gif, .webp
- Vidéos : .mp4, .avi, .mov, .mkv

### 3. convert_audio.py
**Objectif** : Convertir audio en MP3 optimisé pour Whisper

```bash
# Conversion simple
python convert_audio.py audio.opus

# Préparation batch pour Whisper
python convert_audio.py /path/to/media --whisper

# Preset qualité différente
python convert_audio.py audio.m4a --preset standard

# Parallélisation
python convert_audio.py *.opus --workers 8

# Vérifier FFmpeg
python convert_audio.py --check
```

**Presets disponibles** :
- `whisper` : 16kHz mono, 128k (optimal pour API)
- `standard` : 44.1kHz stéréo, 192k
- `low` : 16kHz mono, 96k (économique)

### 4. transcribe.py
**Objectif** : Transcrire audio avec Whisper API + cache intelligent

```bash
# Transcription simple
python transcribe.py audio.mp3

# Batch avec langue
python transcribe.py *.mp3 --language fr

# Forcer re-transcription
python transcribe.py audio.mp3 --force

# Statistiques cache
python transcribe.py --cache-stats

# Nettoyer cache ancien
python transcribe.py --clear-cache 30

# Parallélisation (attention aux limites API)
python transcribe.py *.mp3 --workers 2
```

**Fonctionnalités** :
- Cache par hash de fichier
- Retry automatique avec backoff
- Support multi-langue
- Gestion erreurs robuste

### 5. analyze.py
**Objectif** : Analyser données et générer rapports multi-formats

```bash
# Rapport Markdown
python analyze.py messages.json -f markdown -o report.md

# Export CSV pour Excel
python analyze.py messages.json -f csv -o data.csv

# Analyse JSON complète
python analyze.py messages.json -f json -o analysis.json

# Filtrer contacts
python analyze.py messages.json --contacts "John,Marie" -f markdown

# Filtrer dates
python analyze.py messages.json --date-from 2024-01-01 --date-to 2024-12-31
```

**Analyses disponibles** :
- Statistiques contacts (messages, mots, médias)
- Analyse temporelle (heures pic, jours actifs)
- Contenu (mots fréquents, emojis)
- Transcriptions (langues, durées estimées)
- Patterns communication

### 6. process_all.py
**Objectif** : Pipeline complet automatisé

```bash
# Traitement complet
python process_all.py /path/to/whatsapp/

# Contacts spécifiques
python process_all.py /path/to/whatsapp/ --contacts "+1 234 567 8900,John Doe"

# Sans transcription (pas d'API key)
python process_all.py /path/to/whatsapp/ --skip-transcription

# Dossier de sortie personnalisé
python process_all.py /path/to/whatsapp/ -o my_analysis/
```

**Pipeline complet** :
1. Parse HTML → messages reçus
2. Trouve médias → mapping automatique
3. Convertit audio → MP3 optimisé Whisper
4. Transcrit → cache intelligent
5. Analyse → rapports multi-formats

---

## 📊 Formats de Sortie

### JSON (messages.json)
```json
{
  "contact": "+1 234 567 8900",
  "timestamp": "2024-01-15T14:30:00",
  "content": "Message text content",
  "has_media": true,
  "media": {"type": "audio", "src": "path/to/file"},
  "transcription": "Transcribed text if audio",
  "transcribed": true
}
```

### Markdown Report
- En-tête avec métadonnées
- Top contacts avec stats
- Analyse contenu (mots, emojis)
- Patterns temporels
- Médias et transcriptions

### CSV Export
Colonnes : contact, timestamp, content, has_media, media_type, transcription, word_count

---

## 🛠 Dépannage

### Erreurs Courantes

**"FFmpeg not found"**
```bash
# Installer FFmpeg
choco install ffmpeg
# Ou télécharger et ajouter au PATH
```

**"OpenAI API key required"**
```bash
export OPENAI_API_KEY="sk-proj-..."
# Ou utiliser --api-key dans commande
```

**"No messages found"**
- Vérifier format HTML (MobileTrans vs WhatsApp Web)
- Utiliser --format pour forcer détection
- Contrôler avec --stats-only

**"Conversion failed"**
- Vérifier format audio supporté
- Tester avec --check pour FFmpeg
- Utiliser preset 'low' si problème qualité

### Logs et Debug

**Consulter logs** :
```bash
# Logs dans claude_tools/logs/
ls claude_tools/logs/

# Erreurs uniquement
cat claude_tools/logs/*_errors.log

# Résumé JSON
cat claude_tools/logs/*_summary.json
```

**Mode verbose** :
La plupart des outils loggent automatiquement. Pour plus de détails, consulter les fichiers de logs générés.

---

## 💡 Conseils d'Utilisation pour Claude

### Workflow Recommandé

1. **Exploration rapide** :
   ```bash
   python parse_received.py contact.html --stats-only
   ```

2. **Test sur échantillon** :
   ```bash
   python process_all.py sample.html --skip-transcription
   ```

3. **Production complète** :
   ```bash
   python process_all.py /path/to/whatsapp/ -o analysis_$(date +%Y%m%d)
   ```

### Optimisations

- **Cache** : Les transcriptions sont mises en cache automatiquement
- **Parallélisme** : Utiliser --workers selon capacité machine
- **Filtrage** : Traiter par chunks de contacts pour grosses bases
- **Formats** : JSON pour programmatique, Markdown pour humain

### Patterns Typiques

**Analyse rapide** :
```bash
# Vue d'ensemble en 30 secondes
python parse_received.py *.html --stats-only | grep -E "(messages|contacts)"
```

**Focus audio** :
```bash
# Pipeline audio complet
python find_media.py /path --voice-only --report voices.json
python convert_audio.py $(cat voices.json | jq -r '.[].path') --whisper
python transcribe.py whisper_ready/*.mp3 -o transcriptions.json
```

**Analyse temporelle** :
```bash
# Patterns par période
python analyze.py messages.json --date-from 2024-01-01 --date-to 2024-03-31 -f markdown
```

---

## 🔄 Mise à Jour et Maintenance

### Cache Management
```bash
# Statistiques cache
python transcribe.py --cache-stats

# Nettoyer ancien cache (>30 jours)
python transcribe.py --clear-cache 30

# Nettoyer tout
python transcribe.py --clear-cache 0
```

### Logs Rotation
```bash
# Nettoyer anciens logs
find claude_tools/logs/ -name "*.log" -mtime +7 -delete
```

### Performance Tuning
- Ajuster --workers selon CPU/API limits
- Utiliser --skip-transcription pour analyse rapide
- Filtrer contacts pour gros datasets
- Utiliser cache pour éviter re-processing

---

## 📋 Checklist de Validation

Avant d'utiliser sur données importantes :

- [ ] FFmpeg installé et fonctionnel (`--check`)
- [ ] API Key OpenAI configurée (si transcription)
- [ ] Test sur fichier échantillon
- [ ] Vérification formats HTML supportés
- [ ] Espace disque suffisant pour outputs
- [ ] Backup données originales

---

## 🎯 Cas d'Usage Typiques

### Analyse Forensique
```bash
python process_all.py evidence/ --contacts "suspect1,suspect2" -o forensic_analysis/
```

### Étude Linguistique
```bash
python transcribe.py voices/ --language fr
python analyze.py transcriptions.json -f csv | grep -v "non-verbal"
```

### Archive Personnelle
```bash
python process_all.py my_whatsapp_backup/ -o personal_archive_2024/
```

### Analyse Business
```bash
python process_all.py business_chats/ --skip-transcription -o quarterly_comms/
```

---

**Cette boîte à outils est conçue pour rendre Claude autonome et efficace dans le traitement des données WhatsApp. Chaque outil peut être utilisé indépendamment ou dans le pipeline complet selon les besoins.**