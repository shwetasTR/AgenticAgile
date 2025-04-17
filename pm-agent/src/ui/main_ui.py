import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import json
import os
import sys
import threading

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.pdf_parser import PdfParser
from parsers.xml_parser import XmlParser
from parsers.notes_parser import NotesParser
from parsers.url_parser import UrlParser
from features.feature_extractor import FeatureExtractor
from generators.story_generator import StoryGenerator
from generators.criteria_generator import CriteriaGenerator
from generators.testcase_generator import TestCaseGenerator
from exporters.ado_exporter import ADOExporter
from utils.gemini_client import GeminiClient

class AgileEcosystemUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Agile Ecosystem - Feature Creation")
        self.root.geometry("900x700")
        
        # Initialize Gemini client
        self.gemini_client = GeminiClient()
        
        # Initialize components
        self.feature_data = None
        self.user_stories = None
        self.acceptance_criteria = None
        self.test_cases = None
        
        # Create UI components
        self.create_ui()
        
    def create_ui(self):
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.feature_tab = ttk.Frame(self.notebook)
        self.stories_tab = ttk.Frame(self.notebook)
        self.criteria_tab = ttk.Frame(self.notebook)
        self.testcases_tab = ttk.Frame(self.notebook)
        self.export_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.feature_tab, text="Feature Creation")
        self.notebook.add(self.stories_tab, text="User Stories")
        self.notebook.add(self.criteria_tab, text="Acceptance Criteria")
        self.notebook.add(self.testcases_tab, text="Test Cases")
        self.notebook.add(self.export_tab, text="Export")
        
        # Setup each tab
        self.setup_feature_tab()
        self.setup_stories_tab()
        self.setup_criteria_tab()
        self.setup_testcases_tab()
        self.setup_export_tab()
        
    def setup_feature_tab(self):
        # Input type selection
        input_frame = ttk.LabelFrame(self.feature_tab, text="Select Input Type")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.input_type = tk.StringVar(value="notes")
        
        ttk.Radiobutton(input_frame, text="PDF File", variable=self.input_type, 
                        value="pdf", command=self.toggle_input_fields).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(input_frame, text="URL", variable=self.input_type, 
                        value="url", command=self.toggle_input_fields).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(input_frame, text="Notes", variable=self.input_type, 
                        value="notes", command=self.toggle_input_fields).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(input_frame, text="XML File", variable=self.input_type, 
                        value="xml", command=self.toggle_input_fields).pack(side=tk.LEFT, padx=10, pady=5)
        
        # PDF file selection
        self.pdf_frame = ttk.Frame(self.feature_tab)
        self.pdf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.pdf_frame, text="PDF File:").pack(side=tk.LEFT, padx=5, pady=5)
        self.pdf_path_var = tk.StringVar()
        ttk.Entry(self.pdf_frame, textvariable=self.pdf_path_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.pdf_frame, text="Browse...", command=self.browse_pdf).pack(side=tk.LEFT, padx=5, pady=5)
        
        # URL input
        self.url_frame = ttk.Frame(self.feature_tab)
        self.url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.url_frame, text="URL:").pack(side=tk.LEFT, padx=5, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(self.url_frame, textvariable=self.url_var, width=60).pack(side=tk.LEFT, padx=5, pady=5)
        
        # XML file selection
        self.xml_frame = ttk.Frame(self.feature_tab)
        self.xml_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.xml_frame, text="XML File:").pack(side=tk.LEFT, padx=5, pady=5)
        self.xml_path_var = tk.StringVar()
        ttk.Entry(self.xml_frame, textvariable=self.xml_path_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.xml_frame, text="Browse...", command=self.browse_xml).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Notes input
        self.notes_frame = ttk.Frame(self.feature_tab)
        self.notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(self.notes_frame, text="Notes:").pack(anchor=tk.W, padx=5, pady=5)
        self.notes_text = scrolledtext.ScrolledText(self.notes_frame, wrap=tk.WORD, height=10)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Feature name
        feature_name_frame = ttk.Frame(self.feature_tab)
        feature_name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(feature_name_frame, text="Feature Name:").pack(side=tk.LEFT, padx=5, pady=5)
        self.feature_name_var = tk.StringVar()
        ttk.Entry(feature_name_frame, textvariable=self.feature_name_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Process button
        button_frame = ttk.Frame(self.feature_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="Process Feature", command=self.process_feature)
        self.process_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.feature_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Initially show only notes frame
        self.toggle_input_fields()
        
    def setup_stories_tab(self):
        # Controls frame
        controls_frame = ttk.Frame(self.stories_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate User Stories", command=self.generate_stories).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(controls_frame, text="Save User Stories", command=self.save_stories).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Stories display
        stories_frame = ttk.Frame(self.stories_tab)
        stories_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.stories_text = scrolledtext.ScrolledText(stories_frame, wrap=tk.WORD)
        self.stories_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_criteria_tab(self):
        # Controls frame
        controls_frame = ttk.Frame(self.criteria_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate Acceptance Criteria", command=self.generate_criteria).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(controls_frame, text="Save Acceptance Criteria", command=self.save_criteria).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Criteria display
        criteria_frame = ttk.Frame(self.criteria_tab)
        criteria_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.criteria_text = scrolledtext.ScrolledText(criteria_frame, wrap=tk.WORD)
        self.criteria_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_testcases_tab(self):
        # Controls frame
        controls_frame = ttk.Frame(self.testcases_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate Test Cases", command=self.generate_testcases).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(controls_frame, text="Save Test Cases", command=self.save_testcases).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Test cases display
        testcases_frame = ttk.Frame(self.testcases_tab)
        testcases_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.testcases_text = scrolledtext.ScrolledText(testcases_frame, wrap=tk.WORD)
        self.testcases_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_export_tab(self):
        # Export options
        export_frame = ttk.LabelFrame(self.export_tab, text="Export Options")
        export_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # ADO export
        ado_frame = ttk.Frame(export_frame)
        ado_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(ado_frame, text="Azure DevOps Organization:").pack(side=tk.LEFT, padx=5, pady=5)
        self.ado_org_var = tk.StringVar()
        ttk.Entry(ado_frame, textvariable=self.ado_org_var, width=30).pack(side=tk.LEFT, padx=5, pady=5)
        
        ado_project_frame = ttk.Frame(export_frame)
        ado_project_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(ado_project_frame, text="Azure DevOps Project:").pack(side=tk.LEFT, padx=5, pady=5)
        self.ado_project_var = tk.StringVar()
        ttk.Entry(ado_project_frame, textvariable=self.ado_project_var, width=30).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Export buttons
        buttons_frame = ttk.Frame(self.export_tab)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Export to JSON", command=self.export_to_json).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Export to Azure DevOps", command=self.export_to_ado).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Export status
        self.export_status_var = tk.StringVar(value="Ready for export")
        export_status_label = ttk.Label(self.export_tab, textvariable=self.export_status_var, relief=tk.SUNKEN, anchor=tk.W)
        export_status_label.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
    def toggle_input_fields(self):
        input_type = self.input_type.get()
        
        # Hide all frames first
        self.pdf_frame.pack_forget()
        self.url_frame.pack_forget()
        self.notes_frame.pack_forget()
        self.xml_frame.pack_forget()
        
        # Show the selected frame
        if input_type == "pdf":
            self.pdf_frame.pack(fill=tk.X, padx=10, pady=5)
        elif input_type == "url":
            self.url_frame.pack(fill=tk.X, padx=10, pady=5)
        elif input_type == "notes":
            self.notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        elif input_type == "xml":
            self.xml_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path_var.set(filename)
    
    def browse_xml(self):
        filename = filedialog.askopenfilename(
            title="Select XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.xml_path_var.set(filename)
    
    def process_feature(self):
        input_type = self.input_type.get()
        feature_name = self.feature_name_var.get()
        
        if not feature_name:
            self.status_var.set("Error: Feature name is required")
            return
        
        self.status_var.set("Processing feature...")
        self.process_button.config(state=tk.DISABLED)
        
        # Run processing in a separate thread to keep UI responsive
        threading.Thread(target=self._process_feature_thread, args=(input_type, feature_name)).start()
    
    def _process_feature_thread(self, input_type, feature_name):
        try:
            if input_type == "pdf":
                pdf_path = self.pdf_path_var.get()
                if not pdf_path:
                    self.update_status("Error: PDF file path is required")
                    return
                
                parser = PdfParser()
                self.feature_data = parser.parse(pdf_path)
                
            elif input_type == "url":
                url = self.url_var.get()
                if not url:
                    self.update_status("Error: URL is required")
                    return
                
                parser = UrlParser()
                self.feature_data = parser.parse(url)
                
            elif input_type == "notes":
                notes = self.notes_text.get("1.0", tk.END).strip()
                if not notes:
                    self.update_status("Error: Notes are required")
                    return
                
                parser = NotesParser()
                self.feature_data = parser.parse(notes)
                
            elif input_type == "xml":
                xml_path = self.xml_path_var.get()
                if not xml_path:
                    self.update_status("Error: XML file path is required")
                    return
                
                parser = XmlParser()
                self.feature_data = parser.parse(xml_path)
            
            # Add feature name to the data
            self.feature_data["name"] = feature_name
            
            # Update UI
            self.update_status(f"Feature '{feature_name}' processed successfully")
            self.notebook.select(1)  # Switch to User Stories tab
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
    
    def update_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))
    
    def generate_stories(self):
        if not self.feature_data:
            self.status_var.set("Error: No feature data available. Process a feature first.")
            return
        
        self.stories_text.delete("1.0", tk.END)
        self.stories_text.insert(tk.END, "Generating user stories...\n")
        
        # Run in a separate thread
        threading.Thread(target=self._generate_stories_thread).start()
    
    def _generate_stories_thread(self):
        try:
            generator = StoryGenerator(self.gemini_client)
            self.user_stories = generator.generate(self.feature_data)
            
            # Display stories
            self.root.after(0, lambda: self.stories_text.delete("1.0", tk.END))
            stories_json = json.dumps(self.user_stories, indent=2)
            self.root.after(0, lambda: self.stories_text.insert(tk.END, stories_json))
            
            self.update_status("User stories generated successfully")
        except Exception as e:
            self.update_status(f"Error generating user stories: {str(e)}")
    
    def save_stories(self):
        if not self.user_stories:
            self.status_var.set("Error: No user stories to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save User Stories",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.user_stories, f, indent=2)
                self.status_var.set(f"User stories saved to {filename}")
            except Exception as e:
                self.status_var.set(f"Error saving user stories: {str(e)}")
    
    def generate_criteria(self):
        if not self.user_stories:
            self.status_var.set("Error: No user stories available. Generate user stories first.")
            return
        
        self.criteria_text.delete("1.0", tk.END)
        self.criteria_text.insert(tk.END, "Generating acceptance criteria...\n")
        
        # Run in a separate thread
        threading.Thread(target=self._generate_criteria_thread).start()
    
    def _generate_criteria_thread(self):
        try:
            generator = CriteriaGenerator(self.gemini_client)
            self.acceptance_criteria = generator.generate(self.user_stories)
            
            # Display criteria
            self.root.after(0, lambda: self.criteria_text.delete("1.0", tk.END))
            criteria_json = json.dumps(self.acceptance_criteria, indent=2)
            self.root.after(0, lambda: self.criteria_text.insert(tk.END, criteria_json))
            
            self.update_status("Acceptance criteria generated successfully")
        except Exception as e:
            self.update_status(f"Error generating acceptance criteria: {str(e)}")
    
    def save_criteria(self):
        if not self.acceptance_criteria:
            self.status_var.set("Error: No acceptance criteria to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Acceptance Criteria",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.acceptance_criteria, f, indent=2)
                self.status_var.set(f"Acceptance criteria saved to {filename}")
            except Exception as e:
                self.status_var.set(f"Error saving acceptance criteria: {str(e)}")
    
    def generate_testcases(self):
        if not self.acceptance_criteria:
            self.status_var.set("Error: No acceptance criteria available. Generate acceptance criteria first.")
            return
        
        self.testcases_text.delete("1.0", tk.END)
        self.testcases_text.insert(tk.END, "Generating test cases...\n")
        
        # Run in a separate thread
        threading.Thread(target=self._generate_testcases_thread).start()
    
    def _generate_testcases_thread(self):
        try:
            generator = TestCaseGenerator(self.gemini_client)
            self.test_cases = generator.generate(self.acceptance_criteria)
            
            # Display test cases
            self.root.after(0, lambda: self.testcases_text.delete("1.0", tk.END))
            testcases_json = json.dumps(self.test_cases, indent=2)
            self.root.after(0, lambda: self.testcases_text.insert(tk.END, testcases_json))
            
            self.update_status("Test cases generated successfully")
        except Exception as e:
            self.update_status(f"Error generating test cases: {str(e)}")
    
    def save_testcases(self):
        if not self.test_cases:
            self.status_var.set("Error: No test cases to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Test Cases",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.test_cases, f, indent=2)
                self.status_var.set(f"Test cases saved to {filename}")
            except Exception as e:
                self.status_var.set(f"Error saving test cases: {str(e)}")
    
    def export_to_json(self):
        if not self.user_stories or not self.acceptance_criteria or not self.test_cases:
            self.export_status_var.set("Error: Missing data. Generate all required artifacts first.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export to JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                export_data = {
                    "feature": self.feature_data,
                    "user_stories": self.user_stories,
                    "acceptance_criteria": self.acceptance_criteria,
                    "test_cases": self.test_cases
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                self.export_status_var.set(f"Data exported to {filename}")
            except Exception as e:
                self.export_status_var.set(f"Error exporting data: {str(e)}")
    
    def export_to_ado(self):
        if not self.user_stories or not self.acceptance_criteria or not self.test_cases:
            self.export_status_var.set("Error: Missing data. Generate all required artifacts first.")
            return
        
        org = self.ado_org_var.get()
        project = self.ado_project_var.get()
        
        if not org or not project:
            self.export_status_var.set("Error: Azure DevOps organization and project are required")
            return
        
        self.export_status_var.set("Exporting to Azure DevOps...")
        
        # Run in a separate thread
        threading.Thread(target=self._export_to_ado_thread, args=(org, project)).start()
    
    def _export_to_ado_thread(self, org, project):
        try:
            exporter = ADOExporter(org, project)
            result = exporter.export(
                self.feature_data,
                self.user_stories,
                self.acceptance_criteria,
                self.test_cases
            )
            
            self.update_export_status(f"Export to Azure DevOps completed: {result}")
        except Exception as e:
            self.update_export_status(f"Error exporting to Azure DevOps: {str(e)}")
    
    def update_export_status(self, message):
        self.root.after(0, lambda: self.export_status_var.set(message))

def main():
    root = tk.Tk()
    app = AgileEcosystemUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
