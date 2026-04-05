from main import create_app


if __name__ == "__main__":
    app = create_app()
    print("Bot is running...")
    app.run_polling()