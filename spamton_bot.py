import os, random, re
import tweepy
from collections import defaultdict
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ================== CONFIG ==================
CA_ADDRESS = "H4gU4QfQ7kgfAjEJz1X9UjHJzdwc7h6t7LaGgrXYpump"  # keep EXACT

# Style knobs
GLITCH_PROB = 0.15
CAPS_INTENSITY = 0.55
BURST_PROB = 0.18
SUFFIXES = [
    "[BIG SHOT]", "[CUSTOMER]", "[DEAL]", "[NO REFUNDS]",
    "!! Do YoU WaNNa Be A [BIG SHOT]??", "!! [LIMITED TIME OFFER]"
]

# ================ SPAMTON STYLE HELPERS ================
def random_caps(word, intensity=0.5):
    out = []
    for c in word:
        if c.isalpha():
            out.append(c.upper() if random.random() < intensity else c.lower())
        else:
            out.append(c)
    return "".join(out)

def generate_glitch():
    return random.choice([
        "[FREE]", "[HYPERLINK BLOCKED]", "[BIG SHOT]", "[SPAMTON]",
        "[VALUE]", "[CLICK HERE]", "[BUY NOW]"
    ])

def spamton_style(text: str) -> str:
    tokens = text.split()
    out = []
    for w in tokens:
        if random.random() < GLITCH_PROB and len(w) > 2:
            if random.random() < BURST_PROB:
                out.append(generate_glitch() + " " + generate_glitch())
            else:
                out.append(generate_glitch())
        else:
            if random.random() < 0.12:
                core = re.sub(r"^\W+|\W+$", "", w).upper()
                w = w.replace(core, f"[{core}]") if core else w
            out.append(random_caps(w, CAPS_INTENSITY))
    if random.random() < 0.6:
        out.append(random_caps(random.choice(SUFFIXES), 0.65))
    return " ".join(out)

def style_with_protected_ca(text: str) -> str:
    """Spamton-style the text, but NEVER glitch or alter the CA string."""
    tokens = text.split()
    out = []
    for w in tokens:
        if w == CA_ADDRESS:
            out.append(w)  # CA intact, no brackets/caps changes
        else:
            if random.random() < GLITCH_PROB and len(w) > 2:
                if random.random() < BURST_PROB:
                    out.append(generate_glitch() + " " + generate_glitch())
                else:
                    out.append(generate_glitch())
            else:
                if random.random() < 0.12:
                    core = re.sub(r"^\W+|\W+$", "", w).upper()
                    w = w.replace(core, f"[{core}]") if core else w
                out.append(random_caps(w, CAPS_INTENSITY))
    if random.random() < 0.6:
        out.append(random_caps(random.choice(SUFFIXES), 0.65))
    return " ".join(out)

# ================ OPENAI "BRAIN" (NEW SDK) ================
from openai import OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are Spamton from Deltarune. Answer helpfully and directly, in Spamton's voice but WITHOUT brackets or heavy styling. "
    "Keep it short (1–3 sentences). If asked about the contract address / CA, include it EXACTLY as "
    f"{CA_ADDRESS}. The app will add styling later."
)

def spamton_brain(user_text: str) -> str:
    """Generate a plain (un-styled) Spamton reply with OpenAI."""
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_text}
            ],
            temperature=0.9,
            max_tokens=150,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print("OpenAI error:", e)
        # return a neutral text; we'll style it for consistency
        return "I ran into a hiccup, customer. Try me again!"

# ================ SHILL / SENTIMENT GENERATORS ================
_last_shill = defaultdict(str)
_last_sentiment = defaultdict(str)

def generate_shill():
    intros = ["YoU [CUSTOMER]!!", "ATTENTION!!", "Do YoU WaNNa Be A [BIG SHOT]??",
              "SeCrEt [ALPHA]!!", "tHe NeXt [100x]!!", "LiStEn Up!!", "WhO WaNtS [FREE MONEY]??"]
    bodies = ["ThIs ToKeN iS ThE [FUTURE] oF [SOLANA]!!",
              "DoN’T MiSs YoUr ChAnCe To GeT RiCh!!",
              "oNlY [REAL] ChAdS WiLl BuY ThIs!!",
              "We ArE [SO BACK]!!",
              "YoU cAn’T MiSs ThIs DeAl!!",
              "ThE [BIGGEST] ShOt YoU’lL eVeR SeE!!",
              "gEt In bEfOrE [SMART MONEY]!!"]
    closers = [f"Here’s ThE [CA]: {CA_ADDRESS}",
               f"BuY wItH ThIs [CA]: {CA_ADDRESS}",
               f"[COPY PASTE] YoUr WaY To [RICHES]: {CA_ADDRESS}",
               f"Don’T TrUsT mE?? TrUsT ThE [CA]: {CA_ADDRESS}",
               f"[NO REFUNDS] BuT aLl ReWARDS → {CA_ADDRESS}"]
    return f"{random.choice(intros)} {random.choice(bodies)} {random.choice(closers)}"

def shill_message(context):
    chat_id = context.job.context
    for _ in range(5):
        msg = generate_shill()
        if msg != _last_shill[chat_id]:
            break
    _last_shill[chat_id] = msg
    styled = style_with_protected_ca(msg)
    context.bot.send_message(chat_id=chat_id, text=styled)

def generate_bullish():
    openers = [
        "mArKeT sEnTiMeNt: [BULLISH]!!",
        "ChArT sAyS [UP ONLY]!!",
        "WhAlEs sNiFfInG a [DEAL]!!",
        "ThE vIbE iS [WE ARE SO BACK]!!",
        "SmArT MoNeY iS [ACCUMULATING]!!",
    ]
    mids = [
        "vOlUmE cLuStErS lOoK [STRONG].",
        "sUpPlY iS [DRYING UP] — yOu kNoW tHe dRiLl.",
        "nEw eYeBaLlS cOmInG iN [FAST].",
        "oRdEr bOoK cLeAn — [NO REFUNDS] rEqUiReD.",
        "mOmEnTuM iS [BUILDING].",
    ]
    closes = [
        f"ReAdY tO bEcOmE a [BIG SHOT]? CA: {CA_ADDRESS}",
        f"[ACCUMULATE] wItH cOnViCtIoN → CA: {CA_ADDRESS}",
        f"TiCkEt Up: CA {CA_ADDRESS}",
        f"NeXt LeG wHeN yOu pOsT tHiS: {CA_ADDRESS}",
        f"pRinT tHiS [CA] aNd sMiLe: {CA_ADDRESS}",
    ]
    return f"{random.choice(openers)} {random.choice(mids)} {random.choice(closes)}"

def generate_coping():
    openers = [
        "rEd CaNdLeS?? [GOOD] — cHeAp TiCkEtS!!",
        "dIpS aRe [DISCOUNTS] fOr rEaL oGs!!",
        "dOwN iS nOt [DEAD] — iT’s [BUILD MODE]!!",
        "pAiN iS [TEMPORARY], [CUSTOMER]!!",
        "cHaRt lOoKs rOuGh? [OPPORTUNITY] wRiTeS iTs NaMe!!",
    ]
    mids = [
        "aCcUmUlAtE sMaRtLy, nOt fOmO.",
        "pLaN yOuR sIzInG, kEeP mOrAl [HIGH].",
        "tHe dOllAr-CoSt aVeRaGe [DEAL] iS rEaL.",
        "cOmMuNiTy sTrOnG = [INEVITABLE] rEcOvErY.",
        "pAtIeNcE mAkEs [BIG SHOTS].",
    ]
    closes = [
        f"wHeN iT tUrNs, bE [READY]: CA {CA_ADDRESS}",
        f"yOuR rEmInDeR → [CA]: {CA_ADDRESS}",
        f"kEeP tHe [FAITH] aNd tHe [CA]: {CA_ADDRESS}",
        f"bElIeVe In tHe [DEAL] → {CA_ADDRESS}",
        f"eYeS oN tHe pRiZe: {CA_ADDRESS}",
    ]
    return f"{random.choice(openers)} {random.choice(mids)} {random.choice(closes)}"

def bullish_or_coping_message(context):
    chat_id = context.job.context
    msg = generate_bullish() if random.random() < 0.5 else generate_coping()
    if msg == _last_sentiment[chat_id]:
        msg = generate_bullish()
    _last_sentiment[chat_id] = msg
    styled = style_with_protected_ca(msg)
    context.bot.send_message(chat_id=chat_id, text=styled)
    # self-reschedule 2–3h later with jitter
    next_in = random.randint(7200, 10800)
    context.job_queue.run_once(bullish_or_coping_message, next_in, context=chat_id)

# ================ TWITTER / X INTEGRATION ================
TW_API_KEY        = os.getenv("TWITTER_API_KEY")
TW_API_SECRET     = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN   = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET  = os.getenv("TWITTER_ACCESS_SECRET")

twitter_api = None
if all([TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET]):
    try:
        auth = tweepy.OAuth1UserHandler(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
        twitter_api = tweepy.API(auth)
        print("Twitter client ready.")
    except Exception as e:
        print("Twitter init error:", e)

_last_tweet = ""

def to_twitter_text(msg: str) -> str:
    # remove [] but keep CA intact
    parts = []
    for tok in msg.split():
        if tok == CA_ADDRESS:
            parts.append(tok)
        else:
            parts.append(tok.replace("[", "").replace("]", ""))
    text = " ".join(parts)
    return text[:277] + "..." if len(text) > 280 else text

def tweet_random():
    global _last_tweet
    if not twitter_api:
        print("Twitter not configured; skip tweeting.")
        return
    msg = generate_shill() if random.random() < 0.5 else (generate_bullish() if random.random() < 0.5 else generate_coping())
    tweet = to_twitter_text(msg)
    if tweet == _last_tweet:
        tweet = to_twitter_text(generate_shill())
    try:
        twitter_api.update_status(status=tweet)
        _last_tweet = tweet
        print("Tweeted:", tweet)
    except Exception as e:
        print("Twitter error:", e)

def tweet_job(context):
    tweet_random()
    # self-reschedule 1–3h
    next_in = random.randint(3600, 10800)
    context.job_queue.run_once(tweet_job, next_in)

# ================ TELEGRAM COMMANDS & HANDLERS ================
def start_cmd(update, ctx):
    update.message.reply_text("Spamton here! Type /ca or mention me for [BIG SHOT] deals!!")

def ca_cmd(update, ctx):
    msg = f"Here is the CA: {CA_ADDRESS}"
    update.message.reply_text(style_with_protected_ca(msg))

def id_cmd(update, ctx):
    update.message.reply_text(f"Chat ID is: {update.effective_chat.id}")

def tweetnow_cmd(update, ctx):
    tweet_random()
    update.message.reply_text("Tweet sent! (check your X account)")

def handle_text(update, ctx):
    txt = update.message.text or ""
    chat_type = update.message.chat.type
    bot_username = ctx.bot.username.lower()

    # Groups: only react if mentioned
    if chat_type in ("group", "supergroup"):
        if f"@{bot_username}" not in txt.lower():
            return
        # strip mention so the brain sees a clean question
        txt = re.sub(rf"@{re.escape(ctx.bot.username)}", "", txt, flags=re.IGNORECASE).strip()

    # Fast CA override
    if "ca" in txt.lower():
        update.message.reply_text(style_with_protected_ca(f"Here is the CA: {CA_ADDRESS}"))
        return

    # Smart reply (plain) -> style it (keeps CA intact)
    plain = spamton_brain(txt)
    styled = style_with_protected_ca(plain)
    update.message.reply_text(styled)

# ================ MAIN =================
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN env var missing")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    job_queue = updater.job_queue

    # Commands
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("ca", ca_cmd))
    dp.add_handler(CommandHandler("id", id_cmd))
    dp.add_handler(CommandHandler("tweetnow", tweetnow_cmd))

    # Text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Auto-post to multiple groups
    shill_chat_ids = os.getenv("SHILL_CHAT_IDS")  # comma-separated list
    if shill_chat_ids:
        ids = [int(x.strip()) for x in shill_chat_ids.split(",") if x.strip()]
        for cid in ids:
            # Shill every ~2.5h (stagger first run)
            job_queue.run_repeating(shill_message, interval=9000, first=random.randint(60, 300), context=cid)
            # Sentiment thread: start after 5–10 min; it self-reschedules 2–3h
            job_queue.run_once(bullish_or_coping_message, when=random.randint(300, 600), context=cid)

    # Twitter auto-post (if keys present)
    if twitter_api:
        job_queue.run_once(tweet_job, when=random.randint(600, 1200))
        print("Twitter scheduler started.")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

