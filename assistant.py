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
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

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
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
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
                
                # Check for escape sequences (arrow keys)
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
        
        # Display file content with line numbers
        max_display = height - 15  # Leave room for header, footer, and menu
        
        for i, line in enumerate(self.edited_content[:max_display]):
            line_num = f"{i+1:4d}"
            print(f"{Colors.BLUE}{line_num}{Colors.RESET} {line.rstrip()}")
        
        if len(self.edited_content) > max_display:
            print(f"{Colors.YELLOW}... ({len(self.edited_content) - max_display} more lines){Colors.RESET}")
        
        print("=" * width)
        print(f"{Colors.BOLD}Commands:{Colors.RESET}")
        print(f"  {Colors.GREEN}(C){Colors.RESET}lose  {Colors.GREEN}(E){Colors.RESET}dit  {Colors.GREEN}(S){Colors.RESET}ave  {Colors.GREEN}(A){Colors.RESET}save as")
        print(f"  {Colors.GREEN}(D){Colors.RESET}own  {Colors.GREEN}(U){Colors.RESET}p    {Colors.GREEN}(Q){Colors.RESET}uit")
    
    def handle_file_editor_input(self) -> str:
        """Handle input in file editor mode."""
        try:
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
                self.edit_mode()
            elif key == 'd':
                # Scroll down (placeholder)
                pass
            elif key == 'u':
                # Scroll up (placeholder)
                pass
            
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
            new_name = input(f"{Colors.YELLOW}Enter new filename: {Colors.RESET}")
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
    
    def edit_mode(self):
        """Enter edit mode for block selection and editing."""
        print(f"{Colors.CYAN}Edit mode - Block selection and editing features coming soon!{Colors.RESET}")
        input("Press Enter to continue...")
    
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
