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
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("❓ Unknown Program Detected")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)
        
        # Program info
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px;")
        info_layout = QVBoxLayout()
        
        name_label = QLabel(f"Program: {detected_name}")
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)
        
        path_label = QLabel(f"Location: {self.exe_path}")
        path_label.setStyleSheet("font-family: monospace; font-size: 11px;")
        info_layout.addWidget(path_label)
        
        if self.pe_info.get('company_name'):
            company_label = QLabel(f"Company: {self.pe_info['company_name']}")
            info_layout.addWidget(company_label)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # Explanation
        explanation = QLabel("Easy EXE couldn't identify this program automatically. Please help by selecting the type:")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("margin: 10px; color: #555;")
        layout.addWidget(explanation)
        
        # Radio buttons for choice
        self.button_group = QButtonGroup()
        
        game_radio = QRadioButton("🎮 This is a game - Search Lutris for optimized installers")
        game_radio.setChecked(True)  # Default selection
        game_radio.toggled.connect(lambda checked: self.set_choice("game" if checked else None))
        self.button_group.addButton(game_radio)
        layout.addWidget(game_radio)
        
        app_radio = QRadioButton("📦 This is an application - Set up with Wine")
        app_radio.toggled.connect(lambda checked: self.set_choice("app" if checked else None))
        self.button_group.addButton(app_radio)
        layout.addWidget(app_radio)
        
        # Info boxes
        game_info = QLabel("• Games benefit from Lutris's community-optimized configurations\n• Automatic dependency management and performance tweaks")
        game_info.setStyleSheet("margin-left: 30px; color: #666; font-size: 12px;")
        layout.addWidget(game_info)
        
        layout.addWidget(QWidget())  # Spacer
        
        app_info = QLabel("• Applications get configured Wine environments\n• Isolated prefixes for stability and compatibility")
        app_info.setStyleSheet("margin-left: 30px; color: #666; font-size: 12px;")
        layout.addWidget(app_info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.clicked.connect(self.accept)
        continue_btn.setDefault(True)
        button_layout.addWidget(continue_btn)
        
        layout.addWidget(QWidget())  # Spacer
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
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
        self.setMinimumSize(550, 400)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("💡 Linux Alternative Available!")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin: 10px;")
        layout.addWidget(header)
        
        alternatives = self.program_config.get("alternatives", {})
        recommended = alternatives.get("recommended", {})
        
        if recommended:
            # Program comparison
            comparison_frame = QFrame()
            comparison_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; padding: 15px;")
            comparison_layout = QGridLayout()
            
            # Windows program
            win_label = QLabel("Windows Version:")
            win_label.setStyleSheet("font-weight: bold;")
            comparison_layout.addWidget(win_label, 0, 0)
            
            win_name = QLabel(self.program_config['name'])
            win_name.setStyleSheet("font-size: 14px;")
            comparison_layout.addWidget(win_name, 1, 0)
            
            win_details = QLabel("• Requires Wine compatibility layer\n• May have compatibility issues\n• Uses system resources for emulation")
            win_details.setStyleSheet("color: #666; font-size: 12px;")
            comparison_layout.addWidget(win_details, 2, 0)
            
            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setStyleSheet("color: #ddd;")
            comparison_layout.addWidget(separator, 0, 1, 3, 1)
            
            # Linux alternative
            linux_label = QLabel("Linux Alternative:")
            linux_label.setStyleSheet("font-weight: bold; color: #4caf50;")
            comparison_layout.addWidget(linux_label, 0, 2)
            
            alt_name = QLabel(recommended['name'])
            alt_name.setStyleSheet("font-size: 14px; color: #4caf50;")
            comparison_layout.addWidget(alt_name, 1, 2)
            
            linux_details = QLabel("• Native Linux application\n• Better performance and integration\n• Regular updates and support")
            linux_details.setStyleSheet("color: #666; font-size: 12px;")
            comparison_layout.addWidget(linux_details, 2, 2)
            
            comparison_frame.setLayout(comparison_layout)
            layout.addWidget(comparison_frame)
            
            # Installation options
            packages = recommended.get("packages", {})
            available_managers = self.easy_exe._get_available_package_managers()
            install_options = [(manager, packages[manager]) for manager in available_managers if manager in packages]
            
            if install_options:
                install_frame = QFrame()
                install_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px;")
                install_layout = QVBoxLayout()
                
                install_label = QLabel("📦 Installation Options:")
                install_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
                install_layout.addWidget(install_label)
                
                for manager, package in install_options[:3]:  # Show first 3 options
                    cmd = self.easy_exe._get_install_command(manager, package)
                    cmd_label = QLabel(f"{manager}: {cmd}")
                    cmd_label.setStyleSheet("font-family: monospace; font-size: 11px; margin-left: 20px;")
                    install_layout.addWidget(cmd_label)
                
                install_frame.setLayout(install_layout)
                layout.addWidget(install_frame)
        
        # Action buttons
        layout.addWidget(QWidget())  # Spacer
        
        button_layout = QVBoxLayout()
        
        if recommended:
            install_btn = QPushButton(f"🚀 Install {recommended['name']} (Recommended)")
            install_btn.setStyleSheet("QPushButton { background-color: #4caf50; color: white; font-weight: bold; padding: 10px; }")
            install_btn.clicked.connect(lambda: self.set_choice("install"))
            button_layout.addWidget(install_btn)
        
        continue_btn = QPushButton(f"📦 Continue with {self.program_config['name']} (Wine)")
        continue_btn.clicked.connect(lambda: self.set_choice("continue"))
        button_layout.addWidget(continue_btn)
        
        browse_btn = QPushButton("🌐 Browse More Alternatives Online")
        browse_btn.clicked.connect(lambda: self.set_choice("browse"))
        button_layout.addWidget(browse_btn)
        
        # Settings
        settings_layout = QHBoxLayout()
        self.disable_checkbox = QCheckBox("Don't show alternative suggestions again")
        settings_layout.addWidget(self.disable_checkbox)
        settings_layout.addWidget(QWidget())  # Spacer
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        settings_layout.addWidget(cancel_btn)
        
        button_layout.addLayout(settings_layout)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
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
        self.setMinimumSize(500, 350)
        
        layout = QVBoxLayout()
        
        # Warning icon and header
        header_layout = QHBoxLayout()
        warning_label = QLabel("⚠️")
        warning_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(warning_label)
        
        title_label = QLabel(f"Important Notice - {self.program_name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f57c00;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(QWidget())  # Spacer
        
        layout.addLayout(header_layout)
        
        # Warning message
        message_template = self.easy_exe.messages.get(self.warning_type, {}).get("message", "")
        message = message_template.format(game_name=self.program_name)
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("margin: 10px; font-size: 13px;")
        layout.addWidget(message_label)
        
        # Instructions
        instructions = self.easy_exe.messages.get(self.warning_type, {}).get("instructions", [])
        if instructions:
            instructions_frame = QFrame()
            instructions_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px;")
            instructions_layout = QVBoxLayout()
            
            instructions_title = QLabel("💡 How to handle this in Linux:")
            instructions_title.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
            instructions_layout.addWidget(instructions_title)
            
            for instruction in instructions:
                instruction_label = QLabel(f"• {instruction}")
                instruction_label.setWordWrap(True)
                instruction_label.setStyleSheet("margin-left: 10px; margin-bottom: 2px;")
                instructions_layout.addWidget(instruction_label)
            
            instructions_frame.setLayout(instructions_layout)
            layout.addWidget(instructions_frame)
        
        layout.addWidget(QWidget())  # Spacer
        
        # Options
        self.disable_checkbox = QCheckBox(f"Don't show {self.warning_type.replace('_', ' ')} warnings again")
        layout.addWidget(self.disable_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel - Let me handle this first")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        continue_btn = QPushButton(f"Continue launching {self.program_name}")
        continue_btn.clicked.connect(self.accept)
        continue_btn.setDefault(True)
        button_layout.addWidget(continue_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def should_disable_warnings(self) -> bool:
        return self.disable_checkbox.isChecked()

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