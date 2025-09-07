# A simple Markdown Editor with LaTeX Support

I've created a complete Markdown editor with preview functionality, syntax highlighting, and LaTeX support. 
This application uses PyQt5.

## Requirements

Before running this application, you need to install the following packages:

```bash
pip install PyQt5 PyQtWebEngine markdown chardet
```

## Features

1. **Dual-pane interface**: Left for editing, right for preview (with adjustable splitter) 
2. **Syntax highlighting**: Custom MarkdownHighlighter class for visual distinction of Markdown elements 
3. **Real-time preview**: Automatic update of preview with debounce timer for performance
4. **LaTeX support**: Integrated MathJax for rendering mathematical formulas
5. **Encoding detection**: Uses chardet to automatically detect file encoding when opening
6. **Complete menu system**: File, Edit, View, and Help menus with appropriate actions
7. **Keyboard shortcuts**: All standard shortcuts (Ctrl+C, Ctrl+V, Ctrl+S, etc.) implemented

The application implements a custom `MarkdownHighlighter` class that inherits from `QSyntaxHighlighter` to provide syntax highlighting for Markdown content.  
This gives the editor pane visual cues similar to what you'd see on markdown platforms.

For the preview pane, it uses `QWebEngineView` to render the converted HTML with proper styling and MathJax integration for LaTeX formulas. 

The application handles different text encodings by using the `chardet` library to detect the encoding of files when opening them, ensuring all special characters display correctly. 

All menu items have appropriate keyboard shortcuts assigned, making the application efficient to use without a mouse. 


