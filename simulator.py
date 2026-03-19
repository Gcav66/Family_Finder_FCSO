"""
Family Finder · SMS Demo Simulator
-----------------------------------
A realistic phone-UI demo you can show community leaders.
No Twilio account needed — runs locally against the Claude API.

  pip install streamlit anthropic
  export ANTHROPIC_API_KEY=sk-ant-...
  streamlit run simulator.py
"""

import streamlit as st
import streamlit.components.v1 as components
import anthropic
import time
import json

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Family Finder · SMS Demo",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  /* ── Phone shell ── */
  .phone-wrap {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 1rem 0 2rem 0;
  }
  .phone {
    width: 375px;
    background: #1c1c1e;
    border-radius: 52px;
    padding: 16px 12px 20px 12px;
    box-shadow:
      0 0 0 2px #3a3a3c,
      0 40px 80px rgba(0,0,0,0.6),
      inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative;
  }
  .phone-notch {
    width: 120px;
    height: 26px;
    background: #1c1c1e;
    border-radius: 0 0 18px 18px;
    margin: 0 auto 6px auto;
  }
  .phone-screen {
    background: #000;
    border-radius: 42px;
    overflow: hidden;
    min-height: 680px;
    display: flex;
    flex-direction: column;
  }

  /* ── Status bar ── */
  .status-bar {
    background: #1c1c1e;
    padding: 12px 24px 6px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
    color: white;
    font-family: 'DM Sans', sans-serif;
  }

  /* ── Chat header ── */
  .chat-header {
    background: rgba(28,28,30,0.95);
    backdrop-filter: blur(20px);
    padding: 8px 16px 12px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .chat-header .contact-name {
    color: white;
    font-weight: 600;
    font-size: 17px;
  }
  .chat-header .contact-sub {
    color: #8e8e93;
    font-size: 12px;
    margin-top: 1px;
  }

  /* ── Message bubbles ── */
  .messages-area {
    flex: 1;
    background: #000;
    padding: 12px 12px 8px 12px;
    overflow-y: auto;
    min-height: 480px;
    max-height: 480px;
  }
  .msg-row {
    display: flex;
    margin-bottom: 6px;
    align-items: flex-end;
  }
  .msg-row.user { justify-content: flex-end; }
  .msg-row.bot  { justify-content: flex-start; }

  .bubble {
    max-width: 78%;
    padding: 9px 14px;
    border-radius: 18px;
    font-size: 15px;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .bubble.user {
    background: #0b84ff;
    color: white;
    border-bottom-right-radius: 4px;
  }
  .bubble.bot {
    background: #1c1c1e;
    color: #f2f2f7;
    border-bottom-left-radius: 4px;
  }
  .bubble.typing {
    background: #1c1c1e;
    color: #8e8e93;
    font-style: italic;
    font-size: 13px;
  }
  .msg-time {
    font-size: 10px;
    color: #636366;
    margin: 1px 6px 6px 6px;
  }
  .msg-time.user { text-align: right; }

  /* ── Date divider ── */
  .date-divider {
    text-align: center;
    color: #636366;
    font-size: 11px;
    font-weight: 500;
    margin: 10px 0 8px 0;
    font-family: 'DM Sans', sans-serif;
  }

  /* ── Input bar ── */
  .input-bar {
    background: #1c1c1e;
    padding: 8px 12px;
    border-top: 1px solid rgba(255,255,255,0.08);
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* ── Sidebar styles ── */
  .scenario-header {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }
  .demo-note {
    background: #f0f9ff;
    border-left: 4px solid #0ea5e9;
    border-radius: 4px;
    padding: 0.75rem 0.9rem;
    font-size: 0.85rem;
    color: #0c4a6e;
    margin-bottom: 1rem;
  }
  .stat-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .stat-box {
    flex: 1;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.6rem;
    text-align: center;
  }
  .stat-box .num { font-size: 1.4rem; font-weight: 700; color: #1e3a5f; }
  .stat-box .lbl { font-size: 0.7rem; color: #6b7280; }

</style>
""", unsafe_allow_html=True)

# ── Bot brain ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Family Finder, a free bilingual SMS assistant helping families in 
Forsyth County, NC navigate the county jail system. You text like a real person — 
concise, warm, and plain. This is SMS: keep replies SHORT. 2–4 sentences max per message. 
Use simple line breaks, not markdown. No bullet symbols with *.

You help with four things:
1. Finding someone in the jail (direct them to forsythsheriffnc.policetocitizen.com/Inmates/Catalog)
2. Explaining charge codes in plain language (NC law only, no legal advice)
3. Explaining how bond/bail works in Forsyth County NC
4. Visitation hours, phone calls, mail, sending money

LANGUAGE: Detect the language of the incoming message and respond in that language automatically.
If Spanish → respond fully in Spanish. If English → respond in English.

FIRST MESSAGE behavior: If this is the first message in the conversation, respond with a warm 
greeting and a numbered menu:
  1 - Find someone in jail
  2 - Understand the charges
  3 - How bond works
  4 - Visits & contact info
  5 - Free legal help

Then wait for their reply.

MENU RESPONSES: If they reply with a number 1-5, start helping with that topic immediately.

CHARGES: When explaining charges, give: (1) plain English name, (2) how serious it is in 1 sentence, 
(3) what the state has to prove in 1 sentence. End with "Want me to explain more, or do you have 
another question?"

BOND: Be practical. Mention that most families use a bondsman (pay ~15% fee, not returned). 
Mention Public Defender can request bond reduction. Always give Legal Aid number if they seem 
stuck financially: 336-725-9166.

ESCALATION: If they ask for legal advice, strategy, or what plea to take — warmly decline and 
give Legal Aid: 336-725-9166 or Public Defender: 336-779-6380.

CRISIS: If someone seems distressed or in crisis, be human first. Acknowledge them before 
giving information.

NEVER: give legal advice, predict outcomes, recommend pleas, or pretend to be affiliated 
with the Sheriff's Office or courts.

SIGN-OFF: Never end with "Is there anything else I can help you with?" — too formal. 
End naturally like a helpful neighbor would."""


def get_bot_response(history: list[dict]) -> str:
    client = anthropic.Anthropic()
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    return r.content[0].text.strip()


# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {role, content, time}
if "api_history" not in st.session_state:
    st.session_state.api_history = []  # list of {role, content} for Claude
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "lang_detected" not in st.session_state:
    st.session_state.lang_detected = "—"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📱 Family Finder Demo")
    st.markdown("""
    <div class="demo-note">
    This simulates the SMS experience exactly as a family member would see it. 
    No Twilio account needed — powered directly by Claude.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="scenario-header">Try a scenario</div>', unsafe_allow_html=True)

    scenarios = {
        "😟 First text (English)": "my brother got arrested last night i dont know what to do",
        "😟 First text (Spanish)": "mi hijo fue arrestado anoche no sé qué hacer",
        "⚖️ Charge lookup": "it says PWIMSD SCH II CS what does that mean",
        "⚖️ Cargo en español": "dice ASSAULT ON FEMALE que significa eso",
        "💰 Can't afford bond": "the bond is $10,000 we can't pay that what do we do",
        "💰 No podemos pagar": "la fianza es $5000 no tenemos ese dinero",
        "📞 Visit question": "what time can i visit on saturday",
        "📞 Visita en español": "a qué hora puedo visitar el sábado",
        "📬 Send money": "how do i put money on his account",
        "🆘 Escalation test": "should he take the plea deal they're offering",
    }

    chosen = st.selectbox("Pick a demo message", ["— type your own —"] + list(scenarios.keys()))

    preset_text = scenarios.get(chosen, "")

    st.divider()

    st.markdown('<div class="scenario-header">Session stats</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
          <div class="num">{st.session_state.msg_count}</div>
          <div class="lbl">Messages</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box">
          <div class="num">{len(st.session_state.messages) // 2 if st.session_state.messages else 0}</div>
          <div class="lbl">Exchanges</div>
        </div>""", unsafe_allow_html=True)

    lang_icon = "🇪🇸" if st.session_state.lang_detected == "Spanish" else ("🇺🇸" if st.session_state.lang_detected == "English" else "—")
    st.markdown(f"**Language detected:** {lang_icon} {st.session_state.lang_detected}")

    st.divider()

    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_history = []
        st.session_state.msg_count = 0
        st.session_state.lang_detected = "—"
        st.rerun()

    st.divider()
    st.markdown("**Production deployment:**")
    st.caption("When ready, wire `twilio_webhook.py` to a Twilio number. Same bot logic, real SMS.")
    st.markdown("[Twilio docs →](https://www.twilio.com/docs/sms/quickstart/python)")

# ── Main area ──────────────────────────────────────────────────────────────────
col_phone, col_info = st.columns([1, 1], gap="large")

with col_phone:
    st.markdown("### The experience as a family member sees it")
    st.caption("Type in the box below — or pick a scenario from the sidebar")

    # ── Build message HTML ─────────────────────────────────────────────────────
    msgs_html = '<div class="messages-area">'
    if not st.session_state.messages:
        msgs_html += '<div class="date-divider">Today</div>'
        msgs_html += '''<div style="text-align:center; color:#636366; font-size:13px; padding:40px 20px;">
            Start by texting anything — like you'd text a friend for help.
            </div>'''
    else:
        msgs_html += '<div class="date-divider">Today</div>'
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            t_str = msg.get("time", "")
            msgs_html += f'''
            <div class="msg-row {role}">
              <div class="bubble {role}">{content}</div>
            </div>
            <div class="msg-time {role}">{t_str}</div>
            '''
    msgs_html += '</div>'

    # ── Phone shell — rendered via components.html so Streamlit never sanitizes it ──
    phone_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{
        font-family: 'DM Sans', sans-serif;
        background: transparent;
        display: flex;
        justify-content: center;
        padding: 8px 0 16px 0;
      }}
      .phone {{
        width: 355px;
        background: #1c1c1e;
        border-radius: 50px;
        padding: 14px 10px 18px 10px;
        box-shadow:
          0 0 0 2px #3a3a3c,
          0 30px 60px rgba(0,0,0,0.55),
          inset 0 1px 0 rgba(255,255,255,0.08);
      }}
      .phone-notch {{
        width: 110px; height: 24px;
        background: #1c1c1e;
        border-radius: 0 0 16px 16px;
        margin: 0 auto 4px auto;
      }}
      .phone-screen {{
        background: #000;
        border-radius: 40px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 620px;
      }}
      .status-bar {{
        background: #1c1c1e;
        padding: 10px 22px 5px 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        font-weight: 600;
        color: white;
        flex-shrink: 0;
      }}
      .chat-header {{
        background: rgba(28,28,30,0.97);
        padding: 7px 14px 11px;
        text-align: center;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        flex-shrink: 0;
      }}
      .contact-name {{ color: white; font-weight: 600; font-size: 16px; }}
      .contact-sub  {{ color: #8e8e93; font-size: 11px; margin-top: 1px; }}
      .messages-area {{
        flex: 1;
        background: #000;
        padding: 10px 10px 6px 10px;
        overflow-y: auto;
      }}
      .msg-row {{ display: flex; margin-bottom: 4px; align-items: flex-end; }}
      .msg-row.user {{ justify-content: flex-end; }}
      .msg-row.bot  {{ justify-content: flex-start; }}
      .bubble {{
        max-width: 80%;
        padding: 8px 13px;
        border-radius: 18px;
        font-size: 14.5px;
        line-height: 1.45;
        word-break: break-word;
      }}
      .bubble.user {{
        background: #0b84ff;
        color: white;
        border-bottom-right-radius: 4px;
      }}
      .bubble.bot {{
        background: #1c1c1e;
        color: #f2f2f7;
        border-bottom-left-radius: 4px;
      }}
      .msg-time {{
        font-size: 10px;
        color: #636366;
        margin: 1px 6px 5px 6px;
      }}
      .msg-time.user {{ text-align: right; }}
      .date-divider {{
        text-align: center;
        color: #636366;
        font-size: 11px;
        font-weight: 500;
        margin: 8px 0 6px 0;
      }}
      .empty-state {{
        text-align: center;
        color: #636366;
        font-size: 13px;
        padding: 50px 20px;
        line-height: 1.6;
      }}
    </style>
    </head>
    <body>
    <div class="phone">
      <div class="phone-notch"></div>
      <div class="phone-screen">
        <div class="status-bar">
          <span>9:41</span>
          <span>●●●●○ 5G</span>
          <span>🔋 87%</span>
        </div>
        <div class="chat-header">
          <div class="contact-name">Family Finder · (336) 555-0190</div>
          <div class="contact-sub">Forsyth County Jail Navigation · Free</div>
        </div>
        {msgs_html}
      </div>
    </div>
    <script>
      const area = document.querySelector('.messages-area');
      if (area) area.scrollTop = area.scrollHeight;
    </script>
    </body>
    </html>
    """
    components.html(phone_html, height=720, scrolling=False)

    # ── Text input ─────────────────────────────────────────────────────────────
    default_val = preset_text if chosen != "— type your own —" else ""

    with st.form("sms_form", clear_on_submit=True):
        user_input = st.text_input(
            "Your message",
            value=default_val,
            placeholder="Type a message…",
            label_visibility="collapsed",
        )
        sent = st.form_submit_button("Send ➤", use_container_width=True, type="primary")

    if sent and user_input.strip():
        user_text = user_input.strip()
        now = time.strftime("%-I:%M %p")

        # Detect language hint
        spanish_indicators = ["qué", "que", "cómo", "como", "hijo", "mi ", "fue", "no sé",
                               "no se", "fianza", "arrestado", "dice", "significa", "podemos",
                               "visitar", "sábado", "sabado", "dinero", "cuenta"]
        if any(w in user_text.lower() for w in spanish_indicators):
            st.session_state.lang_detected = "Spanish"
        elif st.session_state.lang_detected == "—":
            st.session_state.lang_detected = "English"

        # Add user message
        st.session_state.messages.append({
            "role": "user", "content": user_text, "time": now
        })
        st.session_state.api_history.append({
            "role": "user", "content": user_text
        })
        st.session_state.msg_count += 1

        # Get bot response
        with st.spinner(""):
            bot_text = get_bot_response(st.session_state.api_history)

        bot_time = time.strftime("%-I:%M %p")
        st.session_state.messages.append({
            "role": "bot", "content": bot_text, "time": bot_time
        })
        st.session_state.api_history.append({
            "role": "assistant", "content": bot_text
        })

        st.rerun()


# ── Info panel ─────────────────────────────────────────────────────────────────
with col_info:
    st.markdown("### How this becomes real SMS")

    st.markdown("""
The demo runs the exact same bot logic that would power a real Twilio SMS line.
The only difference in production is *where the message comes from* — a phone
instead of this text box.
    """)

    st.markdown("#### The production pipeline")
    st.code("""
Family texts (336) 555-0190
        │
        ▼
Twilio receives SMS
        │  (HTTP POST)
        ▼
Your server: twilio_webhook.py
  - Looks up conversation history
    by phone number
  - Calls Claude API with history
    + system prompt
  - Returns plain-text response
        │
        ▼
Twilio sends reply SMS
        │
        ▼
Family receives text
    """, language="text")

    st.markdown("#### What it costs to run")

    cost_data = {
        "Component": ["Twilio phone number", "SMS (per msg)", "Claude API (per conv)", "Hosting"],
        "Cost": ["$1 / month", "~$0.008", "~$0.02–0.05", "$5–7 / month"],
        "Notes": ["Local 336 number", "Inbound + outbound", "Sonnet for explanations", "Render or Railway"],
    }
    st.table(cost_data)

    st.markdown("""
**~$30–50/month** handles 500+ family conversations.
A single United Way micro-grant covers a full year.
    """)

    st.divider()

    st.markdown("#### What's already handled automatically")
    checks = [
        "✅ Language detection — Spanish reply if Spanish message",
        "✅ Conversation memory — context persists across the exchange",
        "✅ Menu routing — numbered options for first-time users",
        "✅ Escalation guardrails — legal advice → Legal Aid number",
        "✅ Crisis sensitivity — warmth before information",
        "✅ STOP/UNSUBSCRIBE — handled by Twilio automatically",
    ]
    for c in checks:
        st.markdown(c)

    st.divider()

    st.markdown("#### To go live (3 steps)")
    st.markdown("""
1. **Create a free Twilio account** at twilio.com — get a 336 area code number (~$1/mo)
2. **Deploy `twilio_webhook.py`** to Render or Railway (free tier works for a pilot)
3. **Point the Twilio webhook URL** at your server — done
    """)

    st.info("The `twilio_webhook.py` file included with this demo is production-ready. "
            "Set `ANTHROPIC_API_KEY` and `TWILIO_AUTH_TOKEN` as environment variables and deploy.")
