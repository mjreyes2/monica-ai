"""
Monica Adobe Creative Suite Trainer
Guides users through Adobe products with step-by-step instructions.
Uses screen reading to see what user is doing and provide contextual help.

Author: Monica AI
Date: December 2025
"""

import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AdobeStep:
    """A step in an Adobe tutorial."""
    step_number: int
    instruction: str
    shortcut: str = ""
    tip: str = ""
    visual_cue: str = ""  # What to look for on screen


# Adobe Creative Suite Knowledge Base
ADOBE_PRODUCTS = {
    'photoshop': {
        'name': 'Adobe Photoshop',
        'description': 'Image editing and manipulation',
        'file_types': ['.psd', '.jpg', '.png', '.gif', '.tiff', '.raw'],
        'common_tasks': [
            'remove background', 'resize image', 'crop image', 'adjust colors',
            'add text', 'create layers', 'apply filters', 'retouch photos',
            'create selection', 'use masks', 'blend images', 'add effects'
        ],
        'shortcuts': {
            'new_file': 'Ctrl+N',
            'open': 'Ctrl+O',
            'save': 'Ctrl+S',
            'save_as': 'Ctrl+Shift+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Shift+Z',
            'copy': 'Ctrl+C',
            'paste': 'Ctrl+V',
            'cut': 'Ctrl+X',
            'free_transform': 'Ctrl+T',
            'deselect': 'Ctrl+D',
            'select_all': 'Ctrl+A',
            'invert_selection': 'Ctrl+Shift+I',
            'zoom_in': 'Ctrl++',
            'zoom_out': 'Ctrl+-',
            'fit_screen': 'Ctrl+0',
            'brush_size_up': ']',
            'brush_size_down': '[',
            'default_colors': 'D',
            'swap_colors': 'X',
            'new_layer': 'Ctrl+Shift+N',
            'merge_layers': 'Ctrl+E',
            'flatten_image': 'Ctrl+Shift+E',
        },
        'tools': {
            'V': 'Move Tool',
            'M': 'Marquee Selection',
            'L': 'Lasso Tool',
            'W': 'Magic Wand / Quick Selection',
            'C': 'Crop Tool',
            'I': 'Eyedropper',
            'J': 'Healing Brush / Spot Healing',
            'B': 'Brush Tool',
            'S': 'Clone Stamp',
            'E': 'Eraser',
            'G': 'Gradient / Paint Bucket',
            'P': 'Pen Tool',
            'T': 'Type Tool',
            'U': 'Shape Tools',
            'H': 'Hand Tool',
            'Z': 'Zoom Tool',
        }
    },
    
    'illustrator': {
        'name': 'Adobe Illustrator',
        'description': 'Vector graphics and illustration',
        'file_types': ['.ai', '.eps', '.svg', '.pdf'],
        'common_tasks': [
            'create shapes', 'draw paths', 'add text', 'create logos',
            'design icons', 'create patterns', 'use gradients', 'trace images',
            'create artboards', 'export for web', 'create mockups'
        ],
        'shortcuts': {
            'new_file': 'Ctrl+N',
            'open': 'Ctrl+O',
            'save': 'Ctrl+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Shift+Z',
            'group': 'Ctrl+G',
            'ungroup': 'Ctrl+Shift+G',
            'bring_to_front': 'Ctrl+Shift+]',
            'send_to_back': 'Ctrl+Shift+[',
            'lock': 'Ctrl+2',
            'unlock_all': 'Ctrl+Alt+2',
            'hide': 'Ctrl+3',
            'show_all': 'Ctrl+Alt+3',
        },
        'tools': {
            'V': 'Selection Tool',
            'A': 'Direct Selection',
            'P': 'Pen Tool',
            'T': 'Type Tool',
            'L': 'Line Tool',
            'M': 'Rectangle Tool',
            'E': 'Ellipse Tool',
            'B': 'Paintbrush',
            'N': 'Pencil Tool',
            'R': 'Rotate Tool',
            'S': 'Scale Tool',
            'O': 'Reflect Tool',
        }
    },
    
    'premiere_pro': {
        'name': 'Adobe Premiere Pro',
        'description': 'Video editing and production',
        'file_types': ['.prproj', '.mp4', '.mov', '.avi', '.mkv'],
        'common_tasks': [
            'import footage', 'create sequence', 'cut clips', 'add transitions',
            'add titles', 'color correction', 'add audio', 'export video',
            'add effects', 'speed/duration', 'multi-cam editing', 'audio mixing'
        ],
        'shortcuts': {
            'import': 'Ctrl+I',
            'new_sequence': 'Ctrl+N',
            'save': 'Ctrl+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Shift+Z',
            'cut': 'Ctrl+K',
            'ripple_delete': 'Shift+Delete',
            'play/pause': 'Space',
            'mark_in': 'I',
            'mark_out': 'O',
            'insert': ',',
            'overwrite': '.',
            'render': 'Enter',
            'export': 'Ctrl+M',
            'zoom_in_timeline': '=',
            'zoom_out_timeline': '-',
        },
        'panels': {
            'Project': 'Shift+1',
            'Source': 'Shift+2',
            'Timeline': 'Shift+3',
            'Program': 'Shift+4',
            'Effect Controls': 'Shift+5',
            'Audio Mixer': 'Shift+6',
            'Effects': 'Shift+7',
        }
    },
    
    'after_effects': {
        'name': 'Adobe After Effects',
        'description': 'Motion graphics and visual effects',
        'file_types': ['.aep', '.mov', '.mp4', '.gif'],
        'common_tasks': [
            'create composition', 'animate layers', 'add effects', 'keyframing',
            'motion tracking', 'green screen', 'text animation', 'shape layers',
            'expressions', 'render queue', '3D layers', 'camera animation'
        ],
        'shortcuts': {
            'new_composition': 'Ctrl+N',
            'import': 'Ctrl+I',
            'save': 'Ctrl+S',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Shift+Z',
            'ram_preview': '0 (numpad)',
            'add_keyframe': 'Alt+Shift+P/S/R/T',
            'easy_ease': 'F9',
            'pre_compose': 'Ctrl+Shift+C',
            'split_layer': 'Ctrl+Shift+D',
            'duplicate': 'Ctrl+D',
            'render_queue': 'Ctrl+M',
        },
        'properties': {
            'P': 'Position',
            'S': 'Scale',
            'R': 'Rotation',
            'T': 'Opacity',
            'A': 'Anchor Point',
            'U': 'Show Keyframes',
            'E': 'Show Effects',
            'M': 'Show Masks',
        }
    },
    
    'indesign': {
        'name': 'Adobe InDesign',
        'description': 'Page layout and publishing',
        'file_types': ['.indd', '.idml', '.pdf'],
        'common_tasks': [
            'create document', 'add text frames', 'place images', 'create master pages',
            'add page numbers', 'create table of contents', 'export to PDF',
            'create styles', 'text wrap', 'create spreads'
        ],
        'shortcuts': {
            'new_document': 'Ctrl+N',
            'place': 'Ctrl+D',
            'save': 'Ctrl+S',
            'export': 'Ctrl+E',
            'text_frame': 'T',
            'rectangle_frame': 'F',
            'pages_panel': 'F12',
        }
    },
    
    'lightroom': {
        'name': 'Adobe Lightroom',
        'description': 'Photo editing and organization',
        'file_types': ['.lrcat', '.jpg', '.raw', '.dng'],
        'common_tasks': [
            'import photos', 'organize library', 'develop photos', 'adjust exposure',
            'crop and straighten', 'apply presets', 'export photos', 'create collections',
            'batch editing', 'HDR merge', 'panorama merge'
        ],
        'shortcuts': {
            'import': 'Ctrl+Shift+I',
            'export': 'Ctrl+Shift+E',
            'develop_module': 'D',
            'library_module': 'G',
            'before_after': '\\',
            'crop': 'R',
            'spot_removal': 'Q',
            'adjustment_brush': 'K',
            'graduated_filter': 'M',
            'radial_filter': 'Shift+M',
        }
    },
    
    'xd': {
        'name': 'Adobe XD',
        'description': 'UI/UX design and prototyping',
        'file_types': ['.xd'],
        'common_tasks': [
            'create artboards', 'design UI', 'create components', 'add interactions',
            'prototype', 'share designs', 'create design systems', 'responsive design'
        ],
        'shortcuts': {
            'rectangle': 'R',
            'ellipse': 'E',
            'line': 'L',
            'pen': 'P',
            'text': 'T',
            'artboard': 'A',
            'zoom': 'Z',
            'prototype_mode': 'Ctrl+Tab',
            'preview': 'Ctrl+Enter',
        }
    },
    
    'audition': {
        'name': 'Adobe Audition',
        'description': 'Audio editing and production',
        'file_types': ['.sesx', '.wav', '.mp3', '.aiff'],
        'common_tasks': [
            'record audio', 'edit waveform', 'remove noise', 'apply effects',
            'multitrack mixing', 'podcast editing', 'audio restoration'
        ],
        'shortcuts': {
            'play/stop': 'Space',
            'record': 'Shift+Space',
            'zoom_in': '=',
            'zoom_out': '-',
            'normalize': 'Ctrl+Shift+N',
        }
    },
    
    'animate': {
        'name': 'Adobe Animate',
        'description': '2D animation and interactive content',
        'file_types': ['.fla', '.swf', '.html5'],
        'common_tasks': [
            'create animations', 'frame-by-frame', 'tweening', 'create symbols',
            'add interactivity', 'export animations', 'character rigging'
        ],
        'shortcuts': {
            'play': 'Enter',
            'insert_keyframe': 'F6',
            'insert_blank_keyframe': 'F7',
            'convert_to_symbol': 'F8',
            'test_movie': 'Ctrl+Enter',
        }
    },
}


class AdobeTrainer:
    """
    Provides step-by-step guidance for Adobe Creative Suite products.
    """
    
    def __init__(self, ai_manager=None, screen_reader=None):
        self.ai_manager = ai_manager
        self.screen_reader = screen_reader
        
        # Current tutorial state
        self.current_product = None
        self.current_task = None
        self.current_step = 0
        self.tutorial_steps: List[AdobeStep] = []
        
        print("[ADOBE] Adobe Trainer initialized")
    
    def get_products(self) -> List[str]:
        """Get list of supported Adobe products."""
        return list(ADOBE_PRODUCTS.keys())
    
    def get_product_info(self, product: str) -> Dict:
        """Get information about an Adobe product."""
        return ADOBE_PRODUCTS.get(product.lower(), {})
    
    def get_shortcuts(self, product: str) -> Dict[str, str]:
        """Get keyboard shortcuts for a product."""
        info = self.get_product_info(product)
        return info.get('shortcuts', {})
    
    def get_tools(self, product: str) -> Dict[str, str]:
        """Get tools for a product."""
        info = self.get_product_info(product)
        return info.get('tools', {})
    
    def start_tutorial(self, product: str, task: str) -> str:
        """
        Start a tutorial for a specific task.
        
        Args:
            product: Adobe product name
            task: What the user wants to accomplish
        """
        self.current_product = product.lower()
        self.current_task = task
        self.current_step = 0
        
        # Generate tutorial steps using AI
        if self.ai_manager:
            self.tutorial_steps = self._generate_tutorial(product, task)
        else:
            self.tutorial_steps = self._get_basic_tutorial(product, task)
        
        if not self.tutorial_steps:
            return f"I don't have a specific tutorial for '{task}' in {product}, but I can help you figure it out. What would you like to do first?"
        
        return self._format_step(0)
    
    def next_step(self) -> str:
        """Get the next step in the tutorial."""
        if not self.tutorial_steps:
            return "No tutorial in progress. Tell me what you want to create!"
        
        self.current_step += 1
        
        if self.current_step >= len(self.tutorial_steps):
            return "[*] Tutorial complete! Great job! Would you like to try something else?"
        
        return self._format_step(self.current_step)
    
    def previous_step(self) -> str:
        """Go back to the previous step."""
        if self.current_step > 0:
            self.current_step -= 1
        return self._format_step(self.current_step)
    
    def repeat_step(self) -> str:
        """Repeat the current step."""
        return self._format_step(self.current_step)
    
    def _format_step(self, step_index: int) -> str:
        """Format a tutorial step for display."""
        if step_index >= len(self.tutorial_steps):
            return "Tutorial complete!"
        
        step = self.tutorial_steps[step_index]
        
        result = f"[*] Step {step.step_number}: {step.instruction}"
        
        if step.shortcut:
            result += f"\n⌨[*] Shortcut: {step.shortcut}"
        
        if step.tip:
            result += f"\n[Idea] Tip: {step.tip}"
        
        result += f"\n\n(Step {step_index + 1} of {len(self.tutorial_steps)})"
        
        return result
    
    def _generate_tutorial(self, product: str, task: str) -> List[AdobeStep]:
        """Generate tutorial steps using AI."""
        if not self.ai_manager:
            return []
        
        product_info = self.get_product_info(product)
        shortcuts = product_info.get('shortcuts', {})
        
        prompt = f"""You are an expert Adobe {product_info.get('name', product)} instructor.
Create a step-by-step tutorial for: "{task}"

Format each step as:
STEP [number]: [instruction]
SHORTCUT: [keyboard shortcut if applicable]
TIP: [helpful tip]

Keep instructions clear and beginner-friendly. Include 5-10 steps.
Use these shortcuts when relevant: {json.dumps(shortcuts)}"""

        try:
            response = self.ai_manager.get_response(prompt)
            return self._parse_tutorial_response(response)
        except Exception as e:
            print(f"[ADOBE] AI tutorial generation failed: {e}")
            return []
    
    def _parse_tutorial_response(self, response: str) -> List[AdobeStep]:
        """Parse AI response into tutorial steps."""
        steps = []
        current_step = None
        
        for line in response.split('\n'):
            line = line.strip()
            
            if line.upper().startswith('STEP'):
                if current_step:
                    steps.append(current_step)
                
                # Parse step number and instruction
                parts = line.split(':', 1)
                if len(parts) > 1:
                    try:
                        step_num = int(''.join(filter(str.isdigit, parts[0])))
                    except:
                        step_num = len(steps) + 1
                    
                    current_step = AdobeStep(
                        step_number=step_num,
                        instruction=parts[1].strip()
                    )
            
            elif current_step:
                if line.upper().startswith('SHORTCUT:'):
                    current_step.shortcut = line.split(':', 1)[1].strip()
                elif line.upper().startswith('TIP:'):
                    current_step.tip = line.split(':', 1)[1].strip()
        
        if current_step:
            steps.append(current_step)
        
        return steps
    
    def _get_basic_tutorial(self, product: str, task: str) -> List[AdobeStep]:
        """Get basic tutorial steps without AI."""
        task_lower = task.lower()
        
        # Photoshop basic tutorials
        if product == 'photoshop':
            if 'remove background' in task_lower:
                return [
                    AdobeStep(1, "Open your image in Photoshop", "Ctrl+O"),
                    AdobeStep(2, "Select the Quick Selection Tool from the toolbar", "W", "Hold Shift to add to selection"),
                    AdobeStep(3, "Click and drag over the subject you want to keep"),
                    AdobeStep(4, "Go to Select > Select and Mask for fine-tuning"),
                    AdobeStep(5, "Adjust the edge detection and smoothing settings"),
                    AdobeStep(6, "Set Output to 'New Layer with Layer Mask'"),
                    AdobeStep(7, "Click OK to apply the mask"),
                    AdobeStep(8, "Hide or delete the original background layer"),
                    AdobeStep(9, "Save your image as PNG to preserve transparency", "Ctrl+Shift+S"),
                ]
            elif 'resize' in task_lower:
                return [
                    AdobeStep(1, "Open your image", "Ctrl+O"),
                    AdobeStep(2, "Go to Image > Image Size", "Ctrl+Alt+I"),
                    AdobeStep(3, "Make sure the chain link icon is active to maintain proportions"),
                    AdobeStep(4, "Enter your desired width or height"),
                    AdobeStep(5, "Choose the resampling method (Bicubic for best quality)"),
                    AdobeStep(6, "Click OK to apply"),
                    AdobeStep(7, "Save your resized image", "Ctrl+S"),
                ]
        
        # Premiere Pro basic tutorials
        elif product == 'premiere_pro':
            if 'cut' in task_lower or 'edit' in task_lower:
                return [
                    AdobeStep(1, "Import your footage: File > Import", "Ctrl+I"),
                    AdobeStep(2, "Create a new sequence: File > New > Sequence", "Ctrl+N"),
                    AdobeStep(3, "Drag your clip from Project panel to Timeline"),
                    AdobeStep(4, "Position the playhead where you want to cut"),
                    AdobeStep(5, "Press C to select the Razor tool"),
                    AdobeStep(6, "Click on the clip to make the cut"),
                    AdobeStep(7, "Press V to switch back to Selection tool"),
                    AdobeStep(8, "Select and delete unwanted sections", "Delete"),
                    AdobeStep(9, "Close gaps by right-clicking > Ripple Delete"),
                ]
        
        # Default: return empty and let AI handle it
        return []
    
    def ask_guidance(self, question: str) -> str:
        """
        Answer a question about Adobe products.
        Uses screen context if available.
        """
        # Get screen context if available
        screen_context = ""
        if self.screen_reader:
            try:
                screen_text = self.screen_reader.capture_and_read_screen()
                if screen_text:
                    screen_context = f"\n\nCurrent screen shows: {screen_text[:500]}"
            except:
                pass
        
        if self.ai_manager:
            # Determine which product based on question or screen
            product = self._detect_product(question + screen_context)
            product_info = self.get_product_info(product) if product else {}
            
            prompt = f"""You are Monica, an expert Adobe Creative Suite instructor.
The user is asking about: {question}
{f"They appear to be using {product_info.get('name', 'an Adobe product')}." if product else ""}
{screen_context}

Provide a helpful, step-by-step answer. Include keyboard shortcuts when relevant.
Be encouraging and patient like a good teacher."""

            try:
                return self.ai_manager.get_response(prompt)
            except:
                pass
        
        return "I'd be happy to help! Could you tell me which Adobe product you're using and what you're trying to accomplish?"
    
    def _detect_product(self, text: str) -> Optional[str]:
        """Detect which Adobe product is being discussed."""
        text_lower = text.lower()
        
        for product in ADOBE_PRODUCTS.keys():
            if product in text_lower:
                return product
            
            # Check product name
            info = ADOBE_PRODUCTS[product]
            if info['name'].lower() in text_lower:
                return product
        
        return None
    
    def get_quick_help(self, product: str, topic: str) -> str:
        """Get quick help on a specific topic."""
        info = self.get_product_info(product)
        
        if not info:
            return f"I don't have information about {product}. Available products: {', '.join(self.get_products())}"
        
        topic_lower = topic.lower()
        
        # Check for shortcut request
        if 'shortcut' in topic_lower:
            shortcuts = info.get('shortcuts', {})
            if shortcuts:
                result = f"⌨[*] {info['name']} Shortcuts:\n"
                for action, shortcut in list(shortcuts.items())[:10]:
                    result += f"• {action.replace('_', ' ').title()}: {shortcut}\n"
                return result
        
        # Check for tools request
        if 'tool' in topic_lower:
            tools = info.get('tools', {})
            if tools:
                result = f"[Tool] {info['name']} Tools:\n"
                for key, tool in tools.items():
                    result += f"• {key}: {tool}\n"
                return result
        
        # General info
        return f"""[*] {info['name']}
{info['description']}

Common tasks: {', '.join(info.get('common_tasks', [])[:5])}

Say "shortcuts" for keyboard shortcuts or ask me how to do something specific!"""


# Singleton instance
_trainer = None

def get_adobe_trainer(ai_manager=None, screen_reader=None) -> AdobeTrainer:
    """Get or create the Adobe trainer singleton."""
    global _trainer
    if _trainer is None:
        _trainer = AdobeTrainer(ai_manager, screen_reader)
    elif ai_manager:
        _trainer.ai_manager = ai_manager
    elif screen_reader:
        _trainer.screen_reader = screen_reader
    return _trainer


# Test
if __name__ == "__main__":
    print("Adobe Trainer Test")
    trainer = get_adobe_trainer()
    
    print("\nSupported products:", trainer.get_products())
    print("\nPhotoshop shortcuts:", trainer.get_shortcuts('photoshop'))
    
    print("\nStarting tutorial...")
    print(trainer.start_tutorial('photoshop', 'remove background'))
    print("\nNext step:")
    print(trainer.next_step())
