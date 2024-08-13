# Script with agents that handle fitness and welbeing conversations.

import sqlite3
import os
import pprint
from typing import List
from enum import Enum
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.memory import ChatMemoryBuffer

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Get the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the SQLite database file within the concierge folder
db_path = os.path.join(script_dir, 'fitness_wellness.db')

# Database setup
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute(
    '''CREATE TABLE IF NOT EXISTS workouts (id INTEGER PRIMARY KEY, workout_details TEXT)''')
cursor.execute(
    '''CREATE TABLE IF NOT EXISTS meals (id INTEGER PRIMARY KEY, meal_details TEXT)''')
cursor.execute(
    '''CREATE TABLE IF NOT EXISTS mental_health (id INTEGER PRIMARY KEY, feeling TEXT)''')
cursor.execute(
    '''CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, goal TEXT)''')
conn.commit()


class Speaker(str, Enum):
    TRACK_WORKOUT = "track_workout"
    NUTRITION_GUIDE = "nutrition_guide"
    MENTAL_HEALTH = "mental_health"
    GOAL_SETTING = "goal_setting"
    CONCIERGE = "concierge"
    ORCHESTRATOR = "orchestrator"

# Define the done function for use in each agent


def done(state):
    print("Task is complete")
    state["current_speaker"] = None
    state["just_finished"] = True
    return "done"


# Workout Tracker Agent

def track_workout_agent_factory(state: dict) -> OpenAIAgent:
    def log_workout(workout_details: str) -> str:
        print(f"Logging workout: {workout_details}")
        cursor.execute(
            "INSERT INTO workouts (workout_details) VALUES (?)", (workout_details,))
        conn.commit()
        return f"Workout logged: {workout_details}"

    def view_progress() -> str:
        print("Viewing workout progress")
        cursor.execute("SELECT * FROM workouts ORDER BY id DESC LIMIT 5")
        workouts = cursor.fetchall()
        progress = "\n".join(
            [f"Workout {i+1}: {details}" for i, (id, details) in enumerate(reversed(workouts))])
        return f"Your last 5 workouts:\n{progress}"

    def calculate_streak() -> str:
        cursor.execute("SELECT COUNT(*) FROM workouts")
        workout_count = cursor.fetchone()[0]
        return f"Great job! You've logged {workout_count} workouts. Keep up the streak!"

    tools = [
        FunctionTool.from_defaults(fn=log_workout),
        FunctionTool.from_defaults(fn=view_progress),
        FunctionTool.from_defaults(fn=calculate_streak),
        FunctionTool.from_defaults(fn=done),
    ]

    system_prompt = f"""
    You are a helpful assistant that logs workouts and tracks progress.
    The current user state is:
    {pprint.pformat(state, indent=4)}
    You can log workouts, show recent progress, and calculate the user's workout streak.
    Always offer to calculate the streak after logging a workout.
    If the user asks to do anything unrelated, call the "done" tool.
    """

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(api_key=OPENAI_API_KEY, model="gpt-4"),
        system_prompt=system_prompt,
    )


# Nutrition Guide Agent

def nutrition_guide_agent_factory(state: dict) -> OpenAIAgent:
    def log_meal(meal_details: str) -> str:
        print(f"Logging meal: {meal_details}")
        cursor.execute(
            "INSERT INTO meals (meal_details) VALUES (?)", (meal_details,))
        conn.commit()
        return f"Meal logged: {meal_details}"

    def get_dietary_advice() -> str:
        cursor.execute(
            "SELECT meal_details FROM meals ORDER BY id DESC LIMIT 3")
        recent_meals = cursor.fetchall()
        meals_str = ", ".join([meal[0] for meal in recent_meals])
        return f"Based on your recent meals ({meals_str}), try to incorporate more leafy greens and lean proteins in your next meal. Don't forget to stay hydrated!"

    def calculate_calorie_intake() -> str:
        cursor.execute("SELECT COUNT(*) FROM meals")
        meal_count = cursor.fetchone()[0]
        estimated_calories = meal_count * 500  # Rough estimate
        return f"You've logged {meal_count} meals. Your estimated calorie intake is around {estimated_calories} calories. Remember, this is a rough estimate!"

    tools = [
        FunctionTool.from_defaults(fn=log_meal),
        FunctionTool.from_defaults(fn=get_dietary_advice),
        FunctionTool.from_defaults(fn=calculate_calorie_intake),
        FunctionTool.from_defaults(fn=done),
    ]

    system_prompt = f"""
    You are a helpful assistant providing dietary advice and logging meals.
    The current user state is:
    {pprint.pformat(state, indent=4)}
    You can log meals, provide dietary advice based on recent meals, and estimate calorie intake.
    Always offer to calculate calorie intake after logging a meal.
    If the user asks to do anything unrelated, call the "done" tool.
    """

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(api_key=OPENAI_API_KEY, model="gpt-4"),
        system_prompt=system_prompt,
    )

# Mental Health Agent


def mental_health_agent_factory(state: dict) -> OpenAIAgent:
    def daily_check_in(feeling: str) -> str:
        print(f"Checking in: {feeling}")
        cursor.execute(
            "INSERT INTO mental_health (feeling) VALUES (?)", (feeling,))
        conn.commit()
        return f"Thank you for sharing. You are feeling: {feeling}"

    def suggest_relaxation() -> str:
        return "Try this quick relaxation technique: Take 5 deep breaths, counting to 4 as you inhale and 6 as you exhale. Focus on the sensation of your breath."

    def track_mood_trend() -> str:
        cursor.execute(
            "SELECT feeling FROM mental_health ORDER BY id DESC LIMIT 7")
        recent_feelings = cursor.fetchall()
        feelings_str = ", ".join([feeling[0] for feeling in recent_feelings])
        return f"Your recent mood trend: {feelings_str}. Remember, it's normal for moods to fluctuate. If you're consistently feeling down, consider talking to a professional."

    tools = [
        FunctionTool.from_defaults(fn=daily_check_in),
        FunctionTool.from_defaults(fn=suggest_relaxation),
        FunctionTool.from_defaults(fn=track_mood_trend),
        FunctionTool.from_defaults(fn=done),
    ]

    system_prompt = f"""
    You are a helpful assistant performing daily mental health check-ins and suggesting relaxation techniques.
    The current user state is:
    {pprint.pformat(state, indent=4)}
    You can log daily feelings, suggest relaxation techniques, and track mood trends.
    Always offer to track mood trends after a check-in.
    If the user asks to do anything unrelated, call the "done" tool.
    """

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(api_key=OPENAI_API_KEY, model="gpt-4"),
        system_prompt=system_prompt,
    )

# Goal Setting and Motivation Agent


def goal_setting_agent_factory(state: dict) -> OpenAIAgent:
    def set_goal(goal: str) -> str:
        print(f"Setting goal: {goal}")
        cursor.execute("INSERT INTO goals (goal) VALUES (?)", (goal,))
        conn.commit()
        return f"Goal set: {goal}"

    def provide_motivation() -> str:
        cursor.execute("SELECT goal FROM goals ORDER BY id DESC LIMIT 1")
        latest_goal = cursor.fetchone()
        if latest_goal:
            return f"Remember your goal: {latest_goal[0]}. You've got this! Every small step counts towards your big achievement."
        else:
            return "You're on the right track! Keep pushing forward, and don't forget to set a goal to stay focused."

    def track_goal_progress() -> str:
        cursor.execute("SELECT COUNT(*) FROM goals")
        goal_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workouts")
        workout_count = cursor.fetchone()[0]
        return f"You've set {goal_count} goals and completed {workout_count} workouts. That's amazing progress! Keep up the great work!"

    tools = [
        FunctionTool.from_defaults(fn=set_goal),
        FunctionTool.from_defaults(fn=provide_motivation),
        FunctionTool.from_defaults(fn=track_goal_progress),
        FunctionTool.from_defaults(fn=done),
    ]

    system_prompt = f"""
    You are a helpful assistant for setting personal fitness goals and providing motivation.
    The current user state is:
    {pprint.pformat(state, indent=4)}
    You can set goals, provide motivation based on the latest goal, and track overall goal progress.
    Always offer to track goal progress after setting a new goal.
    If the user asks to do anything unrelated, call the "done" tool.
    """

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(api_key=OPENAI_API_KEY, model="gpt-4"),
        system_prompt=system_prompt,
    )


# Concierge Agent

def concierge_agent_factory(state: dict) -> OpenAIAgent:

    def dummy_tool() -> bool:
        print("Doing nothing.")

    tools = [
        FunctionTool.from_defaults(fn=dummy_tool)
    ]

    system_prompt = (f"""
        You are a helpful assistant that is helping a user navigate their fitness and wellness journey.
        Your job is to ask the user questions to figure out what they want to do, and give them the available things they can do.
        That includes:
        * tracking workouts
        * providing nutrition guidance
        * performing mental health check-ins
        * setting fitness goals and providing motivation

        The current state of the user is:
        {pprint.pformat(state, indent=4)}
    """)

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(api_key=OPENAI_API_KEY, model="gpt-4o"),
        system_prompt=system_prompt,
    )

# Orchestration Agent


def orchestration_agent_factory(state: dict) -> OpenAIAgent:
    tools = []

    system_prompt = (f"""
        You are an orchestration agent.
        Your job is to decide which agent to run based on the current state of the user and what they've asked to do. Agents are identified by short strings.
        What you do is return the name of the agent to run next. You do not do anything else.
        
        The current state of the user is:
        {pprint.pformat(state, indent=4)}

        Look at the chat history and the current state and you MUST return one of these strings identifying an agent to run:
        * "{Speaker.TRACK_WORKOUT.value}" - if the user wants to track a workout
        * "{Speaker.NUTRITION_GUIDE.value}" - if the user wants nutrition guidance
        * "{Speaker.MENTAL_HEALTH.value}" - if the user wants a mental health check-in
        * "{Speaker.GOAL_SETTING.value}" - if the user wants to set a goal or needs motivation
        * "{Speaker.CONCIERGE.value}" - if the user wants to do something else, or hasn't said what they want to do, or you can't figure out what they want to do. Choose this by default.

        Output one of these strings and ONLY these strings, without quotes.
        NEVER respond with anything other than one of the above five strings. DO NOT be helpful or conversational.
    """)

    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(model="gpt-4o", temperature=0.4),
        system_prompt=system_prompt,
    )


def get_initial_state() -> dict:
    return {
        "current_speaker": None,
        "just_finished": False,
    }


def run() -> None:
    state = get_initial_state()
    root_memory = ChatMemoryBuffer.from_defaults(token_limit=8000)
    first_run = True

    while True:
        if first_run:
            user_msg_str = "Hello"
            first_run = False
        else:
            user_msg_str = input("> ").strip()

        current_history = root_memory.get()

        print("Deciding next action...")
        orchestration_response = orchestration_agent_factory(
            state).chat(user_msg_str, chat_history=current_history)
        next_speaker = str(orchestration_response).strip()

        print(f"Selected agent: {next_speaker}")

        if next_speaker == Speaker.TRACK_WORKOUT:
            current_speaker = track_workout_agent_factory(state)
        elif next_speaker == Speaker.NUTRITION_GUIDE:
            current_speaker = nutrition_guide_agent_factory(state)
        elif next_speaker == Speaker.MENTAL_HEALTH:
            current_speaker = mental_health_agent_factory(state)
        elif next_speaker == Speaker.GOAL_SETTING:
            current_speaker = goal_setting_agent_factory(state)
        elif next_speaker == Speaker.CONCIERGE:
            current_speaker = concierge_agent_factory(state)
        else:
            print("Invalid speaker selected. Using concierge agent.")
            current_speaker = concierge_agent_factory(state)

        state["current_speaker"] = next_speaker

        try:
            response = current_speaker.chat(
                user_msg_str, chat_history=current_history)
            print("Bot response:")
            print(response)
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            continue

        new_history = current_speaker.memory.get_all()
        root_memory.set(new_history)

        state["current_speaker"] = None
        # Separator between interactions
        print("---")


if __name__ == "__main__":
    run()
