import logging
import sqlite3
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== CONFIGURACIÓN =====
BOT_TOKEN = "8805260643:AAG42mUp-Rl_pdmiRzkmEmVKTuca7JxaPJM"
MONEDA = "⭐ COINS"
DB_PATH = "/tmp/users.db"

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)

# ===== BASE DE DATOS =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  coins INTEGER DEFAULT 0,
                  referidos INTEGER DEFAULT 0,
                  ultimo_tap INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_coins(user_id, cantidad):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET coins = coins + ? WHERE user_id=?", (cantidad, user_id))
    conn.commit()
    conn.close()

def update_tap(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET ultimo_tap = ? WHERE user_id=?", (int(time.time()), user_id))
    conn.commit()
    conn.close()

def add_referido(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET referidos = referidos + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ===== COMANDO START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Anónimo"
    
    if not get_user(user_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO usuarios (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        conn.close()
        
        args = context.args
        if args:
            try:
                ref_id = int(args[0])
                if ref_id != user_id:
                    add_coins(ref_id, 10)
                    add_referido(ref_id)
                    add_coins(user_id, 5)
                    await update.message.reply_text("🎉 ¡Has sido referido! +5 coins de bonus")
            except:
                pass
    
    user = get_user(user_id)
    text = f"""
🔥 *BIENVENIDO A COINTAP MASTER* 🔥

👤 @{username}
🪙 Tus coins: {user[2]}
👥 Referidos: {user[3]}

👇 Toca el botón para ganar
"""
    keyboard = [
        [InlineKeyboardButton("🪙 TAP (+1 coin)", callback_data="tap")],
        [InlineKeyboardButton("👥 Invitar amigos", callback_data="referir")],
        [InlineKeyboardButton("🏆 Ranking", callback_data="ranking")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ===== TAP =====
async def tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = get_user(user_id)
    if not user:
        await query.edit_message_text("❌ Error: Usuario no registrado")
        return
    
    if user[4] and time.time() - user[4] < 2:
        await query.edit_message_text(
            "⏳ *Espera 2 segundos entre taps*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="volver")]])
        )
        return
    
    add_coins(user_id, 1)
    update_tap(user_id)
    user = get_user(user_id)
    
    await query.edit_message_text(
        f"✅ *¡+1 {MONEDA}!*\n\n🪙 Total: {user[2]} coins",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="volver")]])
    )

# ===== REFERIR =====
async def referir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    link = f"https://t.me/Cointapmaster_bot?start={user_id}"
    await query.edit_message_text(
        f"👥 *INVITA A TUS AMIGOS*\n\nLink: `{link}`\n\n🎁 Tú +10 coins, ellos +5 coins",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="volver")]])
    )

# ===== RANKING =====
async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, coins FROM usuarios ORDER BY coins DESC LIMIT 10")
    top = c.fetchall()
    conn.close()
    
    texto = "🏆 *TOP 10 JUGADORES*\n\n"
    if top:
        for i, (user, coins) in enumerate(top, 1):
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            texto += f"{medalla} @{user} → {coins} {MONEDA}\n"
    else:
        texto = "📭 Sin jugadores aún. ¡Sé el primero!"
    
    await query.edit_message_text(
        texto,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="volver")]])
    )

# ===== VOLVER =====
async def volver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or "Anónimo"
    user = get_user(user_id)
    if not user:
        await start(update, context)
        return
    
    text = f"""
🔥 *COINTAP MASTER* 🔥

👤 @{username}
🪙 Tus coins: {user[2]}
👥 Referidos: {user[3]}
"""
    keyboard = [
        [InlineKeyboardButton("🪙 TAP (+1 coin)", callback_data="tap")],
        [InlineKeyboardButton("👥 Invitar amigos", callback_data="referir")],
        [InlineKeyboardButton("🏆 Ranking", callback_data="ranking")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ===== MAIN =====
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(tap, pattern="tap"))
    app.add_handler(CallbackQueryHandler(referir, pattern="referir"))
    app.add_handler(CallbackQueryHandler(ranking, pattern="ranking"))
    app.add_handler(CallbackQueryHandler(volver, pattern="volver"))
    
    print("🤖 Bot CoinTap Master funcionando...")
    print("🔗 https://t.me/Cointapmaster_bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
