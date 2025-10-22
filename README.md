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

## LaTeX Support in Markdown Editor

### Supported LaTeX Formula Formats

1. **Inline formulas (within text line)**
   - Standard syntax: `$formula$`  
     Example: `$E = mc^2$` → $E = mc^2$
   - LaTeX syntax: `\(formula\)`  
     Example: `\(x^2 + y^2 = r^2\)` → \(x^2 + y^2 = r^2\)

2. **Display formulas (as separate block)**
   - Double dollar: `$$formula$$`  
     $$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$
   - LaTeX syntax: `\[formula\]`  
     \[
     \sum_{i=1}^{n} i = \frac{n(n+1)}{2}
     \]

3. **Standalone LaTeX commands (without delimiters)**  
   The editor automatically recognizes and renders LaTeX commands even without `$...$`:

   - **Text**  
     `\text{cm}` → units of measurement  
     `\text{m/s}` → meters per second

   - **Fractions**  
     `\frac{1}{2}` → ½  
     `\frac{a}{b}` → fraction

   - **Vectors**  
     `\vec{a}` → vector a  
     `\overrightarrow{AB}` → vector AB  
     `\overleftarrow{CD}` → left-pointing vector CD

   - **Arrows and operators**  
     `\implies` → ⇒  
     `\iff` → ⇔  
     `\cdot` → ·  
     `\times` → ×  
     `\uparrow` → ↑  
     `\downarrow` → ↓

   - **Roots**  
     `\sqrt{2}` → √2  
     `\sqrt[3]{8}` → ³√8

   - **Overlines and accents**  
     `\overline{AB}` → line over AB  
     `\underline{text}` → underline  
     `\hat{x}` → hat over x  
     `\bar{y}` → bar over y  
     `\tilde{z}` → tilde over z

   - **Boxes**  
     `\boxed{x = 5}` → result in a box  
     `\boxed{E = mc^2}` → formula in a box

   - **Greek letters**  
     `\alpha, \beta, \gamma, \delta, \theta, \pi, \sigma, \omega`  
     `\Delta, \Gamma, \Lambda, \Omega, \Sigma, \Phi, \Psi`

   - **Special symbols**  
     `\infty` → ∞  
     `\partial` → ∂  
     `\nabla` → ∇  
     `\hbar` → ℏ

### Usage Examples

**Physics**  
Newton's second law: \vec{F} = m\vec{a}  
Speed of light: $c = 3 \times 10^8$ \text{m/s}  
Kinetic energy:  
$$E_k = \frac{mv^2}{2}$$

**Mathematics**  
Pythagorean theorem: $a^2 + b^2 = c^2$  
Quadratic formula:  
\[
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\]  
Answer: \boxed{x = 42}

### Test Files
- `test_latex.md` – basic examples  
- `test_latex_extended.md` – extended examples covering all variants

### Version
Markdown Editor v0.0.5 with full LaTeX support
