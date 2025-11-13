"""
Data Processor
Processes and analyzes data from HeyReach and Smartlead
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and analyze outreach data"""
    
    def __init__(self):
        """Initialize data processor"""
        self.linkedin_data = None
        self.email_data = None
    
    def process_data(self, linkedin_data: Dict, email_data: Dict) -> Dict:
        """
        Process and combine data from both platforms
        
        Args:
            linkedin_data: Data from HeyReach
            email_data: Data from Smartlead
            
        Returns:
            Processed data dictionary
        """
        self.linkedin_data = linkedin_data
        self.email_data = email_data
        
        combined_metrics = self._calculate_combined_metrics()
        performance_summary = self._generate_performance_summary()
        recommendations = self._generate_recommendations()
        
        return {
            'linkedin': linkedin_data,
            'email': email_data,
            'combined_metrics': combined_metrics,
            'performance_summary': performance_summary,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_combined_metrics(self) -> Dict:
        """Calculate combined metrics across both platforms"""
        
        # Total outreach
        total_outreach = (
            self.linkedin_data.get('total_invites_sent', 0) + 
            self.email_data.get('total_emails_sent', 0)
        )
        
        # Total responses
        total_responses = (
            self.linkedin_data.get('total_replies', 0) + 
            self.email_data.get('total_replied', 0)
        )
        
        # Overall response rate
        overall_response_rate = (
            (total_responses / total_outreach * 100) if total_outreach > 0 else 0
        )
        
        # Total active campaigns
        total_campaigns = (
            self.linkedin_data.get('total_campaigns', 0) + 
            self.email_data.get('total_campaigns', 0)
        )
        
        return {
            'total_outreach_actions': total_outreach,
            'total_responses': total_responses,
            'overall_response_rate': round(overall_response_rate, 2),
            'total_active_campaigns': total_campaigns,
            'linkedin_percentage': round(
                (self.linkedin_data.get('total_invites_sent', 0) / total_outreach * 100) 
                if total_outreach > 0 else 0, 2
            ),
            'email_percentage': round(
                (self.email_data.get('total_emails_sent', 0) / total_outreach * 100) 
                if total_outreach > 0 else 0, 2
            )
        }
    
    def _generate_performance_summary(self) -> Dict:
        """Generate performance summary with key insights"""
        
        linkedin_reply_rate = self.linkedin_data.get('reply_rate', 0)
        email_reply_rate = self.email_data.get('reply_rate', 0)
        
        # Determine best performing channel
        best_channel = "LinkedIn" if linkedin_reply_rate > email_reply_rate else "Email"
        
        # Performance status
        linkedin_status = self._get_performance_status(linkedin_reply_rate, 'linkedin')
        email_status = self._get_performance_status(email_reply_rate, 'email')
        
        return {
            'best_performing_channel': best_channel,
            'linkedin_performance': {
                'reply_rate': linkedin_reply_rate,
                'status': linkedin_status,
                'campaigns': self.linkedin_data.get('total_campaigns', 0)
            },
            'email_performance': {
                'reply_rate': email_reply_rate,
                'open_rate': self.email_data.get('open_rate', 0),
                'status': email_status,
                'campaigns': self.email_data.get('total_campaigns', 0)
            }
        }
    
    def _get_performance_status(self, reply_rate: float, channel: str) -> str:
        """Determine performance status based on reply rate"""
        
        # Benchmarks
        benchmarks = {
            'linkedin': {'excellent': 30, 'good': 20, 'average': 10},
            'email': {'excellent': 15, 'good': 10, 'average': 5}
        }
        
        bench = benchmarks.get(channel, benchmarks['email'])
        
        if reply_rate >= bench['excellent']:
            return "Excellent"
        elif reply_rate >= bench['good']:
            return "Good"
        elif reply_rate >= bench['average']:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on data"""
        
        recommendations = []
        
        # LinkedIn recommendations
        linkedin_acceptance = self.linkedin_data.get('acceptance_rate', 0)
        linkedin_reply = self.linkedin_data.get('reply_rate', 0)
        
        if linkedin_acceptance < 30:
            recommendations.append(
                "🎯 LinkedIn: Connection acceptance rate is below 30%. "
                "Consider refining your connection request message and targeting."
            )
        
        if linkedin_reply < 15:
            recommendations.append(
                "💬 LinkedIn: Reply rate is below 15%. "
                "Test new message sequences and personalization strategies."
            )
        
        # Email recommendations
        email_open = self.email_data.get('open_rate', 0)
        email_reply = self.email_data.get('reply_rate', 0)
        email_bounce = self.email_data.get('bounce_rate', 0)
        
        if email_open < 40:
            recommendations.append(
                "📧 Email: Open rate is below 40%. "
                "Test new subject lines and sender names."
            )
        
        if email_reply < 8:
            recommendations.append(
                "✉️ Email: Reply rate is below 8%. "
                "Improve personalization and value proposition in emails."
            )
        
        if email_bounce > 5:
            recommendations.append(
                "⚠️ Email: Bounce rate is above 5%. "
                "Clean your email list and verify email addresses before sending."
            )
        
        # Deliverability check
        delivery_rate = self.email_data.get('delivery_rate', 0)
        if delivery_rate < 95:
            recommendations.append(
                "🔧 Email: Delivery rate is below 95%. "
                "Check email warming status and domain reputation."
            )
        
        # General recommendations
        combined = self._calculate_combined_metrics()
        if combined['overall_response_rate'] < 10:
            recommendations.append(
                "📊 Overall: Response rate is below 10%. "
                "Consider reviewing your ICP targeting and message-market fit."
            )
        
        # Add positive feedback
        if not recommendations:
            recommendations.append(
                "🎉 Great work! Your campaigns are performing well. "
                "Continue testing and optimizing for even better results."
            )
        
        return recommendations
    
    def generate_dataframe(self, data_type: str) -> pd.DataFrame:
        """
        Generate pandas DataFrame for analysis
        
        Args:
            data_type: 'linkedin', 'email', or 'combined'
            
        Returns:
            DataFrame with campaign data
        """
        if data_type == 'linkedin':
            campaigns = self.linkedin_data.get('campaigns_data', [])
            df = pd.DataFrame(campaigns)
            
        elif data_type == 'email':
            campaigns = self.email_data.get('campaigns_data', [])
            df = pd.DataFrame(campaigns)
            
        elif data_type == 'combined':
            linkedin_campaigns = self.linkedin_data.get('campaigns_data', [])
            email_campaigns = self.email_data.get('campaigns_data', [])
            
            # Add platform identifier
            for camp in linkedin_campaigns:
                camp['platform'] = 'LinkedIn'
            for camp in email_campaigns:
                camp['platform'] = 'Email'
            
            df = pd.DataFrame(linkedin_campaigns + email_campaigns)
        
        else:
            df = pd.DataFrame()
        
        return df
    
    def export_to_csv(self, output_path: str, data_type: str = 'combined'):
        """
        Export data to CSV file
        
        Args:
            output_path: Path to save CSV file
            data_type: Type of data to export
        """
        try:
            df = self.generate_dataframe(data_type)
            df.to_csv(output_path, index=False)
            logger.info(f"✅ Data exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def get_top_campaigns(self, n: int = 5, metric: str = 'reply_rate') -> Dict:
        """
        Get top performing campaigns
        
        Args:
            n: Number of top campaigns to return
            metric: Metric to sort by
            
        Returns:
            Dictionary with top LinkedIn and email campaigns
        """
        # LinkedIn top campaigns
        linkedin_campaigns = self.linkedin_data.get('campaigns_data', [])
        linkedin_df = pd.DataFrame(linkedin_campaigns)
        
        if not linkedin_df.empty and 'reply_rate' in linkedin_df.columns:
            top_linkedin = linkedin_df.nlargest(n, 'reply_rate').to_dict('records')
        else:
            top_linkedin = []
        
        # Email top campaigns
        email_campaigns = self.email_data.get('campaigns_data', [])
        email_df = pd.DataFrame(email_campaigns)
        
        if not email_df.empty and 'reply_rate' in email_df.columns:
            top_email = email_df.nlargest(n, 'reply_rate').to_dict('records')
        else:
            top_email = []
        
        return {
            'top_linkedin_campaigns': top_linkedin,
            'top_email_campaigns': top_email
        }
