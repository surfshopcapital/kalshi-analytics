# pages/Changelog.py

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
import uuid

# ── Data persistence setup ────────────────────────────────────
CHANGELOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "changelog_items.json")

def load_changelog() -> list:
    """Load changelog items from JSON file"""
    if os.path.exists(CHANGELOG_FILE):
        try:
            with open(CHANGELOG_FILE, 'r') as f:
                data = json.load(f)
                # Convert date strings back to date objects for proper display
                for item in data:
                    if item.get('deadline'):
                        item['deadline'] = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
                return data
        except Exception as e:
            st.error(f"Error loading changelog: {e}")
            return []
    return []

def save_changelog(items: list):
    """Save changelog items to JSON file"""
    try:
        # Convert date objects to strings for JSON serialization
        items_to_save = []
        for item in items:
            item_copy = item.copy()
            if item_copy.get('deadline') and hasattr(item_copy['deadline'], 'strftime'):
                item_copy['deadline'] = item_copy['deadline'].strftime('%Y-%m-%d')
            items_to_save.append(item_copy)
        
        os.makedirs(os.path.dirname(CHANGELOG_FILE), exist_ok=True)
        with open(CHANGELOG_FILE, 'w') as f:
            json.dump(items_to_save, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving changelog: {e}")
        return False

def get_priority_color(priority: int) -> str:
    """Return color for priority level"""
    colors = {
        1: "🔴",  # Critical
        2: "🟠",  # High
        3: "🟡",  # Medium
        4: "🔵",  # Low
        5: "⚪"   # Very Low
    }
    return colors.get(priority, "⚪")

def get_status_color(status: str) -> str:
    """Return color for status"""
    colors = {
        "To Do": "🔴",
        "In Progress": "🟡", 
        "Done": "🟢",
        "Cancelled": "⚫"
    }
    return colors.get(status, "��")

def main():
    # Page title and description (no set_page_config needed for pages)
    st.title("Changelog")
    st.markdown("Track changes and updates to the dashboard")
    
    # ── Compact header with styling ──────────────────────────────────
    st.markdown("""
        <style>
        .compact-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            color: white;
            margin-bottom: 1rem;
        }
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            padding: 0.25rem 0.75rem;
            font-size: 0.85rem;
        }
        .compact-row {
            padding: 0.5rem 0;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            min-height: 60px;
        }
        .item-content {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .small-text { font-size: 0.85rem; }
        .tiny-text { font-size: 0.75rem; color: #6b7280; }
        .center-text {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 60px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="compact-header"><h3 style="margin:0;">📝 Project Changelog</h3></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("") # Spacer
    
    # ── Load existing items ───────────────────────────────────────
    if 'changelog_items' not in st.session_state:
        st.session_state.changelog_items = load_changelog()
    
    # ── Compact Metrics ──────────────────────────────────────────
    items = st.session_state.changelog_items
    total_items = len(items)
    done_items = len([i for i in items if i.get('status') == 'Done'])
    in_progress = len([i for i in items if i.get('status') == 'In Progress'])
    high_priority = len([i for i in items if i.get('priority', 5) <= 2])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"**📊 {total_items}** Total")
    with col2:
        st.markdown(f"**✅ {done_items}** Done")
    with col3:
        st.markdown(f"**🔄 {in_progress}** Progress")
    with col4:
        st.markdown(f"**🔥 {high_priority}** High Pri")
    with col5:
        if total_items > 0:
            st.markdown(f"**{(done_items/total_items*100):.0f}%** Complete")
    
    # ── Add new item section ──────────────────────────────────────
    with st.expander("➕ Add New Item", expanded=False):
        with st.form("add_item_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_title = st.text_input("📝 Task/Feature Description", placeholder="e.g., Add a watchlist feature")
                new_description = st.text_area("💭 Additional Details (optional)", placeholder="More context about this item...")
            
            with col2:
                new_priority = st.selectbox("🎯 Priority", [1, 2, 3, 4, 5], 
                                          format_func=lambda x: f"{x} - {['Critical', 'High', 'Medium', 'Low', 'Very Low'][x-1]}")
                new_status = st.selectbox("📍 Status", ["To Do", "In Progress", "Done", "Cancelled"])
                new_deadline = st.date_input("📅 Deadline", value=None)
            
            submitted = st.form_submit_button("🚀 Add Item")
            
            if submitted and new_title:
                new_item = {
                    'id': str(uuid.uuid4()),
                    'title': new_title,
                    'description': new_description,
                    'priority': new_priority,
                    'status': new_status,
                    'deadline': new_deadline,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                st.session_state.changelog_items.append(new_item)
                save_changelog(st.session_state.changelog_items)
                st.success("✅ Item added successfully!")
                st.rerun()
    
    # ── Display items ─────────────────────────────────────────────
    if not items:
        st.info("🎯 No changelog items yet. Add your first item above!")
        return
    
    # ── Compact Filters ───────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_status = st.selectbox("Status", ["All", "To Do", "Progress", "Done", "Cancelled"], index=1, format_func=lambda x: "In Progress" if x == "Progress" else x)
    with col2:
        filter_priority = st.selectbox("Priority", ["All", "High (1-2)", "Med (3)", "Low (4-5)"])
    with col3:
        sort_by = st.selectbox("Sort", ["Priority", "Deadline", "Created", "Status"])
    with col4:
        st.markdown("") # Spacer
    
    # ── Apply filters ─────────────────────────────────────────────
    filtered_items = items.copy()
    
    if filter_status != "All":
        status_filter = "In Progress" if filter_status == "Progress" else filter_status
        filtered_items = [i for i in filtered_items if i.get('status') == status_filter]
    
    if filter_priority == "High (1-2)":
        filtered_items = [i for i in filtered_items if i.get('priority', 5) <= 2]
    elif filter_priority == "Med (3)":
        filtered_items = [i for i in filtered_items if i.get('priority', 5) == 3]
    elif filter_priority == "Low (4-5)":
        filtered_items = [i for i in filtered_items if i.get('priority', 5) >= 4]
    
    # ── Sort items ────────────────────────────────────────────────
    if sort_by == "Priority":
        filtered_items.sort(key=lambda x: x.get('priority', 5))
    elif sort_by == "Deadline":
        filtered_items.sort(key=lambda x: x.get('deadline') or date(2099, 12, 31))
    elif sort_by == "Created":
        filtered_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Status":
        status_order = {"To Do": 1, "In Progress": 2, "Done": 3, "Cancelled": 4}
        filtered_items.sort(key=lambda x: status_order.get(x.get('status', 'To Do'), 1))
    
    # ── Compact Item Display ─────────────────────────────────────
    st.markdown(f"**📋 Items ({len(filtered_items)})**")
    
    for i, item in enumerate(filtered_items):
        priority_emoji = get_priority_color(item.get('priority', 5))
        status_emoji = get_status_color(item.get('status', 'To Do'))
        
        # Calculate deadline info
        deadline_text = ""
        if item.get('deadline'):
            days_left = (item['deadline'] - date.today()).days
            if days_left < 0:
                deadline_text = f"⚠️ {abs(days_left)}d ago"
            elif days_left == 0:
                deadline_text = "🎯 Today"
            else:
                deadline_text = f"📅 {days_left}d"
        else:
            deadline_text = "📅 None"
        
        # Compact single-row display
        col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])
        
        with col1:
            # Title with priority and status inline
            st.markdown(f'<div class="compact-row"><div class="item-content"><span class="small-text"><strong>{priority_emoji} {item["title"]}</strong></span><br><span class="tiny-text">{item.get("description", "")[:50]}{"..." if len(item.get("description", "")) > 50 else ""}</span></div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="center-text small-text">P{item.get("priority", 5)}</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'<div class="center-text small-text">{status_emoji}</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'<div class="center-text small-text">{deadline_text}</div>', unsafe_allow_html=True)
        
        with col5:
            # Compact action buttons
            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("⚙️", key=f"edit_{item['id']}", help="Edit item"):
                    st.session_state[f"editing_{item['id']}"] = not st.session_state.get(f"editing_{item['id']}", False)
            with action_col2:
                if st.button("✅", key=f"done_{item['id']}", help="Mark as Done"):
                    # Mark item as done
                    for j, existing_item in enumerate(st.session_state.changelog_items):
                        if existing_item['id'] == item['id']:
                            st.session_state.changelog_items[j]['status'] = 'Done'
                            st.session_state.changelog_items[j]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                            break
                    save_changelog(st.session_state.changelog_items)
                    st.rerun()
            with action_col3:
                if st.button("🗑️", key=f"delete_{item['id']}", help="Delete item"):
                    # Delete item
                    st.session_state.changelog_items = [i for i in st.session_state.changelog_items if i['id'] != item['id']]
                    save_changelog(st.session_state.changelog_items)
                    st.rerun()
        
        # Collapsible edit form (only show if edit button clicked)
        if st.session_state.get(f"editing_{item['id']}", False):
            with st.form(f"edit_form_{item['id']}"):
                edit_col1, edit_col2, edit_col3, edit_col4 = st.columns(4)
                
                with edit_col1:
                    edit_status = st.selectbox("Status", ["To Do", "In Progress", "Done", "Cancelled"], 
                                             index=["To Do", "In Progress", "Done", "Cancelled"].index(item.get('status', 'To Do')), key=f"status_{item['id']}")
                
                with edit_col2:
                    edit_priority = st.selectbox("Priority", [1, 2, 3, 4, 5], 
                                               index=item.get('priority', 5) - 1, key=f"priority_{item['id']}")
                
                with edit_col3:
                    edit_deadline = st.date_input("Deadline", value=item.get('deadline'), key=f"deadline_{item['id']}")
                
                with edit_col4:
                    st.markdown("<br>", unsafe_allow_html=True)  # Spacer
                    if st.form_submit_button("💾"):
                        # Update item
                        for j, existing_item in enumerate(st.session_state.changelog_items):
                            if existing_item['id'] == item['id']:
                                st.session_state.changelog_items[j].update({
                                    'status': edit_status,
                                    'priority': edit_priority,
                                    'deadline': edit_deadline,
                                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                                })
                                break
                        save_changelog(st.session_state.changelog_items)
                        st.session_state[f"editing_{item['id']}"] = False
                        st.success("Updated!")
                        st.rerun()
                    
                    if st.form_submit_button("🗑️"):
                        st.session_state.changelog_items = [i for i in st.session_state.changelog_items if i['id'] != item['id']]
                        save_changelog(st.session_state.changelog_items)
                        st.session_state[f"editing_{item['id']}"] = False
                        st.success("Deleted!")
                        st.rerun()

if __name__ == "__main__":
    main()
