"""Analytics dashboard page with metrics, visualizations, and insights."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from src.db.database import Database
from src.analytics.analytics_service import AnalyticsService


def format_timedelta(seconds: float) -> str:
    """Format seconds as human-readable time."""
    if seconds is None:
        return "N/A"
    
    td = timedelta(seconds=int(seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def render_analytics_page(db: Database):
    """Render analytics dashboard page."""
    st.header("Analytics & Insights")
    
    # Initialize analytics service
    analytics = AnalyticsService(db)
    
    # Key Metrics Section
    st.subheader("Key Metrics")
    metrics = analytics.get_key_metrics()
    
    metric_cols = st.columns(5)
    with metric_cols[0]:
        st.metric("Total Jobs", metrics['total_jobs'])
    with metric_cols[1]:
        st.metric("Applications Submitted", metrics['applications_submitted'])
    with metric_cols[2]:
        avg_time = metrics.get('average_time_to_apply_seconds')
        st.metric("Avg Time-to-Apply", format_timedelta(avg_time) if avg_time else "N/A")
    with metric_cols[3]:
        st.metric("Resumes Generated", metrics['resume_generation_count'])
    with metric_cols[4]:
        approval_rate = metrics['bullet_approval_rate']
        st.metric("Bullet Approval Rate", f"{approval_rate:.1%}")
    
    st.divider()
    
    # Time-to-Apply Analysis
    st.subheader("Time-to-Apply Analysis")
    
    time_stats = analytics.get_time_to_apply_stats()
    time_dist = analytics.get_time_to_apply_distribution()
    
    if time_stats['count'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Count", time_stats['count'])
        with col2:
            st.metric("Average", format_timedelta(time_stats.get('average_seconds')))
        with col3:
            st.metric("Median", format_timedelta(time_stats.get('median_seconds')))
        with col4:
            st.metric("Range", 
                     f"{format_timedelta(time_stats.get('min_seconds'))} - {format_timedelta(time_stats.get('max_seconds'))}")
        
        # Histogram
        if time_dist:
            df_time = pd.DataFrame(time_dist)
            # Convert to hours for better visualization
            df_time['hours'] = df_time['duration_seconds'] / 3600
            
            st.write("**Distribution of Time-to-Apply**")
            st.bar_chart(df_time.set_index('hours')['duration_seconds'], height=300)
    else:
        st.info("No time-to-apply data available. Time-to-apply is tracked when a job status changes to 'Applied'.")
    
    st.divider()
    
    # Application Funnel
    st.subheader("Application Funnel")
    
    funnel = analytics.get_application_funnel()
    
    if funnel['total'] > 0:
        status_counts = funnel['status_counts']
        status_order = ['New', 'Interested', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn']
        
        # Create funnel data
        funnel_data = []
        for status in status_order:
            if status in status_counts:
                funnel_data.append({
                    'Status': status,
                    'Count': status_counts[status]
                })
        
        if funnel_data:
            df_funnel = pd.DataFrame(funnel_data)
            
            # Display metrics
            funnel_cols = st.columns(len(funnel_data))
            for i, row in df_funnel.iterrows():
                with funnel_cols[i]:
                    st.metric(row['Status'], row['Count'])
            
            # Bar chart
            st.bar_chart(df_funnel.set_index('Status')['Count'], height=300)
            
            # Conversion rates
            if funnel['conversion_rates']:
                st.write("**Conversion Rates**")
                conv_cols = st.columns(len(funnel['conversion_rates']))
                for i, (stage, rate) in enumerate(funnel['conversion_rates'].items()):
                    with conv_cols[i]:
                        st.metric(stage.replace('_', ' ').title(), f"{rate:.1%}")
    else:
        st.info("No job data available.")
    
    st.divider()
    
    # Recent Activity
    st.subheader("Recent Activity")
    
    try:
        from src.analytics.event_tracker import EventTracker
        event_tracker = EventTracker(db)
        recent_events = event_tracker.get_events(limit=20)
        
        if recent_events:
            events_df = pd.DataFrame(recent_events)
            events_df['created_at'] = pd.to_datetime(events_df['created_at'])
            events_df = events_df.sort_values('created_at', ascending=False)
            
            # Display recent events
            for event in recent_events[:10]:
                event_type = event['event_type'].replace('_', ' ').title()
                created_at = event['created_at']
                metadata = event.get('metadata', {})
                
                with st.expander(f"{event_type} - {created_at}", expanded=False):
                    if metadata:
                        st.json(metadata)
        else:
            st.info("No recent events tracked.")
    except Exception as e:
        st.warning(f"Could not load recent events: {e}")

