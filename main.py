import ast
import os
import textwrap
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from openai import OpenAI
from typing import Dict, List, Optional
import json
import threading

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.structures = []
        
    def visit_FunctionDef(self, node):
        params = [arg.arg for arg in node.args.args]
        self.structures.append({
            'type': 'function',
            'name': node.name,
            'lineno': node.lineno,
            'params': params,
            'code': ast.unparse(node)
        })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.structures.append({
            'type': 'class',
            'name': node.name,
            'lineno': node.lineno,
            'code': ast.unparse(node)
        })
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.structures.append({
            'type': 'loop',
            'lineno': node.lineno,
            'code': ast.unparse(node)
        })
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.structures.append({
            'type': 'loop',
            'lineno': node.lineno,
            'code': ast.unparse(node)
        })
        self.generic_visit(node)

class CodeCommenterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Code Commenter")
        self.setup_ui()
        self.api_key = None
        self.client = None
        self.theme = "light"
        self.load_settings()
        
    def setup_ui(self):
        # Menu Bar
        self.create_menu()
        
        # Main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.columnconfigure(3, weight=1)
        self.main_container.rowconfigure(1, weight=1)
        
        # Toolbar
        self.create_toolbar()
        
        # Code areas
        self.create_code_areas()
        
        # Status bar
        self.create_status_bar()
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_container, mode='indeterminate')
        self.progress.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(5,0))
        self.progress.grid_remove()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set API Key", command=self.set_api_key)
        settings_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.main_container)
        toolbar.grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0,10))
        
        ttk.Button(toolbar, text="Process Code", command=self.process_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear All", command=self.clear_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load Sample", command=self.load_sample).pack(side=tk.LEFT, padx=2)
        
        # Comment style selector
        ttk.Label(toolbar, text="Style:").pack(side=tk.LEFT, padx=(10,2))
        self.style_var = tk.StringVar(value="detailed")
        style_combo = ttk.Combobox(toolbar, textvariable=self.style_var, values=["brief", "detailed", "technical"])
        style_combo.pack(side=tk.LEFT, padx=2)
        
    def create_code_areas(self):
        # Labels
        ttk.Label(self.main_container, text="Commented Code").grid(row=0, column=3, pady=5)
        
        # Text areas with line numbers
        self.original_code = self.create_text_widget(self.main_container, 1, 1)
        self.commented_code = self.create_text_widget(self.main_container, 1, 3)
        
        # Separator
        separator = ttk.Separator(self.main_container, orient="vertical")
        separator.grid(row=1, column=2, sticky="ns", padx=10)
        
    def create_text_widget(self, parent, row, col):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, sticky="nsew")
        
        # Line numbers
        line_numbers = tk.Text(frame, width=4, padx=3, takefocus=0, border=0, background='lightgray')
        line_numbers.pack(side="left", fill="y")
        
        # Main text area
        text_area = scrolledtext.ScrolledText(frame, width=60, height=30, wrap=tk.NONE)
        text_area.pack(side="left", fill="both", expand=True)
        
        # Sync scroll
        def sync_scroll(*args):
            line_numbers.yview_moveto(args[0])
        text_area.vbar = text_area.vbar
        text_area.vbar.configure(command=lambda *args: (text_area.yview(*args), sync_scroll(*args)))
        
        # Update line numbers
        def update_line_numbers(event=None):
            lines = text_area.get("1.0", "end-1c").count("\n") + 1
            line_numbers.delete("1.0", "end")
            line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        
        text_area.bind("<KeyRelease>", update_line_numbers)
        update_line_numbers()
        
        return text_area
        
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status = ttk.Label(self.main_container, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(5,0))
        
    def process_code(self):
        if not self.api_key or not self.client:
            messagebox.showerror("Error", "Please set your OpenAI API key first")
            return
            
        code = self.original_code.get("1.0", tk.END).strip()
        if not code:
            return
            
        self.progress.grid()
        self.progress.start()
        self.status_var.set("Processing code...")
        
        def process():
            try:
                structures = self.analyze_code(code)
                commented_code = self.add_ai_comments(code, structures)
                self.root.after(0, lambda: self.update_ui(commented_code))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.show_error(error_msg))
            finally:
                self.root.after(0, self.finish_processing)
                
        threading.Thread(target=process, daemon=True).start()
        
    def update_ui(self, commented_code):
        self.commented_code.delete("1.0", tk.END)
        self.commented_code.insert("1.0", commented_code)
        self.status_var.set("Code processing completed")
        
    def finish_processing(self):
        self.progress.stop()
        self.progress.grid_remove()
        
    def show_error(self, error_message):
        messagebox.showerror("Error", error_message)
        self.status_var.set("Error occurred during processing")
        
    def analyze_code(self, code: str) -> List[Dict]:
        tree = ast.parse(code)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        return analyzer.structures
        
    def add_ai_comments(self, code: str, structures: List[Dict]) -> str:
        lines = code.split('\n')
        style = self.style_var.get()
        
        for structure in sorted(structures, key=lambda x: x['lineno'], reverse=True):
            prompt = f"Generate a {style} comment for this {structure['type']}:\n{structure['code']}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a code documentation expert. Generate clear and concise comments."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            comment = response.choices[0].message.content.strip()
            lines.insert(structure['lineno'] - 1, f"# {comment}")
            
        return '\n'.join(lines)
        
    def set_api_key(self):
        key = simpledialog.askstring("API Key", "Enter your OpenAI API key:", show='*')
        if key:
            self.api_key = key
            self.client = OpenAI(api_key=key)
            self.save_settings()
            self.status_var.set("API key updated")
            
    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        # Add theme implementation here
        self.save_settings()
        
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.api_key = settings.get('api_key')
                if self.api_key:
                    self.client = OpenAI(api_key=self.api_key)
                self.theme = settings.get('theme', 'light')
        except FileNotFoundError:
            pass
            
    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump({
                'api_key': self.api_key,
                'theme': self.theme
            }, f)
            
    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as f:
                self.original_code.delete("1.0", tk.END)
                self.original_code.insert("1.0", f.read())
                
    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.commented_code.get("1.0", tk.END))
                
    def show_about(self):
        messagebox.showinfo("About", "Code Commenter v2.0\nAn AI-powered code documentation tool")
        
    def clear_text(self):
        self.original_code.delete("1.0", tk.END)
        self.commented_code.delete("1.0", tk.END)
        self.status_var.set("Ready")
        
    def load_sample(self):
        sample_code = textwrap.dedent("""
        def calculate_fibonacci(n: int) -> list:
            fib = [0, 1]
            for i in range(2, n):
                fib.append(fib[i-1] + fib[i-2])
            return fib
            
        class DataProcessor:
            def __init__(self, data: list):
                self.data = data
                
            def process(self) -> dict:
                result = {}
                for item in self.data:
                    if item in result:
                        result[item] += 1
                    else:
                        result[item] = 1
                return result
        """).strip()
        
        self.original_code.delete("1.0", tk.END)
        self.original_code.insert("1.0", sample_code)

def main():
    root = tk.Tk()
    root.geometry("1200x800")
    app = CodeCommenterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()