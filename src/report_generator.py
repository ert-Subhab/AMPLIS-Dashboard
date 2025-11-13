"""
Report Generator
Generates HTML reports with visualizations
"""

from jinja2 import Template
from datetime import datetime
from typing import Dict
import plotly.graph_objects as go
import plotly.express as px
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate HTML reports with visualizations"""
    
    def __init__(self, template_path: str = None):
        """
        Initialize report generator
        
        Args:
            template_path: Path to HTML template (optional)
        """
        self.template_path = template_path
    
    def generate_html_report(self, processed_data: Dict, output_path: str):
        """
        Generate comprehensive HTML report
        
        Args:
            processed_data: Processed data from DataProcessor
            output_path: Path to save HTML report
        """
        try:
            # Generate charts
            charts = self._generate_charts(processed_data)
            
            # Generate HTML
            html_content = self._build_html(processed_data, charts)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML report generated: {output_path}")
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
    
    def _generate_charts(self, data: Dict) -> Dict:
        """Generate all charts for the report"""
        
        charts = {}
        
        # Chart 1: Platform Comparison
        charts['platform_comparison'] = self._create_platform_comparison_chart(data)
        
        # Chart 2: LinkedIn Performance
        charts['linkedin_metrics'] = self._create_linkedin_metrics_chart(data)
        
        # Chart 3: Email Performance
        charts['email_metrics'] = self._create_email_metrics_chart(data)
        
        # Chart 4: Combined Outreach Volume
        charts['outreach_volume'] = self._create_outreach_volume_chart(data)
        
        return charts
    
    def _create_platform_comparison_chart(self, data: Dict) -> str:
        """Create platform comparison chart"""
        
        linkedin = data['linkedin']
        email = data['email']
        
        fig = go.Figure(data=[
            go.Bar(
                name='LinkedIn',
                x=['Sent', 'Replies', 'Reply Rate %'],
                y=[
                    linkedin.get('total_invites_sent', 0),
                    linkedin.get('total_replies', 0),
                    linkedin.get('reply_rate', 0)
                ],
                marker_color='#0077B5'
            ),
            go.Bar(
                name='Email',
                x=['Sent', 'Replies', 'Reply Rate %'],
                y=[
                    email.get('total_emails_sent', 0),
                    email.get('total_replied', 0),
                    email.get('reply_rate', 0)
                ],
                marker_color='#EA4335'
            )
        ])
        
        fig.update_layout(
            title='Platform Performance Comparison',
            barmode='group',
            height=400
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_linkedin_metrics_chart(self, data: Dict) -> str:
        """Create LinkedIn metrics funnel chart"""
        
        linkedin = data['linkedin']
        
        values = [
            linkedin.get('total_invites_sent', 0),
            linkedin.get('total_invites_accepted', 0),
            linkedin.get('total_messages_sent', 0),
            linkedin.get('total_replies', 0)
        ]
        
        fig = go.Figure(go.Funnel(
            y=['Invites Sent', 'Accepted', 'Messages Sent', 'Replies'],
            x=values,
            textinfo="value+percent initial",
            marker={"color": ["#0077B5", "#0095D5", "#00B0F0", "#00C8FF"]}
        ))
        
        fig.update_layout(
            title='LinkedIn Outreach Funnel',
            height=400
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_email_metrics_chart(self, data: Dict) -> str:
        """Create email metrics funnel chart"""
        
        email = data['email']
        
        values = [
            email.get('total_emails_sent', 0),
            email.get('total_emails_delivered', 0),
            email.get('total_opened', 0),
            email.get('total_clicked', 0),
            email.get('total_replied', 0)
        ]
        
        fig = go.Figure(go.Funnel(
            y=['Sent', 'Delivered', 'Opened', 'Clicked', 'Replied'],
            x=values,
            textinfo="value+percent initial",
            marker={"color": ["#EA4335", "#FBBC04", "#34A853", "#4285F4", "#9C27B0"]}
        ))
        
        fig.update_layout(
            title='Email Outreach Funnel',
            height=400
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_outreach_volume_chart(self, data: Dict) -> str:
        """Create outreach volume pie chart"""
        
        combined = data['combined_metrics']
        
        fig = go.Figure(data=[go.Pie(
            labels=['LinkedIn', 'Email'],
            values=[
                combined.get('linkedin_percentage', 0),
                combined.get('email_percentage', 0)
            ],
            hole=.3,
            marker_colors=['#0077B5', '#EA4335']
        )])
        
        fig.update_layout(
            title='Outreach Volume by Platform',
            height=400
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _build_html(self, data: Dict, charts: Dict) -> str:
        """Build complete HTML report"""
        
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Outreach Performance Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .date {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .metric-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .metric-label {
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .chart-container {
            margin: 20px 0;
        }
        
        .recommendations {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .recommendations h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        
        .recommendation-item {
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .recommendation-item:last-child {
            border-bottom: none;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .status-excellent { background: #d4edda; color: #155724; }
        .status-good { background: #d1ecf1; color: #0c5460; }
        .status-average { background: #fff3cd; color: #856404; }
        .status-poor { background: #f8d7da; color: #721c24; }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Outreach Performance Report</h1>
            <p class="date">{{ generated_date }}</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Outreach</h3>
                <div class="metric-value">{{ total_outreach }}</div>
                <div class="metric-label">LinkedIn + Email</div>
            </div>
            
            <div class="metric-card">
                <h3>Total Responses</h3>
                <div class="metric-value">{{ total_responses }}</div>
                <div class="metric-label">Combined replies</div>
            </div>
            
            <div class="metric-card">
                <h3>Overall Response Rate</h3>
                <div class="metric-value">{{ overall_response_rate }}%</div>
                <div class="metric-label">Across all channels</div>
            </div>
            
            <div class="metric-card">
                <h3>Active Campaigns</h3>
                <div class="metric-value">{{ total_campaigns }}</div>
                <div class="metric-label">LinkedIn + Email</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Platform Comparison</h2>
            <div class="chart-container">
                {{ platform_comparison_chart }}
            </div>
        </div>
        
        <div class="section">
            <h2>💼 LinkedIn Performance</h2>
            <p><strong>Status:</strong> <span class="status-badge status-{{ linkedin_status_class }}">{{ linkedin_status }}</span></p>
            <div class="chart-container">
                {{ linkedin_chart }}
            </div>
        </div>
        
        <div class="section">
            <h2>📧 Email Performance</h2>
            <p><strong>Status:</strong> <span class="status-badge status-{{ email_status_class }}">{{ email_status }}</span></p>
            <div class="chart-container">
                {{ email_chart }}
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Outreach Distribution</h2>
            <div class="chart-container">
                {{ outreach_volume_chart }}
            </div>
        </div>
        
        <div class="recommendations">
            <h3>💡 Recommendations</h3>
            {% for rec in recommendations %}
            <div class="recommendation-item">{{ rec }}</div>
            {% endfor %}
        </div>
        
        <footer>
            <p>Generated by Outreach Reporting Automation | {{ generated_date }}</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # Prepare template data
        combined = data['combined_metrics']
        performance = data['performance_summary']
        
        template_data = {
            'generated_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'total_outreach': f"{combined['total_outreach_actions']:,}",
            'total_responses': f"{combined['total_responses']:,}",
            'overall_response_rate': combined['overall_response_rate'],
            'total_campaigns': combined['total_active_campaigns'],
            'platform_comparison_chart': charts['platform_comparison'],
            'linkedin_chart': charts['linkedin_metrics'],
            'email_chart': charts['email_metrics'],
            'outreach_volume_chart': charts['outreach_volume'],
            'linkedin_status': performance['linkedin_performance']['status'],
            'linkedin_status_class': performance['linkedin_performance']['status'].lower().replace(' ', '-'),
            'email_status': performance['email_performance']['status'],
            'email_status_class': performance['email_performance']['status'].lower().replace(' ', '-'),
            'recommendations': data['recommendations']
        }
        
        # Render template
        jinja_template = Template(template)
        return jinja_template.render(**template_data)
