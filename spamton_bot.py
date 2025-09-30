from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import os, random

GLITCH_WORDS = [
    "[BIG SHOT]", "[HYPERLINK BLOCKED]", "[CUSTOMER]",
    "[DEAL]", "[VALUE]", "[LIMITED TIME OFFER]"
]
SUFFIXES = [
    "!!!", "??!?!!",
    "!! Do YoU WaNNa Be A [BIG SHOT]??",
    "!!?? (pLeAse... bUy sOmEtHinG...)"
]

def random_caps(s, p=0.5):
    out = []
    for c in s:
        if c.isalpha():
            out.append(c.upper() if random.random() < p else c.lower())
        else:
            out.append(c)
    return "".join(out)

def spamtonify(text, glitch=0.3, caps=0.5):
    out = []
    for w in text.split():
        if random.random() < glitch:
            out.append(random.choice(GLITCH_WORDS))
        else:
            if random.random() < 0.2:
                w = f"[{w.upper()}]"
            out.append(random_caps(w, caps))
    return " ".join(out) + " " + random_caps(random.choice(SUFFIXES), 0.65)

def start_cmd(update, ctx):
    update.message.reply_text("MENTION ME, [CUSTOMER]!! I'LL SPAMTONIFY YOUR WORDS!!")

def handle_text(update, ctx):
    bot_username = ctx.bot.username.lower()
    text = update.message.text
    user = update.message.from_user.first_name

    # only react if bot is mentioned
    if f"@{bot_username}" in text.lower():
        clean_text = text.replace(f"@{ctx.bot.username}", "").strip()
        if clean_text:
            spamtoned = spamtonify(clean_text)
            update.message.reply_text(f"{user}: {spamtoned}")
        else:
            update.message.reply_text(f"{user}: You CALLED?? Do YoU WaNNa Be A [BIG SHOT]??")

def main():
    token = os.getenv("BOT_TOKEN")
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

