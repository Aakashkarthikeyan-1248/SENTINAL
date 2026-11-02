"""
Streamlit Web Reviewer Dashboard for SENTINAL.
Enables security operators to inspect video footage, examine candidate incidents,
view visual evidence snapshots, and triage candidates (Acknowledge, Dismiss, Escalate).
"""

import os
import streamlit as st
from PIL import Image

from sentinal.db import get_all_incidents, update_incident_status, is_using_supabase
from sentinal.cv_pipeline import process_video_stream
from sentinal.generate_sample_clip import generate_synthetic_cctv

# Page Config
st.set_page_config(
    page_title="SENTINAL | AI-Assisted CCTV Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-new {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-acknowledged {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-escalated {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-dismissed {
        background-color: #F3F4F6;
        color: #4B5563;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


def get_status_badge(status: str) -> str:
    status_lower = status.lower()
    if status_lower == "new":
        return f'<span class="badge-new">NEW CANDIDATE</span>'
    elif status_lower == "acknowledged":
        return f'<span class="badge-acknowledged">ACKNOWLEDGED</span>'
    elif status_lower == "escalated":
        return f'<span class="badge-escalated">ESCALATED ⚠️</span>'
    elif status_lower == "dismissed":
        return f'<span class="badge-dismissed">DISMISSED</span>'
    return f'<span>{status}</span>'


# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/cctv.png", width=64)
    st.markdown("### **SENTINAL Control**")
    
    backend_status = "Supabase (Cloud PostgreSQL)" if is_using_supabase() else "Local SQLite (sentinal.db)"
    st.caption(f"Active Backend: **{backend_status}**")
    
    st.divider()
    st.markdown("#### **1. Video Source**")
    video_choice = st.radio("Select source:", ["Sample Simulation Clip", "Upload Video File"], index=0)
    
    sample_clip_path = "data/samples/sample_unattended_clip.mp4"
    selected_video_path = None

    if video_choice == "Sample Simulation Clip":
        if not os.path.exists(sample_clip_path):
            with st.spinner("Generating sample CCTV simulation clip..."):
                generate_synthetic_cctv(sample_clip_path)
        selected_video_path = sample_clip_path
        st.success("Loaded synthetic CCTV station test feed.")
    else:
        uploaded_file = st.file_uploader("Upload CCTV Footage (.mp4, .avi)", type=["mp4", "avi", "mov"])
        if uploaded_file is not None:
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            saved_path = os.path.join(upload_dir, uploaded_file.name)
            with open(saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_video_path = saved_path
            st.success(f"Uploaded: {uploaded_file.name}")

    st.markdown("#### **2. Detection Parameters**")
    unattended_thresh = st.slider("Unattended Threshold (seconds)", min_value=2.0, max_value=30.0, value=5.0, step=1.0)
    proximity_thresh = st.slider("Separation Distance (pixels)", min_value=50.0, max_value=400.0, value=180.0, step=10.0)

    if st.button("🚀 Run CCTV Intelligence Analysis", type="primary", use_container_width=True):
        if selected_video_path and os.path.exists(selected_video_path):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(ratio, msg):
                progress_bar.progress(ratio)
                status_text.text(msg)

            with st.spinner("Analyzing frames & tracking objects..."):
                try:
                    new_candidates = process_video_stream(
                        selected_video_path,
                        unattended_sec_thresh=unattended_thresh,
                        proximity_pixel_thresh=proximity_thresh,
                        progress_callback=update_progress
                    )
                    progress_bar.progress(1.0)
                    status_text.text("Analysis complete!")
                    st.success(f"Identified {len(new_candidates)} candidate event(s)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Processing error: {e}")
        else:
            st.warning("Please upload or select a valid video source.")


# Main Dashboard Area
st.markdown('<div class="main-header">SENTINAL: Incident Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-assisted CCTV event triage with human-in-the-loop review.</div>', unsafe_allow_html=True)

tab_triage, tab_player, tab_history = st.tabs(["📋 Incident Review Feed", "🎥 Video Player", "📊 System Audit Log"])

# TAB 1: TRIAGE FEED
with tab_triage:
    all_incidents = get_all_incidents()
    pending_incidents = [inc for inc in all_incidents if inc.get("status") == "NEW"]
    reviewed_incidents = [inc for inc in all_incidents if inc.get("status") != "NEW"]

    col_metric1, col_metric2, col_metric3 = st.columns(3)
    col_metric1.metric("Pending Human Review", len(pending_incidents))
    col_metric2.metric("Acknowledged / Escalated", sum(1 for i in reviewed_incidents if i.get("status") in ["ACKNOWLEDGED", "ESCALATED"]))
    col_metric3.metric("Dismissed / False Positives", sum(1 for i in reviewed_incidents if i.get("status") == "DISMISSED"))

    st.markdown("---")

    if not pending_incidents:
        st.info("No unreviewed candidate incidents pending. Run analysis from the sidebar to inspect CCTV clips.")
    else:
        st.subheader(f"Candidates Awaiting Review ({len(pending_incidents)})")

        for inc in pending_incidents:
            inc_id = inc["id"]
            with st.container(border=True):
                col_img, col_details = st.columns([1, 2])

                with col_img:
                    ev_path = inc.get("evidence_path")
                    if ev_path and os.path.exists(ev_path):
                        img = Image.open(ev_path)
                        st.image(img, caption=f"Snapshot @ {inc.get('timestamp')}", use_container_width=True)
                    else:
                        st.warning("Visual evidence snapshot not found.")

                with col_details:
                    badge_html = get_status_badge(inc.get("status", "NEW"))
                    st.markdown(f"### Incident `{inc_id}` &nbsp; {badge_html}", unsafe_allow_html=True)
                    st.markdown(f"**Event Type:** {inc.get('event_type').replace('_', ' ').title()}")
                    st.markdown(f"**Camera / Source:** `{inc.get('video_source')}` | **Timestamp:** `{inc.get('timestamp')}`")
                    st.markdown(f"**Confidence Score:** `{float(inc.get('confidence', 0.0))*100:.0f}%`")
                    
                    st.info(f"🤖 **Candidate Summary:** {inc.get('summary')}")

                    reviewer_note = st.text_input(
                        "Reviewer Notes / Operator Assessment:",
                        value=inc.get("reviewer_notes", ""),
                        key=f"note_{inc_id}"
                    )

                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("✅ Acknowledge", key=f"ack_{inc_id}", use_container_width=True):
                            update_incident_status(inc_id, "ACKNOWLEDGED", reviewer_note)
                            st.toast(f"Incident {inc_id} marked as ACKNOWLEDGED")
                            st.rerun()

                    with btn_col2:
                        if st.button("⚠️ Escalate to Security", key=f"esc_{inc_id}", type="primary", use_container_width=True):
                            update_incident_status(inc_id, "ESCALATED", reviewer_note)
                            st.toast(f"Incident {inc_id} ESCALATED to Security dispatch")
                            st.rerun()

                    with btn_col3:
                        if st.button("❌ Dismiss (Benign)", key=f"dism_{inc_id}", use_container_width=True):
                            update_incident_status(inc_id, "DISMISSED", reviewer_note)
                            st.toast(f"Incident {inc_id} DISMISSED")
                            st.rerun()


# TAB 2: VIDEO PLAYER
with tab_player:
    st.subheader("CCTV Surveillance Feed Playback")
    if selected_video_path and os.path.exists(selected_video_path):
        st.video(selected_video_path)
        st.caption(f"Currently playing: {selected_video_path}")
    else:
        st.warning("No video selected. Choose a source in the sidebar.")


# TAB 3: AUDIT LOG
with tab_history:
    st.subheader("Complete Incident Audit Log")
    if all_incidents:
        display_data = []
        for item in all_incidents:
            display_data.append({
                "Incident ID": item.get("id"),
                "Timestamp": item.get("timestamp"),
                "Source Video": item.get("video_source"),
                "Type": item.get("event_type"),
                "Status": item.get("status"),
                "Confidence": f"{float(item.get('confidence', 0.0))*100:.0f}%",
                "Reviewer Notes": item.get("reviewer_notes"),
                "Logged At": item.get("created_at")
            })
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No records logged in the database yet.")
