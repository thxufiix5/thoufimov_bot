========================================
  MOVIESDA TELEGRAM BOT - SETUP GUIDE
========================================

📁 FILES IN THIS FOLDER:
------------------------
  bot.py           -> Bot code (DO NOT RENAME)
  requirements.txt -> Python packages list
  README.txt       -> This file (instructions)

⚠️ STEP 1: BOT TOKEN SET PANNANUM!
-----------------------------------
  1. bot.py file open pannu (VS Code la)
  2. Line 15 paaru:
     BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
  3. "YOUR_BOT_TOKEN_HERE" ah DELETE pannitu,
     unoda real BotFather token paste pannu
  4. Save pannu (Ctrl + S)

🚀 STEP 2: VS CODE LA OPEN PANNANUM
------------------------------------
  1. VS Code open pannu
  2. File -> Open Folder -> Itha folder select pannu

🚀 STEP 3: TERMINAL LA COMMANDS
--------------------------------
  Terminal -> New Terminal (Ctrl + `)

  Command 1 - Virtual Environment Create:
  ----------------------------------------
      python -m venv venv

  Command 2 - Activate pannu:
  ---------------------------
      Windows:  venv\Scriptsctivate
      Mac:      source venv/bin/activate

  Command 3 - Packages Install:
  ------------------------------
      pip install -r requirements.txt

  Command 4 - Bot Run:
  --------------------
      python bot.py

✅ READY! Bot start aagum! Telegram la test pannu!

🛑 STOP BOT:
------------
  Terminal la Ctrl + C press pannu

🔁 NEXT TIME RUN PANNA (Daily):
-------------------------------
  Just 2 commands:
      venv\Scriptsctivate
      python bot.py

❓ HELP / DOUBT:
----------------
  @BotFather la token get pannu
