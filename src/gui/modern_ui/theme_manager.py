"""
Modern Theme Manager for WhatsApp Extractor v2 - 2025 Design System
Implements advanced theming with neumorphism, glassmorphism, and adaptive colors
"""

import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import colorsys

class ModernThemeManager:
    """Advanced theme management with 2025 design principles"""
    
    # 2025 Color Palettes
    THEMES = {
        'light': {
            'primary': '#6366f1',      # Indigo 500
            'primary_hover': '#4f46e5', # Indigo 600
            'primary_light': '#a5b4fc', # Indigo 300
            'secondary': '#06b6d4',     # Cyan 500
            'accent': '#f59e0b',        # Amber 500
            'success': '#10b981',       # Emerald 500
            'warning': '#f59e0b',       # Amber 500
            'error': '#ef4444',         # Red 500
            'info': '#3b82f6',          # Blue 500
            
            # Backgrounds with neumorphism
            'bg_primary': '#f8fafc',    # Slate 50
            'bg_secondary': '#f1f5f9',  # Slate 100
            'bg_tertiary': '#e2e8f0',   # Slate 200
            'bg_glass': '#ffffff',      # Glass effect (sans alpha pour Tkinter)
            'bg_elevated': '#ffffff',   # White
            
            # Text colors
            'text_primary': '#0f172a',  # Slate 900
            'text_secondary': '#475569', # Slate 600
            'text_tertiary': '#94a3b8', # Slate 400
            'text_inverse': '#ffffff',
            
            # Borders and shadows
            'border_light': '#e2e8f0',  # Slate 200
            'border_medium': '#cbd5e1', # Slate 300
            'border_dark': '#94a3b8',   # Slate 400
            'shadow_color': '#94a3b8',  # Simplified pour Tkinter
            'shadow_inset': '#f1f5f9',  # Simplified pour Tkinter
            
            # Interactive states
            'hover_overlay': '#f1f5f9',  # Simplified pour Tkinter
            'pressed_overlay': '#e2e8f0', # Simplified pour Tkinter
            'focus_ring': '#a5b4fc',     # Simplified pour Tkinter
        },
        
        'dark': {
            'primary': '#6366f1',       # Indigo 500
            'primary_hover': '#7c3aed',  # Violet 600
            'primary_light': '#8b5cf6',  # Violet 500
            'secondary': '#06b6d4',     # Cyan 500
            'accent': '#f59e0b',        # Amber 500
            'success': '#10b981',       # Emerald 500
            'warning': '#f59e0b',       # Amber 500
            'error': '#ef4444',         # Red 500
            'info': '#3b82f6',          # Blue 500
            
            # Dark backgrounds with neumorphism
            'bg_primary': '#0f172a',    # Slate 900
            'bg_secondary': '#1e293b',  # Slate 800
            'bg_tertiary': '#334155',   # Slate 700
            'bg_glass': '#1e293b',      # Dark glass effect (sans alpha pour Tkinter)
            'bg_elevated': '#1e293b',   # Slate 800
            
            # Dark text colors
            'text_primary': '#f8fafc',  # Slate 50
            'text_secondary': '#cbd5e1', # Slate 300
            'text_tertiary': '#64748b', # Slate 500
            'text_inverse': '#0f172a',
            
            # Dark borders and shadows
            'border_light': '#334155',  # Slate 700
            'border_medium': '#475569', # Slate 600
            'border_dark': '#64748b',   # Slate 500
            'shadow_color': '#000000',  # Simplified pour Tkinter
            'shadow_inset': '#475569',  # Simplified pour Tkinter
            
            # Dark interactive states
            'hover_overlay': '#334155',  # Simplified pour Tkinter
            'pressed_overlay': '#475569', # Simplified pour Tkinter
            'focus_ring': '#8b5cf6',     # Simplified pour Tkinter
        }
    }
    
    # Typography Scale (2025 standards)
    TYPOGRAPHY = {
        'display': {'size': 48, 'weight': 'bold', 'line_height': 1.1},
        'h1': {'size': 36, 'weight': 'bold', 'line_height': 1.2},
        'h2': {'size': 30, 'weight': 'bold', 'line_height': 1.2},
        'h3': {'size': 24, 'weight': 'bold', 'line_height': 1.3},
        'h4': {'size': 20, 'weight': 'bold', 'line_height': 1.3},
        'h5': {'size': 16, 'weight': 'bold', 'line_height': 1.4},
        'body_large': {'size': 16, 'weight': 'normal', 'line_height': 1.5},
        'body': {'size': 14, 'weight': 'normal', 'line_height': 1.5},
        'body_small': {'size': 12, 'weight': 'normal', 'line_height': 1.4},
        'caption': {'size': 11, 'weight': 'normal', 'line_height': 1.3},
        'button': {'size': 14, 'weight': 'medium', 'line_height': 1.2},
    }
    
    # Spacing System (8px grid)
    SPACING = {
        'xs': 4,    # 0.25rem
        'sm': 8,    # 0.5rem
        'md': 16,   # 1rem
        'lg': 24,   # 1.5rem
        'xl': 32,   # 2rem
        'xxl': 48,  # 3rem
        'xxxl': 64, # 4rem
    }
    
    # Border radius (modern, more rounded)
    RADIUS = {
        'none': 0,
        'sm': 6,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'full': 9999,
    }
    
    # Animation durations (ms)
    ANIMATION = {
        'fast': 150,
        'normal': 250,
        'slow': 350,
        'slower': 500,
    }
    
    def __init__(self):
        self.current_theme = 'light'
        self.auto_theme = True
        self.custom_colors = {}
        self.preferences_file = Path("theme_preferences.json")
        self.load_preferences()
        
        # Auto-detect system theme
        if self.auto_theme:
            self.detect_system_theme()
    
    def detect_system_theme(self) -> str:
        """Detect system theme preference"""
        try:
            import winreg
            # Windows registry check for dark mode
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            
            theme = 'light' if value else 'dark'
            self.current_theme = theme
            return theme
        except:
            # Fallback: check time for auto theme
            hour = datetime.now().hour
            self.current_theme = 'light' if 6 <= hour <= 18 else 'dark'
            return self.current_theme
    
    def get_color(self, color_name: str, alpha: float = 1.0) -> str:
        """Get color from current theme with optional alpha"""
        theme = self.THEMES[self.current_theme]
        
        if color_name in self.custom_colors:
            color = self.custom_colors[color_name]
        elif color_name in theme:
            color = theme[color_name]
        else:
            color = theme['text_primary']  # Fallback
        
        if alpha < 1.0:
            return self.add_alpha(color, alpha)
        return color
    
    def add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to hex color (simplified for Tkinter compatibility)"""
        if alpha >= 1.0:
            return hex_color
        
        # Pour Tkinter, on simule l'alpha en éclaircissant/assombrissant la couleur
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Simulate alpha by blending with white/black based on current theme
        bg_color = 255 if self.current_theme == 'light' else 0
        
        # Blend with background
        r = int(r * alpha + bg_color * (1 - alpha))
        g = int(g * alpha + bg_color * (1 - alpha))
        b = int(b * alpha + bg_color * (1 - alpha))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_neumorphism_colors(self, base_color: str) -> Dict[str, str]:
        """Generate neumorphism shadow colors"""
        # Convert hex to HSL for manipulation
        h, s, l = self.hex_to_hsl(base_color)
        
        # Light shadow (highlight)
        light_l = min(1.0, l + 0.1)
        light_shadow = self.hsl_to_hex(h, s, light_l)
        
        # Dark shadow
        dark_l = max(0.0, l - 0.1)
        dark_shadow = self.hsl_to_hex(h, s, dark_l)
        
        return {
            'light_shadow': light_shadow,
            'dark_shadow': dark_shadow,
            'inset_light': self.add_alpha(light_shadow, 0.5),
            'inset_dark': self.add_alpha(dark_shadow, 0.3),
        }
    
    def hex_to_hsl(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSL"""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return colorsys.rgb_to_hls(r, g, b)
    
    def hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL color to hex"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def create_gradient(self, color1: str, color2: str, steps: int = 10) -> list:
        """Create color gradient between two colors"""
        h1, s1, l1 = self.hex_to_hsl(color1)
        h2, s2, l2 = self.hex_to_hsl(color2)
        
        gradient = []
        for i in range(steps):
            ratio = i / (steps - 1)
            h = h1 + (h2 - h1) * ratio
            s = s1 + (s2 - s1) * ratio
            l = l1 + (l2 - l1) * ratio
            gradient.append(self.hsl_to_hex(h, s, l))
        
        return gradient
    
    def apply_theme_to_ttk(self, style: ttk.Style):
        """Apply modern theme to ttk widgets"""
        theme = self.THEMES[self.current_theme]
        
        # Configure base theme (check if exists first)
        try:
            style.theme_names()
            if 'modern_2025' in style.theme_names():
                style.theme_use('modern_2025')
                return
        except:
            pass
            
        style.theme_create('modern_2025', parent='clam', settings={
            # TLabel styles
            'TLabel': {
                'configure': {
                    'background': theme['bg_primary'],
                    'foreground': theme['text_primary'],
                    'font': ('Segoe UI Variable', 14),
                    'borderwidth': 0,
                }
            },
            
            # Modern button with neumorphism
            'Modern.TButton': {
                'configure': {
                    'background': theme['bg_elevated'],
                    'foreground': theme['text_primary'],
                    'font': ('Segoe UI Variable', 14, 'normal'),
                    'borderwidth': 0,
                    'focuscolor': 'none',
                    'padding': (16, 12),
                    'relief': 'flat',
                },
                'map': {
                    'background': [
                        ('pressed', theme['primary']),
                        ('active', theme['bg_tertiary']),
                        ('!active', theme['bg_elevated'])
                    ],
                    'foreground': [
                        ('pressed', theme['text_inverse']),
                        ('active', theme['text_primary']),
                        ('!active', theme['text_primary'])
                    ],
                }
            },
            
            # Primary button
            'Primary.TButton': {
                'configure': {
                    'background': theme['primary'],
                    'foreground': theme['text_inverse'],
                    'font': ('Segoe UI Variable', 14, 'bold'),
                    'borderwidth': 0,
                    'focuscolor': 'none',
                    'padding': (20, 14),
                    'relief': 'flat',
                },
                'map': {
                    'background': [
                        ('pressed', theme['primary_hover']),
                        ('active', theme['primary_hover']),
                        ('!active', theme['primary'])
                    ],
                }
            },
            
            # Modern entry with glass effect
            'Modern.TEntry': {
                'configure': {
                    'background': theme['bg_glass'],
                    'foreground': theme['text_primary'],
                    'font': ('Segoe UI Variable', 14),
                    'borderwidth': 1,
                    'relief': 'solid',
                    'bordercolor': theme['border_light'],
                    'padding': (12, 8),
                },
                'map': {
                    'bordercolor': [
                        ('focus', theme['primary']),
                        ('!focus', theme['border_light'])
                    ],
                    'background': [
                        ('focus', theme['bg_elevated']),
                        ('!focus', theme['bg_glass'])
                    ],
                }
            },
            
            # Modern frame
            'Modern.TFrame': {
                'configure': {
                    'background': theme['bg_elevated'],
                    'borderwidth': 1,
                    'relief': 'solid',
                    'bordercolor': theme['border_light'],
                }
            },
            
            # Glass frame
            'Glass.TFrame': {
                'configure': {
                    'background': theme['bg_glass'],
                    'borderwidth': 0,
                    'relief': 'flat',
                }
            },
            
            # Modern progressbar
            'Modern.Horizontal.TProgressbar': {
                'configure': {
                    'background': theme['primary'],
                    'troughcolor': theme['bg_tertiary'],
                    'borderwidth': 0,
                    'lightcolor': theme['primary'],
                    'darkcolor': theme['primary'],
                    'thickness': 8,
                }
            },
            
            # Modern scrollbar
            'Modern.Vertical.TScrollbar': {
                'configure': {
                    'background': theme['bg_secondary'],
                    'troughcolor': theme['bg_tertiary'],
                    'borderwidth': 0,
                    'arrowcolor': theme['text_secondary'],
                    'width': 12,
                },
                'map': {
                    'background': [
                        ('active', theme['primary']),
                        ('!active', theme['bg_secondary'])
                    ],
                }
            },
            
            # Modern notebook
            'Modern.TNotebook': {
                'configure': {
                    'background': theme['bg_primary'],
                    'borderwidth': 0,
                    'tabmargins': [0, 0, 0, 0],
                }
            },
            
            'Modern.TNotebook.Tab': {
                'configure': {
                    'background': theme['bg_secondary'],
                    'foreground': theme['text_secondary'],
                    'font': ('Segoe UI Variable', 12, 'normal'),
                    'padding': (16, 12),
                    'borderwidth': 0,
                },
                'map': {
                    'background': [
                        ('selected', theme['bg_elevated']),
                        ('active', theme['bg_tertiary']),
                        ('!active', theme['bg_secondary'])
                    ],
                    'foreground': [
                        ('selected', theme['text_primary']),
                        ('active', theme['text_primary']),
                        ('!active', theme['text_secondary'])
                    ],
                }
            },
        })
        
        style.theme_use('modern_2025')
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.auto_theme = False
        self.save_preferences()
    
    def set_theme(self, theme_name: str):
        """Set specific theme"""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.auto_theme = False
            self.save_preferences()
    
    def save_preferences(self):
        """Save theme preferences to file"""
        preferences = {
            'current_theme': self.current_theme,
            'auto_theme': self.auto_theme,
            'custom_colors': self.custom_colors,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
        except Exception as e:
            print(f"Failed to save theme preferences: {e}")
    
    def load_preferences(self):
        """Load theme preferences from file"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    preferences = json.load(f)
                
                self.current_theme = preferences.get('current_theme', 'light')
                self.auto_theme = preferences.get('auto_theme', True)
                self.custom_colors = preferences.get('custom_colors', {})
        except Exception as e:
            print(f"Failed to load theme preferences: {e}")
    
    def get_font(self, type_name: str) -> tuple:
        """Get font configuration for typography type"""
        if type_name not in self.TYPOGRAPHY:
            type_name = 'body'
        
        typo = self.TYPOGRAPHY[type_name]
        weight = 'bold' if typo['weight'] == 'bold' else 'normal'
        
        return ('Segoe UI Variable', typo['size'], weight)
    
    def get_spacing(self, size: str) -> int:
        """Get spacing value"""
        return self.SPACING.get(size, self.SPACING['md'])
    
    def get_radius(self, size: str) -> int:
        """Get border radius value"""
        return self.RADIUS.get(size, self.RADIUS['md'])
    
    def create_shadow_style(self, elevation: int = 1) -> str:
        """Create CSS-like shadow style for elevation"""
        shadow_color = self.get_color('shadow_color')
        
        shadows = {
            1: f"0 1px 3px {shadow_color}",
            2: f"0 4px 6px {shadow_color}",
            3: f"0 10px 15px {shadow_color}",
            4: f"0 20px 25px {shadow_color}",
            5: f"0 25px 50px {shadow_color}",
        }
        
        return shadows.get(elevation, shadows[1])