from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import os, random, re

# ====== Word banks for auto-generation ======
ADJECTIVES = [
    "BIG", "LIMITED", "FREE", "HOT", "VALUE", "GUARANTEED",
    "ONCE-IN-A-LIFETIME", "PREMIUM", "RISK-FREE", "SECRET",
    "MEGA", "ULTIMATE", "SPECIAL", "TRUSTED", "HYPERLINK",
    "EXCLUSIVE", "DISCOUNTED", "EXTRA", "CHEAP", "BONUS",
    "VIP", "PLATINUM", "GOLD", "CERTIFIED", "OFFICIAL"
]

NOUNS = [
    "DEAL", "CUSTOMER", "OFFER", "SALE", "MONEY", "BONUS",
    "DISCOUNT", "LOTTERY", "JACKPOT", "SAVINGS", "CASH",
    "NFT", "PRIZE", "SUBSCRIPTION", "MEMBERSHIP", "LOAN",
    "CLICK", "DOWNLOAD", "SHIPPING", "REFUND", "WARRANTY",
    "COUPON", "VOUCHER", "TRIAL", "UPGRADE", "ACCESS"
]

TECH = [
    "404 ERROR", "SYSTEM32", "ACCESS DENIED", "FILE NOT FOUND",
    "BLUE SCREEN", "MISSING DLL", "LOGIN FAILED",
    "UNREGISTERED VERSION", "BUFFER OVERFLOW", "OUT OF RANGE",
    "SIGNAL LOST", "DISK ERROR", "EXPIRED LICENSE",
    "HYPERLINK BLOCKED", "CONNECTION RESET", "TIMEOUT",
    "FIREWALL DETECTED", "PASSWORD REQUIRED"
]

MEMES = [
    "HOT SINGLE IN YOUR AREA", "CONGRATULATIONS WINNER!",
    "WE ARE SO BACK", "COOKED", "BASED", "YOU CALLED??",
    "CHA-CHING!", "MONEY MONEY MONEY", "VOID IF REMOVED",
    "TERMS AND CONDITIONS APPLY", "BATTERY NOT INCLUDED",
    "AS SEEN ON TV", "CLICK HERE", "BUY NOW", "TRY NOW",
    "NO REFUNDS", "FREE SHIPPING", "LOW PRICE", "ACT FAST"
]

SUFFIXES = [
    "!!!", "??!?!!",
    "!! Do YoU WaNNa Be A [BIG SHOT]??",
    "!!?? (pLeAse... bUy sOmEtHinG...)",
    "!!! [HYPERLINK BLOCKED]",
    "!! [LIMITED TIME OFFER]"
]

# ====== Generators ======
def generate_glitch():
    """Return one glitch like [BIG DEAL] or [BLUE SCREEN]."""
    category = random.choice([ADJECTIVES, NOUNS, TECH, MEMES])
    # 45% chance to create a 2–3 piece combo like [BIG DEAL BLUE SCREEN]
    if random.random() < 0.45:
        parts = [random.choice(ADJECTIVES), random.choice(NOUNS)]
        if random.random() < 0.35:  # maybe add a third piece
            parts.append(random.choice(TECH + MEMES))
        phrase = " ".join(parts)
    else:
        phrase = random.choice(category)
    return f"[{phrase}]"

def generate_glitch_burst(min_n=1, max_n=3):
    """Return 1–3 glitches joined with spaces, e.g. [FREE][CLICK HERE]..."""
    k = random.randint(min_n, max_n)
    return " ".join(generate_glitch() for _ in range(k))

def random_caps(s, p=0.5):
    out = []
    for c in s:
        if c.isalpha():
            out.append(c.upper() if random.random() < p else c.lower())
        else:
            out.append(c)
    return "".join(out)

# ====== Spamtonify pipeline ======
def spamtonify(text, glitch=0.30, caps=0.50, burst_min=1, burst_max=3):
    """
    glitch: chance (0..1) to replace a word with glitches
    caps: intensity (0..1) of RaNdOm CaPs
    burst_min/max: how many glitches to insert when triggered
    """
    out = []
    for w in text.split():
        if random.random() < glitch:
            out.append(generate_glitch_burst(burst_min, burst_max))
        else:
            # 20% chance to bracketize the real word
            if random.random() < 0.20:
                w = f"[{w.upper()}]"
            out.append(random_caps(w, caps))
    suffix = " " + random_caps(random.choice(SUFFIXES), 0.65)
    return " ".join(out) + suffix

# ====== Telegram handlers ======
def start_cmd(update, ctx):
    update.message.reply_text("MENTION ME, [CUSTOMER]!! I'LL SPAMTONIFY YOUR WORDS!!")

def handle_text(update, ctx):
    bot_username = ctx.bot.username.lower()
    txt = update.message.text or ""
    # Only react in groups if bot is mentioned
    if f"@{bot_username}" in txt.lower():
        # Strip the mention (case-insensitive)
        clean = re.sub(rf"@{re.escape(ctx.bot.username)}", "", txt, flags=re.IGNORECASE).strip()
        if not clean:
            clean = "HELLO"
        update.message.reply_text(spamtonify(clean))
    # In private chat (DM), reply to everything
    elif update.message.chat.type == "private":
        update.message.reply_text(spamtonify(txt))

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN env var missing")
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

