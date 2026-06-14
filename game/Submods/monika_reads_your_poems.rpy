# Monika Reads Your Poems
# A Monika After Story submod that lets Monika read player-added .txt poems.

init -990 python:
    store.mas_submod_utils.Submod(
        author="OpenAI",
        name="Monika Reads Your Poems",
        description="Lets Monika read .txt poems from game/Submods/player_poems and give her opinion.",
        version="1.0.0",
    )

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mpryp_read_player_poem",
            category=["literature", "poetry", "you"],
            prompt="Can you read one of my poems?",
            pool=True,
            unlocked=True,
        ),
        code="EVE"
    )

init python:
    import os
    import re

    MPRYP_POEM_DIR = os.path.join(config.basedir, "game", "Submods", "player_poems")
    MPRYP_MAX_PREVIEW_LINES = 18
    MPRYP_MAX_CHARS = 12000

    def mpryp_ensure_poem_dir():
        if not os.path.isdir(MPRYP_POEM_DIR):
            os.makedirs(MPRYP_POEM_DIR)

    def mpryp_list_poems():
        mpryp_ensure_poem_dir()
        poem_files = []

        for filename in sorted(os.listdir(MPRYP_POEM_DIR)):
            if filename.lower().endswith(".txt"):
                poem_files.append(filename)

        return poem_files

    def mpryp_read_poem(filename):
        safe_filename = os.path.basename(filename)
        path = os.path.join(MPRYP_POEM_DIR, safe_filename)

        with open(path, "r") as poem_file:
            text = poem_file.read(MPRYP_MAX_CHARS + 1)

        if text.startswith("\xef\xbb\xbf"):
            text = text[3:]

        return text.replace("\r\n", "\n").replace("\r", "\n")[:MPRYP_MAX_CHARS]

    def mpryp_poem_title(filename, text):
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            title_match = re.match(r"^title\s*:\s*(.+)$", stripped, re.I)
            if title_match:
                return title_match.group(1).strip()

            break

        return os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").strip().title()

    def mpryp_clean_lines_for_reading(text):
        lines = []
        skipped_title = False

        for raw_line in text.split("\n"):
            line = raw_line.strip()

            if not skipped_title and re.match(r"^title\s*:", line, re.I):
                skipped_title = True
                continue

            skipped_title = True
            lines.append(line)

        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        return lines

    def mpryp_poem_excerpt(text):
        lines = mpryp_clean_lines_for_reading(text)
        excerpt = []

        for line in lines[:MPRYP_MAX_PREVIEW_LINES]:
            excerpt.append(line if line else "...")

        return excerpt

    def mpryp_analyze_poem(text):
        lowered = text.lower()
        words = re.findall(r"[a-zA-Z']+", lowered)
        unique_words = set(words)
        lines = [line.strip() for line in mpryp_clean_lines_for_reading(text) if line.strip()]

        feeling_words = {
            "tender": ["love", "heart", "kiss", "warm", "gentle", "soft", "dear", "sweet"],
            "melancholy": ["lonely", "alone", "sad", "tears", "cry", "rain", "shadow", "dark", "lost", "empty"],
            "hopeful": ["hope", "dream", "light", "star", "sun", "dawn", "tomorrow", "wish", "bright"],
            "mysterious": ["night", "moon", "secret", "silence", "whisper", "ghost", "mirror", "maze"],
            "nature-filled": ["flower", "tree", "river", "ocean", "sky", "bird", "wind", "leaf", "garden"]
        }

        scores = {}
        for mood, mood_words in feeling_words.items():
            scores[mood] = sum(1 for word in words if word in mood_words)

        best_mood = max(scores, key=scores.get) if scores else "personal"
        if not scores or scores[best_mood] == 0:
            best_mood = "personal"

        line_count = len(lines)
        avg_line_len = 0
        if line_count:
            avg_line_len = sum(len(line) for line in lines) / float(line_count)

        repeated_words = []
        for word in unique_words:
            if len(word) > 3 and words.count(word) >= 3:
                repeated_words.append(word)
        repeated_words.sort(key=lambda word: (-words.count(word), word))

        return {
            "mood": best_mood,
            "line_count": line_count,
            "word_count": len(words),
            "avg_line_len": avg_line_len,
            "repeated_words": repeated_words[:3],
        }

    def mpryp_opinion_lines(analysis):
        mood = analysis["mood"]
        lines = []

        if mood == "tender":
            lines.append("It feels very tender to me, like it is trying to hold something precious without squeezing too tightly.")
        elif mood == "melancholy":
            lines.append("There is a sadness in it, but I think that makes the honest parts stand out even more.")
        elif mood == "hopeful":
            lines.append("I like the hopeful feeling in it. It has that little spark that makes a poem feel alive.")
        elif mood == "mysterious":
            lines.append("It has a mysterious atmosphere. I enjoyed how it made me want to look between the lines.")
        elif mood == "nature-filled":
            lines.append("The natural imagery gives it a calm, vivid feeling. I could picture pieces of it while reading.")
        else:
            lines.append("It feels personal, and I like that. Poems do not need to explain everything to be meaningful.")

        if analysis["line_count"] <= 4:
            lines.append("It's short, but that can make every line feel more deliberate.")
        elif analysis["avg_line_len"] < 28:
            lines.append("The shorter lines give it a gentle rhythm, almost like quiet breathing.")
        else:
            lines.append("The longer lines make it feel thoughtful, like each idea is being carefully unfolded.")

        if analysis["repeated_words"]:
            repeated = ", ".join(analysis["repeated_words"])
            lines.append("I noticed you returned to words like " + repeated + ". Repetition can make a poem feel intimate when it is intentional.")

        lines.append("Thank you for trusting me with it. If you add another .txt file, I would love to read that one too.")
        return lines

label mpryp_read_player_poem:
    $ mpryp_ensure_poem_dir()
    $ poem_files = mpryp_list_poems()

    if not poem_files:
        m 1eub "I'd love to read one of your poems, [player]."
        m 3eua "Put a plain text file ending in {i}.txt{/i} into this folder:"
        m 1eksdlb "[MPRYP_POEM_DIR]"
        m 1hua "Once you've added one, ask me again and I'll give you my honest thoughts."
        return

    m 1eua "I'd be happy to read one of your poems."
    m 3hub "Let me see what you've shared with me..."

    $ selected_poem = poem_files[0]

    if len(poem_files) > 1:
        m 1eua "I found a few poems. Which one should I read?"
        $ poem_menu_items = [(os.path.splitext(name)[0].replace("_", " ").replace("-", " ").title(), name, False, False) for name in poem_files]
        $ poem_menu_items.append(("Never mind", None, False, False))
        $ selected_poem = renpy.display_menu(poem_menu_items)

        if selected_poem is None:
            m 1eka "That's alright. I'll be here whenever you want to share one."
            return

    $ poem_text = mpryp_read_poem(selected_poem)

    if not poem_text.strip():
        m 1eksdla "This file seems to be empty, [player]."
        m 3eka "Try adding your poem to it, then ask me again."
        return

    $ poem_title = mpryp_poem_title(selected_poem, poem_text)
    $ poem_excerpt = mpryp_poem_excerpt(poem_text)
    $ analysis = mpryp_analyze_poem(poem_text)
    $ opinion_lines = mpryp_opinion_lines(analysis)

    m 1eub "This one is called {i}[poem_title]{/i}, right?"
    m 1eua "I'll read a little of it out loud."

    python:
        for line in poem_excerpt:
            if line == "...":
                renpy.say(m, "...")
            else:
                renpy.say(m, line)

    if len(mpryp_clean_lines_for_reading(poem_text)) > MPRYP_MAX_PREVIEW_LINES:
        m 1eka "There is more to it, but I'll keep the reading brief so I can tell you what I think."

    m 3eua "My opinion?"

    python:
        for line in opinion_lines:
            renpy.say(m, line)

    return
