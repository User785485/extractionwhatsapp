"""
Modern UI Widgets for WhatsApp Extractor v2 - 2025 Design
Custom widgets with advanced animations, neumorphism, and glassmorphism
"""

import tkinter as tk
from tkinter import ttk, Canvas
import math
from typing import Callable, Optional, Dict, Any, List
import threading
import time

# Optional PIL import
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class ModernButton(tk.Frame):
    """Modern button with neumorphism, hover effects, and animations"""
    
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None,
                 style: str = "primary", icon: Optional[str] = None, 
                 theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.text = text
        self.command = command
        self.style = style
        self.icon = icon
        self.theme = theme_manager
        self.is_hovered = False
        self.is_pressed = False
        self.is_disabled = False
        
        # Animation properties
        self.hover_progress = 0.0
        self.press_progress = 0.0
        self.animation_running = False
        
        self.setup_widget()
        self.bind_events()
    
    def setup_widget(self):
        """Setup the button widget"""
        self.configure(
            relief='flat',
            bd=0,
            highlightthickness=0,
            cursor='hand2'
        )
        
        # Create canvas for custom drawing
        self.canvas = Canvas(
            self,
            highlightthickness=0,
            bd=0,
            relief='flat'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Apply theme colors
        self.update_colors()
        
        # Initial draw
        self.draw_button()
    
    def update_colors(self):
        """Update colors from theme"""
        if not self.theme:
            return
            
        if self.style == 'primary':
            self.bg_color = self.theme.get_color('primary')
            self.text_color = self.theme.get_color('text_inverse')
            self.hover_color = self.theme.get_color('primary_hover')
        elif self.style == 'secondary':
            self.bg_color = self.theme.get_color('bg_elevated')
            self.text_color = self.theme.get_color('text_primary')
            self.hover_color = self.theme.get_color('bg_tertiary')
        else:  # outline
            self.bg_color = self.theme.get_color('bg_primary')
            self.text_color = self.theme.get_color('primary')
            self.hover_color = self.theme.get_color('bg_secondary')
        
        self.configure(bg=self.theme.get_color('bg_primary'))
        self.canvas.configure(bg=self.theme.get_color('bg_primary'))
    
    def draw_button(self):
        """Draw the button with current state"""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            self.after(10, self.draw_button)
            return
        
        # Calculate colors based on state
        bg_color = self.interpolate_color(
            self.bg_color, 
            self.hover_color, 
            self.hover_progress
        )
        
        # Draw neumorphic background
        self.draw_neumorphic_rect(0, 0, width, height, bg_color)
        
        # Draw text and icon
        self.draw_content(width, height)
    
    def draw_neumorphic_rect(self, x1, y1, x2, y2, color):
        """Draw neumorphic rectangle"""
        radius = self.theme.get_radius('md') if self.theme else 12
        
        # Main background
        self.draw_rounded_rect(x1, y1, x2, y2, radius, color)
        
        if not self.is_pressed:
            # Light shadow (top-left)
            shadow_color = self.theme.get_color('shadow_inset', 0.1) if self.theme else '#ffffff20'
            self.draw_rounded_rect(x1, y1, x2-2, y2-2, radius, shadow_color)
            
            # Dark shadow (bottom-right)
            shadow_color = self.theme.get_color('shadow_color', 0.2) if self.theme else '#00000020'
            self.draw_rounded_rect(x1+2, y1+2, x2, y2, radius, shadow_color)
    
    def draw_rounded_rect(self, x1, y1, x2, y2, radius, color):
        """Draw rounded rectangle"""
        # Create rounded rectangle using multiple canvas elements
        points = []
        
        # Top side
        points.extend([x1 + radius, y1, x2 - radius, y1])
        # Right side
        points.extend([x2, y1 + radius, x2, y2 - radius])
        # Bottom side
        points.extend([x2 - radius, y2, x1 + radius, y2])
        # Left side
        points.extend([x1, y2 - radius, x1, y1 + radius])
        
        if len(points) >= 6:
            self.canvas.create_polygon(points, fill=color, outline='', smooth=True)
        
        # Draw corners
        self.canvas.create_oval(x1, y1, x1 + 2*radius, y1 + 2*radius, 
                               fill=color, outline='')
        self.canvas.create_oval(x2 - 2*radius, y1, x2, y1 + 2*radius, 
                               fill=color, outline='')
        self.canvas.create_oval(x1, y2 - 2*radius, x1 + 2*radius, y2, 
                               fill=color, outline='')
        self.canvas.create_oval(x2 - 2*radius, y2 - 2*radius, x2, y2, 
                               fill=color, outline='')
    
    def draw_content(self, width, height):
        """Draw button text and icon"""
        center_x = width // 2
        center_y = height // 2
        
        # Calculate text properties
        font_size = 14
        if self.theme:
            font = self.theme.get_font('button')
            font_size = font[1]
        
        # Draw text
        if self.text:
            self.canvas.create_text(
                center_x, center_y,
                text=self.text,
                font=('Segoe UI Variable', font_size, 'bold'),
                fill=self.text_color,
                anchor='center'
            )
    
    def interpolate_color(self, color1: str, color2: str, progress: float) -> str:
        """Interpolate between two colors"""
        if not color1.startswith('#') or not color2.startswith('#'):
            return color1
        
        # Convert hex to RGB
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)
        
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * progress)
        g = int(g1 + (g2 - g1) * progress)
        b = int(b1 + (b2 - b1) * progress)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def bind_events(self):
        """Bind mouse events"""
        widgets = [self, self.canvas]
        
        for widget in widgets:
            widget.bind('<Enter>', self.on_enter)
            widget.bind('<Leave>', self.on_leave)
            widget.bind('<Button-1>', self.on_press)
            widget.bind('<ButtonRelease-1>', self.on_release)
    
    def on_enter(self, event=None):
        """Handle mouse enter"""
        if self.is_disabled:
            return
        self.is_hovered = True
        self.animate_hover(True)
    
    def on_leave(self, event=None):
        """Handle mouse leave"""
        if self.is_disabled:
            return
        self.is_hovered = False
        self.animate_hover(False)
    
    def on_press(self, event=None):
        """Handle mouse press"""
        if self.is_disabled:
            return
        self.is_pressed = True
        self.animate_press(True)
    
    def on_release(self, event=None):
        """Handle mouse release"""
        if self.is_disabled:
            return
        self.is_pressed = False
        self.animate_press(False)
        
        # Execute command if mouse is still over button
        if self.is_hovered and self.command:
            self.command()
    
    def animate_hover(self, hover_in: bool):
        """Animate hover effect"""
        target = 1.0 if hover_in else 0.0
        self.animate_property('hover_progress', target, 150)
    
    def animate_press(self, press_in: bool):
        """Animate press effect"""
        target = 1.0 if press_in else 0.0
        self.animate_property('press_progress', target, 100)
    
    def animate_property(self, property_name: str, target: float, duration: int):
        """Animate a property to target value"""
        if self.animation_running:
            return
        
        def animate():
            self.animation_running = True
            start_value = getattr(self, property_name)
            start_time = time.time()
            
            while True:
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                progress = min(elapsed / duration, 1.0)
                
                # Easing function (ease-out)
                eased_progress = 1 - (1 - progress) ** 3
                
                current_value = start_value + (target - start_value) * eased_progress
                setattr(self, property_name, current_value)
                
                self.after_idle(self.draw_button)
                
                if progress >= 1.0:
                    break
                
                time.sleep(0.016)  # ~60 FPS
            
            self.animation_running = False
        
        threading.Thread(target=animate, daemon=True).start()

class ModernCard(tk.Frame):
    """Modern card widget with glassmorphism effect"""
    
    def __init__(self, parent, theme_manager=None, elevation: int = 1, 
                 glass: bool = False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.theme = theme_manager
        self.elevation = elevation
        self.glass = glass
        
        self.setup_widget()
    
    def setup_widget(self):
        """Setup the card widget"""
        if not self.theme:
            return
        
        if self.glass:
            bg_color = self.theme.get_color('bg_glass')
            border_color = self.theme.get_color('border_light', 0.3)
        else:
            bg_color = self.theme.get_color('bg_elevated')
            border_color = self.theme.get_color('border_light')
        
        self.configure(
            bg=bg_color,
            relief='solid',
            bd=1,
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=1
        )

class ModernProgressBar(tk.Frame):
    """Modern progress bar with smooth animations"""
    
    def __init__(self, parent, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.theme = theme_manager
        self.progress = 0.0
        self.target_progress = 0.0
        self.animation_id = None
        
        self.setup_widget()
    
    def setup_widget(self):
        """Setup the progress bar"""
        self.configure(
            height=8,
            bg=self.theme.get_color('bg_tertiary') if self.theme else '#e2e8f0'
        )
        
        self.canvas = Canvas(
            self,
            highlightthickness=0,
            bd=0,
            relief='flat',
            height=8
        )
        self.canvas.pack(fill='both', expand=True)
        
        self.canvas.configure(
            bg=self.theme.get_color('bg_tertiary') if self.theme else '#e2e8f0'
        )
        
        self.draw_progress()
    
    def draw_progress(self):
        """Draw the progress bar"""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1:
            self.after(10, self.draw_progress)
            return
        
        # Draw background
        radius = height // 2
        self.draw_rounded_rect(0, 0, width, height, radius, 
                              self.theme.get_color('bg_tertiary') if self.theme else '#e2e8f0')
        
        # Draw progress
        if self.progress > 0:
            progress_width = width * self.progress
            self.draw_rounded_rect(0, 0, progress_width, height, radius,
                                  self.theme.get_color('primary') if self.theme else '#6366f1')
    
    def draw_rounded_rect(self, x1, y1, x2, y2, radius, color):
        """Draw rounded rectangle"""
        if x2 - x1 < 2 * radius:
            radius = (x2 - x1) // 2
        
        self.canvas.create_oval(x1, y1, x1 + 2*radius, y2, fill=color, outline='')
        self.canvas.create_oval(x2 - 2*radius, y1, x2, y2, fill=color, outline='')
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=color, outline='')
    
    def set_progress(self, value: float):
        """Set progress value (0.0 to 1.0) with animation"""
        self.target_progress = max(0.0, min(1.0, value))
        self.animate_to_target()
    
    def animate_to_target(self):
        """Animate progress to target value"""
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        def animate():
            diff = self.target_progress - self.progress
            if abs(diff) < 0.001:
                self.progress = self.target_progress
                self.draw_progress()
                return
            
            self.progress += diff * 0.1  # Smooth animation
            self.draw_progress()
            
            self.animation_id = self.after(16, animate)  # ~60 FPS
        
        animate()

class ModernToast(tk.Toplevel):
    """Modern toast notification with auto-dismiss"""
    
    def __init__(self, parent, message: str, type: str = "info", 
                 duration: int = 3000, theme_manager=None):
        super().__init__(parent)
        
        self.message = message
        self.type = type
        self.duration = duration
        self.theme = theme_manager
        
        self.setup_window()
        self.create_content()
        self.show_animation()
        
        # Auto dismiss
        self.after(self.duration, self.hide_animation)
    
    def setup_window(self):
        """Setup toast window"""
        self.withdraw()  # Hide initially
        self.overrideredirect(True)  # No window decorations
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.0)  # Start transparent
        
        # Position at top-right of parent
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        
        self.geometry(f"300x60+{parent_x + parent_width - 320}+{parent_y + 20}")
    
    def create_content(self):
        """Create toast content"""
        # Get colors based on type
        if self.type == "success":
            bg_color = self.theme.get_color('success') if self.theme else '#10b981'
            icon = "✓"
        elif self.type == "error":
            bg_color = self.theme.get_color('error') if self.theme else '#ef4444'
            icon = "✗"
        elif self.type == "warning":
            bg_color = self.theme.get_color('warning') if self.theme else '#f59e0b'
            icon = "⚠"
        else:  # info
            bg_color = self.theme.get_color('info') if self.theme else '#3b82f6'
            icon = "ℹ"
        
        self.configure(bg=bg_color)
        
        # Main frame
        main_frame = tk.Frame(self, bg=bg_color)
        main_frame.pack(fill='both', expand=True, padx=16, pady=12)
        
        # Icon
        icon_label = tk.Label(
            main_frame,
            text=icon,
            font=('Segoe UI Variable', 16, 'bold'),
            fg='white',
            bg=bg_color
        )
        icon_label.pack(side='left', padx=(0, 12))
        
        # Message
        message_label = tk.Label(
            main_frame,
            text=self.message,
            font=('Segoe UI Variable', 12),
            fg='white',
            bg=bg_color,
            wraplength=200,
            justify='left'
        )
        message_label.pack(side='left', fill='both', expand=True)
    
    def show_animation(self):
        """Animate toast appearance"""
        self.deiconify()
        
        def animate_in():
            current_alpha = self.attributes('-alpha')
            if current_alpha < 0.95:
                self.attributes('-alpha', current_alpha + 0.05)
                self.after(16, animate_in)
            else:
                self.attributes('-alpha', 0.95)
        
        animate_in()
    
    def hide_animation(self):
        """Animate toast disappearance"""
        def animate_out():
            current_alpha = self.attributes('-alpha')
            if current_alpha > 0.05:
                self.attributes('-alpha', current_alpha - 0.05)
                self.after(16, animate_out)
            else:
                self.destroy()
        
        animate_out()

class ModernInput(tk.Frame):
    """Modern input field with floating label and validation"""
    
    def __init__(self, parent, placeholder: str = "", label: str = "",
                 validator: Optional[Callable] = None, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.placeholder = placeholder
        self.label = label
        self.validator = validator
        self.theme = theme_manager
        self.is_focused = False
        self.is_valid = True
        self.show_placeholder = True
        
        self.setup_widget()
        self.bind_events()
    
    def setup_widget(self):
        """Setup the input widget"""
        self.configure(bg=self.theme.get_color('bg_primary') if self.theme else 'white')
        
        # Label (floating)
        if self.label:
            self.label_widget = tk.Label(
                self,
                text=self.label,
                font=('Segoe UI Variable', 10),
                fg=self.theme.get_color('text_secondary') if self.theme else '#64748b',
                bg=self.theme.get_color('bg_primary') if self.theme else 'white'
            )
            self.label_widget.pack(anchor='w', pady=(0, 4))
        
        # Input frame
        self.input_frame = tk.Frame(
            self,
            bg=self.theme.get_color('bg_elevated') if self.theme else 'white',
            relief='solid',
            bd=1,
            highlightthickness=1
        )
        self.input_frame.pack(fill='x', pady=(0, 4))
        
        # Entry widget
        self.entry = tk.Entry(
            self.input_frame,
            font=('Segoe UI Variable', 14),
            bg=self.theme.get_color('bg_elevated') if self.theme else 'white',
            fg=self.theme.get_color('text_primary') if self.theme else 'black',
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        self.entry.pack(fill='both', expand=True, padx=12, pady=10)
        
        # Validation message
        self.validation_label = tk.Label(
            self,
            text="",
            font=('Segoe UI Variable', 9),
            fg=self.theme.get_color('error') if self.theme else '#ef4444',
            bg=self.theme.get_color('bg_primary') if self.theme else 'white'
        )
        
        self.update_border()
        self.update_placeholder()
    
    def bind_events(self):
        """Bind events"""
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.bind('<KeyRelease>', self.on_key_release)
    
    def on_focus_in(self, event=None):
        """Handle focus in"""
        self.is_focused = True
        self.update_border()
        self.update_placeholder()
    
    def on_focus_out(self, event=None):
        """Handle focus out"""
        self.is_focused = False
        self.validate_input()
        self.update_border()
        self.update_placeholder()
    
    def on_key_release(self, event=None):
        """Handle key release"""
        self.update_placeholder()
        if self.validator:
            self.validate_input()
    
    def update_border(self):
        """Update border color based on state"""
        if not self.theme:
            return
        
        if not self.is_valid:
            color = self.theme.get_color('error')
        elif self.is_focused:
            color = self.theme.get_color('primary')
        else:
            color = self.theme.get_color('border_light')
        
        self.input_frame.configure(highlightcolor=color, highlightbackground=color)
    
    def update_placeholder(self):
        """Update placeholder visibility"""
        has_text = bool(self.entry.get())
        
        if not has_text and not self.is_focused and self.placeholder:
            if self.show_placeholder:
                return
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=self.theme.get_color('text_tertiary') if self.theme else '#94a3b8')
            self.show_placeholder = True
        elif has_text or self.is_focused:
            if self.show_placeholder and self.entry.get() == self.placeholder:
                self.entry.delete(0, 'end')
                self.show_placeholder = False
            self.entry.configure(fg=self.theme.get_color('text_primary') if self.theme else 'black')
    
    def validate_input(self):
        """Validate input value"""
        if not self.validator:
            return True
        
        value = self.get()
        try:
            self.is_valid = self.validator(value)
            if self.is_valid:
                self.validation_label.pack_forget()
            else:
                self.validation_label.configure(text="Invalid input")
                self.validation_label.pack(anchor='w')
        except Exception as e:
            self.is_valid = False
            self.validation_label.configure(text=str(e))
            self.validation_label.pack(anchor='w')
        
        self.update_border()
        return self.is_valid
    
    def get(self) -> str:
        """Get input value"""
        value = self.entry.get()
        if self.show_placeholder and value == self.placeholder:
            return ""
        return value
    
    def set(self, value: str):
        """Set input value"""
        self.entry.delete(0, 'end')
        self.entry.insert(0, value)
        self.show_placeholder = False
        self.update_placeholder()