"""
RCA Report Generator.

This module generates structured RCA reports in various formats.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from app.rca.root_cause_engine import RCAResult


@dataclass
class RCAReport:
    """Structured RCA report."""
    report_id: str
    equipment: str
    issue: str
    root_cause: str
    confidence: float
    alternative_causes: List[Dict]
    evidence: List[str]
    recommended_actions: List[str]
    investigation_steps: List[str]
    similar_cases: List[Dict]
    created_at: datetime
    report_format: str = "json"


class ReportGenerator:
    """
    Generate RCA reports in various formats.
    
    Supports:
    - JSON (structured data)
    - Text (human-readable)
    - HTML (web-friendly)
    """
    
    def __init__(self, reports_dir: str = "./data/rca_reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        rca_result: RCAResult,
        issue: Optional[str] = None,
        format: str = "json"
    ) -> RCAReport:
        """
        Generate RCA report from analysis result.
        
        Args:
            rca_result: RCA analysis result
            issue: Issue description
            format: Output format ('json', 'text', 'html')
            
        Returns:
            RCAReport object
        """
        report = RCAReport(
            report_id=rca_result.analysis_id,
            equipment=rca_result.equipment_name,
            issue=issue or f"Analysis of {rca_result.equipment_name}",
            root_cause=rca_result.primary_cause.cause,
            confidence=rca_result.primary_cause.confidence,
            alternative_causes=[
                {
                    'cause': alt.cause,
                    'confidence': alt.confidence,
                    'reasoning': alt.reasoning
                }
                for alt in rca_result.secondary_causes
            ],
            evidence=rca_result.primary_cause.evidence,
            recommended_actions=rca_result.recommended_actions,
            investigation_steps=rca_result.investigation_steps,
            similar_cases=[
                {
                    'case_id': c.case_id,
                    'type': c.case_type,
                    'issue': c.issue,
                    'root_cause': c.root_cause,
                    'similarity': c.match_score
                }
                for c in rca_result.similar_cases[:5]
            ],
            created_at=rca_result.timestamp,
            report_format=format
        )
        
        return report
    
    def save_report(self, report: RCAReport) -> str:
        """Save report to file."""
        filename = f"rca_report_{report.report_id}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'report_id': report.report_id,
                'equipment': report.equipment,
                'issue': report.issue,
                'root_cause': report.root_cause,
                'confidence': report.confidence,
                'alternative_causes': report.alternative_causes,
                'evidence': report.evidence,
                'recommended_actions': report.recommended_actions,
                'investigation_steps': report.investigation_steps,
                'similar_cases': report.similar_cases,
                'created_at': report.created_at.isoformat(),
                'report_format': report.report_format
            }, f, indent=2)
        
        return str(filepath)
    
    def load_report(self, report_id: str) -> Optional[RCAReport]:
        """Load report from file."""
        filename = f"rca_report_{report_id}.json"
        filepath = self.reports_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            return RCAReport(
                report_id=data['report_id'],
                equipment=data['equipment'],
                issue=data['issue'],
                root_cause=data['root_cause'],
                confidence=data['confidence'],
                alternative_causes=data['alternative_causes'],
                evidence=data['evidence'],
                recommended_actions=data['recommended_actions'],
                investigation_steps=data['investigation_steps'],
                similar_cases=data['similar_cases'],
                created_at=datetime.fromisoformat(data['created_at']),
                report_format=data['report_format']
            )
        except Exception:
            return None
    
    def generate_text_report(self, report: RCAReport) -> str:
        """Generate human-readable text report."""
        lines = [
            "=" * 60,
            "ROOT CAUSE ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Report ID: {report.report_id}",
            f"Equipment: {report.equipment}",
            f"Date: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 60,
            "ISSUE",
            "-" * 60,
            report.issue,
            "",
            "-" * 60,
            "ROOT CAUSE",
            "-" * 60,
            f"Primary Cause: {report.root_cause}",
            f"Confidence: {report.confidence:.0f}%",
            "",
        ]
        
        if report.alternative_causes:
            lines.extend([
                "-" * 60,
                "ALTERNATIVE CAUSES",
                "-" * 60,
            ])
            for alt in report.alternative_causes:
                lines.append(f"  • {alt['cause']} (Confidence: {alt['confidence']:.0f}%)")
                lines.append(f"    Reason: {alt['reasoning']}")
            lines.append("")
        
        if report.evidence:
            lines.extend([
                "-" * 60,
                "SUPPORTING EVIDENCE",
                "-" * 60,
            ])
            for evidence in report.evidence[:10]:
                lines.append(f"  ✓ {evidence}")
            lines.append("")
        
        if report.recommended_actions:
            lines.extend([
                "-" * 60,
                "RECOMMENDED ACTIONS",
                "-" * 60,
            ])
            for i, action in enumerate(report.recommended_actions, 1):
                lines.append(f"  {i}. {action}")
            lines.append("")
        
        if report.investigation_steps:
            lines.extend([
                "-" * 60,
                "INVESTIGATION STEPS",
                "-" * 60,
            ])
            for step in report.investigation_steps:
                lines.append(f"  {step}")
            lines.append("")
        
        if report.similar_cases:
            lines.extend([
                "-" * 60,
                "SIMILAR HISTORICAL CASES",
                "-" * 60,
            ])
            for case in report.similar_cases[:5]:
                lines.append(f"  Case {case['case_id']}: {case['issue']}")
                lines.append(f"    Root Cause: {case['root_cause']}")
                lines.append(f"    Similarity: {case['similarity']*100:.0f}%")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("END OF REPORT")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def generate_html_report(self, report: RCAReport) -> str:
        """Generate HTML report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>RCA Report - {report.equipment}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #e0e0e0; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: #2a2a4e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        h1 {{ color: #f97316; margin: 0; }}
        h2 {{ color: #f97316; border-bottom: 2px solid #374151; padding-bottom: 10px; }}
        .card {{ background: #2a2a4e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .confidence {{ font-size: 2em; color: #22c55e; font-weight: bold; }}
        .confidence.low {{ color: #ef4444; }}
        .confidence.medium {{ color: #eab308; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #374151; }}
        .evidence {{ color: #22c55e; }}
        .alternative {{ color: #eab308; }}
        .step {{ padding: 10px; background: #1a1a2e; margin: 5px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Root Cause Analysis Report</h1>
            <p>Equipment: <strong>{report.equipment}</strong></p>
            <p>Report ID: {report.report_id}</p>
            <p>Date: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card">
            <h2>Root Cause</h2>
            <p style="font-size: 1.5em; color: #f97316;">{report.root_cause}</p>
            <p class="confidence {'low' if report.confidence < 50 else 'medium' if report.confidence < 70 else ''}">
                Confidence: {report.confidence:.0f}%
            </p>
        </div>
        
        <div class="card">
            <h2>Issue</h2>
            <p>{report.issue}</p>
        </div>
"""
        
        if report.alternative_causes:
            html += """
        <div class="card">
            <h2>Alternative Causes</h2>
            <ul>
"""
            for alt in report.alternative_causes:
                html += f"""
                <li class="alternative">
                    <strong>{alt['cause']}</strong> ({alt['confidence']:.0f}%)
                    <br><small>{alt['reasoning']}</small>
                </li>
"""
            html += """
            </ul>
        </div>
"""
        
        if report.evidence:
            html += """
        <div class="card">
            <h2>Supporting Evidence</h2>
            <ul>
"""
            for evidence in report.evidence[:10]:
                html += f"""
                <li class="evidence">✓ {evidence}</li>
"""
            html += """
            </ul>
        </div>
"""
        
        if report.recommended_actions:
            html += """
        <div class="card">
            <h2>Recommended Actions</h2>
            <ol>
"""
            for action in report.recommended_actions:
                html += f"""
                <li>{action}</li>
"""
            html += """
            </ol>
        </div>
"""
        
        if report.investigation_steps:
            html += """
        <div class="card">
            <h2>Investigation Steps</h2>
"""
            for step in report.investigation_steps:
                html += f"""
            <div class="step">{step}</div>
"""
            html += """
        </div>
"""
        
        if report.similar_cases:
            html += """
        <div class="card">
            <h2>Similar Historical Cases</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #374151;">
                    <th style="padding: 10px; text-align: left;">Case ID</th>
                    <th style="padding: 10px; text-align: left;">Issue</th>
                    <th style="padding: 10px; text-align: left;">Root Cause</th>
                    <th style="padding: 10px; text-align: left;">Similarity</th>
                </tr>
"""
            for case in report.similar_cases[:5]:
                html += f"""
                <tr style="border-bottom: 1px solid #374151;">
                    <td style="padding: 10px;">{case['case_id']}</td>
                    <td style="padding: 10px;">{case['issue'][:50]}...</td>
                    <td style="padding: 10px;">{case['root_cause']}</td>
                    <td style="padding: 10px;">{case['similarity']*100:.0f}%</td>
                </tr>
"""
            html += """
            </table>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def get_all_reports(self) -> List[RCAReport]:
        """Get all saved reports."""
        reports = []
        
        for filepath in self.reports_dir.glob("rca_report_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                reports.append(RCAReport(
                    report_id=data['report_id'],
                    equipment=data['equipment'],
                    issue=data['issue'],
                    root_cause=data['root_cause'],
                    confidence=data['confidence'],
                    alternative_causes=data['alternative_causes'],
                    evidence=data['evidence'],
                    recommended_actions=data['recommended_actions'],
                    investigation_steps=data['investigation_steps'],
                    similar_cases=data['similar_cases'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    report_format=data['report_format']
                ))
            except Exception:
                continue
        
        # Sort by date descending
        reports.sort(key=lambda x: x.created_at, reverse=True)
        return reports


# Singleton instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get global report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator