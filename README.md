# NTHU Course Selecting System

This is a smart course recommendation system specifically designed for Computer Science students at National Tsing Hua University (NTHU). The goal of this project is to help students automatically plan their four-year curriculum based on departmental graduation requirements and individual preferences. It effectively avoids course time conflicts and optimizes the learning path.


## Features

* **Intelligent Scheduling**: Automatically generates recommended course schedules for all eight semesters, from freshman to senior year.
* **High Customization**:

  * Customize the desired number of credits per semester.
  * Include elective courses from other departments such as Mathematics or Physics.
  * Specify professional elective categories (A/B/C/D) that you prefer not to prioritize.
  * Choose a preferred combination of science foundation courses (Physics/Chemistry/Biology).
* **Graduation Requirement Compliance**: The scheduling logic incorporates all CS department graduation requirements, including required courses, professional electives, general education, and language courses.
* **Conflict Avoidance**: Built-in mechanism to detect and prevent time conflicts between courses.
* **Built-in Login System**: Provides a simple login interface to protect system access.
* **Dual-Mode Operation**:

  * Web-based UI using Streamlit for intuitive operation.
  * Command-line interface (CLI) for developers to quickly test and validate results.


## Tech Stack

* **Core Framework**: Python, Streamlit
* **Data Processing**: Pandas, NumPy


## Installation Guide

All required packages are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```


## How to Run

This project is structured as a single-application system, making it very easy to launch.

### Main Usage (Web UI)

1. In your terminal, make sure you are in the project folder and have activated your virtual environment.
2. Run the following command:

   ```bash
   streamlit run app.py
   ```
3. Your browser will automatically open at `http://localhost:8501`.
4. You will first see a login page. After logging in, you can begin using the course recommendation system.
   (Test account: `testuser` / Password: `password123`)

### Developer Test Mode (Command Line Interface)

This mode allows you to execute the course planner directly in the terminal using arguments.

1. Run `cli.py` with any desired parameters. Use `--help` to view all available options.

   ```bash
   # View all available commands
   python cli.py --help

   # Run with default settings
   python cli.py

   # Customize credits per semester
   python cli.py --credits 20 20 18 18 15 15 12 10
   ```


## File Structure

The project uses a separation-of-concerns architecture to ensure clear and maintainable code.

```
├── data/                    # CSV files containing course data
├── app.py                   # Streamlit main application (includes login and UI logic)
├── cli.py                   # Command-line interface script
├── course_logic.py          # Core backend logic (scheduling algorithms)
├── requirements.txt         # Python dependencies list
└── README.md                # This documentation file
```


