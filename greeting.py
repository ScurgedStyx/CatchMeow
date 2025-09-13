def greeting_response(_: str) -> dict:
    """
    Ignore any incoming user text and always return the same greeting,
    plus suggested replies for Yes/No.
    """
    return {
        "text": "hey, nice to have you here today! Are you ready for the game?",
        "suggested_replies": ["Yes", "No"]
    }


def handle_ready(answer: str) -> dict:
    """
    Handle the user's choice after the greeting.
    Returns a small action hint you can use to start or idle the game.
    """
    a = (answer or "").strip().lower()
    if a.startswith("y"):
        return {
            "text": "Awesome! Starting a new round…",
            "action": "start_game"
        }
    elif a.startswith("n"):
        return {
            "text": "No worries — say 'Yes' whenever you're ready.",
            "action": "idle"
        }
    else:
        return {
            "text": "Please choose: Yes or No.",
            "suggested_replies": ["Yes", "No"],
            "action": "await_ready"
        }


if __name__ == "__main__":
    print(greeting_response("anything")["text"])

    user = input("> ")
    print(handle_ready(user)["text"])