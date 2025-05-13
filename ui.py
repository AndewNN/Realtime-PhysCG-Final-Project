import pygame as pg
import numpy as np
import pygame.surfarray as arraysurf
from Cloth import Cloth
import torch

def get_screen_resolution():
    """Get the user's screen resolution"""
    info = pg.display.Info()
    return info.current_w, info.current_h

class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pg.font.Font(None, 36)
        self.small_font = pg.font.Font(None, 28)
        self.buttons = []
        self.selected_button = None
        self.show_parameters = False
        self.parameters = {
            'height': 80,
            'width': 160,
            'spacing': 1.0,
            'mass': 30,
            'gravity': 0.01,
            'stiffness': 4.0,
            'alpha': 0.003,
            'decay': 0.99997,
            'init_energy': 1000,
            'method': 'Verlet',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        }
        self.dropdown_open = False  # Add this line
        self.editing_parameter = None  # Track which parameter is being edited
        self.edit_text = ""  # Store text while editing
        
        # Define toolbar dimensions
        self.toolbar_height = 50
        self.button_size = 40
        self.toolbar_padding = 5
        self.couu = 0
        
        # Create toolbar buttons with icons
        icons = self._create_icons()
        x_pos = self.toolbar_padding
        
        # Add toolbar buttons
        self.add_button(
            (x_pos, self.toolbar_padding, self.button_size, self.button_size),
            "Run",
            (0, 120, 255),
            icons['play']
        )
        x_pos += self.button_size + self.toolbar_padding
        
        self.add_button(
            (x_pos, self.toolbar_padding, self.button_size, self.button_size),
            "Reset",
            (0, 120, 255),
            icons['reset']
        )
        x_pos += self.button_size + self.toolbar_padding
        
        self.add_button(
            (x_pos, self.toolbar_padding, self.button_size, self.button_size),
            "Parameters",
            (0, 120, 255),
            icons['gear']
        )
        
        # Add exit button at the far right
        x_pos = self.screen.get_width() - self.button_size - self.toolbar_padding
        self.add_button(
            (x_pos, self.toolbar_padding, self.button_size, self.button_size),
            "Exit",
            (255, 60, 60),  # Red color for exit button
            icons['exit']
        )

        self.cloth = None
        self.running = False

    def _create_icons(self):
        """Create simple geometric icons using pygame"""
        icons = {}
        
        # Play icon (triangle)
        play_surf = pg.Surface((self.button_size, self.button_size), pg.SRCALPHA)
        points = [(10, 10), (10, 30), (30, 20)]
        pg.draw.polygon(play_surf, (255, 255, 255), points)
        icons['play'] = play_surf
        
        # Reset icon (circular arrow)
        reset_surf = pg.Surface((self.button_size, self.button_size), pg.SRCALPHA)
        pg.draw.arc(reset_surf, (255, 255, 255), (5, 5, 30, 30), 0, 5, 2)
        pg.draw.polygon(reset_surf, (255, 255, 255), [(35, 15), (35, 25), (25, 20)])
        icons['reset'] = reset_surf
        
        # Gear icon (simple gear shape)
        gear_surf = pg.Surface((self.button_size, self.button_size), pg.SRCALPHA)
        pg.draw.circle(gear_surf, (255, 255, 255), (20, 20), 15, 2)
        for i in range(8):
            angle = i * 45
            rad = angle * 3.14159 / 180
            x = 20 + 15 * np.cos(rad)
            y = 20 + 15 * np.sin(rad)
            pg.draw.circle(gear_surf, (255, 255, 255), (int(x), int(y)), 3)
        icons['gear'] = gear_surf
        
        # Exit icon (X shape)
        exit_surf = pg.Surface((self.button_size, self.button_size), pg.SRCALPHA)
        thickness = 2
        margin = 12
        # Draw X shape
        pg.draw.line(exit_surf, (255, 255, 255), 
                     (margin, margin), 
                     (self.button_size - margin, self.button_size - margin), 
                     thickness)
        pg.draw.line(exit_surf, (255, 255, 255), 
                     (self.button_size - margin, margin), 
                     (margin, self.button_size - margin), 
                     thickness)
        icons['exit'] = exit_surf
        
        return icons

    def add_button(self, rect, text, color=(0, 120, 255), icon=None):
        button = {
            'rect': rect,
            'text': text,
            'color': color,
            'surface': self.font.render(text, True, (255, 255, 255)),
            'hover': False,
            'icon': icon
        }
        self.buttons.append(button)

    def draw(self):
        # Draw toolbar background
        toolbar_rect = pg.Rect(0, 0, self.screen.get_width(), self.toolbar_height)
        pg.draw.rect(self.screen, (40, 40, 40), toolbar_rect)
        pg.draw.line(self.screen, (100, 100, 100), (0, self.toolbar_height), 
                    (self.screen.get_width(), self.toolbar_height), 2)

        # Draw buttons
        for button in self.buttons:
            # Draw button background
            if button['hover']:
                pg.draw.rect(self.screen, (60, 60, 60), button['rect'])
                # Draw tooltip
                tooltip = self.small_font.render(button['text'], True, (255, 255, 255))
                tooltip_rect = tooltip.get_rect(midtop=(
                    button['rect'][0] + button['rect'][2]/2,
                    button['rect'][1] + button['rect'][3] + 5
                ))
                self.screen.blit(tooltip, tooltip_rect)
            
            # Draw button icon
            if button['icon']:
                icon_rect = button['icon'].get_rect(center=(
                    button['rect'][0] + button['rect'][2]/2,
                    button['rect'][1] + button['rect'][3]/2
                ))
                self.screen.blit(button['icon'], icon_rect)

        # Draw parameter panel if enabled
        if self.show_parameters:
            panel_rect = pg.Rect(self.screen.get_width() - 300, 0, 300, self.screen.get_height())
            pg.draw.rect(self.screen, (20, 20, 20), panel_rect)
            pg.draw.line(self.screen, (100, 100, 100), (panel_rect.x, 0), (panel_rect.x, panel_rect.height), 2)

            # Draw "Parameters" title
            title = self.font.render("Parameters", True, (255, 255, 255))
            self.screen.blit(title, (panel_rect.x + 20, 20))
            
            y_offset = 80
            dropdownList = []
            for param, value in self.parameters.items():
                # Parameter name
                param_surface = self.small_font.render(param + ":", True, (200, 200, 200))
                self.screen.blit(param_surface, (panel_rect.x + 20, y_offset))
                
                # Parameter value/checkbox
                if isinstance(value, bool):
                    checkbox_rect = pg.Rect(panel_rect.x + 200, y_offset, 20, 20)
                    pg.draw.rect(self.screen, (255, 140, 0) if value else (50, 50, 50), checkbox_rect)
                    pg.draw.rect(self.screen, (200, 200, 200), checkbox_rect, 2)
                else:
                    if param == 'device' or param == 'method':
                        value_rect = pg.Rect(panel_rect.x + 200, y_offset, 100, 25)
                        # Draw main box
                        pg.draw.rect(self.screen, (40, 40, 40), value_rect)
                        pg.draw.rect(self.screen, (200, 200, 200), value_rect, 2)
                        
                        # Draw dropdown arrow
                        arrow_points = [
                            (value_rect.right - 20, value_rect.centery - 3),
                            (value_rect.right - 15, value_rect.centery + 3),
                            (value_rect.right - 10, value_rect.centery - 3)
                        ]
                        pg.draw.polygon(self.screen, (200, 200, 200), arrow_points)
                        
                        # Draw current value
                        text = self.small_font.render(value, True, (255, 140, 0))
                        self.screen.blit(text, (value_rect.x + 5, value_rect.y + 2))
                        
                        # Add to dropdown list for click handling
                        dropdownList.append((value_rect, param))
                    else:
                        value_rect = pg.Rect(panel_rect.x + 200, y_offset, 60, 25)
                        pg.draw.rect(self.screen, (40, 40, 40), value_rect)
                        pg.draw.rect(self.screen, (200, 200, 200), value_rect, 2)
                        
                        if self.editing_parameter == param:
                            text = self.small_font.render(self.edit_text + "|", True, (255, 140, 0))
                        else:
                            text = self.small_font.render(str(value), True, (255, 140, 0))
                        self.screen.blit(text, (value_rect.x + 5, value_rect.y + 2))
                
                y_offset += 40

            for value_rect, param in dropdownList:
                if self.dropdown_open and self.editing_parameter == param:
                    options = ['cuda', 'cpu'] if self.editing_parameter == 'device' else ['Euler', 'Verlet']
                    dropdown_height = len(options) * 25
                    dropdown_rect = pg.Rect(value_rect.x, value_rect.bottom, value_rect.width, dropdown_height)
                    pg.draw.rect(self.screen, (60, 60, 60), dropdown_rect)
                    pg.draw.rect(self.screen, (200, 200, 200), dropdown_rect, 2)
                    
                    for i, option in enumerate(options):
                        option_rect = pg.Rect(dropdown_rect.x, dropdown_rect.y + i * 25, dropdown_rect.width, 25)
                        if option_rect.collidepoint(pg.mouse.get_pos()):
                            pg.draw.rect(self.screen, (80, 80, 80), option_rect)
                        
                        text = self.small_font.render(option, True, (255, 140, 0))
                        self.screen.blit(text, (option_rect.x + 5, option_rect.y + 2))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Close dropdown if click is outside
                if self.dropdown_open:
                    panel_x = self.screen.get_width() - 300
                    param_index = list(self.parameters.keys()).index(self.editing_parameter)
                    value_rect = pg.Rect(panel_x + 200, 80 + param_index * 40, 100, 25)
                    dropdown_rect = pg.Rect(value_rect.x, value_rect.bottom, value_rect.width, 50)
                    
                    # Check for clicks inside dropdown menu
                    if dropdown_rect.collidepoint(event.pos):
                        options = ['cuda', 'cpu'] if self.editing_parameter == 'device' else ['Euler', 'Verlet']
                        option_idx = (event.pos[1] - dropdown_rect.y) // 25
                        if 0 <= option_idx < len(options):
                            if self.editing_parameter == 'device':
                                selected_device = options[option_idx]
                                if selected_device == 'cuda' and torch.cuda.is_available():
                                    self.parameters['device'] = 'cuda'
                                else:
                                    self.parameters['device'] = 'cpu'
                            else:  # method parameter
                                self.parameters['method'] = options[option_idx]
                            
                            self.dropdown_open = False
                            self.editing_parameter = None
                            if self.cloth is not None:
                                self.setup_cloth()
                            return
                    
                    # Close dropdown if clicked outside
                    if not dropdown_rect.collidepoint(event.pos) and not value_rect.collidepoint(event.pos):
                        self.dropdown_open = False
                        self.editing_parameter = None
                        return

                # Rest of the click handling
                if self.show_parameters:
                    panel_rect = pg.Rect(self.screen.get_width() - 300, 0, 300, self.screen.get_height())
                    if panel_rect.collidepoint(event.pos):
                        panel_x = self.screen.get_width() - 300
                        y_offset = 80
                        for param, value in self.parameters.items():
                            if isinstance(value, bool):
                                checkbox_rect = pg.Rect(panel_x + 200, y_offset, 20, 20)
                                if checkbox_rect.collidepoint(event.pos):
                                    self.parameters[param] = not value
                                    return
                            else:
                                if param == 'device' or param == 'method':
                                    value_rect = pg.Rect(panel_x + 200, y_offset, 100, 25)
                                    if value_rect.collidepoint(event.pos):
                                        self.dropdown_open = not self.dropdown_open
                                        self.editing_parameter = param
                                        return
                                else:
                                    value_rect = pg.Rect(panel_x + 200, y_offset, 60, 25)
                                    if value_rect.collidepoint(event.pos):
                                        self.editing_parameter = param
                                        self.edit_text = str(value)
                                        return
                            y_offset += 40
                        return

                # Handle toolbar buttons
                for button in self.buttons:
                    if pg.Rect(button['rect']).collidepoint(event.pos):
                        if button['text'] == "Run":
                            if self.cloth is None:
                                self.setup_cloth()
                            self.running = not self.running
                        elif button['text'] == "Reset":
                            self.cloth = None
                            self.running = False
                            self.setup_cloth()
                        elif button['text'] == "Parameters":
                            self.toggle_parameters()
                        elif button['text'] == "Exit":
                            self.quit()
                        return
            
        elif event.type == pg.KEYDOWN:
            # Only process keyboard input if parameters panel is open
            if self.show_parameters and self.editing_parameter:
                if event.key == pg.K_RETURN:
                    try:
                        if isinstance(self.parameters[self.editing_parameter], int):
                            self.parameters[self.editing_parameter] = int(self.edit_text)
                        elif isinstance(self.parameters[self.editing_parameter], float):
                            self.parameters[self.editing_parameter] = float(self.edit_text)
                    except ValueError:
                        pass  # Invalid input, keep old value
                    self.editing_parameter = None
                elif event.key == pg.K_ESCAPE:
                    self.editing_parameter = None
                elif event.key == pg.K_BACKSPACE:
                    self.edit_text = self.edit_text[:-1]
                elif event.unicode.isprintable():
                    self.edit_text += event.unicode

            # Global escape key handling
            if event.key == pg.K_ESCAPE and not self.editing_parameter:
                self.quit()
        
        elif event.type == pg.MOUSEMOTION:
            # Update button hover states
            mouse_pos = event.pos
            for button in self.buttons:
                button['hover'] = pg.Rect(button['rect']).collidepoint(mouse_pos)
                # Don't show hover effects on buttons behind parameter panel
                if self.show_parameters:
                    panel_rect = pg.Rect(self.screen.get_width() - 300, 0, 300, self.screen.get_height())
                    if panel_rect.collidepoint(button['rect'][0], button['rect'][1]):
                        button['hover'] = False

    def clear(self):
        self.buttons.clear()
        self.selected_button = None

    def setup_cloth(self):
        """Initialize cloth with current parameters"""
        self.cloth = Cloth(
            height=int(self.parameters['height']),
            width=int(self.parameters['width']),
            spacing=self.parameters['spacing'],
            mass=self.parameters['mass'],
            gravity=self.parameters['gravity'],
            stiffness=self.parameters['stiffness'],
            alpha=self.parameters['alpha'],
            decay=self.parameters['decay'],
            init_energy=self.parameters['init_energy'],
            device=self.parameters['device'],
            method=self.parameters['method'].lower()  # Add method parameter
        )

    def update(self):
        """Update the simulation"""
        if self.running and self.cloth is not None:
            # Get the rendered frame from cloth
            frame = self.cloth.forward()[::-1, ]
            
            # Convert numpy array to pygame surface efficiently
            frame = np.transpose(frame, (1, 0, 2))  # Swap axes for pygame
            surface = pg.surfarray.make_surface(frame)
            
            # Scale the surface to fit the display area
            display_area = pg.Rect(0, self.toolbar_height, 
                                 self.screen.get_width() - (300 if self.show_parameters else 0),
                                 self.screen.get_height() - self.toolbar_height)
            
            scaled_surface = pg.transform.scale(surface, display_area.size)
            self.screen.blit(scaled_surface, display_area)

    def reset(self):
        # Reset the UI state if needed
        self.clear()
        self.update()

    def quit(self):
        # Clean up resources if needed
        pg.quit()

    def toggle_parameters(self):
        """Toggle the visibility of the parameters panel"""
        self.show_parameters = not self.show_parameters
        return self.show_parameters