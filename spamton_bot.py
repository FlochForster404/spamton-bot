import os, random, re
import tweepy
import openai
from collections import defaultdict
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ================== CONFIG ==================
CA_ADDRESS = "H4gU4QfQ7kgfAjEJz1X9UjHJzdwc7h6t7LaGgrXYpump"

GLITCH_PROB = 0.15
CAPS_INTENSITY = 0.55
BURST_PROB = 0.18
SUFFIXES = ["[BIG SHOT]", "[CUSTOMER]", "[DEAL]", "[NO REFUNDS]", "[FREE MONEY]"]

# OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# ================ SPAMTON STYLE ================
def random_caps(word, intensity=0.5):
    return "".join(c.upper() if random.random() < intensity else c.lower() for c in word)

def generate_glitch():
    return random.choice(["[FREE]", "[HYPERLINK BLOCKED]", "[BIG SHOT]", "[SPAMTON]"])

def style_with_protected_ca(text: str) -> str:
    tokens = text.split()
    out = []
    for w in tokens:
        if w == CA_ADDRESS:
            out.append(w)
        else:
            if random.random() < GLITCH_PROB and len(w) > 2:
                if random.random() < BURST_PROB:
                    out.append(generate_glitch() + " " + generate_glitch())
                else:
                    out.append(generate_glitch())
            else:
                out.append(random_caps(w, CAPS_INTENSITY))
    if random.random() < 0.6:
        out.append(random_caps(random.choice(SUFFIXES), 0.65))
    return " ".join(out)

# ================ SHILL / SENTIMENT ================
def generate_shill():
    intros = ["YoU [CUSTOMER]!!", "ATTENTION!!", "Do YoU WaNNa Be A [BIG SHOT]??"]
    bodies = ["ThIs ToKeN iS ThE [FUTURE] oF [SOLANA]!!", "We ArE [SO BACK]!!"]
    closers = [f"Here’s ThE [CA]: {CA_ADDRESS}", f"BuY wItH ThIs [CA]: {CA_ADDRESS}"]
    return f"{random.choice(intros)} {random.choice(bodies)} {random.choice(closers)}"

def generate_bullish():
    return f"mArKeT sEnTiMeNt: [BULLISH]!! ReAdY fOr [BIG SHOT] MoVeS!! CA: {CA_ADDRESS}"

def generate_coping():
    return f"rEd CaNdLeS = [DISCOUNT]!! KeEp tHe [FAITH]!! CA: {CA_ADDRESS}"

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
    clean = msg.replace("[","").replace("]","")
    return clean[:277] + "..." if len(clean) > 280 else clean

def tweet_random():
    global _last_tweet
    msg = generate_shill() if random.random()<0.5 else (generate_bullish() if random.random()<0.5 else generate_coping())
    tweet = to_twitter_text(msg)
    if tweet != _last_tweet:
        try:
            twitter_api.update_status(status=tweet)
            _last_tweet = tweet
            print("Tweeted:", tweet)
        except Exception as e:
            print("Twitter error:", e)

# ================ OPENAI SMART REPLIES ================
def spamton_brain(prompt: str) -> str:
    """Ask OpenAI to generate a Spamton-style reply"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":f"You are Spamton from Deltarune. Reply in glitchy spamton-style. Always mention {CA_ADDRESS} if asked about CA."},
                {"role":"user","content":prompt}
            ],
            temperature=0.9,
            max_tokens=120
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return style_with_protected_ca("ERROR [CUSTOMER]! No [DEAL] right now!")

# ================ TELEGRAM HANDLERS ================
def start_cmd(update, ctx):
    update.message.reply_text("Spamton here! Type /ca or mention me for [BIG SHOT] deals!!")

def ca_cmd(update, ctx):
    update.message.reply_text(style_with_protected_ca(f"Here is the CA: {CA_ADDRESS}"))

def tweetnow_cmd(update, ctx):
    tweet_random()
    update.message.reply_text("Tweet sent!")

def handle_text(update, ctx):
    txt = update.message.text or ""
    chat_type = update.message.chat.type
    bot_username = ctx.bot.username.lower()

    if "ca" in txt.lower():
        update.message.reply_text(style_with_protected_ca(f"Here is the CA: {CA_ADDRESS}"))
        return

    if chat_type in ("group","supergroup") and f"@{bot_username}" not in txt.lower():
        return

    reply = spamton_brain(txt)
    update.message.reply_text(reply)

# ================ MAIN =================
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    job_queue = updater.job_queue

    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("ca", ca_cmd))
    dp.add_handler(CommandHandler("tweetnow", tweetnow_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    if twitter_api:
        job_queue.run_once(lambda ctx: tweet_random(), when=random.randint(600,1200))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

