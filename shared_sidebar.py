# shared_sidebar.py

# Safe import with fallback
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

def render_shared_sidebar():
    """
    Render a shared sidebar component that appears on all pages.
    This maintains the data source selection across page navigation.
    """
    
    if not STREAMLIT_AVAILABLE or st is None:
        # Fallback for non-Streamlit environments
        print("Streamlit not available - using fallback sidebar")
        return
    
    try:
        # ── Data Source Selection ─────────────────────────────────────────────
        st.sidebar.markdown("## 📊 Data Source")
        
        # Simple fallback data status - no external dependencies
        data_status = {
            'kalshi': {'available': True, 'markets_count': 0, 'last_updated': None},
            'polymarket': {'available': True, 'markets_count': 0, 'last_updated': None}
        }
        
        # Create data source selector
        available_sources = []
        if data_status.get('kalshi', {}).get('available', False):
            available_sources.append('Kalshi')
        if data_status.get('polymarket', {}).get('available', False):
            available_sources.append('Polymarket')
        
        # If no sources are available, show basic options
        if not available_sources:
            available_sources = ['Kalshi', 'Polymarket']
            st.sidebar.info("ℹ️ Data sources may not be loaded yet. Select anyway to proceed.")
        
        if available_sources:
            # Use a sleek dropdown instead of multiselect
            # Default to "Both" if available, otherwise first available source
            default_option = "Both" if len(available_sources) > 1 else available_sources[0]
            
            # Create the dropdown options
            dropdown_options = []
            if len(available_sources) > 1:
                dropdown_options.append("Both")
            dropdown_options.extend(available_sources)
            
            selected_source = st.sidebar.selectbox(
                "Select data source:",
                options=dropdown_options,
                index=0,  # Default to first option (Both if available)
                help="Choose which data source to include in your analysis"
            )
            
            # Store selection in session state
            st.session_state.selected_data_source = selected_source
            
            # Show data source status if available
            if data_status and any(data_status.get(source.lower(), {}).get('available', False) for source in available_sources):
                st.sidebar.markdown("### 📈 Data Status")
                for source in available_sources:
                    source_lower = source.lower()
                    status = data_status.get(source_lower, {})
                    
                    if status.get('available', False):
                        count = status.get('markets_count', 0)
                        updated = status.get('last_updated')
                        if updated:
                            try:
                                updated_str = updated.strftime("%Y-%m-%d %H:%M")
                            except:
                                updated_str = "Unknown"
                        else:
                            updated_str = "Unknown"
                        
                        st.sidebar.markdown(f"**{source}**: {count:,} markets")
                        st.sidebar.markdown(f"*Updated: {updated_str}*")
                    else:
                        st.sidebar.markdown(f"**{source}**: Not available")
            else:
                st.sidebar.markdown("### 📈 Data Status")
                st.sidebar.markdown("ℹ️ Data status unavailable")
        else:
            st.sidebar.warning("⚠️ No data sources available")
            st.sidebar.markdown("Please refresh your data using the refresh scripts.")
            st.session_state.selected_data_source = None
            
    except Exception as e:
        # Fallback if anything goes wrong
        try:
            st.sidebar.error(f"⚠️ Sidebar error: {str(e)}")
            st.sidebar.markdown("## 📊 Data Source")
            st.sidebar.markdown("**Kalshi** (default)")
            st.session_state.selected_data_source = 'Kalshi'
        except:
            # Ultimate fallback - just set a default
            try:
                st.session_state.selected_data_source = 'Kalshi'
            except:
                pass

def get_selected_data_sources():
    """
    Get the currently selected data sources based on the sidebar selection.
    
    Returns:
        list: List of data source names to include
    """
    if not STREAMLIT_AVAILABLE or st is None:
        return ['kalshi']  # Default fallback
    
    try:
        selected = st.session_state.get('selected_data_source', 'Both')
        
        if selected == 'Both':
            return ['kalshi', 'polymarket']
        elif selected == 'Kalshi':
            return ['kalshi']
        elif selected == 'Polymarket':
            return ['polymarket']
        else:
            return ['kalshi']  # Default fallback
    except Exception:
        return ['kalshi']  # Default fallback

def get_selected_data_source_display():
    """
    Get a human-readable string for the selected data source.
    
    Returns:
        str: Display string for the selected data source
    """
    if not STREAMLIT_AVAILABLE or st is None:
        return "Kalshi (default)"
    
    try:
        selected = st.session_state.get('selected_data_source', 'Both')
        return selected if selected else "Kalshi (default)"
    except Exception:
        return "Kalshi (default)"
