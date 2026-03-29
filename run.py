"""Auto-reload bot runner. Watches for code changes and restarts automatically."""
import sys
from watchfiles import run_process


def run_bot():
    """Target function that runs the bot."""
    from app.main import main
    main()


if __name__ == "__main__":
    print("🔄 Запуск бота с автоперезагрузкой...")
    print("   Бот перезапустится при изменении .py файлов в app/")
    print("   Нажми Ctrl+C для остановки\n")
    run_process(
        "app",
        target=run_bot,
        callback=lambda changes: print(f"\n♻️  Обнаружены изменения, перезапуск бота..."),
    )
