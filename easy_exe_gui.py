#!/usr/bin/env python3
"""
Easy EXE GUI Components - PyQt6 interface for Easy EXE
Provides modern GUI dialogs while maintaining CLI compatibility
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess
import webbrowser

try:
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QTextEdit, QCheckBox, QButtonGroup, QRadioButton,
        QScrollArea, QWidget, QMessageBox, QProgressDialog, QFrame,
        QGridLayout, QSpacerItem, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette
    HAS_QT = True
except ImportError:
    HAS_QT = False
    # Create dummy classes when PyQt6 is not available
    class QThread:
        pass
    class QDialog:
        pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
    class Qt:
        class WindowModality:
            WindowModal = None

if HAS_QT:
    class DependencyInstallThread(QThread):
        """Background thread for installing dependencies"""
        progress_update = pyqtSignal(str)
        installation_complete = pyqtSignal(bool, str)
        
        def __init__(self, command: str, package_name: str):
            super().__init__()
            self.command = command
            self.package_name = package_name
        
        def run(self):
            try:
                self.progress_update.emit(f"Installing {self.package_name}...")
                result = subprocess.run(
                    self.command.split(), 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                self.installation_complete.emit(True, f"{self.package_name} installed successfully!")
            except subprocess.CalledProcessError as e:
                self.installation_complete.emit(False, f"Installation failed: {e}")
            except Exception as e:
                self.installation_complete.emit(False, f"Error: {e}")
else:
    class DependencyInstallThread:
        def __init__(self, *args, **kwargs):
            pass

class EasyEXEGUI:
    """GUI interface for Easy EXE dialogs and interactions"""
    
    def __init__(self, easy_exe_instance):
        self.easy_exe = easy_exe_instance
        self.app = None
        
        # Initialize Qt application if GUI is available
        if HAS_QT and not QApplication.instance():
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Easy EXE")
            self.app.setApplicationDisplayName("Easy EXE - Windows Executable Launcher")
            
            # Set application style
            self.app.setStyle('Fusion')  # Modern, consistent look across platforms
    
    def is_gui_available(self) -> bool:
        """Check if GUI is available and display is accessible"""
        if not HAS_QT:
            return False
        
        # Check if we have a display (not running headless)
        try:
            if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
                return True
            return False
        except:
            return False
    
    def show_dependency_dialog(self, missing_deps: List[Tuple[str, Dict]], distro: str, required: bool) -> bool:
        """Show dependency installation dialog"""
        if not self.is_gui_available():
            return False
            
        dialog = DependencyDialog(missing_deps, distro, required, self.easy_exe)
        return dialog.exec() == QDialog.DialogCode.Accepted
    
    def show_unknown_program_dialog(self, exe_path: str, pe_info: Dict) -> Tuple[bool, str]:
        """Show unknown program identification dialog"""
        if not self.is_gui_available():
            return False, "fallback"
            
        dialog = UnknownProgramDialog(exe_path, pe_info)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.get_choice()
        return False, "cancel"
    
    def show_alternative_dialog(self, program_config: Dict) -> Tuple[bool, str]:
        """Show Linux alternative suggestion dialog"""
        if not self.is_gui_available():
            return False, "continue"
            
        dialog = AlternativeDialog(program_config, self.easy_exe)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.get_choice()
        return False, "continue"
    
    def show_warning_dialog(self, warning_type: str, program_name: str) -> Tuple[bool, bool]:
        """Show warning dialog and return (continue, disable_future)"""
        if not self.is_gui_available():
            return True, False
            
        dialog = WarningDialog(warning_type, program_name, self.easy_exe)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.should_disable_warnings()
        return False, dialog.should_disable_warnings()

if HAS_QT:
    class DependencyDialog(QDialog):
        """Dialog for showing missing dependencies and installation options"""
        
        def __init__(self, missing_deps: List[Tuple[str, Dict]], distro: str, required: bool, easy_exe):
            super().__init__()
            self.missing_deps = missing_deps
            self.distro = distro
            self.required = required
            self.easy_exe = easy_exe
            self.install_thread = None
            
            self.setup_ui()
        
        def setup_ui(self):
            self.setWindowTitle("Easy EXE - Dependencies")
            self.setMinimumSize(600, 400)
            
            layout = QVBoxLayout()
            
            # Header
            if self.required:
                header = QLabel("❌ Missing Core Dependencies")
                header.setStyleSheet("font-size: 18px; font-weight: bold; color: #d32f2f; margin: 10px;")
                subtitle = QLabel("Easy EXE cannot continue without these essential tools.")
            else:
                header = QLabel("💡 Enhanced Experience Available")
                header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin: 10px;")
                subtitle = QLabel("Easy EXE is ready! Consider these enhancements for the best experience:")
            
            subtitle.setStyleSheet("margin: 5px 10px; font-size: 14px;")
            layout.addWidget(header)
            layout.addWidget(subtitle)
            
            # Scrollable dependencies list
            scroll = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout()
            
            for dep_name, dep_info in self.missing_deps:
                dep_frame = self.create_dependency_frame(dep_name, dep_info)
                scroll_layout.addWidget(dep_frame)
            
            scroll_widget.setLayout(scroll_layout)
            scroll.setWidget(scroll_widget)
            scroll.setWidgetResizable(True)
            layout.addWidget(scroll)
            
            # Terminal instructions
            instructions_frame = QFrame()
            instructions_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;")
            instructions_layout = QVBoxLayout()
            
            instructions_label = QLabel("🖥️ Terminal Installation Guide:")
            instructions_label.setStyleSheet("font-weight: bold; margin: 5px;")
            instructions_layout.addWidget(instructions_label)
            
            terminal_text = QTextEdit()
            terminal_text.setMaximumHeight(100)
            terminal_text.setPlainText(self.get_terminal_instructions())
            terminal_text.setReadOnly(True)
            terminal_text.setStyleSheet("background-color: #2b2b2b; color: #ffffff; font-family: monospace;")
            instructions_layout.addWidget(terminal_text)
            
            instructions_frame.setLayout(instructions_layout)
            layout.addWidget(instructions_frame)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            if self.required:
                exit_btn = QPushButton("Exit - Install Dependencies First")
                exit_btn.clicked.connect(self.reject)
                button_layout.addWidget(exit_btn)
            else:
                continue_btn = QPushButton("Continue Without Enhancements")
                continue_btn.clicked.connect(self.accept)
                button_layout.addWidget(continue_btn)
            
            layout.addWidget(QWidget())  # Spacer
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
        
        def create_dependency_frame(self, dep_name: str, dep_info: Dict) -> QFrame:
            """Create a frame for a single dependency"""
            frame = QFrame()
            frame.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; margin: 5px; padding: 10px;")
            
            layout = QVBoxLayout()
            
            # Dependency name and description
            name_label = QLabel(f"📦 {dep_name}")
            name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(name_label)
            
            desc_label = QLabel(dep_info['description'])
            desc_label.setStyleSheet("color: #666; margin-left: 20px;")
            layout.addWidget(desc_label)
            
            # Installation command
            commands = dep_info.get("commands", {})
            install_cmd = commands.get(self.distro, commands.get("unknown", f"# Please install {dep_name}"))
            
            cmd_layout = QHBoxLayout()
            cmd_label = QLabel(f"Install: {install_cmd}")
            cmd_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 5px; border-radius: 2px;")
            cmd_layout.addWidget(cmd_label)
            
            # Quick install button (if not enhancement-only dialog)
            if not self.required and self.can_auto_install(install_cmd):
                install_btn = QPushButton("Install")
                install_btn.setMaximumWidth(80)
                install_btn.clicked.connect(lambda: self.install_dependency(install_cmd, dep_name))
                cmd_layout.addWidget(install_btn)
            
            layout.addLayout(cmd_layout)
            
            # Benefits (for enhancements)
            if not self.required and "benefits" in dep_info:
                benefits_label = QLabel("Benefits:")
                benefits_label.setStyleSheet("font-weight: bold; margin-top: 5px; margin-left: 20px;")
                layout.addWidget(benefits_label)
                
                for benefit in dep_info["benefits"][:3]:  # Show first 3 benefits
                    benefit_label = QLabel(f"• {benefit}")
                    benefit_label.setStyleSheet("margin-left: 40px; color: #555;")
                    layout.addWidget(benefit_label)
            
            frame.setLayout(layout)
            return frame
        
        def can_auto_install(self, command: str) -> bool:
            """Check if we can auto-install this dependency"""
            # Only allow auto-install for safe package managers
            safe_commands = ['sudo apt install', 'sudo pacman -S', 'flatpak install']
            return any(command.startswith(safe) for safe in safe_commands)
        
        def install_dependency(self, command: str, package_name: str):
            """Install dependency in background thread"""
            if self.install_thread and self.install_thread.isRunning():
                return
            
            # Show progress dialog
            self.progress = QProgressDialog(f"Installing {package_name}...", "Cancel", 0, 0, self)
            self.progress.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress.show()
            
            # Start installation thread
            self.install_thread = DependencyInstallThread(command, package_name)
            self.install_thread.progress_update.connect(self.progress.setLabelText)
            self.install_thread.installation_complete.connect(self.installation_finished)
            self.install_thread.start()
        
        def installation_finished(self, success: bool, message: str):
            """Handle installation completion"""
            self.progress.close()
            
            if success:
                QMessageBox.information(self, "Installation Complete", message)
            else:
                QMessageBox.warning(self, "Installation Failed", message)
        
        def get_terminal_instructions(self) -> str:
            """Get terminal installation instructions"""
            instructions = []
            instructions.append("1. Open terminal: Ctrl+Alt+T (or search 'Terminal')")
            instructions.append("2. Copy and run these commands:")
            instructions.append("")
            
            for dep_name, dep_info in self.missing_deps:
                commands = dep_info.get("commands", {})
                install_cmd = commands.get(self.distro, commands.get("unknown", f"# Install {dep_name}"))
                instructions.append(f"   {install_cmd}")
            
            instructions.append("")
            instructions.append("3. Run Easy EXE again after installation!")
            
            return "\n".join(instructions)

    class UnknownProgramDialog(QDialog):
        """Dialog for identifying unknown programs"""
        
        def __init__(self, exe_path: str, pe_info: Dict):
            super().__init__()
            self.exe_path = exe_path
            self.pe_info = pe_info
            self.choice = "game"  # Default choice
            
            self.setup_ui()
        
        def setup_ui(self):
            detected_name = self.pe_info.get('product_name', Path(self.exe_path).stem)
            self.setWindowTitle(f"Unknown Program: {detected_name}")
            
            layout = QVBoxLayout()
            layout.setSpacing(10)
            
            # Header
            header = QLabel("❓ Unknown Program Detected")
            header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 8px;")
            layout.addWidget(header)
            
            # Program info (more compact)
            info_frame = QFrame()
            info_frame.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;")
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            name_label = QLabel(f"{detected_name}")
            name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            info_layout.addWidget(name_label)
            
            if self.pe_info.get('company_name'):
                company_label = QLabel(f"by {self.pe_info['company_name']}")
                company_label.setStyleSheet("color: #666; font-size: 11px;")
                info_layout.addWidget(company_label)
            
            info_frame.setLayout(info_layout)
            layout.addWidget(info_frame)
            
            # Explanation (more concise)
            explanation = QLabel("Help classify this program for optimal setup:")
            explanation.setStyleSheet("margin: 5px; color: #555; font-size: 12px;")
            layout.addWidget(explanation)
            
            # Radio buttons for choice (more compact)
            self.button_group = QButtonGroup()
            
            game_radio = QRadioButton("🎮 Game - Use Lutris for optimized setup")
            game_radio.setChecked(True)  # Default selection
            game_radio.toggled.connect(lambda checked: self.set_choice("game" if checked else None))
            self.button_group.addButton(game_radio)
            layout.addWidget(game_radio)
            
            app_radio = QRadioButton("📦 Application - Set up with Wine")
            app_radio.toggled.connect(lambda checked: self.set_choice("app" if checked else None))
            self.button_group.addButton(app_radio)
            layout.addWidget(app_radio)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
            
            button_layout.addStretch()
            
            continue_btn = QPushButton("Continue")
            continue_btn.clicked.connect(self.accept)
            continue_btn.setDefault(True)
            button_layout.addWidget(continue_btn)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            # Apply compact sizing
            self.apply_compact_sizing()
        
        def apply_compact_sizing(self):
            """Apply smart compact sizing"""
            self.adjustSize()
            
            screen = QApplication.primaryScreen().availableGeometry()
            max_width = int(screen.width() * 0.30)  # Slightly smaller for simple dialog
            max_height = int(screen.height() * 0.25)
            
            min_width = 350
            min_height = 180
            
            optimal_size = self.sizeHint()
            final_width = min(max(optimal_size.width(), min_width), max_width)
            final_height = min(max(optimal_size.height(), min_height), max_height)
            
            self.resize(final_width, final_height)
            self.move(
                (screen.width() - final_width) // 2,
                (screen.height() - final_height) // 2
            )
        
        def set_choice(self, choice: str):
            if choice:
                self.choice = choice
        
        def get_choice(self) -> str:
            return self.choice

    class AlternativeDialog(QDialog):
        """Dialog for suggesting Linux alternatives"""
        
        def __init__(self, program_config: Dict, easy_exe):
            super().__init__()
            self.program_config = program_config
            self.easy_exe = easy_exe
            self.choice = "continue"
            
            self.setup_ui()
        
        def setup_ui(self):
            self.setWindowTitle("Linux Alternative Available")
            
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("💡 Linux Alternative Available!")
            header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; margin: 8px;")
            layout.addWidget(header)
            
            alternatives = self.program_config.get("alternatives", {})
            recommended = alternatives.get("recommended", {})
            
            if recommended:
                # Compact program comparison
                comparison_frame = QFrame()
                comparison_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; padding: 12px;")
                comparison_layout = QVBoxLayout()
                comparison_layout.setSpacing(8)
                
                # Windows vs Linux comparison (horizontal)
                vs_layout = QHBoxLayout()
                
                # Windows side
                win_layout = QVBoxLayout()
                win_label = QLabel("Windows:")
                win_label.setStyleSheet("font-weight: bold; color: #666;")
                win_layout.addWidget(win_label)
                
                win_name = QLabel(self.program_config['name'])
                win_name.setStyleSheet("font-size: 13px;")
                win_layout.addWidget(win_name)
                
                vs_layout.addLayout(win_layout)
                
                # Arrow
                arrow_label = QLabel("→")
                arrow_label.setStyleSheet("font-size: 18px; color: #1976d2; margin: 0 10px;")
                vs_layout.addWidget(arrow_label)
                
                # Linux side
                linux_layout = QVBoxLayout()
                linux_label = QLabel("Linux:")
                linux_label.setStyleSheet("font-weight: bold; color: #4caf50;")
                linux_layout.addWidget(linux_label)
                
                alt_name = QLabel(recommended['name'])
                alt_name.setStyleSheet("font-size: 13px; color: #4caf50; font-weight: bold;")
                linux_layout.addWidget(alt_name)
                
                vs_layout.addLayout(linux_layout)
                vs_layout.addStretch()  # Push content left
                
                comparison_layout.addLayout(vs_layout)
                
                # Quick summary
                if recommended.get("quick_summary"):
                    summary_label = QLabel(recommended["quick_summary"])
                    summary_label.setStyleSheet("color: #555; font-size: 12px; margin-left: 10px;")
                    summary_label.setWordWrap(True)
                    comparison_layout.addWidget(summary_label)
                
                # Critical caveat (only if present)
                if recommended.get("critical_caveat"):
                    caveat_label = QLabel(f"⚠️ {recommended['critical_caveat']}")
                    caveat_label.setStyleSheet("color: #f57c00; font-size: 11px; margin-left: 10px; font-style: italic;")
                    caveat_label.setWordWrap(True)
                    comparison_layout.addWidget(caveat_label)
                
                comparison_frame.setLayout(comparison_layout)
                layout.addWidget(comparison_frame)
            
            # Action buttons (more compact)
            button_layout = QVBoxLayout()
            button_layout.setSpacing(6)
            
            if recommended:
                install_btn = QPushButton(f"🚀 Install {recommended['name']}")
                install_btn.setStyleSheet("QPushButton { background-color: #4caf50; color: white; font-weight: bold; padding: 8px; }")
                install_btn.clicked.connect(lambda: self.set_choice("install"))
                button_layout.addWidget(install_btn)
            
            continue_btn = QPushButton(f"📦 Continue with {self.program_config['name']}")
            continue_btn.clicked.connect(lambda: self.set_choice("continue"))
            button_layout.addWidget(continue_btn)
            
            # More info and settings in horizontal layout
            bottom_layout = QHBoxLayout()
            
            more_info_btn = QPushButton("🌐 More Info")
            more_info_btn.setMaximumWidth(100)
            more_info_btn.clicked.connect(lambda: self.set_choice("browse"))
            bottom_layout.addWidget(more_info_btn)
            
            bottom_layout.addStretch()
            
            self.disable_checkbox = QCheckBox("Don't show again")
            bottom_layout.addWidget(self.disable_checkbox)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setMaximumWidth(80)
            cancel_btn.clicked.connect(self.reject)
            bottom_layout.addWidget(cancel_btn)
            
            button_layout.addLayout(bottom_layout)
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
            
            # Apply compact sizing (3x3 grid approach)
            self.apply_compact_sizing()
        
        def apply_compact_sizing(self):
            """Apply smart compact sizing - max 33% of screen"""
            # Calculate optimal size first
            self.adjustSize()
            
            # Get screen dimensions
            screen = QApplication.primaryScreen().availableGeometry()
            
            # 3x3 grid approach - max 33% of screen in either dimension
            max_width = int(screen.width() * 0.33)
            max_height = int(screen.height() * 0.33)
            
            # Reasonable minimums for readability
            min_width = 420
            min_height = 200
            
            # Smart sizing
            optimal_size = self.sizeHint()
            final_width = min(max(optimal_size.width(), min_width), max_width)
            final_height = min(max(optimal_size.height(), min_height), max_height)
            
            self.resize(final_width, final_height)
            
            # Center on screen
            self.move(
                (screen.width() - final_width) // 2,
                (screen.height() - final_height) // 2
            )
        
        def set_choice(self, choice: str):
            self.choice = choice
            if self.disable_checkbox.isChecked():
                self.easy_exe.state["user_preferences"]["show_alternative_suggestions"] = False
                self.easy_exe.save_state()
            self.accept()
        
        def get_choice(self) -> str:
            return self.choice

    class WarningDialog(QDialog):
        """Dialog for showing warnings with options"""
        
        def __init__(self, warning_type: str, program_name: str, easy_exe):
            super().__init__()
            self.warning_type = warning_type
            self.program_name = program_name
            self.easy_exe = easy_exe
            self.disable_warnings = False
            
            self.setup_ui()
        
        def setup_ui(self):
            self.setWindowTitle(f"Warning - {self.program_name}")
            
            layout = QVBoxLayout()
            layout.setSpacing(10)
            
            # Warning icon and header (more compact)
            header_layout = QHBoxLayout()
            warning_label = QLabel("⚠️")
            warning_label.setStyleSheet("font-size: 24px;")
            header_layout.addWidget(warning_label)
            
            title_label = QLabel(f"Notice - {self.program_name}")
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f57c00;")
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            
            layout.addLayout(header_layout)
            
            # Warning message
            message_template = self.easy_exe.messages.get(self.warning_type, {}).get("message", "")
            message = message_template.format(game_name=self.program_name)
            
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("margin: 5px; font-size: 12px;")
            layout.addWidget(message_label)
            
            # Instructions (more compact)
            instructions = self.easy_exe.messages.get(self.warning_type, {}).get("instructions", [])
            if instructions:
                instructions_frame = QFrame()
                instructions_frame.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;")
                instructions_layout = QVBoxLayout()
                instructions_layout.setSpacing(3)
                
                instructions_title = QLabel("💡 How to handle this:")
                instructions_title.setStyleSheet("font-weight: bold; font-size: 12px;")
                instructions_layout.addWidget(instructions_title)
                
                # Show only first 2 instructions to keep compact
                for instruction in instructions[:2]:
                    instruction_label = QLabel(f"• {instruction}")
                    instruction_label.setWordWrap(True)
                    instruction_label.setStyleSheet("margin-left: 5px; font-size: 11px;")
                    instructions_layout.addWidget(instruction_label)
                
                instructions_frame.setLayout(instructions_layout)
                layout.addWidget(instructions_frame)
            
            # Options and buttons (horizontal layout)
            bottom_layout = QHBoxLayout()
            
            self.disable_checkbox = QCheckBox("Don't show again")
            self.disable_checkbox.setStyleSheet("font-size: 11px;")
            bottom_layout.addWidget(self.disable_checkbox)
            
            bottom_layout.addStretch()
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            bottom_layout.addWidget(cancel_btn)
            
            continue_btn = QPushButton("Continue")
            continue_btn.clicked.connect(self.accept)
            continue_btn.setDefault(True)
            bottom_layout.addWidget(continue_btn)
            
            layout.addLayout(bottom_layout)
            self.setLayout(layout)
            
            # Apply compact sizing
            self.apply_compact_sizing()
        
        def apply_compact_sizing(self):
            """Apply smart compact sizing"""
            self.adjustSize()
            
            screen = QApplication.primaryScreen().availableGeometry()
            max_width = int(screen.width() * 0.32)
            max_height = int(screen.height() * 0.28)
            
            min_width = 380
            min_height = 160
            
            optimal_size = self.sizeHint()
            final_width = min(max(optimal_size.width(), min_width), max_width)
            final_height = min(max(optimal_size.height(), min_height), max_height)
            
            self.resize(final_width, final_height)
            self.move(
                (screen.width() - final_width) // 2,
                (screen.height() - final_height) // 2
            )
        
        def should_disable_warnings(self) -> bool:
            return self.disable_checkbox.isChecked()

else:
    # Dummy classes when PyQt6 is not available
    class DependencyDialog:
        def __init__(self, *args, **kwargs):
            pass
    
    class UnknownProgramDialog:
        def __init__(self, *args, **kwargs):
            pass
    
    class AlternativeDialog:
        def __init__(self, *args, **kwargs):
            pass
    
    class WarningDialog:
        def __init__(self, *args, **kwargs):
            pass

def create_gui_wrapper(easy_exe_instance):
    """Create GUI wrapper instance"""
    return EasyEXEGUI(easy_exe_instance)

# Test function for development
if __name__ == "__main__":
    if HAS_QT:
        app = QApplication(sys.argv)
        
        # Mock data for testing
        mock_deps = [
            ("wine", {
                "description": "Windows application compatibility layer",
                "commands": {"ubuntu": "sudo apt install wine"},
                "benefits": ["Essential for running Windows applications", "Mature and stable"]
            })
        ]
        
        dialog = DependencyDialog(mock_deps, "ubuntu", False, None)
        dialog.show()
        
        sys.exit(app.exec())
    else:
        print("PyQt6 not available - GUI components disabled")