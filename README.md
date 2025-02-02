# Auto Code Commenter

Auto Code Commenter is an AI-powered tool that helps you automatically add meaningful comments to your Python code. It uses OpenAI's API to analyze code structures and generate detailed comments, making it easier to understand and document your code.

## Features
- **Analyze Python Code**: Identifies functions, classes, and loops in your code.
- **Auto-Generate Comments**: Adds comments based on your selected style (brief, detailed, or technical).
- **Customizable Themes**: Toggle between light and dark themes.
- **Code Editor**: Includes a built-in editor for writing and editing Python code.
- **File Management**: Open and save Python files directly in the application.

## Requirements
- Python 3.8 or higher
- Required libraries: `openai`, `tkinter`

Install dependencies using:
```bash
pip install openai
```

## Usage
1. **Set API Key**: Provide your OpenAI API key in the application.
2. **Load Code**: Open a Python file or paste your code into the editor.
3. **Select Style**: Choose a commenting style (brief, detailed, or technical).
4. **Process Code**: Click the "Process Code" button to generate comments.
5. **Save Code**: Save the commented code to a file.

## How to Run
1. Clone the repository or download the script.
2. Run the script using:
   ```bash
   python script_name.py
   ```
3. The graphical user interface will launch, allowing you to use the tool.

## Settings
The application saves your OpenAI API key and theme preference in a `settings.json` file. These settings are automatically loaded when the application starts.

## Example
Sample Python code:
```python
def calculate_fibonacci(n: int) -> list:
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
```
After processing, the code will include meaningful comments generated by AI.
