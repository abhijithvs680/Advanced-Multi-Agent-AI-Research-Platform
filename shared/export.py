"""
Export Module - Generate reports in various formats.
Supports PDF, LaTeX, and Jupyter notebook exports.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import io

from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation"""
    format: str
    filename: str
    content: bytes
    mime_type: str


class ReportGenerator:
    """
    Generate publication-ready reports from research results.
    
    Supported formats:
    - PDF: via reportlab
    - LaTeX: via Jinja2 templates
    - Markdown: plain text
    - Jupyter: via nbformat
    """
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown(
        self,
        job_data: Dict[str, Any],
        include_raw: bool = False
    ) -> ExportResult:
        """Generate Markdown report"""
        md = []
        
        # Title
        md.append(f"# Research Report: {job_data.get('topic', 'Untitled')}")
        md.append(f"\n**Domain:** {job_data.get('domain', 'N/A')}")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")
        
        # Executive Summary
        if job_data.get('analysis'):
            md.append("## Executive Summary")
            md.append(job_data['analysis'].get('summary', 'No summary available.'))
            md.append("")
        
        # Literature Review
        if job_data.get('papers'):
            md.append("## Literature Review")
            md.append(f"Analyzed {len(job_data['papers'])} relevant papers.")
            md.append("")
            
            if job_data.get('analysis', {}).get('key_findings'):
                md.append("### Key Findings")
                for finding in job_data['analysis']['key_findings']:
                    md.append(f"- {finding}")
                md.append("")
            
            if job_data.get('analysis', {}).get('research_gaps'):
                md.append("### Research Gaps")
                for gap in job_data['analysis']['research_gaps']:
                    md.append(f"- {gap}")
                md.append("")
        
        # Hypotheses
        if job_data.get('hypotheses', {}).get('hypotheses'):
            md.append("## Research Hypotheses")
            for hyp in job_data['hypotheses']['hypotheses']:
                md.append(f"### {hyp.get('id', 'H')}: {hyp.get('statement', '')}")
                md.append(f"**Rationale:** {hyp.get('rationale', '')}")
                md.append(f"**Novelty Score:** {hyp.get('novelty_score', 0):.2f}")
                md.append("")
        
        # Methodology
        if job_data.get('methodology', {}).get('experimental_design'):
            design = job_data['methodology']['experimental_design']
            md.append("## Experimental Design")
            md.append(f"**Null Hypothesis:** {design.get('null_hypothesis', '')}")
            md.append(f"**Alternative Hypothesis:** {design.get('alternative_hypothesis', '')}")
            md.append("")
            
            if design.get('model_architectures'):
                md.append("### Model Architectures")
                for model in design['model_architectures']:
                    md.append(f"- **{model.get('name', '')}**: {model.get('rationale', '')}")
                md.append("")
            
            if design.get('evaluation', {}).get('metrics'):
                md.append("### Evaluation Metrics")
                md.append(", ".join(design['evaluation']['metrics']))
                md.append("")
        
        # Results
        if job_data.get('result'):
            md.append("## Results")
            result = job_data['result']
            
            if result.get('best_model'):
                md.append("### Best Model")
                md.append(f"- **Type:** {result['best_model'].get('model_type', 'N/A')}")
                md.append(f"- **Score:** {result['best_model'].get('score', 0):.4f}")
                md.append("")
            
            if result.get('metrics'):
                md.append("### Performance Metrics")
                for key, value in result['metrics'].items():
                    if isinstance(value, float):
                        md.append(f"- **{key}:** {value:.4f}")
                    else:
                        md.append(f"- **{key}:** {value}")
                md.append("")
        
        # References
        if job_data.get('papers'):
            md.append("## References")
            for i, paper in enumerate(job_data['papers'][:20], 1):
                authors = ", ".join(paper.get('authors', [])[:3])
                if len(paper.get('authors', [])) > 3:
                    authors += " et al."
                md.append(f"{i}. {authors} ({paper.get('year', 'N/A')}). {paper.get('title', 'Untitled')}.")
            md.append("")
        
        # Raw data
        if include_raw:
            md.append("## Raw Data")
            md.append("```json")
            md.append(json.dumps(job_data, indent=2, default=str))
            md.append("```")
        
        content = "\n".join(md)
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.md"
        
        return ExportResult(
            format="markdown",
            filename=filename,
            content=content.encode('utf-8'),
            mime_type="text/markdown"
        )
    
    def generate_latex(self, job_data: Dict[str, Any]) -> ExportResult:
        """Generate LaTeX report"""
        topic = job_data.get('topic', 'Untitled Research')
        domain = job_data.get('domain', 'General')
        
        latex = []
        latex.append(r"\documentclass[11pt]{article}")
        latex.append(r"\usepackage[utf8]{inputenc}")
        latex.append(r"\usepackage{hyperref}")
        latex.append(r"\usepackage{geometry}")
        latex.append(r"\geometry{margin=1in}")
        latex.append("")
        latex.append(f"\\title{{{self._latex_escape(topic)}}}")
        latex.append(r"\author{Multi-Agent Research Platform}")
        latex.append(f"\\date{{{datetime.now().strftime('%B %d, %Y')}}}")
        latex.append("")
        latex.append(r"\begin{document}")
        latex.append(r"\maketitle")
        latex.append("")
        
        # Abstract
        if job_data.get('analysis', {}).get('summary'):
            latex.append(r"\begin{abstract}")
            latex.append(self._latex_escape(job_data['analysis']['summary']))
            latex.append(r"\end{abstract}")
            latex.append("")
        
        # Introduction
        latex.append(r"\section{Introduction}")
        latex.append(f"This report presents the findings of an automated research study on {self._latex_escape(topic)} in the domain of {self._latex_escape(domain)}.")
        latex.append("")
        
        # Hypotheses
        if job_data.get('hypotheses', {}).get('hypotheses'):
            latex.append(r"\section{Research Hypotheses}")
            for hyp in job_data['hypotheses']['hypotheses']:
                latex.append(f"\\subsection{{{hyp.get('id', 'H')}}}")
                latex.append(f"\\textbf{{Statement:}} {self._latex_escape(hyp.get('statement', ''))}")
                latex.append("")
                latex.append(f"\\textbf{{Rationale:}} {self._latex_escape(hyp.get('rationale', ''))}")
                latex.append("")
        
        # Methodology
        if job_data.get('methodology', {}).get('experimental_design'):
            latex.append(r"\section{Methodology}")
            design = job_data['methodology']['experimental_design']
            latex.append(f"\\textbf{{Null Hypothesis:}} {self._latex_escape(design.get('null_hypothesis', ''))}")
            latex.append("")
        
        # Results
        if job_data.get('result'):
            latex.append(r"\section{Results}")
            result = job_data['result']
            if result.get('best_model'):
                latex.append(f"Best performing model: {self._latex_escape(result['best_model'].get('model_type', 'N/A'))}")
                latex.append(f" with score {result['best_model'].get('score', 0):.4f}.")
            latex.append("")
        
        # References
        if job_data.get('papers'):
            latex.append(r"\section{References}")
            latex.append(r"\begin{enumerate}")
            for paper in job_data['papers'][:15]:
                authors = ", ".join(paper.get('authors', [])[:2])
                if len(paper.get('authors', [])) > 2:
                    authors += " et al."
                title = self._latex_escape(paper.get('title', 'Untitled'))
                latex.append(f"\\item {authors} ({paper.get('year', 'N/A')}). {title}.")
            latex.append(r"\end{enumerate}")
        
        latex.append(r"\end{document}")
        
        content = "\n".join(latex)
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.tex"
        
        return ExportResult(
            format="latex",
            filename=filename,
            content=content.encode('utf-8'),
            mime_type="application/x-latex"
        )
    
    def generate_jupyter(self, job_data: Dict[str, Any]) -> ExportResult:
        """Generate Jupyter notebook"""
        try:
            import nbformat
            from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
        except ImportError:
            raise ImportError("nbformat package required. Run: pip install nbformat")
        
        nb = new_notebook()
        cells = []
        
        # Title cell
        cells.append(new_markdown_cell(
            f"# Research Report: {job_data.get('topic', 'Untitled')}\n\n"
            f"**Domain:** {job_data.get('domain', 'N/A')}\n\n"
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ))
        
        # Imports
        cells.append(new_code_cell(
            "import json\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "\n"
            "# Set style\n"
            "plt.style.use('seaborn-v0_8-whitegrid')\n"
            "sns.set_palette('husl')"
        ))
        
        # Data cell
        cells.append(new_code_cell(
            f"# Research data\n"
            f"data = {json.dumps(job_data, indent=2, default=str)}"
        ))
        
        # Summary
        if job_data.get('analysis'):
            cells.append(new_markdown_cell(
                f"## Executive Summary\n\n{job_data['analysis'].get('summary', 'No summary.')}"
            ))
        
        # Papers analysis
        if job_data.get('papers'):
            cells.append(new_markdown_cell("## Literature Analysis"))
            cells.append(new_code_cell(
                "# Create papers DataFrame\n"
                "papers_df = pd.DataFrame(data.get('papers', []))\n"
                "papers_df.head(10)"
            ))
            cells.append(new_code_cell(
                "# Citation distribution\n"
                "if 'citation_count' in papers_df.columns:\n"
                "    fig, ax = plt.subplots(figsize=(10, 5))\n"
                "    papers_df['citation_count'].hist(bins=20, ax=ax)\n"
                "    ax.set_xlabel('Citations')\n"
                "    ax.set_ylabel('Number of Papers')\n"
                "    ax.set_title('Citation Distribution')\n"
                "    plt.show()"
            ))
        
        # Results
        if job_data.get('result'):
            cells.append(new_markdown_cell("## Results"))
            cells.append(new_code_cell(
                "# Display results\n"
                "results = data.get('result', {})\n"
                "print(json.dumps(results, indent=2))"
            ))
        
        nb.cells = cells
        
        content = nbformat.writes(nb)
        filename = f"notebook_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.ipynb"
        
        return ExportResult(
            format="jupyter",
            filename=filename,
            content=content.encode('utf-8'),
            mime_type="application/x-ipynb+json"
        )
    
    def generate_pdf(self, job_data: Dict[str, Any]) -> ExportResult:
        """Generate PDF report using reportlab"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            raise ImportError("reportlab package required. Run: pip install reportlab")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20
        )
        story.append(Paragraph(f"Research Report: {job_data.get('topic', 'Untitled')}", title_style))
        story.append(Paragraph(f"<b>Domain:</b> {job_data.get('domain', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary
        if job_data.get('analysis', {}).get('summary'):
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Paragraph(job_data['analysis']['summary'], styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Key findings
        if job_data.get('analysis', {}).get('key_findings'):
            story.append(Paragraph("Key Findings", styles['Heading2']))
            for finding in job_data['analysis']['key_findings'][:5]:
                story.append(Paragraph(f"• {finding}", styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Results table
        if job_data.get('result', {}).get('best_model'):
            story.append(Paragraph("Results", styles['Heading2']))
            bm = job_data['result']['best_model']
            data = [
                ["Model Type", bm.get('model_type', 'N/A')],
                ["Score", f"{bm.get('score', 0):.4f}"]
            ]
            table = Table(data, colWidths=[150, 250])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
        
        doc.build(story)
        
        content = buffer.getvalue()
        filename = f"report_{job_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return ExportResult(
            format="pdf",
            filename=filename,
            content=content,
            mime_type="application/pdf"
        )
    
    def _latex_escape(self, text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text
    
    def export(
        self,
        job_data: Dict[str, Any],
        format: str = "markdown",
        save_to_disk: bool = True
    ) -> ExportResult:
        """
        Export job data to specified format.
        
        Args:
            job_data: Job data dictionary
            format: Export format (markdown, latex, jupyter, pdf)
            save_to_disk: Whether to save file to disk
            
        Returns:
            ExportResult with content and metadata
        """
        generators = {
            "markdown": self.generate_markdown,
            "md": self.generate_markdown,
            "latex": self.generate_latex,
            "tex": self.generate_latex,
            "jupyter": self.generate_jupyter,
            "ipynb": self.generate_jupyter,
            "pdf": self.generate_pdf
        }
        
        generator = generators.get(format.lower())
        if not generator:
            raise ValueError(f"Unsupported format: {format}. Supported: {list(generators.keys())}")
        
        result = generator(job_data)
        
        if save_to_disk:
            filepath = self.output_dir / result.filename
            filepath.write_bytes(result.content)
            logger.info("export_saved", filename=result.filename, format=format)
        
        return result


# Convenience functions
def export_job_report(job_data: Dict[str, Any], format: str = "markdown") -> ExportResult:
    """Export a job report"""
    generator = ReportGenerator()
    return generator.export(job_data, format)
