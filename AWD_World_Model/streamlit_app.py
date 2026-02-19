import streamlit as st
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farm_state import FarmState
from conversational_handler import ConversationalAWDHandler
from llm_client import init_qwen_client, is_qwen_available
from state_tracker import StateHistoryTracker
from state_persistence import StatePersistenceManager, ProactiveMonitor
from weather_service import WeatherService
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _get_nested_value(data, field_path: str):
    value = data
    for key in field_path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def _format_provenance(p) -> str:
    if p is None:
        return ""

    if isinstance(p, dict):
        source = p.get("source")
        timestamp = p.get("timestamp")
        confidence = p.get("confidence")
    else:
        source = getattr(p, "source", None)
        timestamp = getattr(p, "timestamp", None)
        confidence = getattr(p, "confidence", None)

    parts = []
    if source:
        parts.append(f"source: `{source}`")
    if timestamp:
        parts.append(f"time: `{timestamp}`")
    if confidence is not None:
        try:
            parts.append(f"confidence: `{float(confidence):.2f}`")
        except Exception:
            parts.append(f"confidence: `{confidence}`")
    return " | ".join(parts)

# Page config
st.set_page_config(
    page_title="🌾 AWD Rice Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching RA_Frontend design system
st.markdown("""
<style>
    /* Global Variables based on globals.css */
    :root {
        --primary: #030213;
        --secondary: #f2f2f7;
        --accent: #e9ebef;
        --background: #ffffff;
        --text-primary: #030213;
        --text-secondary: #717182;
        --success: #10b981; /* Green-500 equivalent */
        --warning: #f59e0b; /* Amber-500 equivalent */
        --danger: #d4183d;
        --radius: 10px;
    }

    /* Main Container */
    .stApp {
        background-color: var(--background);
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: var(--text-primary);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    
    section[data-testid="stSidebar"] h1 {
        color: var(--primary);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Input Fields */
    div[data-baseweb="select"] > div, input {
        border-radius: var(--radius) !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: var(--radius) !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: transparent !important;
        padding: 1rem 0;
    }
    
    div[data-testid="stChatMessageContent"] {
        border-radius: 12px !important;
        padding: 1rem !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }

    /* User Message Bubble */
    div[data-testid="chatAvatarIcon-user"] + div[data-testid="stChatMessageContent"] {
        background-color: var(--primary) !important;
        color: white !important;
    }

    /* Assistant Message Bubble */
    div[data-testid="chatAvatarIcon-assistant"] + div[data-testid="stChatMessageContent"] {
        background-color: var(--secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* Metrics Cards */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 1rem;
        border-radius: var(--radius);
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* Status Indicators */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    .status-online { background-color: var(--success); }
    .status-offline { background-color: var(--danger); }

</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "farm_state" not in st.session_state:
    st.session_state.farm_state = FarmState()

if "state_tracker" not in st.session_state:
    st.session_state.state_tracker = StateHistoryTracker()

if "persistence_manager" not in st.session_state:
    st.session_state.persistence_manager = StatePersistenceManager()
    
    # Try to load saved state on first run
    saved_state = st.session_state.persistence_manager.load_state("default_user")
    if saved_state:
        try:
            # Reconstruct FarmState from saved dict (handles nested models properly)
            st.session_state.farm_state = FarmState(**saved_state['state'])
            if saved_state.get('history'):
                st.session_state.state_tracker.import_history(saved_state['history'])
        except Exception as e:
            # If loading fails, keep the fresh FarmState
            print(f"⚠️ Could not load saved state: {e}")
    
    # Add initial state snapshot (after potential load)
    st.session_state.state_tracker.add_snapshot(
        state=st.session_state.farm_state.dict(),
        trigger="session_start" if not saved_state else "session_restored",
        confidence=1.0
    )

if "proactive_monitor" not in st.session_state:
    st.session_state.proactive_monitor = ProactiveMonitor()

if "weather_service" not in st.session_state:
    st.session_state.weather_service = WeatherService()

if "handler" not in st.session_state:
    st.session_state.handler = ConversationalAWDHandler(use_llm=True)
    # Async initialization of LLM client
    asyncio.run(init_qwen_client())

# Auto-fetch weather and location on first load
if "weather_fetched" not in st.session_state:
    st.session_state.weather_fetched = False
    st.session_state.weather_error = None
    
    try:
        import httpx  # Check if httpx is installed
        result = asyncio.run(st.session_state.weather_service.auto_fetch_and_update(st.session_state.farm_state))
        if result.get("success"):
            st.session_state.weather_fetched = True
            st.session_state.weather_info = f"✅ {result.get('location')}: {result.get('temperature')}°C, {result.get('rain_forecast')}mm rain"
            st.session_state.state_tracker.add_snapshot(
                state=st.session_state.farm_state.dict(),
                trigger="weather_auto_fetch",
                confidence=0.9
            )
            st.session_state.persistence_manager.save_state(
                user_id="default_user",
                farm_state=st.session_state.farm_state.dict(),
                state_history=st.session_state.state_tracker.export_history(),
                metadata={"last_update_source": "weather_auto_fetch"}
            )
        else:
            st.session_state.weather_error = "Could not fetch weather data"
    except ImportError:
        st.session_state.weather_error = "httpx not installed. Run: pip install httpx"
    except Exception as e:
        st.session_state.weather_error = f"Weather fetch failed: {str(e)}"
        import traceback
        traceback.print_exc()

# --- Sidebar: Farm Profile ---
with st.sidebar:
    st.title("🚜 Farm Profile")
    
    with st.expander("📍 Location & Field", expanded=True):
        # Show current state values
        current_location = st.session_state.farm_state.farm.location or "Not detected"
        current_texture = st.session_state.farm_state.soil.texture_class
        
        # Compact location input
        location = st.text_input(
            "Location", 
            value=current_location,
            help="Auto-detected from IP. Edit if needed.",
            placeholder="e.g., Can Tho, Vietnam"
        )
        
        # Weather information display
        if st.button("🔄 Refresh Weather", help="Update weather data", width='stretch', key="refresh_weather"):
            with st.spinner("Fetching weather..."):
                result = asyncio.run(st.session_state.weather_service.auto_fetch_and_update(st.session_state.farm_state))
                if result.get("success"):
                    st.session_state.weather_data = result
                    st.session_state.state_tracker.add_snapshot(
                        state=st.session_state.farm_state.dict(),
                        trigger="weather_refresh",
                        confidence=0.9
                    )
                    st.session_state.persistence_manager.save_state(
                        user_id="default_user",
                        farm_state=st.session_state.farm_state.dict(),
                        state_history=st.session_state.state_tracker.export_history(),
                        metadata={"last_update_source": "weather_refresh"}
                    )
                st.rerun()
        
        # Display weather metrics
        if hasattr(st.session_state, 'weather_data') and st.session_state.weather_data.get("success"):
            weather = st.session_state.weather_data
            
            # Temperature and Rain in 2 columns
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌡️ Temperature", f"{weather.get('temperature', '--')}°C")
            with col2:
                rain = st.session_state.farm_state.weather.forecast_rain_next_7d_mm
                st.metric("☔ Rain (7d)", f"{rain if rain is not None else '--'}mm")
            
            # Humidity and Wind in 2 columns
            if weather.get('humidity') or weather.get('wind_speed'):
                col1, col2 = st.columns(2)
                with col1:
                    if weather.get('humidity'):
                        st.metric("💧 Humidity", f"{weather.get('humidity')}%")
                with col2:
                    if weather.get('wind_speed'):
                        st.metric("🌬️ Wind", f"{weather.get('wind_speed')} km/h")
        else:
            # Minimal display if weather not loaded
            rain_forecast = st.session_state.farm_state.weather.forecast_rain_next_7d_mm
            if rain_forecast is not None:
                st.caption(f"☔ **{rain_forecast}mm** rain (7d forecast)")
            else:
                st.caption("☔ Click refresh to load weather")
        
        st.divider()
        
        soil_options = ["Clay (Heavy, holds water)", "Loam (Medium)", "Sandy (Light, drains fast)"]
        soil_index = 1  # default
        if current_texture == "clay":
            soil_index = 0
        elif current_texture == "loam":
            soil_index = 1
        elif current_texture == "sandy":
            soil_index = 2
        
        soil_type = st.selectbox("Soil Type", soil_options, index=soil_index)
    
    with st.expander("🌾 Crop Details", expanded=True):
        # Rice variety
        rice_variety = st.text_input(
            "Rice Variety",
            value=st.session_state.farm_state.crop.variety_name or "",
            placeholder="e.g., IR64, Jasmine, OM6976"
        )
        
        variety_duration = st.selectbox(
            "Variety Duration",
            ["Short (90-100 days)", "Medium (105-120 days)", "Long (>130 days)"],
            index=1
        )
        
        sowing_date_default = (datetime.now() - timedelta(days=30)).date()
        saved_sow_date = st.session_state.farm_state.crop.sow_or_transplant_date
        if saved_sow_date:
            try:
                sowing_date_default = datetime.strptime(saved_sow_date, "%Y-%m-%d").date()
            except Exception:
                pass
        
        sowing_date = st.date_input(
            "Sowing / Transplant Date",
            value=sowing_date_default,
            max_value=datetime.now().date()
        )
        
        # Irrigation method
        irrigation_method = st.selectbox(
            "Water management technique",
            ["awd", "continuous_flooding", "rainfed"],
            index=["awd", "continuous_flooding", "rainfed"].index(st.session_state.farm_state.management.mode),
            format_func=lambda m: {
                "awd": "AWD (Alternate Wetting & Drying)",
                "continuous_flooding": "Continuous Flooding",
                "rainfed": "Rainfed",
            }.get(m, m),
            key="water_management_mode"
        )

        if irrigation_method != st.session_state.farm_state.management.mode:
            st.session_state.farm_state.update_from_dict(
                {
                    "management.mode": irrigation_method,
                    "management.mode_source": "sidebar_input",
                    "management.mode_confidence": 1.0,
                },
                source="sidebar_input",
                confidence=1.0,
            )

            st.session_state.state_tracker.add_snapshot(
                state=st.session_state.farm_state.dict(),
                trigger="sidebar_management_mode_update",
                confidence=1.0,
            )

            st.session_state.persistence_manager.save_state(
                user_id="default_user",
                farm_state=st.session_state.farm_state.dict(),
                state_history=st.session_state.state_tracker.export_history(),
                metadata={"last_update_source": "sidebar_management_mode_update"}
            )
        
        # Auto-calculate stage
        days_after = (datetime.now().date() - sowing_date).days
        
        # Simple stage estimation logic
        estimated_stage = "Unknown"
        if days_after < 15:
            estimated_stage = "seedling"
        elif days_after < 50:
            estimated_stage = "tillering"
        elif days_after < 70:
            estimated_stage = "panicle_initiation"
        elif days_after < 90:
            estimated_stage = "flowering"
        elif days_after < 110:
            estimated_stage = "grain_filling"
        else:
            estimated_stage = "maturity"
        
        # Auto-update farm_state immediately so World Model and LLM always see current stage
        st.session_state.farm_state.crop.sow_or_transplant_date = sowing_date.strftime("%Y-%m-%d")
        st.session_state.farm_state.crop.days_after = days_after
        st.session_state.farm_state.crop.growth_stage = estimated_stage
        
        # Compact crop age display
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"🌱 **{estimated_stage.replace('_', ' ').title()}**")
        with col2:
            st.caption(f"📅 **{days_after} days old**")
    
    # Farm area in separate expander to keep it clean
    with st.expander("📐 Farm Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            farm_area = st.number_input(
                "Area (hectares)",
                min_value=0.0,
                value=float(st.session_state.farm_state.farm.area_ha or 0),
                step=0.1,
                format="%.2f"
            )
        with col2:
            if farm_area > 0:
                st.caption("**Quick convert:**")
                st.caption(f"{farm_area:.2f} ha = {int(farm_area * 10000):,} m²")
        
        # Notes field
        notes = st.text_area(
            "Notes",
            value="",
            placeholder="Additional information about your farm...",
            height=80
        )

    # Save Profile Button at bottom
    st.divider()
    if st.button("💾 Update Profile", type="primary", width='stretch'):
        # Map Sidebar Inputs to FarmState
        updates = {
            "farm.location": location,
            "farm.area_ha": farm_area,
            "soil.texture_class": soil_type.split()[0].lower(),  # "clay", "loam", "sandy"
            "crop.variety_name": rice_variety,
            "crop.sow_or_transplant_date": sowing_date.strftime("%Y-%m-%d"),
            "crop.days_after": days_after,
            "crop.growth_stage": estimated_stage
        }
        
        # Set percolation based on soil texture
        if "Clay" in soil_type:
            updates["soil.percolation_class"] = "low"
        elif "Sandy" in soil_type:
            updates["soil.percolation_class"] = "high"
        else:
            updates["soil.percolation_class"] = "medium"
            
        st.session_state.farm_state.update_from_dict(
            updates,
            source="user_profile_update",
            confidence=1.0
        )
        # Track state change
        st.session_state.state_tracker.add_snapshot(
            state=st.session_state.farm_state.dict(),
            trigger="user_profile_update",
            confidence=1.0
        )
        # Save state to disk
        st.session_state.persistence_manager.save_state(
            user_id="default_user",
            farm_state=st.session_state.farm_state.dict(),
            state_history=st.session_state.state_tracker.export_history()
        )
        st.success("✅ Profile Updated! The assistant now knows your field context.")
        st.rerun()

# --- Main Chat Interface ---
st.title("🌾 AWD Water Advisor")
st.markdown("Ask about irrigation, water levels, or AWD safety. I know your farm context!")

# --- Proactive Alerts & Monitoring ---
try:
    prediction = st.session_state.handler.decision_engine.predict_drying_rate(st.session_state.farm_state)
except Exception as e:
    prediction = {"status": "insufficient_data", "days_remaining": 0}
    
try:
    alerts = st.session_state.proactive_monitor.check_for_alerts(
        farm_state=st.session_state.farm_state.dict(),
        prediction=prediction,
        state_history=st.session_state.state_tracker.get_recent_history(5)
    )
except Exception as e:
    alerts = []

if alerts:
    # Show critical/warning alerts prominently
    critical_alerts = [a for a in alerts if a['urgency'] in ['high', 'critical']]
    if critical_alerts:
        for alert in critical_alerts:
            if alert['urgency'] == 'critical':
                st.error(f"**{alert['message']}**\n\n✅ **Action:** {alert['action']}\n\n💡 {alert['reasoning']}")
            else:
                st.warning(f"**{alert['message']}**\n\n✅ **Action:** {alert['action']}\n\n💡 {alert['reasoning']}")
    
    # Show other alerts in expander
    other_alerts = [a for a in alerts if a['urgency'] not in ['high', 'critical']]
    if other_alerts:
        with st.expander(f"💡 {len(other_alerts)} Suggestion(s) & Advisories", expanded=False):
            for alert in other_alerts:
                if alert['type'] == 'positive':
                    st.success(f"**{alert['message']}**\n\n{alert['reasoning']}")
                else:
                    st.info(f"**{alert['message']}**\n\n✅ **Action:** {alert['action']}\n\n💡 {alert['reasoning']}")

# --- World Model Dashboard ---
with st.expander("🧠 World Model State & Predictions", expanded=False):
    st.markdown("### Farm State Evolution & Temporal Reasoning")
    
    # Get state tracking summary
    summary = st.session_state.state_tracker.get_state_summary()
    timeline_data = st.session_state.state_tracker.get_timeline_data()
    
    if summary['tracking_active'] and len(timeline_data) > 1:
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["📊 State Timeline", "🎯 Predictions", "📈 Trajectories", "🧾 Provenance"])
        
        with tab1:
            st.markdown("**How the World Model tracks your farm state over time:**")
            
            # Convert timeline to dataframe for plotting
            df = pd.DataFrame(timeline_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Determine which water field to plot (prefer standing water if available)
            if 'standing_water' in df.columns and df['standing_water'].notna().any():
                # Plot standing water
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['standing_water'],
                    mode='lines+markers',
                    name='Standing Water',
                    line=dict(color='#10b981', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Standing: %{y} cm<extra></extra>'
                ))
                
                # Add target zone
                fig.add_hline(y=5, line_dash="dash", line_color="green", 
                             annotation_text="Target: 5cm")
                fig.add_hline(y=3, line_dash="dash", line_color="orange",
                             annotation_text="Min: 3cm")
                
                fig.update_layout(
                    title="Standing Water Level Evolution",
                    xaxis_title="Time",
                    yaxis_title="Standing Water (cm)",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, width='stretch')
                
            elif 'water_depth' in df.columns and df['water_depth'].notna().any():
                # Plot water table depth
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['water_depth'],
                    mode='lines+markers',
                    name='Water Table Depth',
                    line=dict(color='#3b82f6', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Depth: %{y} cm<extra></extra>'
                ))
                
                # Add safe/unsafe zones
                fig.add_hline(y=15, line_dash="dash", line_color="orange", 
                             annotation_text="Safe Limit (15cm)")
                fig.add_hline(y=10, line_dash="dash", line_color="red",
                             annotation_text="Critical (Flowering)")
                
                fig.update_layout(
                    title="Water Table Depth Evolution",
                    xaxis_title="Time",
                    yaxis_title="Depth Below Surface (cm)",
                    height=400,
                    hovermode='x unified',
                    yaxis=dict(autorange="reversed")  # Deeper = higher number
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("📊 Water level history will appear here once you start tracking measurements.")
            
            # Show state changes table
            st.markdown("**Recent State Updates:**")
            recent = st.session_state.state_tracker.get_recent_history(5)
            if recent:
                changes_data = []
                for snap in recent:
                    changes_data.append({
                        "Time": datetime.fromisoformat(snap.timestamp).strftime("%H:%M:%S"),
                        "Trigger": snap.trigger.replace('_', ' ').title(),
                        "Confidence": f"{snap.confidence*100:.0f}%"
                    })
                st.dataframe(changes_data, width='stretch')
        
        with tab2:
            st.markdown("**Predictive modeling based on current state:**")
            
            # Get prediction from decision engine
            prediction = st.session_state.handler.decision_engine.predict_drying_rate(
                st.session_state.farm_state
            )
            
            if prediction.get("status") == "predicting":
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(
                        "🔮 Predicted Days to 15cm Depth", 
                        f"{prediction['days_remaining']} days",
                        help="Based on soil type, percolation rate, and weather"
                    )
                with col_b:
                    st.metric(
                        "📉 Drying Rate",
                        f"{prediction.get('drying_rate_cm_per_day', 'N/A')} cm/day"
                    )
                
                # Visualize prediction timeline
                water_below = st.session_state.farm_state.water.water_table_cm_below_surface
                water_standing = st.session_state.farm_state.water.standing_water_cm
                if water_standing is not None and water_standing > 0:
                    current_depth = -water_standing
                elif water_below is not None:
                    current_depth = water_below
                else:
                    current_depth = 5
                days_remaining = prediction.get('days_remaining', 5)
                days = int(round(days_remaining))  # Convert to int for range(), handle float
                
                future_dates = [datetime.now() + timedelta(days=i) for i in range(max(1, days + 1))]
                predicted_depths = [current_depth + i * prediction.get('drying_rate_cm_per_day', 1.5) 
                                   for i in range(max(1, days + 1))]
                
                fig_pred = go.Figure()
                fig_pred.add_trace(go.Scatter(
                    x=future_dates,
                    y=predicted_depths,
                    mode='lines+markers',
                    name='Predicted Depth',
                    line=dict(color='#8b5cf6', width=3, dash='dash'),
                    fill='tonexty'
                ))
                
                fig_pred.add_hline(y=15, line_dash="dot", line_color="orange",
                                  annotation_text="Irrigation Needed")
                
                fig_pred.update_layout(
                    title="Predicted Water Table Trajectory",
                    xaxis_title="Date",
                    yaxis_title="Predicted Depth (cm)",
                    height=350,
                    yaxis=dict(autorange="reversed")
                )
                st.plotly_chart(fig_pred, width='stretch')
                
                st.info(f"💡 **Model Reasoning:** {prediction.get('reasoning', 'Calculating based on soil and weather conditions.')}")
            else:
                st.warning("⚠️ Need more information (water level, soil type) to generate predictions.")
        
        with tab3:
            st.markdown("**Field parameter trajectories over time:**")
            
            # Water level trajectory (check both fields)
            water_traj = st.session_state.state_tracker.get_state_trajectory("water.water_table_cm_below_surface")
            standing_traj = st.session_state.state_tracker.get_state_trajectory("water.standing_water_cm")
            
            # Show whichever field has data
            if standing_traj['trajectory'] and standing_traj['change_count'] > 0:
                st.markdown(f"**Standing Water Trend:** `{standing_traj['trend'].upper()}`")
                st.caption(f"Current: {standing_traj['current_value']} cm standing | Updates: {standing_traj['change_count']}")
                
                # Plot standing water trajectory
                if len(standing_traj['trajectory']) > 1:
                    traj_df = pd.DataFrame([
                        {"Time": datetime.fromisoformat(item['timestamp']), "Standing Water (cm)": item['value']}
                        for item in standing_traj['trajectory']
                    ])
                    fig_standing = px.line(traj_df, x="Time", y="Standing Water (cm)", 
                                          title="Standing Water Level Over Time",
                                          markers=True)
                    fig_standing.add_hline(y=5, line_dash="dot", line_color="green",
                                          annotation_text="Target: 5cm")
                    st.plotly_chart(fig_standing, use_container_width=True)
            
            elif water_traj['trajectory'] and water_traj['change_count'] > 0:
                st.markdown(f"**Water Table Depth Trend:** `{water_traj['trend'].upper()}`")
                st.caption(f"Current: {water_traj['current_value']} cm below surface | Updates: {water_traj['change_count']}")
                
                # Plot water table trajectory
                if len(water_traj['trajectory']) > 1:
                    traj_df = pd.DataFrame([
                        {"Time": datetime.fromisoformat(item['timestamp']), "Depth (cm)": item['value']}
                        for item in water_traj['trajectory']
                    ])
                    fig_water = px.line(traj_df, x="Time", y="Depth (cm)", 
                                       title="Water Table Depth Evolution",
                                       markers=True)
                    fig_water.add_hline(y=15, line_dash="dot", line_color="orange",
                                       annotation_text="Critical: 15cm")
                    fig_water.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig_water, use_container_width=True)
            else:
                st.info("💡 No water level updates tracked yet. Chat updates will appear here.")
            
            # Growth stage changes
            stage_changes = st.session_state.state_tracker.get_state_changes("crop.growth_stage", n=10)
            if stage_changes:
                st.markdown("**Growth Stage Transitions:**")
                for change in stage_changes[-3:]:
                    st.text(f"• {change['value']} ({datetime.fromisoformat(change['timestamp']).strftime('%b %d')})")

        with tab4:
            st.markdown("**Latest provenance for each world-model field:**")
            prov_map = getattr(st.session_state.farm_state, "field_provenance", {}) or {}
            if prov_map:
                state_dict = st.session_state.farm_state.dict()
                rows = []
                for field_path, p in prov_map.items():
                    if isinstance(p, dict):
                        source = p.get("source")
                        timestamp = p.get("timestamp")
                        confidence = p.get("confidence")
                    else:
                        source = getattr(p, "source", None)
                        timestamp = getattr(p, "timestamp", None)
                        confidence = getattr(p, "confidence", None)

                    rows.append({
                        "Field": field_path,
                        "Value": _get_nested_value(state_dict, field_path),
                        "Source": source,
                        "Timestamp": timestamp,
                        "Confidence": confidence
                    })

                df_prov = pd.DataFrame(rows)
                if not df_prov.empty and "Timestamp" in df_prov.columns:
                    try:
                        df_prov["Timestamp"] = pd.to_datetime(df_prov["Timestamp"])
                        df_prov = df_prov.sort_values("Timestamp", ascending=False)
                    except Exception:
                        pass

                if "Value" in df_prov.columns:
                    df_prov["Value"] = df_prov["Value"].map(lambda v: "" if v is None else str(v))
                st.dataframe(df_prov, width='stretch', hide_index=True)
            else:
                st.info("No provenance recorded yet. Update fields via chat, profile, or weather fetch.")
    else:
        st.info("🌱 Start chatting and updating your farm status to see the World Model in action! "
               "The system will track state evolution, make predictions, and show temporal reasoning.")

        st.markdown("**Latest provenance for each world-model field:**")
        prov_map = getattr(st.session_state.farm_state, "field_provenance", {}) or {}
        if prov_map:
            state_dict = st.session_state.farm_state.dict()
            rows = []
            for field_path, p in prov_map.items():
                if isinstance(p, dict):
                    source = p.get("source")
                    timestamp = p.get("timestamp")
                    confidence = p.get("confidence")
                else:
                    source = getattr(p, "source", None)
                    timestamp = getattr(p, "timestamp", None)
                    confidence = getattr(p, "confidence", None)

                rows.append({
                    "Field": field_path,
                    "Value": _get_nested_value(state_dict, field_path),
                    "Source": source,
                    "Timestamp": timestamp,
                    "Confidence": confidence
                })

            df_prov = pd.DataFrame(rows)
            if not df_prov.empty and "Timestamp" in df_prov.columns:
                try:
                    df_prov["Timestamp"] = pd.to_datetime(df_prov["Timestamp"])
                    df_prov = df_prov.sort_values("Timestamp", ascending=False)
                except Exception:
                    pass

            if "Value" in df_prov.columns:
                df_prov["Value"] = df_prov["Value"].map(lambda v: "" if v is None else str(v))
            st.dataframe(df_prov, width='stretch', hide_index=True)
        else:
            st.info("No provenance recorded yet. Update fields via chat, profile, or weather fetch.")

# Display current critical context
col1, col2, col3, col4 = st.columns(4)
with col1:
    stage = st.session_state.farm_state.crop.growth_stage or "Unknown"
    st.metric("Crop Stage", stage.replace('_', ' ').title())
with col2:
    water_below = st.session_state.farm_state.water.water_table_cm_below_surface
    water_standing = st.session_state.farm_state.water.standing_water_cm
    
    if water_below is not None:
        level_text = f"{water_below} cm below"
    elif water_standing is not None:
        level_text = f"{water_standing} cm standing"
    else:
        level_text = "Unknown"
    
    st.metric("Water Level", level_text)
with col3:
    # Calculate prediction for UI
    prediction = st.session_state.handler.decision_engine.predict_drying_rate(st.session_state.farm_state)
    if prediction.get("status") == "predicting":
        days = prediction['days_remaining']
        st.metric("Next Irrigation", f"In {days} days")
    elif prediction.get("status") == "ready":
        st.metric("Next Irrigation", "NOW!", delta="-Urgent", delta_color="inverse")
    else:
        st.metric("Next Irrigation", "--")
with col4:
    llm_status = "Online 🟢" if is_qwen_available() else "Offline 🔴"
    st.metric("AI Status", llm_status)

# Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display citations if available
        if message.get("citations"):
            with st.expander("📚 Sources & References"):
                for cite in message["citations"]:
                    st.markdown(f"**[{cite['id']}] {cite['title']}**")
                    st.caption(f"{cite['content'][:200]}...")
                    st.divider()

# Input
if prompt := st.chat_input("Ask me something (e.g., 'Should I irrigate today?')..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing field data..."):
            # Run async process in sync wrapper
            response_data = asyncio.run(
                st.session_state.handler.process_question_async(
                    question=prompt,
                    farm_state=st.session_state.farm_state,
                    context={"conversation_history": st.session_state.messages[-5:]}
                )
            )
            
            # Track state changes if any slots were extracted
            state_updates = response_data.get("state_updates", {})
            if state_updates:
                st.session_state.state_tracker.add_snapshot(
                    state=st.session_state.farm_state.dict(),
                    trigger=f"conversation_extraction: {response_data.get('intent', 'unknown')}",
                    confidence=0.9 if response_data.get("llm_enhanced") else 0.7
                )
                
                # Show what was extracted (World Model transparency)
                with st.expander("🔍 Information Extracted from Your Message", expanded=False):
                    st.markdown("**The World Model updated these fields:**")
                    for key, value in state_updates.items():
                        field_name = key.replace('.', ' → ').replace('_', ' ').title()
                        st.markdown(f"- **{field_name}:** `{value}`")
                        prov_text = _format_provenance(
                            getattr(st.session_state.farm_state, "field_provenance", {}).get(key)
                        )
                        if prov_text:
                            st.caption(prov_text)
                    st.caption("💡 This demonstrates how the system builds and maintains a world model of your farm.")
            
            response_text = response_data["response"]
            citations = response_data.get("citations", [])
            
            # Add confidence indicator
            confidence = response_data.get("confidence", "medium")
            if confidence == "high":
                confidence_badge = "🟢 High Confidence"
            elif confidence == "medium":
                confidence_badge = "🟡 Medium Confidence"
            else:
                confidence_badge = "🟠 Low Confidence - Need More Info"
            
            st.caption(f"**Model Confidence:** {confidence_badge}")
            
            # If there are follow-up questions, append them
            if response_data.get("needs_more_info") and response_data.get("questions"):
                questions_text = "\n\n" + "\n\n".join(response_data["questions"])
                response_text += questions_text
            
            # If Qwen is used, it might return markdown, so we render it
            st.markdown(response_text)
            
            # Display citations
            if citations:
                with st.expander("📚 Sources & References"):
                    for cite in citations:
                        st.markdown(f"**[{cite['id']}] {cite['title']}**")
                        st.caption(f"{cite['content'][:200]}...")
                        st.divider()
            
            # Show "Needs Info" hint if applicable
            if response_data.get("needs_more_info"):
                st.caption("ℹ️ *Please provide the missing details above so I can give precise advice.*")
            
            # Store assistant message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "citations": citations
            })
            
            # Persist state after conversation (World Model continuity)
            st.session_state.persistence_manager.save_state(
                user_id="default_user",
                farm_state=st.session_state.farm_state.dict(),
                state_history=st.session_state.state_tracker.export_history(),
                metadata={
                    "last_intent": response_data.get("intent"),
                    "conversation_count": len(st.session_state.messages)
                }
            )
            
            # Sidebar/cards will refresh on next interaction - no need to force rerun and lose chat display

# --- Debug / State Inspector (Optional) ---
with st.expander("🔍 View Internal Farm State (Debug)"):
    st.json(st.session_state.farm_state.dict())
