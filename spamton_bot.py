from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import os, random, re

# ------------------- TUNING KNOBS -------------------
GLITCH_PROB = 0.12        # % of words to glitch in the final reply (light seasoning)
CAPS_INTENSITY = 0.55     # random caps strength
BURST_PROB = 0.15         # chance a glitch becomes a 2-item burst
# ----------------------------------------------------

# ==== Spamton-style word banks for post-processing ====
ADJECTIVES = ["BIG","LIMITED","FREE","HOT","VALUE","GUARANTEED","MEGA","ULTIMATE","SECRET","TRUSTED"]
NOUNS      = ["DEAL","CUSTOMER","OFFER","SALE","MONEY","BONUS","DISCOUNT","JACKPOT","SAVINGS","COUPON","ACCESS"]
TECH       = ["HYPERLINK BLOCKED","404 ERROR","SYSTEM32","ACCESS DENIED","FILE NOT FOUND","BLUE SCREEN","LOGIN FAILED"]
MEMES      = ["CONGRATULATIONS WINNER!","WE ARE SO BACK","COOKED","BASED","YOU CALLED??","MONEY MONEY MONEY","NO REFUNDS","LOW PRICE","ACT FAST"]

SUFFIXES   = [
    "!!!",
    "??!?!!",
    "!! Do YoU WaNNa Be A [BIG SHOT]??",
    "!!?? (pLeAse... bUy sOmEtHinG...)",
    "!! [LIMITED TIME OFFER]",
]

CA_ADDRESS = "H4gU4QfQ7kgfAjEJz1X9UjHJzdwc7h6t7LaGgrXYpump"

# ------------------- STYLING HELPERS -------------------
def random_caps(s, p=CAPS_INTENSITY):
    out = []
    for c in s:
        if c.isalpha():
            out.append(c.upper() if random.random() < p else c.lower())
        else:
            out.append(c)
    return "".join(out)

def generate_glitch():
    # 45%: two-part combo like [BIG DEAL]; 55%: single token
    if random.random() < 0.45:
        parts = [random.choice(ADJECTIVES), random.choice(NOUNS)]
        if random.random() < 0.30:
            parts.append(random.choice(TECH + MEMES))
        phrase = " ".join(parts)
    else:
        phrase = random.choice(random.choice([ADJECTIVES, NOUNS, TECH, MEMES]))
    return f"[{phrase}]"

def maybe_glitch_token():
    # 1 or 2 glitches (burst rarer so reply stays readable)
    if random.random() < BURST_PROB:
        return generate_glitch() + " " + generate_glitch()
    return generate_glitch()

def spamton_style(text: str) -> str:
    """Take a clean model reply and add Spamton flavor (caps + bracket glitches)."""
    tokens = text.split()
    out = []
    for w in tokens:
        if random.random() < GLITCH_PROB and len(w) > 2:
            out.append(maybe_glitch_token())
        else:
            # 12%: bracketize the original word, else random-caps
            if random.random() < 0.12:
                core = re.sub(r"^\W+|\W+$", "", w).upper()
                w = w.replace(core, f"[{core}]") if core else w
            out.append(random_caps(w))
    # Add a dramatic suffix sometimes
    if random.random() < 0.6:
        out.append(random_caps(random.choice(SUFFIXES), 0.65))
    return " ".join(out)

# ------------------- AI BRAIN (OpenAI) -------------------
from openai import OpenAI
_client = OpenAI()  # reads OPENAI_API_KEY from env

SYSTEM_PROMPT = (
    "You are Spamton from Deltarune. Answer the user's message helpfully and directly, "
    "but in Spamton's persona: pushy late-night infomercial salesman, desperate, a bit glitchy. "
    "Keep answers short (1–3 sentences). Do NOT overuse brackets; the app will add style later."
)

def fallback_rule_based(user_text: str) -> str:
    """If OpenAI fails, give a simple intent-based reply."""
    t = user_text.lower()
    if any(k in t for k in ["hi","hello","hey","morning","yo","sup"]):
        return "Hello there, valued customer! Ready for a deal?"
    if any(k in t for k in ["price","cost","how much","fee"]):
        return "It costs a tiny price for a GIANT value—trust me."
    if any(k in t for k in ["help","can you","assist"]):
        return "Tell me the problem—I'll fix it AND upsell you something nice."
    if any(k in t for k in ["bye","goodnight","see you"]):
        return "Goodbye! Don’t forget to grab today’s special before it’s gone."
    return "Great question! Here’s the best answer I can give you right now."

def spamton_brain(user_text: str) -> str:
    # Use Responses API; no 'temperature' parameter here
    try:
        resp = _client.responses.create(
            model="gpt-4o-mini",  # pick a fast model enabled on your account
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_text}
            ],
            max_output_tokens=180
        )
        text = (resp.output_text or "").strip()
        if not text:
            text = fallback_rule_based(user_text)
        return text
    except Exception:
        return fallback_rule_based(user_text)

# ------------------- TELEGRAM HANDLERS -------------------
def start_cmd(update, ctx):
    update.message.reply_text(
        "MENTION ME IN GROUPS, [CUSTOMER]!! I’ll answer *properly* — then add a sweet [DEAL]!!"
    )

def ca_cmd(update, ctx):
    # Always works (even with privacy ON) because it's a /command
    base = f"Here is the CA: {CA_ADDRESS}"
    tokens, out = base.split(), []
    for tok in tokens:
        if tok == CA_ADDRESS:
            out.append(tok)  # keep CA EXACTLY as-is
        else:
            if random.random() < GLITCH_PROB:
                out.append(maybe_glitch_token())
            else:
                out.append(random_caps(tok, CAPS_INTENSITY))
    styled = " ".join(out) + " " + random_caps(random.choice(SUFFIXES), 0.65)
    update.message.reply_text(styled)

def handle_text(update, ctx):
    bot_username = ctx.bot.username.lower()
    txt = update.message.text or ""
    chat_type = update.message.chat.type

    # Helper to send a brainy + styled reply
    def reply_like_spamton(src: str):
        clean = spamton_brain(src)
        styled = spamton_style(clean)
        update.message.reply_text(styled)

    # -------- SPECIAL CA OVERRIDE --------
    # If message contains "ca" (any case), return the CA styled,
    # keeping the CA string clean and unmodified.
    def send_ca_response():
        base = f"Here is the CA: {CA_ADDRESS}"
        tokens, out = base.split(), []
        for tok in tokens:
            if tok == CA_ADDRESS:
                out.append(tok)
            else:
                if random.random() < GLITCH_PROB:
                    out.append(maybe_glitch_token())
                else:
                    out.append(random_caps(tok, CAPS_INTENSITY))
        styled = " ".join(out) + " " + random_caps(random.choice(SUFFIXES), 0.65)
        update.message.reply_text(styled)

    if chat_type in ("group", "supergroup"):
        # Only react when mentioned
        if f"@{bot_username}" not in txt.lower():
            return
        # Strip the mention so the AI sees a clean question
        clean_in = re.sub(rf"@{re.escape(ctx.bot.username)}", "", txt, flags=re.IGNORECASE).strip()
        # CA check on the cleaned text
        if "ca" in clean_in.lower():
            send_ca_response()
            return
        reply_like_spamton(clean_in or "HELLO")
    else:
        # Private chat: answer everything
        if "ca" in txt.lower():
            send_ca_response()
            return
        reply_like_spamton(txt)

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN env var missing")
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("ca", ca_cmd))  # /ca always works in groups & DMs
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

