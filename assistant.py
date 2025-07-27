#!/usr/bin/env python3
"""
Interactive Command Line Transcript Editor
A utility for browsing and editing podcast transcript markdown files.
"""

import os
import sys
import shutil
import tty
import termios
from pathlib import Path
from typing import List, Optional, Tuple
import readline  # For better input handling

# ANSI color codes for highlighting
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class TranscriptEditor:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.current_path = self.root_path
        self.selected_index = 0
        self.file_list = []
        self.current_file_content = []
        self.current_file_path = None
        self.edited_content = []
        self.is_modified = False
        self.scroll_offset = 0  # Track scroll position in file editor
        
        # Edit mode variables
        self.edit_mode = "browse"  # browse, edit, insert, split
        self.cursor_line = 0  # Current line being edited
        self.cursor_pos = 0   # Cursor position within the line
        self.editing_line = ""  # Current line being edited
        self.original_line = ""  # Original line before editing
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def is_dialog_line(self, line: str) -> bool:
        """Check if a line is a dialog line (starts with timecode)."""
        import re
        # Pattern for timecode: [HH:MM:SS - HH:MM:SS] with optional extra **
        timecode_pattern = r'^\*\*\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]\*\*\*?'
        return bool(re.match(timecode_pattern, line.strip()))
    
    def is_character_line(self, line: str) -> bool:
        """Check if a line is a character line (starts with ##)."""
        return line.strip().startswith('##')
    
    def is_editable_line(self, line: str) -> bool:
        """Check if a line can be edited (has content beyond line number)."""
        stripped = line.strip()
        # Skip lines that are just line numbers or empty
        if not stripped or stripped.isdigit():
            return False
        return True
    
    def get_line_highlight(self, line: str, is_selected: bool = False, is_editing: bool = False) -> str:
        """Get the appropriate highlight for a line based on its type and state."""
        if is_editing:
            if self.is_dialog_line(line):
                return f"{Colors.BG_WHITE}{Colors.BLACK}"
            elif self.is_character_line(line):
                return f"{Colors.BG_YELLOW}{Colors.BLACK}"
            else:
                return f"{Colors.BG_WHITE}{Colors.BLACK}"
        elif is_selected:
            if self.is_dialog_line(line):
                return f"{Colors.BG_MAGENTA}{Colors.BLACK}"
            elif self.is_character_line(line):
                return f"{Colors.BG_CYAN}{Colors.BLACK}"
            else:
                return f"{Colors.BG_BLUE}{Colors.WHITE}"
        else:
            return ""
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions."""
        try:
            return shutil.get_terminal_size()
        except:
            return (80, 24)  # Default fallback
    
    def build_file_tree(self, path: Path, prefix: str = "", is_last: bool = True) -> List[Tuple[str, Optional[Path]]]:
        """Build a tree representation of the file structure with actual paths."""
        tree = []
        
        # Add parent directory option
        if path != self.root_path:
            tree.append((f"{prefix}├── ../", None))
        
        try:
            items = sorted([item for item in path.iterdir() if not item.name.startswith('.')])
            
            for i, item in enumerate(items):
                is_last_item = i == len(items) - 1
                current_prefix = "└── " if is_last_item else "├── "
                next_prefix = "    " if is_last_item else "│   "
                
                if item.is_dir():
                    tree.append((f"{prefix}{current_prefix}{item.name}/", None))
                    tree.extend(self.build_file_tree(item, prefix + next_prefix, is_last_item))
                elif item.suffix.lower() == '.md':
                    tree.append((f"{prefix}{current_prefix}{item.name}", item))
                    
        except PermissionError:
            tree.append((f"{prefix}├── [Permission Denied]", None))
        
        return tree
    
    def display_file_browser(self):
        """Display the file browser with highlighting."""
        self.clear_screen()
        width, height = self.get_terminal_size()
        
        print(f"{Colors.BOLD}{Colors.CYAN}Transcript Editor - File Browser{Colors.RESET}")
        print(f"{Colors.YELLOW}Current Path: {self.current_path}{Colors.RESET}")
        print("=" * width)
        
        # Build and display file tree
        self.file_list = self.build_file_tree(self.current_path)
        
        # Calculate display range
        max_display = height - 10  # Leave room for header and footer
        start_idx = max(0, min(self.selected_index - max_display // 2, len(self.file_list) - max_display))
        end_idx = min(start_idx + max_display, len(self.file_list))
        
        for i in range(start_idx, end_idx):
            display_text, file_path = self.file_list[i]
            
            if i == self.selected_index:
                # Highlight selected item
                if display_text.endswith('/'):
                    print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD} {display_text}{Colors.RESET}")
                elif display_text.endswith('.md'):
                    print(f"{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD} {display_text}{Colors.RESET}")
                else:
                    print(f"{Colors.BG_YELLOW}{Colors.WHITE}{Colors.BOLD} {display_text}{Colors.RESET}")
            else:
                # Normal display
                if display_text.endswith('/'):
                    print(f"{Colors.BLUE} {display_text}{Colors.RESET}")
                elif display_text.endswith('.md'):
                    print(f"{Colors.GREEN} {display_text}{Colors.RESET}")
                else:
                    print(f" {display_text}")
        
        print("=" * width)
        print(f"{Colors.YELLOW}Navigation: {Colors.RESET}↑/↓ or W/S to move, {Colors.GREEN}Enter{Colors.RESET} to select, {Colors.RED}q{Colors.RESET} to quit")
        
        if self.file_list:
            selected_display, selected_path = self.file_list[self.selected_index]
            print(f"{Colors.CYAN}Selected: {selected_display}{Colors.RESET}")
    

    
    def get_key(self) -> str:
        """Get a single key press, handling arrow keys and special characters."""
        try:
            # Save terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                
                # Check for escape sequences (arrow keys and page up/down)
                if ch == '\x1b':
                    next_ch = sys.stdin.read(1)
                    if next_ch == '[':
                        third_ch = sys.stdin.read(1)
                        if third_ch == 'A':
                            return 'up'
                        elif third_ch == 'B':
                            return 'down'
                        elif third_ch == 'C':
                            return 'right'
                        elif third_ch == 'D':
                            return 'left'
                        elif third_ch == '5':  # Page Up
                            fourth_ch = sys.stdin.read(1)
                            if fourth_ch == '~':
                                return 'page_up'
                        elif third_ch == '6':  # Page Down
                            fourth_ch = sys.stdin.read(1)
                            if fourth_ch == '~':
                                return 'page_down'
                        elif third_ch == '3':  # Delete
                            fourth_ch = sys.stdin.read(1)
                            if fourth_ch == '~':
                                return 'delete'
                        elif third_ch == 'H':  # Home
                            return 'home'
                        elif third_ch == 'F':  # End
                            return 'end'
                    else:
                        # Single ESC key (not followed by [)
                        return 'escape'
                
                # Check for special characters
                if ch == '\x7f':  # Backspace
                    return 'backspace'
                elif ch == '\r' or ch == '\n':  # Enter
                    return 'enter'
                
                return ch
            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            # Fallback to regular input if raw mode fails
            return input().lower()
    
    def handle_file_browser_input(self) -> Optional[str]:
        """Handle input in file browser mode."""
        try:
            key = self.get_key().lower()
            
            if key == 'q':
                return "quit"
            elif key in ['w', 'k', 'up']:
                self.selected_index = max(0, self.selected_index - 1)
            elif key in ['s', 'j', 'down']:
                self.selected_index = min(len(self.file_list) - 1, self.selected_index + 1)
            elif key in ['enter', '\r', '\n']:
                if self.file_list:
                    selected_display, selected_path = self.file_list[self.selected_index]
                    
                    if selected_display == "../":
                        # Go to parent directory
                        self.current_path = self.current_path.parent
                        self.selected_index = 0
                    elif selected_display.endswith('/'):
                        # Enter directory
                        dir_name = selected_display.split('── ')[-1].rstrip('/')
                        self.current_path = self.current_path / dir_name
                        self.selected_index = 0
                    elif selected_display.endswith('.md') and selected_path:
                        # Open markdown file using the actual path
                        return str(selected_path)
            
            return None
            
        except (EOFError, KeyboardInterrupt):
            return "quit"
    
    def load_file(self, file_path: str):
        """Load a markdown file for editing."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_file_content = f.readlines()
                self.edited_content = self.current_file_content.copy()
                self.current_file_path = Path(file_path)
                self.is_modified = False
                self.scroll_offset = 0  # Reset scroll position when loading new file
        except Exception as e:
            print(f"{Colors.RED}Error loading file: {e}{Colors.RESET}")
            input("Press Enter to continue...")
    
    def display_file_editor(self):
        """Display the file editor with line numbers and content."""
        self.clear_screen()
        width, height = self.get_terminal_size()
        
        print(f"{Colors.BOLD}{Colors.CYAN}Transcript Editor - File Editor{Colors.RESET}")
        print(f"{Colors.YELLOW}File: {self.current_file_path}{Colors.RESET}")
        if self.is_modified:
            print(f"{Colors.RED}Modified{Colors.RESET}")
        print("=" * width)
        
        # Display file content with line numbers and scrolling
        max_display = height - 15  # Leave room for header, footer, and menu
        
        # Calculate the range of lines to display based on scroll offset
        start_line = self.scroll_offset
        end_line = min(start_line + max_display, len(self.edited_content))
        
        for i in range(start_line, end_line):
            line_num = f"{i+1:4d}"
            
            # Determine if this line is selected or being edited
            is_selected = (self.edit_mode == "edit" and i == self.cursor_line)
            is_editing = ((self.edit_mode == "insert" or self.edit_mode == "split") and i == self.cursor_line)
            
            # Use editing_line if we're editing this line, otherwise use original content
            if is_editing:
                line_content = self.editing_line
            else:
                line_content = self.edited_content[i].rstrip()
            
            # Get appropriate highlighting
            highlight = self.get_line_highlight(line_content, is_selected, is_editing)
            
            # Display the line with highlighting and cursor
            if is_editing and (self.edit_mode == "insert" or self.edit_mode == "split"):
                # Show line with cursor inline
                if highlight:
                    # Split the line at cursor position
                    before_cursor = line_content[:self.cursor_pos]
                    after_cursor = line_content[self.cursor_pos:]
                    print(f"{Colors.BLUE}{line_num}{Colors.RESET} {highlight}{before_cursor}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{highlight}{after_cursor}{Colors.RESET}")
                else:
                    # Split the line at cursor position
                    before_cursor = line_content[:self.cursor_pos]
                    after_cursor = line_content[self.cursor_pos:]
                    print(f"{Colors.BLUE}{line_num}{Colors.RESET} {before_cursor}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{after_cursor}")
            else:
                # Normal display without cursor
                if highlight:
                    print(f"{Colors.BLUE}{line_num}{Colors.RESET} {highlight}{line_content}{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}{line_num}{Colors.RESET} {line_content}")
        
        # Show scroll indicators
        if self.scroll_offset > 0:
            print(f"{Colors.YELLOW}↑ ({self.scroll_offset} lines above){Colors.RESET}")
        if end_line < len(self.edited_content):
            remaining = len(self.edited_content) - end_line
            print(f"{Colors.YELLOW}↓ ({remaining} lines below){Colors.RESET}")
        
        print("=" * width)
        
        if self.edit_mode == "edit":
            print(f"{Colors.BOLD}EDIT MODE:{Colors.RESET}")
            print(f"  {Colors.GREEN}(I){Colors.RESET}nsert  {Colors.GREEN}(S){Colors.RESET}plit  {Colors.GREEN}(↑/↓){Colors.RESET} Move  {Colors.GREEN}(ESC){Colors.RESET} Exit")
        elif self.edit_mode == "insert":
            print(f"{Colors.BOLD}INSERT MODE:{Colors.RESET}")
            print(f"  {Colors.GREEN}(ESC){Colors.RESET} Exit  {Colors.GREEN}(←/→){Colors.RESET} Move  {Colors.GREEN}(Home/End){Colors.RESET} Jump")
        elif self.edit_mode == "split":
            print(f"{Colors.BOLD}SPLIT MODE:{Colors.RESET}")
            print(f"  {Colors.GREEN}(←/→){Colors.RESET} Move  {Colors.GREEN}(Enter){Colors.RESET} Split  {Colors.GREEN}(ESC){Colors.RESET} Exit")
        else:
            print(f"{Colors.BOLD}Commands:{Colors.RESET}")
            print(f"  {Colors.GREEN}(C){Colors.RESET}lose  {Colors.GREEN}(E){Colors.RESET}dit  {Colors.GREEN}(S){Colors.RESET}ave  {Colors.GREEN}(A){Colors.RESET}save as")
            print(f"  {Colors.GREEN}(D){Colors.RESET}own  {Colors.GREEN}(U){Colors.RESET}p    {Colors.GREEN}(Q){Colors.RESET}uit")
            print(f"{Colors.CYAN}Scroll: {self.scroll_offset + 1}-{end_line} of {len(self.edited_content)} lines{Colors.RESET}")
            print(f"{Colors.YELLOW}Navigation: {Colors.RESET}↑/↓ or U/D to scroll, Page Up/Down for faster scrolling")
    
    def handle_file_editor_input(self) -> str:
        """Handle input in file editor mode."""
        try:
            if self.edit_mode == "browse":
                print(f"{Colors.YELLOW}Command: {Colors.RESET}", end='', flush=True)
                key = self.get_key().lower()
                print()  # New line after key press
                
                if key == 'q':
                    if self.is_modified:
                        save = input(f"{Colors.YELLOW}Save changes? (y/n): {Colors.RESET}").lower()
                        if save == 'y':
                            self.save_file()
                    return "browse"
                elif key == 'c':
                    if self.is_modified:
                        save = input(f"{Colors.YELLOW}Save changes? (y/n): {Colors.RESET}").lower()
                        if save == 'y':
                            self.save_file()
                    return "browse"
                elif key == 's':
                    self.save_file()
                elif key == 'a':
                    self.save_file_as()
                elif key == 'e':
                    self.enter_edit_mode()
                elif key in ['d', 'down']:
                    # Scroll down
                    width, height = self.get_terminal_size()
                    max_display = height - 15
                    max_scroll = max(0, len(self.edited_content) - max_display)
                    self.scroll_offset = min(self.scroll_offset + 1, max_scroll)
                elif key in ['u', 'up']:
                    # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif key == 'page_down':
                    # Page down (scroll by half screen)
                    width, height = self.get_terminal_size()
                    max_display = height - 15
                    scroll_amount = max_display // 2
                    max_scroll = max(0, len(self.edited_content) - max_display)
                    self.scroll_offset = min(self.scroll_offset + scroll_amount, max_scroll)
                elif key == 'page_up':
                    # Page up (scroll by half screen)
                    width, height = self.get_terminal_size()
                    max_display = height - 15
                    scroll_amount = max_display // 2
                    self.scroll_offset = max(0, self.scroll_offset - scroll_amount)
                
                return "edit"
            
            elif self.edit_mode == "edit":
                key = self.get_key().lower()
                
                if key == 'escape':
                    self.edit_mode = "browse"
                elif key in ['up', 'k']:
                    self.move_cursor_up()
                elif key in ['down', 'j']:
                    self.move_cursor_down()
                elif key == 'i':
                    self.enter_insert_mode()
                elif key == 's':
                    self.enter_split_mode()
                
                return "edit"
            
            elif self.edit_mode == "insert":
                key = self.get_key()
                
                if key == 'escape':
                    self.exit_insert_mode()
                elif key == 'backspace':
                    self.handle_backspace()
                elif key == 'delete':
                    self.handle_delete()
                elif key in ['left', 'h']:
                    self.move_cursor_left()
                elif key in ['right', 'l']:
                    self.move_cursor_right()
                elif key == 'home':
                    self.cursor_pos = 0
                elif key == 'end':
                    self.cursor_pos = len(self.editing_line)
                elif len(key) == 1 and ord(key) >= 32:  # Printable character
                    self.insert_character(key)
                
                return "edit"
            
            elif self.edit_mode == "split":
                key = self.get_key()
                
                if key == 'escape':
                    self.edit_mode = "edit"
                elif key in ['left', 'h']:
                    self.move_split_cursor_left()
                elif key in ['right', 'l']:
                    self.move_split_cursor_right()
                elif key == 'enter':
                    print(f"{Colors.YELLOW}Split operation triggered!{Colors.RESET}")
                    self.perform_split()
                
                return "edit"
            
            return "edit"
            
        except (EOFError, KeyboardInterrupt):
            return "browse"
    
    def save_file(self):
        """Save the current file."""
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.writelines(self.edited_content)
            self.is_modified = False
            print(f"{Colors.GREEN}File saved successfully!{Colors.RESET}")
            input("Press Enter to continue...")
        except Exception as e:
            print(f"{Colors.RED}Error saving file: {e}{Colors.RESET}")
            input("Press Enter to continue...")
    
    def save_file_as(self):
        """Save the current file with a new name."""
        try:
            # Pre-populate with current filename
            current_name = self.current_file_path.name
            print(f"{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}", end='', flush=True)
            
            # Read input character by character like insert mode
            new_name = ""
            cursor_pos = len(current_name)
            
            while True:
                key = self.get_key()
                
                if key == 'enter':
                    break
                elif key == 'escape':
                    return
                elif key == 'backspace':
                    if cursor_pos > 0:
                        new_name = new_name[:cursor_pos - 1] + new_name[cursor_pos:]
                        cursor_pos -= 1
                        # Redraw the input line
                        print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{new_name[:cursor_pos]}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{new_name[cursor_pos:]}", end='', flush=True)
                elif key in ['left', 'h']:
                    if cursor_pos > 0:
                        cursor_pos -= 1
                        print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{new_name[:cursor_pos]}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{new_name[cursor_pos:]}", end='', flush=True)
                elif key in ['right', 'l']:
                    if cursor_pos < len(new_name):
                        cursor_pos += 1
                        print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{new_name[:cursor_pos]}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{new_name[cursor_pos:]}", end='', flush=True)
                elif key == 'home':
                    cursor_pos = 0
                    print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{new_name}", end='', flush=True)
                elif key == 'end':
                    cursor_pos = len(new_name)
                    print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{new_name}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}", end='', flush=True)
                elif len(key) == 1 and ord(key) >= 32:  # Printable character
                    new_name = new_name[:cursor_pos] + key + new_name[cursor_pos:]
                    cursor_pos += 1
                    print(f"\r{Colors.YELLOW}Enter new filename (current: {current_name}): {Colors.RESET}{new_name[:cursor_pos]}{Colors.BG_WHITE}{Colors.BLACK}█{Colors.RESET}{new_name[cursor_pos:]}", end='', flush=True)
            
            print()  # New line after input
            
            if new_name:
                new_path = self.current_file_path.parent / new_name
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.writelines(self.edited_content)
                self.current_file_path = new_path
                self.is_modified = False
                print(f"{Colors.GREEN}File saved as {new_path}!{Colors.RESET}")
                input("Press Enter to continue...")
        except Exception as e:
            print(f"{Colors.RED}Error saving file: {e}{Colors.RESET}")
            input("Press Enter to continue...")
    
    def enter_edit_mode(self):
        """Enter edit mode for line selection and editing."""
        self.edit_mode = "edit"
        self.cursor_line = self.scroll_offset  # Start at the top of visible area
        # Find first editable line
        while (self.cursor_line < len(self.edited_content) and 
               not self.is_editable_line(self.edited_content[self.cursor_line])):
            self.cursor_line += 1
        if self.cursor_line >= len(self.edited_content):
            self.cursor_line = 0
    
    def move_cursor_up(self):
        """Move cursor up to previous editable line."""
        original_line = self.cursor_line
        while self.cursor_line > 0:
            self.cursor_line -= 1
            if self.is_editable_line(self.edited_content[self.cursor_line]):
                break
        # Adjust scroll if needed
        if self.cursor_line < self.scroll_offset:
            self.scroll_offset = self.cursor_line
    
    def move_cursor_down(self):
        """Move cursor down to next editable line."""
        original_line = self.cursor_line
        while self.cursor_line < len(self.edited_content) - 1:
            self.cursor_line += 1
            if self.is_editable_line(self.edited_content[self.cursor_line]):
                break
        # Adjust scroll if needed
        width, height = self.get_terminal_size()
        max_display = height - 15
        if self.cursor_line >= self.scroll_offset + max_display:
            self.scroll_offset = self.cursor_line - max_display + 1
    
    def enter_insert_mode(self):
        """Enter insert mode for editing the current line."""
        if self.cursor_line < len(self.edited_content):
            self.edit_mode = "insert"
            self.editing_line = self.edited_content[self.cursor_line].rstrip()
            self.original_line = self.editing_line
            self.cursor_pos = len(self.editing_line)  # Start at end of line
    
    def exit_insert_mode(self):
        """Exit insert mode and save changes."""
        if self.editing_line != self.original_line:
            self.edited_content[self.cursor_line] = self.editing_line + '\n'
            self.is_modified = True
        self.edit_mode = "edit"
        self.editing_line = ""
        self.original_line = ""
    
    def handle_backspace(self):
        """Handle backspace key in insert mode."""
        if self.cursor_pos > 0:
            self.editing_line = (self.editing_line[:self.cursor_pos - 1] + 
                               self.editing_line[self.cursor_pos:])
            self.cursor_pos -= 1
    
    def handle_delete(self):
        """Handle delete key in insert mode."""
        if self.cursor_pos < len(self.editing_line):
            self.editing_line = (self.editing_line[:self.cursor_pos] + 
                               self.editing_line[self.cursor_pos + 1:])
    
    def move_cursor_left(self):
        """Move cursor left in insert mode."""
        if self.cursor_pos > 0:
            self.cursor_pos -= 1
    
    def move_cursor_right(self):
        """Move cursor right in insert mode."""
        if self.cursor_pos < len(self.editing_line):
            self.cursor_pos += 1
    
    def insert_character(self, char):
        """Insert a character at cursor position."""
        self.editing_line = (self.editing_line[:self.cursor_pos] + char + 
                           self.editing_line[self.cursor_pos:])
        self.cursor_pos += 1
    
    def enter_split_mode(self):
        """Enter split mode for dialog lines."""
        if (self.cursor_line < len(self.edited_content) and 
            self.is_dialog_line(self.edited_content[self.cursor_line])):
            self.edit_mode = "split"
            self.editing_line = self.edited_content[self.cursor_line].rstrip()
            self.original_line = self.editing_line
            # Find the start of the content (after timecode)
            import re
            timecode_match = re.match(r'^\*\*\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]\*\*\*?', self.editing_line)
            if timecode_match:
                self.cursor_pos = len(timecode_match.group(0))  # Start after timecode
            else:
                self.cursor_pos = len(self.editing_line)  # Fallback to end
        else:
            print(f"{Colors.RED}Can only split dialog lines!{Colors.RESET}")
            input("Press Enter to continue...")
    
    def move_split_cursor_left(self):
        """Move split cursor left, stopping at word boundaries."""
        if self.cursor_pos > 0:
            # Find previous word boundary
            while self.cursor_pos > 0 and self.editing_line[self.cursor_pos - 1].isspace():
                self.cursor_pos -= 1
            while self.cursor_pos > 0 and not self.editing_line[self.cursor_pos - 1].isspace():
                self.cursor_pos -= 1
        print(f"{Colors.YELLOW}Split cursor moved left to position {self.cursor_pos}{Colors.RESET}")
    
    def move_split_cursor_right(self):
        """Move split cursor right, stopping at word boundaries."""
        if self.cursor_pos < len(self.editing_line):
            # Find next word boundary
            while self.cursor_pos < len(self.editing_line) and not self.editing_line[self.cursor_pos].isspace():
                self.cursor_pos += 1
            while self.cursor_pos < len(self.editing_line) and self.editing_line[self.cursor_pos].isspace():
                self.cursor_pos += 1
        print(f"{Colors.YELLOW}Split cursor moved right to position {self.cursor_pos}{Colors.RESET}")
    
    def perform_split(self):
        """Perform the split operation on the dialog line."""
        import re
        
        print(f"{Colors.YELLOW}perform_split called with editing_line: '{self.editing_line}'{Colors.RESET}")
        
        # Extract timecode and content
        timecode_match = re.match(r'^\*\*\[(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})\](\*\*\*?)(.*)', self.editing_line)
        
        # Also get just the timecode part for content_start_pos calculation
        timecode_only_match = re.match(r'^\*\*\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]\*\*\*?', self.editing_line)
        if not timecode_match:
            print(f"{Colors.RED}No timecode match found!{Colors.RESET}")
            self.edit_mode = "edit"
            return
        
        start_time, end_time, extra_stars, content = timecode_match.groups()
        
        # Find the actual content start (after the timecode and **)
        if timecode_only_match:
            timecode_part = timecode_only_match.group(0)
            content_start_pos = len(timecode_part)
        else:
            content_start_pos = 0
        
        print(f"{Colors.YELLOW}Debug: timecode_part='{timecode_part}', len={len(timecode_part)}{Colors.RESET}")
        
        # Calculate cursor position relative to the actual content
        cursor_in_content = self.cursor_pos - content_start_pos
        
        print(f"{Colors.YELLOW}Debug: cursor_pos={self.cursor_pos}, content_start_pos={content_start_pos}, cursor_in_content={cursor_in_content}{Colors.RESET}")
        
        # Ensure cursor position is within bounds
        if cursor_in_content < 0:
            cursor_in_content = 0
        elif cursor_in_content > len(content):
            cursor_in_content = len(content)
        
        # Split the content at the cursor position
        before_cursor = content[:cursor_in_content]
        after_cursor = content[cursor_in_content:]
        
        print(f"{Colors.YELLOW}Debug: before_cursor='{before_cursor}', after_cursor='{after_cursor}'{Colors.RESET}")
        
        # Calculate approximate split time based on content length
        total_chars = len(content)
        split_chars = len(before_cursor)
        
        # Convert times to seconds for calculation
        def time_to_seconds(time_str):
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        
        def seconds_to_time(seconds):
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        
        start_seconds = time_to_seconds(start_time)
        end_seconds = time_to_seconds(end_time)
        total_duration = end_seconds - start_seconds
        
        # Calculate split time proportionally
        # If no content, use cursor position relative to timecode length as ratio
        if total_chars == 0:
            # Use cursor position relative to the timecode part for empty lines
            timecode_part = timecode_match.group(0)
            split_ratio = self.cursor_pos / len(timecode_part) if len(timecode_part) > 0 else 0.5
        else:
            split_ratio = split_chars / total_chars if total_chars > 0 else 0.5
        
        print(f"{Colors.YELLOW}Debug: total_chars={total_chars}, split_chars={split_chars}, split_ratio={split_ratio}{Colors.RESET}")
        
        # Handle case where start and end times are the same (duration = 0)
        if total_duration == 0:
            # For zero duration, create a meaningful split by adding 1 second
            split_seconds = start_seconds + 1
            split_time = seconds_to_time(split_seconds)
        else:
            split_seconds = start_seconds + int(total_duration * split_ratio)
            split_time = seconds_to_time(split_seconds)
        
        # Create new lines with proper formatting
        # First line: from start_time to split_time with content before cursor
        new_line1 = f"**[{start_time} - {split_time}]**{extra_stars}{before_cursor}"
        
        # Second line: from split_time to end_time with content after cursor
        new_line2 = f"**[{split_time} - {end_time}]**{extra_stars}{after_cursor}"
        
        # If there's no content, ensure we still have the proper formatting
        if total_chars == 0:
            new_line1 = f"**[{start_time} - {split_time}]**{extra_stars}"
            new_line2 = f"**[{split_time} - {end_time}]**{extra_stars}"
        
        print(f"{Colors.YELLOW}Debug: extra_stars='{extra_stars}', len={len(extra_stars)}{Colors.RESET}")
        
        # Replace the original line with the first new line
        self.edited_content[self.cursor_line] = new_line1 + '\n'
        
        # Add a blank line between the split lines
        self.edited_content.insert(self.cursor_line + 1, '\n')
        
        # Insert the second new line after the blank line
        self.edited_content.insert(self.cursor_line + 2, new_line2 + '\n')
        
        print(f"{Colors.GREEN}Split completed!{Colors.RESET}")
        print(f"{Colors.GREEN}Line 1: {new_line1}{Colors.RESET}")
        print(f"{Colors.GREEN}Line 2: {new_line2}{Colors.RESET}")
        input("Press Enter to continue...")
        
        self.is_modified = True
        self.edit_mode = "edit"
        self.editing_line = ""
        self.original_line = ""
    
    def run(self):
        """Main execution loop."""
        mode = "browse"
        
        while True:
            if mode == "browse":
                self.display_file_browser()
                result = self.handle_file_browser_input()
                
                if result == "quit":
                    break
                elif result and result.endswith('.md'):
                    self.load_file(result)
                    mode = "edit"
            
            elif mode == "edit":
                self.display_file_editor()
                result = self.handle_file_editor_input()
                
                if result == "browse":
                    mode = "browse"
                elif result == "quit":
                    break

def main():
    """Main entry point."""
    editor = TranscriptEditor()
    
    try:
        editor.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()
