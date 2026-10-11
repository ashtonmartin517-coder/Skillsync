"""
Static learning content for SkillSync.

Everything a student sees (skills, analogies, tasks, glossary, quotes, weekly
pulse cards) lives here so you can improve the platform without touching the
backend logic. Edit this file, restart the server, done.
"""

LEVEL_LABELS = {
    0: "Never heard of it",
    1: "Heard of it",
    2: "Tried it",
    3: "Confident",
}

COURSES = ["B.Tech", "BCA", "MCA", "B.Sc (CS/IT)", "Diploma", "Other"]

# weight: how important the skill is early in a tech career (1-5)
# prereq: skills that should be at level >= 2 before this one makes sense
SKILLS = [
    {
        "id": "terminal", "name": "Terminal & Bash", "area": "Tools", "weight": 5, "prereq": [],
        "question": "How comfortable are you with the terminal (command line, bash)?",
        "analogy": "The terminal is texting your computer very literal instructions instead of clicking icons.",
        "why": "Almost every developer tool (Git, servers, Python) is used from the terminal.",
        "tasks": [
            {"title": "Open your terminal", "detail": "Windows: install Git Bash or WSL. Mac/Linux: open Terminal. Run pwd and ls to see where you are and what is around you.", "minutes": 15},
            {"title": "Move around and make things", "detail": "Use cd to enter folders, mkdir to make one, touch (or echo > file.txt) to make a file, and rm to delete it.", "minutes": 20},
            {"title": "Mini challenge", "detail": "Create a folder called practice, add three files inside it, list them, then delete one. Do it without touching the mouse.", "minutes": 20},
        ],
    },
    {
        "id": "git", "name": "Git (version control)", "area": "Tools", "weight": 5, "prereq": ["terminal"],
        "question": "How well do you know Git (commit, branch, merge)?",
        "analogy": "Git is the save-point system in a video game. Break something, load the last save.",
        "why": "Every company uses Git. Not knowing it is the fastest way to fail a first internship.",
        "tasks": [
            {"title": "Install Git and set your name", "detail": "Install Git, then run: git config --global user.name \"Your Name\" and the same for user.email.", "minutes": 15},
            {"title": "Your first commit", "detail": "In a new folder run git init, create a file, then git add . and git commit -m \"first commit\". Check git log.", "minutes": 25},
            {"title": "Branch and merge", "detail": "Make a branch with git switch -c feature, change a file, commit, switch back to main and run git merge feature.", "minutes": 30},
        ],
    },
    {
        "id": "github", "name": "GitHub profile & repos", "area": "Tools", "weight": 4, "prereq": ["git"],
        "question": "Do you have a GitHub account with at least one project on it?",
        "analogy": "GitHub is Google Drive for code, and it doubles as your public portfolio.",
        "why": "Recruiters open your GitHub before they open your resume.",
        "tasks": [
            {"title": "Create your account", "detail": "Use a professional username (yourname, not coolboy123). Add a photo and a one-line bio.", "minutes": 10},
            {"title": "Push your first repo", "detail": "Create a repo on GitHub, connect it with git remote add origin, and run git push -u origin main.", "minutes": 25},
            {"title": "Write a README", "detail": "A README explains your project in 5 lines: what it is, why you built it, how to run it.", "minutes": 20},
        ],
    },
    {
        "id": "web", "name": "HTML, CSS & JavaScript", "area": "Coding", "weight": 4, "prereq": [],
        "question": "Have you built anything with HTML, CSS or JavaScript?",
        "analogy": "HTML is the skeleton, CSS is the clothes, JavaScript is the movement.",
        "why": "It is the fastest way to build something you can show anyone with a link.",
        "tasks": [
            {"title": "Build a page about yourself", "detail": "One index.html with a heading, a photo, and three paragraphs. Open it in the browser.", "minutes": 30},
            {"title": "Style it with CSS", "detail": "Add colors, fonts and spacing. Make it look good on a phone too.", "minutes": 40},
            {"title": "Add one interaction", "detail": "Make a button that changes the page (dark mode toggle, counter, or a quote shuffler) using JavaScript.", "minutes": 40},
        ],
    },
    {
        "id": "lang", "name": "One programming language", "area": "Coding", "weight": 5, "prereq": [],
        "question": "How well can you write programs in one language (Python, Java, C++)?",
        "analogy": "Learning one language well is like learning to drive one car. The next car feels familiar.",
        "why": "Interviews, internships and every other skill build on this.",
        "tasks": [
            {"title": "Pick ONE language", "detail": "Python is the friendliest for beginners. Write variables, if/else and loops in 30 minutes.", "minutes": 30},
            {"title": "Write functions", "detail": "Write 5 small functions: add two numbers, check even/odd, reverse a string, count vowels, find the max in a list.", "minutes": 40},
            {"title": "Build a tiny program", "detail": "Make a number guessing game or a to-do list that runs in the terminal.", "minutes": 45},
        ],
    },
    {
        "id": "dsa", "name": "Data structures basics", "area": "Coding", "weight": 4, "prereq": ["lang"],
        "question": "Do you know arrays, stacks, queues and hash maps?",
        "analogy": "Data structures are containers. A stack is a pile of plates, a queue is a ticket line.",
        "why": "Technical interviews test how well you pick the right container.",
        "tasks": [
            {"title": "Arrays and strings", "detail": "Learn indexing, slicing and looping. Reverse an array without using a built-in function.", "minutes": 30},
            {"title": "Stack and queue", "detail": "Implement both yourself using a list. Push, pop, enqueue, dequeue.", "minutes": 35},
            {"title": "Hash map", "detail": "Learn dictionaries (Python) or HashMap (Java). Count how many times each word appears in a sentence.", "minutes": 35},
        ],
    },
    {
        "id": "leetcode", "name": "LeetCode / problem solving", "area": "Coding", "weight": 3, "prereq": ["lang"],
        "question": "Have you solved coding problems on LeetCode or similar sites?",
        "analogy": "LeetCode is a gym for your brain. Small daily reps beat one huge session.",
        "why": "Many companies filter candidates with problems like these.",
        "tasks": [
            {"title": "Create your account", "detail": "Sign up on LeetCode and open the Easy problems list. Read, don't panic.", "minutes": 10},
            {"title": "Solve Two Sum", "detail": "Try it yourself for 20 minutes first. Then read the solution and rewrite it from memory.", "minutes": 40},
            {"title": "The 5-a-week habit", "detail": "Solve 5 Easy problems this week. Write one line after each: what trick did it use?", "minutes": 60},
        ],
    },
    {
        "id": "api_db", "name": "APIs & databases", "area": "Coding", "weight": 3, "prereq": ["web"],
        "question": "Do you know what an API and a database are, and have you used either?",
        "analogy": "An API is a waiter between the kitchen and your table. A database is a huge spreadsheet you can question.",
        "why": "Every real app stores data and talks to other services.",
        "tasks": [
            {"title": "Call a free API", "detail": "Use fetch() in JavaScript to call a free public API (for example a random quote API) and show the result on a page.", "minutes": 40},
            {"title": "Learn 4 SQL commands", "detail": "SELECT, INSERT, UPDATE, DELETE. Practice on a free online SQL sandbox.", "minutes": 40},
            {"title": "Store something", "detail": "Make a small app that saves notes in SQLite or a JSON file.", "minutes": 60},
        ],
    },
    {
        "id": "project", "name": "A project that is online", "area": "Career", "weight": 5, "prereq": ["github"],
        "question": "Have you built a project and put it online with a link?",
        "analogy": "A resume says you can cook. A project is the dish on the table.",
        "why": "One live project beats ten certificates.",
        "tasks": [
            {"title": "Pick a real problem", "detail": "Solve something you have faced yourself. Write the problem in two sentences.", "minutes": 20},
            {"title": "Build the smallest version", "detail": "One screen, one feature. Ugly is fine. Push it to GitHub.", "minutes": 120},
            {"title": "Deploy it free", "detail": "Use GitHub Pages, Netlify, Vercel or Render so anyone can open your link.", "minutes": 40},
        ],
    },
    {
        "id": "resume", "name": "Resume & LinkedIn", "area": "Career", "weight": 3, "prereq": [],
        "question": "Do you have a one-page resume and a LinkedIn profile?",
        "analogy": "Your resume is your shop window. People decide in seconds whether to walk in.",
        "why": "Opportunities find people who are easy to find.",
        "tasks": [
            {"title": "Write a one-page resume", "detail": "Sections: education, skills, projects, links. Use one clean template and export as PDF.", "minutes": 45},
            {"title": "Set up LinkedIn", "detail": "Photo, headline (Student | Learning Web Dev), About section, and your GitHub link.", "minutes": 30},
            {"title": "Connect with 10 people", "detail": "Seniors from your college and people in roles you like. Add a short note.", "minutes": 20},
        ],
    },
    {
        "id": "news", "name": "Following tech news", "area": "Awareness", "weight": 2, "prereq": [],
        "question": "Do you follow what is happening in the tech industry?",
        "analogy": "Checking tech news is like checking the weather before you leave. You plan better.",
        "why": "Knowing which skills are in demand helps you choose what to learn.",
        "tasks": [
            {"title": "Pick two sources", "detail": "One newsletter and one site. Hacker News and any beginner-friendly tech newsletter are good starts.", "minutes": 15},
            {"title": "Read for 10 minutes", "detail": "Read headlines only. Write down three words you do not know.", "minutes": 10},
            {"title": "Look up those words", "detail": "Use the Learn tab here. Turning unknown words into known ones is the whole game.", "minutes": 15},
        ],
    },
    {
        "id": "roles", "name": "Tech roles & career paths", "area": "Awareness", "weight": 3, "prereq": [],
        "question": "Do you know the difference between roles like SDE, QA, Data Analyst, DevOps?",
        "analogy": "A hospital has surgeons, nurses and lab techs. Tech has different jobs too. You choose where you fit.",
        "why": "You cannot aim at a role you have never heard of.",
        "tasks": [
            {"title": "Learn 5 roles", "detail": "Software Developer, QA/Tester, Data Analyst, DevOps, UI/UX Designer. One line each: what do they do all day?", "minutes": 20},
            {"title": "Read real job posts", "detail": "Open 3 fresher job posts. Copy the skills they ask for in a note.", "minutes": 25},
            {"title": "Pick a direction for 3 months", "detail": "Choose one role to explore. You can change later. A direction beats no direction.", "minutes": 15},
        ],
    },
    {
        "id": "ai_tools", "name": "Using AI tools wisely", "area": "Awareness", "weight": 3, "prereq": [],
        "question": "Do you use AI assistants (like Claude or ChatGPT) to learn and code?",
        "analogy": "An AI assistant is a very fast tutor who is sometimes confidently wrong. Use it, but verify.",
        "why": "Using AI well is now a hiring skill. Copy-pasting without understanding is not.",
        "tasks": [
            {"title": "Ask it to explain, not to do", "detail": "Pick a topic you do not understand and ask for a simple analogy and a tiny example.", "minutes": 15},
            {"title": "Test what it gave you", "detail": "Run the code it wrote. Break it on purpose. Ask it why it failed.", "minutes": 25},
            {"title": "Rule: explain it back", "detail": "Before you submit any AI-written code, explain each line to a friend (or to yourself in a note).", "minutes": 20},
        ],
    },
]

GLOSSARY = [
    {"term": "Terminal", "tag": "Tools", "analogy": "A text window where you type instructions to your computer instead of clicking.", "example": "ls shows the files in the current folder."},
    {"term": "Bash", "tag": "Tools", "analogy": "The language the terminal speaks on Linux, Mac and Git Bash.", "example": "cd projects moves you into a folder called projects."},
    {"term": "Git", "tag": "Tools", "analogy": "Save points for your code, so you can always go back.", "example": "git commit -m \"added login page\""},
    {"term": "Repository (repo)", "tag": "Tools", "analogy": "A project folder that remembers every change ever made to it.", "example": "Your portfolio website is one repo."},
    {"term": "Commit", "tag": "Tools", "analogy": "One save point with a short note on what changed.", "example": "\"fix button color\" is a good commit message."},
    {"term": "Branch", "tag": "Tools", "analogy": "A parallel copy where you try ideas without breaking the main version.", "example": "Make a branch called dark-mode, test it, merge when happy."},
    {"term": "Merge", "tag": "Tools", "analogy": "Combining your experiment back into the main version.", "example": "Dark mode works, so merge it into main."},
    {"term": "Pull request (PR)", "tag": "Tools", "analogy": "Asking the team: please review my change and add it to the project.", "example": "You fix a typo in an open-source README and open a PR."},
    {"term": "GitHub", "tag": "Tools", "analogy": "A website that stores Git repos online. Your public coding portfolio.", "example": "Recruiters check github.com/yourname."},
    {"term": "LeetCode", "tag": "Coding", "analogy": "A website with coding puzzles. A gym for interview skills.", "example": "Two Sum is the classic first problem."},
    {"term": "Algorithm", "tag": "Coding", "analogy": "A recipe: clear steps that solve one kind of problem every time.", "example": "Steps to find the biggest number in a list."},
    {"term": "Data structure", "tag": "Coding", "analogy": "A way to organise data, like choosing between a shelf, a stack of plates, or a queue.", "example": "Array, stack, queue, hash map."},
    {"term": "Big O", "tag": "Coding", "analogy": "A way to say how slow a solution gets when the input grows. Like how a queue gets slower as more people join.", "example": "Searching one by one in 1 million items is slower than a smart search."},
    {"term": "IDE / Code editor", "tag": "Tools", "analogy": "A word processor made for code, with spell-check for programming.", "example": "VS Code is free and popular."},
    {"term": "Frontend", "tag": "Web", "analogy": "The dining room of a restaurant: everything the customer sees and touches.", "example": "Buttons, colors, layout."},
    {"term": "Backend", "tag": "Web", "analogy": "The kitchen: it prepares everything and customers never see it.", "example": "Login checks, saving data."},
    {"term": "API", "tag": "Web", "analogy": "A waiter who carries your order to the kitchen and brings the food back.", "example": "A weather app asks a weather API for today's forecast."},
    {"term": "Database", "tag": "Web", "analogy": "A giant organised spreadsheet your app can ask questions.", "example": "SQLite, PostgreSQL, MongoDB."},
    {"term": "SQL", "tag": "Web", "analogy": "The language for asking a database questions.", "example": "SELECT name FROM students WHERE year = 1;"},
    {"term": "Framework", "tag": "Web", "analogy": "A ready-made kitchen. Tools are set up, you just cook.", "example": "Flask (Python), React (JavaScript)."},
    {"term": "Library", "tag": "Coding", "analogy": "A toolbox someone else built that you borrow.", "example": "NumPy helps Python do maths quickly."},
    {"term": "Deploy", "tag": "Web", "analogy": "Moving your project from your laptop to a place where everyone can open it.", "example": "Putting your site on Render or Vercel."},
    {"term": "Open source", "tag": "Career", "analogy": "A recipe published for everyone to use, improve and share.", "example": "Linux, Python and Flask are open source."},
    {"term": "Cloud", "tag": "Industry", "analogy": "Renting someone else's computers by the hour instead of buying your own.", "example": "AWS, Google Cloud, Azure."},
    {"term": "AI / LLM", "tag": "Industry", "analogy": "A program trained on huge amounts of text that predicts useful replies. A very well-read autocomplete.", "example": "Claude and ChatGPT are LLMs."},
    {"term": "Internship", "tag": "Career", "analogy": "A short paid or unpaid job to learn on real work. Often the door to a full-time role.", "example": "A 2-month summer internship."},
    {"term": "ATS", "tag": "Career", "analogy": "Software that scans resumes before a human sees them. Keep your resume simple and keyword-rich.", "example": "Plain PDF, standard headings, no fancy graphics."},
    {"term": "CI/CD", "tag": "Industry", "analogy": "A robot that tests and delivers your code every time you save a change.", "example": "Push to GitHub, tests run, the site updates."},
]

# Weekly Pulse. Evergreen explainers about the industry. Add fresh cards each
# week (no live news feed is used on purpose, so nothing here goes stale).
PULSE = [
    {"title": "AI coding assistants are now normal", "tag": "Industry",
     "body": "Most developers use AI to write boilerplate, explain errors and learn faster. Think of it as a tutor, not a replacement.",
     "why": "Companies now expect you to use AI well, and to still understand the code.",
     "action": "Ask an AI to explain one error message today. Then fix it yourself."},
    {"title": "Skills beat college names", "tag": "Career",
     "body": "More companies now check what you can build (projects, GitHub) before checking where you studied.",
     "why": "This is your biggest advantage if you are from a tier-3 college.",
     "action": "Put one project link at the top of your resume."},
    {"title": "Open source is a free internship", "tag": "Career",
     "body": "Anyone can fix small bugs or documentation in public projects. Maintainers notice and remember contributors.",
     "why": "It gives you real teamwork proof without needing a job.",
     "action": "Search GitHub for the label good first issue and read three of them."},
    {"title": "Cloud means renting computers", "tag": "Industry",
     "body": "Instead of buying servers, companies rent them from AWS, Google Cloud or Azure and pay for what they use.",
     "why": "Almost every job post mentions cloud. You only need the basic idea at first.",
     "action": "Create a free account on one provider and just look at the dashboard."},
    {"title": "Soft skills still decide offers", "tag": "Career",
     "body": "Clear communication, asking good questions and finishing what you start matter as much as code.",
     "why": "Two equal candidates: the one who explains well gets the offer.",
     "action": "Explain one thing you learned this week to a friend in 2 minutes."},
]

QUOTES = [
    "Everyone you admire once had no idea what Git was.",
    "Tier 3 is a starting line, not a sentence.",
    "Small commits. Big life.",
    "Your college gets you the interview. Your skills keep you in the room.",
    "Ship it ugly. Fix it loud.",
    "Confusion is just knowledge loading.",
    "One problem a day beats a hundred someday.",
    "You are not behind. You are starting where it counts.",
    "Consistency is the cheat code nobody wants to hear.",
    "Be so good your resume becomes a footnote.",
    "Ask the question. Someone else in the room is also stuck.",
    "Progress is boring on the day and huge in a year.",
]

# XP needed for each level and the title shown on the dashboard
LEVELS = [
    (0, "Day One"), (100, "Curious"), (250, "Learner"), (500, "Builder"),
    (900, "Shipper"), (1400, "Hire-ready"), (2000, "Mentor"),
]
