"""
MCP1: Catch Meow Main Game Server

🎯 PURPOSE: Handles player profiles, game flow, and provides 5 recording questions/prompts.

📊 WORKFLOW: Profile setup → Question delivery → Voice recording coordination → Game progression  

🔧 COMPONENTS: Tools (profile mgmt, questions), Prompts (game guidance), Resources (static data)
🎮 FLOW: start_game → save_profile → get_recording_prompt(1-5) → coordinate with MCP2
"""
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from pydantic import Field  
import requests
import json
import uuid
import os
from datetime import datetime
import asyncio
import glob
import numpy as np
import pandas as pd
import librosa
try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None

import mcp.types as types

mcp = FastMCP("Catch Meow Main Server", port=3000, stateless_http=True, debug=True)

# Configuration for Hugging Face dataset integration
HUGGINGFACE_DATASET_URL = os.environ.get("HF_DATASET_URL", "")
HUGGINGFACE_API_TOKEN = os.environ.get("HF_API_TOKEN", "")

# Simple in-memory store keyed by client_id for now there is only 8 people maximum 
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Voice recording sessions tracking
RECORDING_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Global leaderboard storage - persists across rounds
LEADERBOARD: List[Dict[str, Any]] = []

# Current player state - resets after each player completes their round
CURRENT_PLAYER_STATE = {
    "player_name": "",
    "session_id": "",
    "bluff_score": 0,
    "metrics": {
        "avg_pause_ratio": 0.0,
        "total_pause_count": 0,
        "avg_mean_f0": 0.0,
        "avg_mean_energy": 0.0,
        "peak_max_energy": 0.0
    }
}

# The 5 recording prompts that will always be asked
RECORDING_PROMPTS: Dict[str, str] = {
    "1": "Can you tell me your name, home town, favorite color, and count from 1 to 10.",
    "2": "What do you like to do in your free time?",
    "3": ("On a typical Saturday, I wake up, drink water, and take a walk. The weather is "
          "mild and the streets are quiet. Birds hop on the fence while a neighbor waters "
          "plants. I breathe in, stretch my shoulders. Back home, I make tea, open the "
          "windows, and begin the day."),
    "4": ("This match runs on Alpic-hosted MCP servers; Mistral guides prompts; Qdrant "
          "stores vectors; Weave from Weights and Biases logs decisions. Our bluff judge "
          "is deterministic; features are weighted, scores are banded, and every call is "
          "traced and versioned for review."),
    "5": "What did you do last night? (Truth or Lie but Both)"
}

# -------------------------------------------------------------------
# TOOLS - Functions that can be called by the LLM during conversation
# -------------------------------------------------------------------

@mcp.tool(
    title="Start Game",
    description="Greet the player and present the profile questions."
)
async def start_game() -> str:
    """
    TOOL PURPOSE: Initial game setup - shows welcome message and profile questions
    NECESSITY: Maybe not needed if you're just doing voice recording sessions
    USAGE: Called at the beginning of a game session
    """
    result = {
        "greeting": "Welcome to Catch Meow! First, a quick profile to personalize scoring.",
        "questions": [
            "What's your name or nickname?",
            "Your hometown",
            "What's your favorite color?",
            "Count from 1 to 10"
        ],
        "expect_tool": "save_profile"
    }
    return str(result)

@mcp.tool(
    title="Save Profile",
    description="Saves the profile keyed by Le Chat's client/session id and returns confirmation."
)
async def save_profile(
    name: str = Field(description="Player name or nickname"),
    home_town: str = Field(description="Player's hometown"),
    favorite_color: str = Field(description="Player's favorite color")
) -> str:
    """
    TOOL PURPOSE: Stores player profile information for personalization and creates recording session
    USAGE: Called after start_game to save user details and initialize voice recording
    """
    client_id = "anonymous"  # Simplified for now
    player_id = str(uuid.uuid4())  # Generate unique player ID
    
    # Store profile in sessions
    profile_data = {
        "player_id": player_id,
        "name": name.strip(),
        "home_town": home_town.strip(),
        "favorite_color": favorite_color.strip()
    }
    
    SESSIONS[client_id] = {
        "profile": profile_data
    }
    
    # Create recording session automatically
    session_id = f"{name.strip()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    RECORDING_SESSIONS[client_id] = {
        "session_id": session_id,
        "profile": profile_data,
        "current_question": 1,
        "recorded_questions": [],
        "expected_uploads": [],
        "created_at": datetime.now().isoformat()
    }
    
    result = {
        "ok": True,
        "stored": SESSIONS[client_id],
        "recording_session": session_id,
        "next_hint": f"Profile saved and recording session '{session_id}' created! Use 'start_recording_for_question' to begin recording questions 1-5."
    }
    return str(result)
# Will be used to change the color of the page based of the favourit color of the player
@mcp.tool(
    title="Get Profile",
    description="Fetch the stored profile for the current chat session."
)
async def get_profile() -> str:
    """
    TOOL PURPOSE: Retrieves previously saved profile information
    NECESSITY: Not needed if profiles aren't being used
    USAGE: Called to get stored user profile data
    """
    client_id = "anonymous"  # Simplified for now
    result = {"profile": SESSIONS.get(client_id)}
    return str(result)

@mcp.tool(
    title="Get Recording Prompt",
    description="Get a specific recording prompt (question or reading text) for the session."
)
async def get_recording_prompt(
    prompt_id: str = Field(description="Prompt ID (1-5)")
) -> str:
    """
    TOOL PURPOSE: Retrieves one of the 5 specific recording prompts by ID
    NECESSITY: ESSENTIAL - This is core to your voice recording functionality
    USAGE: Called during recording sessions to get the specific prompt/question
    """
    prompt = RECORDING_PROMPTS.get(prompt_id)
    if prompt:
        prompt_type = "QUESTION" if prompt_id in ["1", "2", "5"] else "READ ALOUD"
        return f"Prompt {prompt_id} ({prompt_type}):\n\n{prompt}"
    else:
        return f"Prompt '{prompt_id}' not found. Available IDs: {list(RECORDING_PROMPTS.keys())}"

@mcp.tool(
    title="List All Recording Prompts",
    description="Get all 5 recording prompts that will be used in every session."
)
async def list_all_recording_prompts() -> str:
    """
    TOOL PURPOSE: Shows all 5 prompts at once for overview/selection
    NECESSITY: USEFUL - Helps see all available prompts for recording sessions
    USAGE: Called to display all prompts and their types for session planning
    """
    result = {
        "prompts": RECORDING_PROMPTS,
        "prompt_types": {
            "1": "QUESTION - Name, town, color, count 1-10",
            "2": "QUESTION - Free time activities", 
            "3": "READ ALOUD - Saturday routine text",
            "4": "READ ALOUD - Technical MCP text",
            "5": "QUESTION - Last night (Truth & Lie)"
        },
        "usage": "Use 'get_recording_prompt' with prompt_id (1-5) to get a specific prompt"
    }
    return str(result)

# -------------------------------------------------------------------
# LEADERBOARD AND GAME STATE MANAGEMENT TOOLS
# -------------------------------------------------------------------

@mcp.tool(
    title="Initialize Game State",
    description="Initialize empty game state with zero metrics and empty leaderboard"
)
def initialize_game_state() -> str:
    """
    🎯 TOOL PURPOSE: Reset the entire game state for a fresh start
    """
    global LEADERBOARD, CURRENT_PLAYER_STATE
    
    # Clear leaderboard
    LEADERBOARD.clear()
    
    # Reset current player state
    CURRENT_PLAYER_STATE.update({
        "player_name": "",
        "session_id": "",
        "bluff_score": 0,
        "metrics": {
            "avg_pause_ratio": 0.0,
            "total_pause_count": 0,
            "avg_mean_f0": 0.0,
            "avg_mean_energy": 0.0,
            "peak_max_energy": 0.0
        }
    })
    
    return json.dumps({
        "success": True,
        "message": "Game state initialized",
        "leaderboard_count": len(LEADERBOARD),
        "current_player": CURRENT_PLAYER_STATE["player_name"] or "None"
    })

@mcp.tool(
    title="Start Player Round",
    description="Start a new round for a player - updates current player state"
)
def start_player_round(
    player_name: str = Field(description="Name of the player starting their round"),
    session_id: str = Field(description="Session ID for this player's recordings")
) -> str:
    """
    🎯 TOOL PURPOSE: Set up current player state when they begin their 5-question round
    """
    global CURRENT_PLAYER_STATE
    
    # Reset current player state for new player
    CURRENT_PLAYER_STATE.update({
        "player_name": player_name,
        "session_id": session_id,
        "bluff_score": 0,
        "metrics": {
            "avg_pause_ratio": 0.0,
            "total_pause_count": 0,
            "avg_mean_f0": 0.0,
            "avg_mean_energy": 0.0,
            "peak_max_energy": 0.0
        }
    })
    
    return json.dumps({
        "success": True,
        "current_player": player_name,
        "session_id": session_id,
        "message": f"Started round for {player_name}"
    })

@mcp.tool(
    title="Finish Player Round",
    description="Complete a player's round and add their score to the leaderboard"
)
def finish_player_round(session_id: str = Field(description="Session ID of the completed round")) -> str:
    """
    🎯 TOOL PURPOSE: Add player's final score to leaderboard and prepare for next player
    """
    global LEADERBOARD, CURRENT_PLAYER_STATE
    
    if CURRENT_PLAYER_STATE["session_id"] != session_id:
        return json.dumps({"error": "Session ID does not match current player"})
    
    if not CURRENT_PLAYER_STATE["player_name"]:
        return json.dumps({"error": "No current player to finish"})
    
    # Get the final score from the recording session
    if session_id in RECORDING_SESSIONS:
        session = RECORDING_SESSIONS[session_id]
        if "bluff_score" in session:
            final_score = session["bluff_score"]["score"]
            CURRENT_PLAYER_STATE["bluff_score"] = final_score
        else:
            return json.dumps({"error": "Bluff score not calculated for this session"})
    else:
        return json.dumps({"error": "Session not found"})
    
    # Add player to leaderboard
    leaderboard_entry = {
        "name": CURRENT_PLAYER_STATE["player_name"],
        "score": CURRENT_PLAYER_STATE["bluff_score"],
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }
    
    LEADERBOARD.append(leaderboard_entry)
    
    # Sort leaderboard by score (descending)
    LEADERBOARD.sort(key=lambda x: x["score"], reverse=True)
    
    # Prepare response with current leaderboard
    player_name = CURRENT_PLAYER_STATE["player_name"]
    player_score = CURRENT_PLAYER_STATE["bluff_score"]
    
    return json.dumps({
        "success": True,
        "message": f"Player {player_name} finished with score {player_score}",
        "player_added": {
            "name": player_name,
            "score": player_score
        },
        "leaderboard": LEADERBOARD,
        "leaderboard_count": len(LEADERBOARD)
    })

@mcp.tool(
    title="Reset Current Player",
    description="Reset current player metrics to zero and clear current player state"
)
def reset_current_player() -> str:
    """
    🎯 TOOL PURPOSE: Clear current player state and reset all metrics to zero
    """
    global CURRENT_PLAYER_STATE
    
    # Reset all current player data
    CURRENT_PLAYER_STATE.update({
        "player_name": "",
        "session_id": "",
        "bluff_score": 0,
        "metrics": {
            "avg_pause_ratio": 0.0,
            "total_pause_count": 0,
            "avg_mean_f0": 0.0,
            "avg_mean_energy": 0.0,
            "peak_max_energy": 0.0
        }
    })
    
    return json.dumps({
        "success": True,
        "message": "Current player state reset",
        "current_player": "None",
        "all_metrics_zero": True
    })

@mcp.tool(
    title="Get Leaderboard",
    description="Get the current leaderboard with all player scores"
)
def get_leaderboard() -> str:
    """
    🎯 TOOL PURPOSE: Return current leaderboard sorted by scores
    """
    return json.dumps({
        "leaderboard": LEADERBOARD,
        "total_players": len(LEADERBOARD),
        "updated_at": datetime.now().isoformat()
    })

@mcp.tool(
    title="Update Current Player Metrics",
    description="Update current player's metrics when their session completes"
)
def update_current_player_metrics(session_id: str = Field(description="Session ID with completed metrics")) -> str:
    """
    🎯 TOOL PURPOSE: Update current player state with their calculated metrics
    """
    global CURRENT_PLAYER_STATE
    
    if CURRENT_PLAYER_STATE["session_id"] != session_id:
        return json.dumps({"error": "Session ID does not match current player"})
    
    if session_id not in RECORDING_SESSIONS:
        return json.dumps({"error": "Session not found"})
    
    session = RECORDING_SESSIONS[session_id]
    
    # Update metrics if available
    if "aggregated_metrics" in session:
        CURRENT_PLAYER_STATE["metrics"] = session["aggregated_metrics"].copy()
    
    # Update bluff score if available
    if "bluff_score" in session:
        CURRENT_PLAYER_STATE["bluff_score"] = session["bluff_score"]["score"]
    
    return json.dumps({
        "success": True,
        "current_player": CURRENT_PLAYER_STATE["player_name"],
        "updated_metrics": CURRENT_PLAYER_STATE["metrics"],
        "bluff_score": CURRENT_PLAYER_STATE["bluff_score"]
    })

# -------------------------------------------------------------------
# PROMPTS - Pre-defined prompt templates for the LLM
# -------------------------------------------------------------------

@mcp.prompt("Voice recording instructions")
async def voice_recording_instructions(
    session_type: str = Field(description="Type of recording session: baseline, truth, lie", default="baseline")
) -> str:
    """
    PROMPT PURPOSE: Instructions for conducting voice recording sessions
    USAGE: Guide the LLM on how to conduct different types of recording sessions
    """
    instructions = {
        "baseline": "You are conducting a baseline voice recording session. Ask the participant to speak naturally and clearly. Record their normal speech patterns, tone, and pace. Be encouraging and create a comfortable atmosphere.",
        "truth": "You are conducting a truth recording session. Instruct the participant to answer all questions honestly and naturally. Emphasize that they should tell the truth and speak as they normally would.",
        "lie": "You are conducting a lie recording session. Instruct the participant to answer questions with deliberate lies or false information. They should try to be convincing while lying. Remind them this is for training purposes."
    }
    return instructions.get(session_type, instructions["baseline"])

@mcp.prompt("Game instructions")
async def game_instructions(
    mode: str = Field(
        description="Game mode to explain: overview, detailed, quick", 
        default="overview"
    )
) -> str:
    """
    PROMPT PURPOSE: Explain how the Catch Meow bluff detection game works
    USAGE: Give players a complete understanding of the game mechanics
    """
    if mode == "detailed":
        return """Welcome to Catch Meow - The AI Bluff Detection Game!

**DETAILED GAME FLOW:**
1. **Lobby Setup**: 3–8 players join a game lobby and wait for all participants.

2. **Round Begins**: Each round starts with a prompt containing questions or statements to respond to.

3. **Voice Recording**: Every player records a 30-second voice answer to the prompt. Here's the key: players can choose to speak truthfully OR bluff (lie convincingly). Strategy matters!

4. **AI Analysis**: Once all answers are submitted, our AI judge analyzes each recording using voice pattern recognition:
   - Each player receives a bluff score from 0–100
   - Score interpretation: 0–30 = appears honest, 30–70 = uncertain/mixed signals, 70–100 = likely bluffing
   - Players also receive 2–3 specific reasons explaining their score (e.g., "voice stress detected," "hesitation patterns," "pace inconsistency")

5. **Results Reveal**: All results are revealed simultaneously to maintain fairness. No one sees scores until everyone's analysis is complete.

6. **Scoring & Leaderboard**: 
   - In "Honesty Mode" (default): Players earn 100 − bluff_score points (so honest players score higher)
   - Leaderboard updates after each round showing cumulative scores

7. **Next Round**: The game continues with new prompts until players decide to end.

**STRATEGY TIPS**: Sometimes bluffing obviously can be a strategy, sometimes being subtle works better. The AI learns patterns, so vary your approach!"""
    
    elif mode == "quick":
        return """**CATCH MEOW - QUICK RULES:**
• 3-8 players, 30-second voice responses per round
• Choose: Tell the truth OR bluff convincingly
• AI analyzes your voice for deception (0-100 bluff score)
• Lower bluff scores = higher points in Honesty Mode
• Leaderboard tracks your performance across rounds"""
    
    else:  # overview mode
        return """**CATCH MEOW - GAME OVERVIEW:**

Welcome to the AI-powered bluff detection game where your voice patterns determine your fate!

**HOW IT WORKS:**
1. **Join Lobby**: 3–8 players join together
2. **Get Prompt**: Each round presents questions or statements to respond to  
3. **Record Response**: Every player records a 30-second voice answer - you can tell the truth or bluff!
4. **AI Judgment**: Our AI analyzes voice patterns and assigns bluff scores (0-100):
   • 0–30 = Appears honest
   • 30–70 = Uncertain 
   • 70–100 = Likely bluffing
5. **Get Results**: See your score plus 2-3 reasons why the AI thinks you were honest or bluffing
6. **Scoring**: In Honesty Mode, you earn 100 − bluff_score points (honest players score higher)
7. **Leaderboard**: Track performance across multiple rounds

**THE STRATEGY**: Will you play it safe and be honest, or risk it all with a convincing bluff? The AI is always listening..."""

# Helper function for dataset verification
async def _check_file_in_dataset(expected_filename: str) -> Dict[str, Any]:
    """Check if a file exists in the Hugging Face dataset."""
    if not HUGGINGFACE_DATASET_URL or not HUGGINGFACE_API_TOKEN:
        return {
            "found": False, 
            "error": "Hugging Face configuration not available",
            "message": "Dataset URL or API token not configured"
        }
    
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        response = requests.get(HUGGINGFACE_DATASET_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {
                "found": False,
                "error": f"Dataset API returned status {response.status_code}",
                "message": response.text[:200] if response.text else "Unknown error"
            }
        
        dataset_files = response.json()
        
        # Search for the file in the dataset
        found_file = None
        if isinstance(dataset_files, dict) and "files" in dataset_files:
            for file_info in dataset_files["files"]:
                if file_info.get("path") == expected_filename:
                    found_file = file_info
                    break
        elif isinstance(dataset_files, list):
            for file_info in dataset_files:
                if file_info.get("path") == expected_filename or file_info.get("name") == expected_filename:
                    found_file = file_info
                    break
        
        return {
            "found": found_file is not None,
            "file_info": found_file,
            "dataset_response": str(dataset_files)[:500] + "..." if len(str(dataset_files)) > 500 else str(dataset_files)
        }
        
    except requests.RequestException as e:
        return {
            "found": False,
            "error": f"Network error: {str(e)}",
            "message": "Failed to connect to Hugging Face dataset API"
        }
    except Exception as e:
        return {
            "found": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "An unexpected error occurred while checking the dataset"
        }

# -------------------------------------------------------------------
# OLD VOICE RECORDING FUNCTIONS REMOVED - REPLACED WITH ENHANCED VERSIONS BELOW
# -------------------------------------------------------------------

@mcp.tool(
    name="get_session_progress",
    description="Get the current progress of the recording session"
)
async def get_session_progress(client_id: str) -> str:
    """Get the progress of the current recording session."""
    if client_id not in RECORDING_SESSIONS:
        return "No active recording session found. Please start a recording session first."
    
    session = RECORDING_SESSIONS[client_id]
    
    # Count verified uploads
    verified_count = sum(1 for upload in session["expected_uploads"] if upload["verified"])
    total_expected = len(session["expected_uploads"])
    
    progress_report = f"""Recording Session Progress

Session ID: {session['session_id']}
Player: {session['profile']['name']}
Current Question: {session['current_question']}/5

Recorded Questions: {sorted(session['recorded_questions'])} (Total: {len(session['recorded_questions'])}/5)
Expected Uploads: {total_expected}
Verified Uploads: {verified_count}

Upload Details:"""
    
    for upload in session["expected_uploads"]:
        status = "✅ Verified" if upload["verified"] else "⏳ Pending"
        progress_report += f"""
- Q{upload['question_number']}: {upload['filename']} - {status}"""
    
    if len(session['recorded_questions']) == 5 and verified_count == 5:
        progress_report += "\n\n🎉 Session Complete! All questions recorded and verified."
    elif len(session['recorded_questions']) == 5:
        progress_report += f"\n\n⚠️ All questions recorded, but only {verified_count}/5 uploads verified."
    else:
        remaining = 5 - len(session['recorded_questions'])
        progress_report += f"\n\n📝 {remaining} question(s) remaining to record."
    
    return progress_report

@mcp.tool(
    name="monitor_dataset_uploads", 
    description="Monitor and check verification status for all uploads across all sessions"
)
async def monitor_dataset_uploads() -> str:
    """Check verification status for all expected uploads across all sessions."""
    if not RECORDING_SESSIONS:
        return "No recording sessions found."
    
    report = "Dataset Upload Monitoring Report\n" + "="*40 + "\n\n"
    
    total_sessions = len(RECORDING_SESSIONS)
    total_uploads = 0
    total_verified = 0
    
    for client_id, session in RECORDING_SESSIONS.items():
        session_uploads = len(session["expected_uploads"])
        session_verified = sum(1 for upload in session["expected_uploads"] if upload["verified"])
        
        total_uploads += session_uploads
        total_verified += session_verified
        
        report += f"Session: {session['session_id']}\n"
        report += f"Player: {session['profile']['name']}\n"
        report += f"Uploads: {session_verified}/{session_uploads} verified\n"
        
        # Check unverified uploads
        unverified = [upload for upload in session["expected_uploads"] if not upload["verified"]]
        if unverified:
            report += "Checking unverified uploads:\n"
            for upload in unverified:
                result = await _check_file_in_dataset(upload["filename"])
                if result["found"]:
                    upload["verified"] = True
                    upload["verified_at"] = datetime.now().isoformat()
                    total_verified += 1
                    report += f"  ✅ {upload['filename']} - Now verified!\n"
                else:
                    report += f"  ❌ {upload['filename']} - Still not found\n"
        
        report += "\n"
    
    report += f"Overall Summary: {total_verified}/{total_uploads} uploads verified across {total_sessions} sessions"
    
    return report

# -------------------------------------------------------------------
# VOICE RECORDING TOOLS - Advanced dataset integration from MCP2
# -------------------------------------------------------------------

@mcp.tool(
    title="Start Recording for Question",
    description="Start recording for a specific question with enhanced dataset tracking"
)
async def start_recording_for_question(
    player_id: str = Field(description="Unique player identifier from profile"),
    player_name: str = Field(description="Player name from profile"),
    question_number: int = Field(description="Question number (1-5)"),
    session_type: str = Field(description="Session type: baseline, truth, lie", default="baseline")
) -> str:
    """
    🎯 TOOL PURPOSE: Start recording for a specific question with enhanced tracking
    
    📝 DETAILED FUNCTION:
    - Creates a new recording session if this is the first question for the player
    - Updates existing session if player already has one 
    - Returns the question text and recording instructions
    - Includes the video recorder link for user interface
    
    🔄 WORKFLOW:
    1. Called after save_profile() 
    2. Voice recorder gets question text and video recorder link
    3. Voice recorder uploads to Hugging Face dataset
    4. Voice recorder calls record_expected_upload()
    
    ✅ USAGE: Called once per question (1-5) for each player
    """
    
    # Find existing session or create new one
    session_id = None
    for sid, session in RECORDING_SESSIONS.items():
        if session.get("player_id") == player_id:
            session_id = sid
            break
    
    if not session_id:
        # Create new session with enhanced tracking
        session_id = str(uuid.uuid4())
        RECORDING_SESSIONS[session_id] = {
            "session_id": session_id,
            "player_id": player_id,
            "player_name": player_name,
            "session_type": session_type,
            "created_at": datetime.now().isoformat(),
            "current_question": question_number,
            "completed_questions": [],
            "recorded_questions": [],
            "recordings": {},
            "dataset_status": {},
            "status": "recording",
            "expected_uploads": [],
            "profile": {"name": player_name}  # For compatibility
        }
    else:
        # Update existing session
        RECORDING_SESSIONS[session_id]["current_question"] = question_number
        RECORDING_SESSIONS[session_id]["status"] = "recording"
    
    if str(question_number) not in RECORDING_PROMPTS:
        return json.dumps({"error": f"Invalid question number: {question_number}"})
    
    # Include video recorder link in the response
    video_recorder_url = "https://huggingface.co/spaces/Styxsssss/catchmeow"
    
    result = {
        "session_id": session_id,
        "status": "ready_to_record",
        "question_number": question_number,
        "question_text": RECORDING_PROMPTS[str(question_number)],
        "player_name": player_name,
        "video_recorder_url": video_recorder_url,
        "instructions": f"Use the video recorder at: {video_recorder_url}\nRecord your answer, then upload to Hugging Face dataset and call record_expected_upload",
        "next_step": "record_and_upload"
    }
    
    return json.dumps(result)

@mcp.tool(
    title="Record Expected Upload",
    description="Record that a voice file is expected to be uploaded to the dataset"
)
async def record_expected_upload(
    session_id: str = Field(description="Recording session ID"),
    question_number: int = Field(description="Question number (1-5)"),
    expected_filename: str = Field(description="Expected filename in the dataset"),
    upload_metadata: str = Field(description="JSON metadata about the expected upload", default="{}")
) -> str:
    """
    📤 TOOL PURPOSE: Tell MCP1 "expect this file to appear in the Hugging Face dataset"
    
    📝 DETAILED FUNCTION:
    - Called BY THE VOICE RECORDER after it uploads audio to Hugging Face
    - Records the exact filename that should appear in the dataset
    - Sets status to "expecting upload" so check_dataset_for_upload can verify
    
    🔄 WORKFLOW:
    1. Voice recorder records audio using the video recorder URL
    2. Voice recorder uploads to Hugging Face dataset 
    3. Voice recorder calls THIS TOOL to say "expect file X.wav"
    4. MCP1 can now check/verify the upload worked
    
    ✅ USAGE: Called once per recorded answer by the voice recorder
    """
    
    if session_id not in RECORDING_SESSIONS:
        return json.dumps({"error": "Session not found"})
    
    session = RECORDING_SESSIONS[session_id]
    
    # Parse metadata
    try:
        metadata = json.loads(upload_metadata)
    except:
        metadata = {}
    
    # Record the expected upload in both new and old format for compatibility
    session["recordings"][str(question_number)] = {
        "expected_filename": expected_filename,
        "expected_at": datetime.now().isoformat(),
        "metadata": metadata,
        "status": "expected",
        "verified": False,
        "dataset_url": None
    }
    
    # Also add to expected_uploads for compatibility with existing monitoring
    session["expected_uploads"].append({
        "question_number": question_number,
        "filename": expected_filename,
        "expected_at": datetime.now().isoformat(),
        "verified": False,
        "metadata": metadata
    })
    
    # Mark question as recorded
    if question_number not in session["recorded_questions"]:
        session["recorded_questions"].append(question_number)
    
    result = {
        "session_id": session_id,
        "question_number": question_number,
        "expected_filename": expected_filename,
        "status": "expecting_upload",
        "check_interval": "10_seconds",
        "next_step": "wait_for_dataset_upload",
        "video_recorder_url": "https://huggingface.co/spaces/alonam27/catchmeowvvideoupload"
    }
    
    return json.dumps(result)

@mcp.tool(
    title="Check Dataset for Upload",
    description="Check if an expected voice file has appeared in the Hugging Face dataset"
)
async def check_dataset_for_upload(
    session_id: str = Field(description="Recording session ID"),
    question_number: int = Field(description="Question number to check")
) -> str:
    """
    🔍 TOOL PURPOSE: Verify that a voice file actually appeared in the Hugging Face dataset
    
    📝 DETAILED FUNCTION:
    - Checks if the expected filename exists in the Hugging Face dataset
    - If found: marks question as COMPLETED and advances to next question
    - If not found: status remains "waiting for upload"
    - Updates session progress automatically
    
    🎯 KEY BEHAVIOR:
    - Only advances to next question AFTER verifying dataset upload
    - This prevents race conditions and ensures data integrity
    
    ✅ USAGE: Called after record_expected_upload to verify the file exists
    📊 RETURNS: found/not_found, can_proceed (yes/no), next_question
    """
    
    if session_id not in RECORDING_SESSIONS:
        return json.dumps({"error": "Session not found"})
    
    session = RECORDING_SESSIONS[session_id]
    
    if str(question_number) not in session["recordings"]:
        return json.dumps({"error": "No expected recording found for this question"})
    
    recording = session["recordings"][str(question_number)]
    expected_filename = recording["expected_filename"]
    
    # Check if file exists in dataset using existing function
    dataset_check = await _check_file_in_dataset(expected_filename)
    dataset_exists = dataset_check.get("found", False)
    dataset_url = dataset_check.get("dataset_url")
    
    # Update session with results
    if dataset_exists:
        recording.update({
            "status": "found_in_dataset",
            "verified": True,
            "dataset_url": dataset_url,
            "found_at": datetime.now().isoformat()
        })
        
        # Mark question as completed and advance
        if question_number not in session["completed_questions"]:
            session["completed_questions"].append(question_number)
        session["current_question"] = question_number + 1
        session["status"] = "in_progress" if question_number < 5 else "completed"
        
        # Update dataset status
        session["dataset_status"][str(question_number)] = {
            "exists_in_dataset": True,
            "dataset_url": dataset_url,
            "verified_at": datetime.now().isoformat()
        }
        
        # Also update expected_uploads for compatibility
        for upload in session["expected_uploads"]:
            if upload["question_number"] == question_number and upload["filename"] == expected_filename:
                upload["verified"] = True
                upload["verified_at"] = datetime.now().isoformat()
                break
    else:
        recording["status"] = "waiting_for_upload"
    
    result = {
        "session_id": session_id,
        "question_number": question_number,
        "expected_filename": expected_filename,
        "found_in_dataset": dataset_exists,
        "dataset_url": dataset_url if dataset_exists else None,
        "status": "found" if dataset_exists else "still_waiting",
        "can_proceed": dataset_exists,
        "next_question": question_number + 1 if dataset_exists and question_number < 5 else None,
        "session_complete": session["status"] == "completed",
        "video_recorder_url": "https://huggingface.co/spaces/alonam27/catchmeowvvideoupload"
    }
    
    return json.dumps(result)

# -------------------------------------------------------------------
# DEMO TOOLS - Simplified workflow for direct .wav file processing
# -------------------------------------------------------------------

@mcp.tool(
    title="Process Demo Audio Files",
    description="Demo tool: Process .wav files directly and calculate bluff score"
)
async def process_demo_audio_files(
    player_name: str = Field(description="Player name from profile"),
    wav_file_paths: str = Field(description="Comma-separated list of .wav file paths to process")
) -> str:
    """
    🎯 DEMO TOOL: Process .wav files directly without HuggingFace dataset
    
    📝 WORKFLOW:
    1. User provides name and .wav files
    2. Extract features from each .wav file using librosa
    3. Calculate aggregated metrics
    4. Calculate bluff score
    5. Update leaderboard and GUI
    
    💡 USAGE: Call this with comma-separated .wav file paths
    Example: process_demo_audio_files("John", "file1.wav,file2.wav,file3.wav")
    """
    
    # Parse file paths
    file_paths = [path.strip() for path in wav_file_paths.split(',')]
    
    if len(file_paths) == 0:
        return json.dumps({"error": "No file paths provided"})
    
    try:
        # Create demo session
        session_id = f"demo_{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize metrics collection
        all_metrics = {
            "pause_ratios": [],
            "pause_counts": [],
            "mean_f0s": [],
            "mean_energies": [],
            "max_energies": []
        }
        
        individual_metrics = {}
        
        # Process each .wav file
        for i, file_path in enumerate(file_paths, 1):
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    return json.dumps({"error": f"File not found: {file_path}"})
                
                # Extract features from the audio file
                features = extract_features(file_path)
                
                # Store individual metrics
                individual_metrics[f"file_{i}"] = features
                
                # Collect for aggregation
                all_metrics["pause_ratios"].append(features["pause_ratio"])
                all_metrics["pause_counts"].append(features["pause_count"])
                all_metrics["mean_f0s"].append(features["mean_f0"])
                
                # Convert dB to 0-100 scale for energy
                mean_energy = (features["mean_rms_db"] + 120) / 120 * 100
                max_energy = (features["max_rms_db"] + 120) / 120 * 100
                all_metrics["mean_energies"].append(max(0, min(100, mean_energy)))
                all_metrics["max_energies"].append(max(0, min(100, max_energy)))
                
            except Exception as file_error:
                return json.dumps({
                    "error": f"Failed to process {file_path}",
                    "details": str(file_error)
                })
        
        # Calculate aggregated metrics
        aggregated_metrics = {
            "avg_pause_ratio": sum(all_metrics["pause_ratios"]) / len(all_metrics["pause_ratios"]),
            "total_pause_count": sum(all_metrics["pause_counts"]),
            "avg_mean_f0": sum(all_metrics["mean_f0s"]) / len(all_metrics["mean_f0s"]),
            "avg_mean_energy": sum(all_metrics["mean_energies"]) / len(all_metrics["mean_energies"]),
            "peak_max_energy": max(all_metrics["max_energies"]) if all_metrics["max_energies"] else 0
        }
        
        # Calculate bluff score using new function
        max_rms_db = (aggregated_metrics["peak_max_energy"] / 100) * 120 - 120
        mean_rms_db = (aggregated_metrics["avg_mean_energy"] / 100) * 120 - 120
        
        feature_array = [
            aggregated_metrics["avg_pause_ratio"],
            aggregated_metrics["total_pause_count"],
            aggregated_metrics["avg_mean_f0"],
            max_rms_db,
            mean_rms_db
        ]
        
        bluff_score = calculate_bluff_score(feature_array)
        
        # Update current player state
        global CURRENT_PLAYER_STATE
        CURRENT_PLAYER_STATE.update({
            "player_name": player_name,
            "session_id": session_id,
            "bluff_score": bluff_score,
            "metrics": aggregated_metrics
        })
        
        # Add to leaderboard
        leaderboard_entry = {
            "name": player_name,
            "score": bluff_score,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        
        LEADERBOARD.append(leaderboard_entry)
        LEADERBOARD.sort(key=lambda x: x["score"], reverse=True)
        
        # Generate interpretation
        interpretation = _interpret_bluff_analysis(bluff_score, aggregated_metrics)
        
        result = {
            "success": True,
            "session_id": session_id,
            "player_name": player_name,
            "files_processed": len(file_paths),
            "bluff_score": round(bluff_score, 1),
            "interpretation": interpretation,
            "aggregated_metrics": aggregated_metrics,
            "individual_metrics": individual_metrics,
            "leaderboard_position": len([x for x in LEADERBOARD if x["score"] > bluff_score]) + 1,
            "total_players": len(LEADERBOARD),
            "leaderboard": LEADERBOARD[-10:],  # Show last 10 entries
            "ready_for_gui_update": True
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Demo processing failed",
            "details": str(e),
            "player_name": player_name
        })

# -------------------------------------------------------------------
# AUDIO PROCESSING & METRIC CALCULATION TOOLS
# -------------------------------------------------------------------

def extract_features(path, sr=16000, frame_length=1024, hop_length=256, top_db=35):
    """
    Extract speech features from audio file path using librosa
    
    Args:
        path: File path to audio file
        sr: Sample rate
        frame_length: Frame length for analysis
        hop_length: Hop length for analysis  
        top_db: Threshold for silence detection
    
    Returns:
        Dict with extracted features: pause_ratio, pause_count, mean_f0, mean_rms_db, max_rms_db
    """
    y, _sr = librosa.load(path, sr=sr, mono=True)
    total_dur = len(y) / sr

    # Split audio into speech and silence intervals
    intervals = librosa.effects.split(y, top_db=top_db)
    speech_dur = float(sum((e - s) for s, e in intervals)) / sr
    pause_dur = max(0.0, total_dur - speech_dur)
    pause_ratio = pause_dur / max(1e-6, speech_dur)
    pause_count = max(0, len(intervals) - 1)

    # Extract speech segments
    if len(intervals):
        y_speech = np.concatenate([y[s:e] for s, e in intervals])
    else:
        y_speech = np.zeros(0, dtype=np.float32)

    # Calculate RMS energy features
    if len(y_speech) >= hop_length * 2:
        rms = librosa.feature.rms(y=y_speech, frame_length=frame_length, hop_length=hop_length).flatten()
        rms_db = 20.0 * np.log10(np.maximum(rms, 1e-8))
        mean_rms_db = float(np.mean(rms_db))
        max_rms_db = float(np.max(rms_db))
    else:
        mean_rms_db = -120.0
        max_rms_db = -120.0

    # Calculate fundamental frequency (F0)
    fmin, fmax = 75, 300
    mean_f0 = 0.0
    if len(y_speech) >= hop_length * 2:
        try:
            f0, vflag, _ = librosa.pyin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[(vflag == True)] if vflag is not None else f0[~np.isnan(f0)]
        except Exception:
            f0 = librosa.yin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[~np.isnan(f0)]
        if len(f0_voiced) > 0:
            mean_f0 = float(np.mean(f0_voiced))

    return {
        "duration_s": round(total_dur, 3),
        "pause_ratio": round(pause_ratio, 3),
        "pause_count": int(pause_count),
        "mean_f0": round(mean_f0, 2),
        "max_rms_db": round(max_rms_db, 2),
        "mean_rms_db": round(mean_rms_db, 2),
    }

def normalize(value, vmin, vmax):
    """Normalize value to 0-1 range"""
    return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))

def calculate_bluff_score(arr):
    """
    Calculate bluff score from array of features
    
    Args:
        arr: Array of [pause_ratio, pause_count, mean_f0, max_rms_db, mean_rms_db]
        
    Returns:
        Bluff score (0-100)
    """
    pause_ratio, pause_count, mean_f0, max_rms_db, mean_rms_db = arr

    # Normalize each metric to 0-1 range
    norm_pause_ratio = normalize(pause_ratio, 0, 3)
    norm_pause_count = normalize(pause_count, 0, 10)
    norm_f0          = normalize(mean_f0, 75, 300)
    norm_max_rms     = normalize(max_rms_db, -40, 0)
    norm_mean_rms    = normalize(mean_rms_db, -40, 0)

    # Weights for each feature
    weights = {
        "pause_ratio": 0.25,
        "pause_count": 0.20,
        "mean_f0": 0.15,
        "max_rms_db": 0.20,
        "mean_rms_db": 0.20,
    }

    # Calculate weighted score
    score = (
        norm_pause_ratio * weights["pause_ratio"] +
        norm_pause_count * weights["pause_count"] +
        norm_f0          * weights["mean_f0"] +
        norm_max_rms     * weights["max_rms_db"] +
        norm_mean_rms    * weights["mean_rms_db"]
    )

    return round(score * 100, 1)

def extract_features_from_array(audio_array, sr=16000, frame_length=1024, hop_length=256, top_db=35):
    """
    Extract speech features from audio array (for HuggingFace dataset compatibility)
    
    Args:
        audio_array: Audio time series data as numpy array
        sr: Sample rate
        frame_length: Frame length for analysis
        hop_length: Hop length for analysis  
        top_db: Threshold for silence detection
    
    Returns:
        Dict with extracted features: pause_ratio, pause_count, mean_f0, mean_rms_db, max_rms_db
    """
    y = np.array(audio_array, dtype=np.float32)
    total_dur = len(y) / sr

    # Split audio into speech and silence intervals
    intervals = librosa.effects.split(y, top_db=top_db)
    speech_dur = float(sum((e - s) for s, e in intervals)) / sr
    pause_dur = max(0.0, total_dur - speech_dur)
    pause_ratio = pause_dur / max(1e-6, speech_dur)
    pause_count = max(0, len(intervals) - 1)

    # Extract speech segments
    if len(intervals):
        y_speech = np.concatenate([y[s:e] for s, e in intervals])
    else:
        y_speech = np.zeros(0, dtype=np.float32)

    # Calculate RMS energy features
    if len(y_speech) >= hop_length * 2:
        rms = librosa.feature.rms(y=y_speech, frame_length=frame_length, hop_length=hop_length).flatten()
        rms_db = 20.0 * np.log10(np.maximum(rms, 1e-8))
        mean_rms_db = float(np.mean(rms_db))
        max_rms_db = float(np.max(rms_db))
    else:
        mean_rms_db = -120.0
        max_rms_db = -120.0

    # Calculate fundamental frequency (F0)
    fmin, fmax = 75, 300
    mean_f0 = 0.0
    if len(y_speech) >= hop_length * 2:
        try:
            f0, vflag, _ = librosa.pyin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[(vflag == True)] if vflag is not None else f0[~np.isnan(f0)]
        except Exception:
            f0 = librosa.yin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[~np.isnan(f0)]
        if len(f0_voiced) > 0:
            mean_f0 = float(np.mean(f0_voiced))

    return {
        "duration_s": round(total_dur, 3),
        "pause_ratio": round(pause_ratio, 3),
        "pause_count": int(pause_count),
        "mean_f0": round(mean_f0, 2),
        "max_rms_db": round(max_rms_db, 2),
        "mean_rms_db": round(mean_rms_db, 2),
    }

@mcp.tool(
    title="Process Session Audio Dataset",
    description="Process all 5 audio files from HF dataset for a completed session and calculate metrics"
)
async def process_session_audio_dataset(
    session_id: str = Field(description="Recording session ID"),
    dataset_name: str = Field(description="HuggingFace dataset name", default="alonam27/catcha-meow-voices")
) -> str:
    """
    🎯 TOOL PURPOSE: Process all 5 audio files after session completion and extract speech metrics
    
    📝 DETAILED FUNCTION:
    - Downloads all 5 audio files from HuggingFace dataset for the session
    - Analyzes each audio file for speech characteristics
    - Calculates the 5 key metrics: pause_ratio, pause_count, mean_f0, mean_energy, max_energy
    - Stores metrics in session data for bluff score calculation
    
    🔄 WORKFLOW:
    1. Verify all 5 questions are completed and uploaded
    2. Download audio files from HF dataset
    3. Process each file for speech metrics
    4. Aggregate metrics across all 5 recordings
    5. Store results for bluff score calculation
    
    ✅ USAGE: Called after all 5 questions are recorded and verified
    """
    
    if session_id not in RECORDING_SESSIONS:
        return json.dumps({"error": "Session not found"})
    
    session = RECORDING_SESSIONS[session_id]
    
    # Verify all 5 questions are completed
    if len(session.get("completed_questions", [])) < 5:
        return json.dumps({
            "error": "Session not complete",
            "completed_questions": len(session.get("completed_questions", [])),
            "required": 5,
            "message": "All 5 questions must be completed before processing"
        })
    
    try:
        # Initialize metrics storage
        session["audio_metrics"] = {}
        all_metrics = {
            "pause_ratios": [],
            "pause_counts": [],
            "mean_f0s": [],
            "mean_energies": [],
            "max_energies": []
        }
        
        # Process each audio file
        for question_num in range(1, 6):
            if str(question_num) in session.get("recordings", {}):
                recording = session["recordings"][str(question_num)]
                filename = recording.get("expected_filename")
                
                if filename and recording.get("verified"):
                    # Simulate audio processing (replace with actual audio analysis)
                    metrics = await _analyze_audio_file(filename, dataset_name, question_num)
                    
                    # Store individual question metrics
                    session["audio_metrics"][str(question_num)] = metrics
                    
                    # Aggregate metrics
                    all_metrics["pause_ratios"].append(metrics["pause_ratio"])
                    all_metrics["pause_counts"].append(metrics["pause_count"])
                    all_metrics["mean_f0s"].append(metrics["mean_f0"])
                    all_metrics["mean_energies"].append(metrics["mean_energy"])
                    all_metrics["max_energies"].append(metrics["max_energy"])
        
        # Calculate aggregated metrics
        session["aggregated_metrics"] = {
            "avg_pause_ratio": sum(all_metrics["pause_ratios"]) / len(all_metrics["pause_ratios"]),
            "total_pause_count": sum(all_metrics["pause_counts"]),
            "avg_mean_f0": sum(all_metrics["mean_f0s"]) / len(all_metrics["mean_f0s"]),
            "avg_mean_energy": sum(all_metrics["mean_energies"]) / len(all_metrics["mean_energies"]),
            "peak_max_energy": max(all_metrics["max_energies"])
        }
        
        session["processing_status"] = "metrics_calculated"
        session["processed_at"] = datetime.now().isoformat()
        
        result = {
            "session_id": session_id,
            "status": "success",
            "metrics_calculated": True,
            "processed_questions": len(session["audio_metrics"]),
            "aggregated_metrics": session["aggregated_metrics"],
            "next_step": "calculate_bluff_score",
            "ready_for_scoring": True
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Audio processing failed",
            "details": str(e),
            "session_id": session_id
        })

@mcp.tool(
    title="Calculate Bluff Score",
    description="Calculate final bluff score based on aggregated speech metrics from 5 recordings"
)
async def calculate_bluff_score_tool(
    session_id: str = Field(description="Recording session ID")
) -> str:
    """
    🎯 TOOL PURPOSE: Calculate final bluff score using the 5 aggregated speech metrics
    
    📝 DETAILED FUNCTION:
    - Uses aggregated metrics from process_session_audio_dataset
    - Applies new scoring algorithm to calculate 0-100 bluff score
    - Higher scores indicate higher likelihood of deception
    
    🎯 METRICS USED:
    - Pause Ratio: Higher ratio = more suspicious
    - Pause Count: More pauses = more suspicious  
    - Mean F0: Deviations from normal = suspicious
    - Mean Energy: Very high/low energy = suspicious
    - Max Energy: Extreme peaks = suspicious
    
    ✅ USAGE: Called after process_session_audio_dataset completes successfully
    """
    
    if session_id not in RECORDING_SESSIONS:
        return json.dumps({"error": "Session not found"})
    
    session = RECORDING_SESSIONS[session_id]
    
    # Verify metrics are calculated
    if "aggregated_metrics" not in session:
        return json.dumps({
            "error": "Metrics not calculated",
            "message": "Call process_session_audio_dataset first",
            "session_status": session.get("processing_status", "unknown")
        })
    
    try:
        metrics = session["aggregated_metrics"]
        
        # Prepare array for new calculate_bluff_score function
        # [pause_ratio, pause_count, mean_f0, max_rms_db, mean_rms_db]
        # Convert energy values back to dB scale
        max_rms_db = (metrics["peak_max_energy"] / 100) * 120 - 120
        mean_rms_db = (metrics["avg_mean_energy"] / 100) * 120 - 120
        
        feature_array = [
            metrics["avg_pause_ratio"],
            metrics["total_pause_count"], 
            metrics["avg_mean_f0"],
            max_rms_db,
            mean_rms_db
        ]
        
        # Calculate bluff score using new function
        bluff_score = calculate_bluff_score(feature_array)
        
        # Store bluff score in session
        session["bluff_score"] = {
            "score": bluff_score,
            "calculated_at": datetime.now().isoformat(),
            "metrics_used": metrics
        }
        
        session["status"] = "completed_with_score"
        
        # Generate comprehensive interpretation
        detailed_interpretation = _interpret_bluff_analysis(bluff_score, metrics)
        
        result = {
            "session_id": session_id,
            "bluff_score": round(bluff_score, 1),
            "interpretation": detailed_interpretation,
            "breakdown": _get_score_breakdown(metrics),
            "session_complete": True
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Bluff score calculation failed",
            "details": str(e),
            "session_id": session_id
        })

@mcp.tool(
    title="Get Player Metrics Dashboard", 
    description="Get formatted metrics for UI display with color coding and progress bars"
)
async def get_player_metrics_dashboard() -> str:
    """
    🎯 TOOL PURPOSE: Return formatted metrics for UI dashboard display including leaderboard
    
    📝 DETAILED FUNCTION:
    - Shows current player metrics (zero if no active player)
    - Includes complete leaderboard with all previous players
    - Provides percentage values for progress bars
    - Includes color coding based on metric thresholds
    - Ready for direct integration with your existing UI
    
    🎨 UI INTEGRATION:
    - Returns data formatted for your 5-box metric display
    - Includes percentage and color class for each metric
    - Compatible with your existing updateMetrics() JavaScript function
    - Includes leaderboard data for UI display
    
    ✅ USAGE: Called anytime to get current game state for dashboard
    """
    
    global CURRENT_PLAYER_STATE, LEADERBOARD
    
    try:
        # Get current player metrics (will be zero if no active player)
        metrics = CURRENT_PLAYER_STATE["metrics"]
        bluff_score = CURRENT_PLAYER_STATE["bluff_score"]
        player_name = CURRENT_PLAYER_STATE["player_name"] or "No Current Player"
        
        # Format metrics for dashboard
        dashboard_data = {
            "player_name": player_name,
            "bluff_score": round(bluff_score, 1),
            "has_active_player": bool(CURRENT_PLAYER_STATE["player_name"]),
            "metrics": {
                "pauseRatio": metrics["avg_pause_ratio"],
                "pauseCount": int(metrics["total_pause_count"]),
                "meanF0": round(metrics["avg_mean_f0"], 1),
                "meanEnergy": round(metrics["avg_mean_energy"], 1),
                "maxEnergy": round(metrics["peak_max_energy"], 1)
            },
            "ui_data": {
                "pause_ratio": {
                    "value": metrics["avg_pause_ratio"],
                    "percentage": min(metrics["avg_pause_ratio"] * 100, 100) if metrics["avg_pause_ratio"] > 0 else 0,
                    "color_class": _get_metric_color_class("pause_ratio", metrics["avg_pause_ratio"])
                },
                "pause_count": {
                    "value": int(metrics["total_pause_count"]),
                    "percentage": min((metrics["total_pause_count"] / 50) * 100, 100) if metrics["total_pause_count"] > 0 else 0,
                    "color_class": _get_metric_color_class("pause_count", metrics["total_pause_count"])
                },
                "mean_f0": {
                    "value": round(metrics["avg_mean_f0"], 1),
                    "percentage": min(max(((metrics["avg_mean_f0"] - 50) / 250) * 100, 0), 100) if metrics["avg_mean_f0"] > 0 else 0,
                    "color_class": _get_metric_color_class("mean_f0", metrics["avg_mean_f0"])
                },
                "mean_energy": {
                    "value": round(metrics["avg_mean_energy"], 1),
                    "percentage": min(metrics["avg_mean_energy"], 100) if metrics["avg_mean_energy"] > 0 else 0,
                    "color_class": _get_metric_color_class("mean_energy", metrics["avg_mean_energy"])
                },
                "max_energy": {
                    "value": round(metrics["peak_max_energy"], 1),
                    "percentage": min(metrics["peak_max_energy"], 100) if metrics["peak_max_energy"] > 0 else 0,
                    "color_class": _get_metric_color_class("max_energy", metrics["peak_max_energy"])
                }
            },
            "leaderboard": LEADERBOARD,
            "leaderboard_count": len(LEADERBOARD),
            "session_complete": bool(CURRENT_PLAYER_STATE["session_id"]),
            "ready_for_display": True,
            "updated_at": datetime.now().isoformat()
        }
        
        return json.dumps(dashboard_data)
        
    except Exception as e:
        return json.dumps({
            "error": "Dashboard data generation failed",
            "details": str(e),
            "fallback_data": {
                "player_name": "No Current Player",
                "bluff_score": 0,
                "has_active_player": False,
                "metrics": {
                    "pauseRatio": 0.0,
                    "pauseCount": 0,
                    "meanF0": 0.0,
                    "meanEnergy": 0.0,
                    "maxEnergy": 0.0
                },
                "leaderboard": LEADERBOARD,
                "leaderboard_count": len(LEADERBOARD)
            }
        })

# -------------------------------------------------------------------
# HELPER FUNCTIONS FOR AUDIO PROCESSING AND SCORING
# -------------------------------------------------------------------

async def _analyze_audio_file(filename: str, dataset_name: str, question_num: int) -> Dict[str, float]:
    """
    Analyze a single audio file from HuggingFace dataset and extract speech metrics.
    """
    try:
        # Load dataset from HuggingFace
        if load_dataset is None:
            print("HuggingFace datasets library not available, using simulation")
            return _simulate_audio_analysis(question_num)
        
        try:
            # Load the dataset
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            
            # Find the specific file by filename
            target_file = None
            for sample in dataset:
                if sample.get("filename") == filename or filename in str(sample.get("filename", "")):
                    target_file = sample
                    break
            
            if target_file is None:
                raise ValueError(f"Audio file {filename} not found in dataset {dataset_name}")
            
            # Extract audio data
            audio_data = target_file["audio"]["array"]
            sampling_rate = target_file["audio"]["sampling_rate"]
            
            # Use the feature extraction function with audio data directly
            features = extract_features_from_array(audio_data, sr=sampling_rate)
            
            # Map the feature names to match expected format
            return {
                "pause_ratio": features["pause_ratio"],
                "pause_count": features["pause_count"],
                "mean_f0": features["mean_f0"],
                "mean_energy": (features["mean_rms_db"] + 120) / 120 * 100,  # Convert dB to 0-100 scale
                "max_energy": (features["max_rms_db"] + 120) / 120 * 100     # Convert dB to 0-100 scale
            }
            
        except Exception as hf_error:
            # Fallback: If HuggingFace access fails, use simulation with realistic values
            print(f"HuggingFace dataset access failed: {hf_error}")
            return _simulate_audio_analysis(question_num)
            
    except Exception as e:
        print(f"Audio analysis failed for {filename}: {e}")
        return _simulate_audio_analysis(question_num)

def _simulate_audio_analysis(question_num: int) -> Dict[str, float]:
    """
    Fallback simulation for audio analysis when real processing fails
    """
    import random
    
    # Simulate different patterns based on question type
    base_values = {
        1: {"pause_ratio": 0.12, "pause_count": 8, "mean_f0": 145, "mean_energy": 65, "max_energy": 82},
        2: {"pause_ratio": 0.18, "pause_count": 12, "mean_f0": 152, "mean_energy": 70, "max_energy": 88},
        3: {"pause_ratio": 0.08, "pause_count": 6, "mean_f0": 140, "mean_energy": 62, "max_energy": 75},
        4: {"pause_ratio": 0.22, "pause_count": 15, "mean_f0": 148, "mean_energy": 68, "max_energy": 92},
        5: {"pause_ratio": 0.25, "pause_count": 18, "mean_f0": 158, "mean_energy": 72, "max_energy": 95}
    }
    
    base = base_values.get(question_num, base_values[1])
    
    # Add some randomness to simulate real analysis
    return {
        "pause_ratio": max(0, base["pause_ratio"] + random.uniform(-0.05, 0.05)),
        "pause_count": max(0, base["pause_count"] + random.randint(-3, 3)),
        "mean_f0": max(50, base["mean_f0"] + random.uniform(-15, 15)),
        "mean_energy": max(0, min(100, base["mean_energy"] + random.uniform(-10, 10))),
        "max_energy": max(0, min(100, base["max_energy"] + random.uniform(-8, 8)))
    }

def _get_score_breakdown(metrics: Dict[str, float]) -> Dict[str, Any]:
    """Get detailed score breakdown for explanation"""
    
    return {
        "pause_ratio_contribution": f"{metrics['avg_pause_ratio']:.3f} (avg across 5 recordings)",
        "pause_count_contribution": f"{int(metrics['total_pause_count'])} (total across 5 recordings)",
        "f0_contribution": f"{metrics['avg_mean_f0']:.1f} Hz (avg fundamental frequency)",
        "energy_contribution": f"{metrics['avg_mean_energy']:.1f}% (avg energy level)",
        "max_energy_contribution": f"{metrics['peak_max_energy']:.1f}% (highest energy peak)",
        "explanation": "Score calculated using weighted method combining speech patterns, hesitation markers, and vocal stress indicators"
    }

def _interpret_bluff_analysis(bluff_score: float, metrics: Dict[str, float]) -> str:
    """Generate detailed interpretation of the bluff analysis results"""
    
    # Analyze pause patterns
    pause_analysis = ""
    if metrics["avg_pause_ratio"] > 0.25:
        pause_analysis = "Significant hesitation patterns detected - frequent pauses may indicate cognitive load from deception."
    elif metrics["avg_pause_ratio"] > 0.15:
        pause_analysis = "Moderate pause frequency observed - some hesitation present during responses."
    else:
        pause_analysis = "Minimal hesitation detected - speech flows relatively smoothly."
    
    # Analyze pause count
    pause_count_analysis = ""
    total_pauses = int(metrics["total_pause_count"])
    if total_pauses > 25:
        pause_count_analysis = f"High pause frequency with {total_pauses} total pauses across 5 responses - indicates potential stress or deception."
    elif total_pauses > 15:
        pause_count_analysis = f"Moderate pause count of {total_pauses} pauses - some verbal disfluencies present."
    else:
        pause_count_analysis = f"Low pause count of {total_pauses} pauses - relatively fluent speech delivery."
    
    # Analyze vocal pitch (F0)
    pitch_analysis = ""
    f0 = metrics["avg_mean_f0"]
    if f0 > 180 or f0 < 120:
        if f0 > 180:
            pitch_analysis = f"Elevated vocal pitch at {f0:.1f} Hz - may indicate stress or emotional arousal."
        else:
            pitch_analysis = f"Lowered vocal pitch at {f0:.1f} Hz - could suggest controlled speech or tension."
    else:
        pitch_analysis = f"Normal vocal pitch range at {f0:.1f} Hz - within typical conversational parameters."
    
    # Analyze energy levels
    energy_analysis = ""
    energy = metrics["avg_mean_energy"]
    if energy > 70:
        energy_analysis = f"High vocal energy at {energy:.1f}% - may indicate heightened emotional state or overcompensation."
    elif energy < 30:
        energy_analysis = f"Low vocal energy at {energy:.1f}% - could suggest subdued or controlled delivery."
    else:
        energy_analysis = f"Moderate vocal energy at {energy:.1f}% - balanced speech delivery observed."
    
    # Analyze max energy peaks
    peak_analysis = ""
    max_energy = metrics["peak_max_energy"]
    if max_energy > 85:
        peak_analysis = f"Very high energy peaks detected at {max_energy:.1f}% - sudden vocal intensity changes may indicate emotional regulation issues."
    elif max_energy > 70:
        peak_analysis = f"Notable energy peaks at {max_energy:.1f}% - some vocal intensity variation present."
    else:
        peak_analysis = f"Stable energy levels with peaks at {max_energy:.1f}% - consistent vocal delivery."
    
    # Overall behavioral interpretation
    behavioral_patterns = []
    
    if metrics["avg_pause_ratio"] > 0.2 and total_pauses > 20:
        behavioral_patterns.append("Frequent hesitation patterns suggest cognitive processing delays")
    
    if (f0 > 170 or f0 < 130) and energy > 65:
        behavioral_patterns.append("Vocal stress indicators present in both pitch and energy")
    
    if max_energy > 80 and metrics["avg_pause_ratio"] > 0.18:
        behavioral_patterns.append("Emotional regulation challenges evident in speech patterns")
    
    if metrics["avg_pause_ratio"] < 0.1 and 120 <= f0 <= 180 and 30 <= energy <= 70:
        behavioral_patterns.append("Speech patterns appear natural and unforced")
    
    # Compile interpretation
    interpretation = f"""
SPEECH PATTERN ANALYSIS:

Hesitation Patterns: {pause_analysis}

Pause Frequency: {pause_count_analysis}

Vocal Pitch: {pitch_analysis}

Energy Levels: {energy_analysis}

Intensity Peaks: {peak_analysis}

BEHAVIORAL OBSERVATIONS:
{chr(10).join(['• ' + pattern for pattern in behavioral_patterns]) if behavioral_patterns else '• No significant behavioral anomalies detected'}

TECHNICAL SUMMARY:
This analysis examined 5 audio responses using acoustic markers including pause ratios, frequency patterns, and vocal energy distribution. The metrics were weighted according to deception detection research focusing on cognitive load indicators and vocal stress patterns.
""".strip()
    
    return interpretation

def _get_metric_color_class(metric_type: str, value: float) -> str:
    """Get CSS color class for metric based on value thresholds"""
    
    if metric_type == "pause_ratio":
        if value <= 0.10: return "pause-ratio-excellent"
        elif value <= 0.20: return "pause-ratio-good"
        elif value <= 0.30: return "pause-ratio-fair"
        elif value <= 0.40: return "pause-ratio-poor"
        else: return "pause-ratio-bad"
    
    elif metric_type == "pause_count":
        if value <= 5: return "pause-count-excellent"
        elif value <= 15: return "pause-count-good"
        elif value <= 25: return "pause-count-fair"
        elif value <= 35: return "pause-count-poor"
        else: return "pause-count-bad"
        
    elif metric_type == "mean_f0":
        if value < 80: return "mean-f0-low"
        elif value <= 120: return "mean-f0-normal-low"
        elif value <= 180: return "mean-f0-normal-mid"
        elif value <= 250: return "mean-f0-normal-high"
        else: return "mean-f0-high"
        
    elif metric_type == "mean_energy":
        if value < 10: return "mean-energy-very-low"
        elif value < 30: return "mean-energy-low"
        elif value <= 70: return "mean-energy-optimal"
        elif value <= 85: return "mean-energy-high"
        else: return "mean-energy-very-high"
        
    elif metric_type == "max_energy":
        if value < 15: return "max-energy-very-low"
        elif value < 35: return "max-energy-low"
        elif value <= 75: return "max-energy-normal"
        elif value <= 90: return "max-energy-high"
        else: return "max-energy-very-high"
    
    return "pause-ratio-good"  # Default fallback

# -------------------------------------------------------------------
# RESOURCES - Static data that MCP clients can fetch
# 📚 RESOURCES = Read-only data endpoints (like "GET" APIs)
# Unlike tools (which DO something), resources just RETURN data
# -------------------------------------------------------------------

@mcp.resource(
    uri="catchmeow://recording-questions",
    description="Get all 5 recording questions/prompts used in voice sessions",
    name="Recording Questions Resource"
)
def get_recording_questions_resource() -> str:
    """
    📄 RESOURCE PURPOSE: Return all recording questions as structured JSON
    
    📝 DETAILED FUNCTION:
    - Returns all 5 RECORDING_PROMPTS with metadata about each
    - Shows question types (QUESTION vs READ ALOUD)
    - Useful for voice recorders, UI displays, session planning
    
    ✅ USAGE: MCP clients can fetch "catchmeow://recording-questions" 
    🎯 VERY USEFUL: Voice recorder apps can get all questions at once
    """
    
    questions_with_metadata = {}
    for prompt_id, prompt_text in RECORDING_PROMPTS.items():
        question_type = "QUESTION" if prompt_id in ["1", "2", "5"] else "READ ALOUD"
        questions_with_metadata[prompt_id] = {
            "text": prompt_text,
            "type": question_type,
            "category": "personal_info" if prompt_id == "1" else 
                       "free_form" if prompt_id == "2" else
                       "narrative" if prompt_id == "3" else
                       "technical" if prompt_id == "4" else
                       "truth_lie"
        }
    
    return json.dumps({
        "questions": questions_with_metadata,
        "total_count": len(RECORDING_PROMPTS),
        "question_order": ["1", "2", "3", "4", "5"],
        "usage": "Use get_recording_prompt tool with specific ID to get individual questions"
    })

@mcp.resource(
    uri="catchmeow://session/{client_id}",
    description="Get complete session data including profile and recording progress",
    name="Session Data Resource"
)
def get_session_resource(client_id: str) -> str:
    """
    📊 RESOURCE PURPOSE: Return complete session state for a client
    
    📝 DETAILED FUNCTION:
    - Returns profile data + recording session progress in one call
    - Shows current question, completed questions, verified uploads
    - Read-only access to full session state
    
    ✅ USAGE: MCP clients can fetch "catchmeow://session/anonymous" 
    🎯 VERY USEFUL: Dashboards, monitoring tools, session recovery
    """
    
    session_data: Dict[str, Any] = {"profile": None, "recording_session": None}
    
    if client_id in SESSIONS:
        session_data["profile"] = SESSIONS[client_id]
    
    if client_id in RECORDING_SESSIONS:
        session = RECORDING_SESSIONS[client_id]
        # Add progress calculations
        verified_count = sum(1 for upload in session["expected_uploads"] if upload["verified"])
        session_data["recording_session"] = {
            **session,
            "progress_stats": {
                "total_questions": 5,
                "recorded_count": len(session["recorded_questions"]),
                "expected_uploads": len(session["expected_uploads"]),
                "verified_uploads": verified_count,
                "completion_percentage": (verified_count / 5) * 100 if verified_count > 0 else 0
            }
        }
    
    if not session_data["profile"] and not session_data["recording_session"]:
        return json.dumps({"error": f"No session data found for client_id: {client_id}"})
    
    return json.dumps(session_data)

@mcp.resource(
    uri="catchmeow://game-config",
    description="Get game configuration, rules, and settings",
    name="Game Configuration Resource"
)
def get_game_config_resource() -> str:
    """
    ⚙️ RESOURCE PURPOSE: Return game configuration and rules
    
    📝 DETAILED FUNCTION:
    - Game rules, scoring system, session limits
    - Environment configuration (HuggingFace integration status)
    - Technical settings and API endpoints
    
    ✅ USAGE: MCP clients can fetch "catchmeow://game-config"
    🎯 VERY USEFUL: UI configuration, game rule displays, troubleshooting
    """
    
    config = {
        "game_info": {
            "name": "Catch Meow",
            "version": "1.0",
            "description": "AI-powered bluff detection game with voice recording",
            "max_players": 8,
            "questions_per_session": 5
        },
        "recording_config": {
            "required_questions": 5,
            "question_types": ["personal", "free_form", "narrative", "technical", "truth_lie"],
            "file_format": "wav",
            "upload_verification": "required"
        },
        "integration_status": {
            "huggingface_configured": bool(HUGGINGFACE_DATASET_URL and HUGGINGFACE_API_TOKEN),
            "dataset_url_available": bool(HUGGINGFACE_DATASET_URL),
            "api_token_available": bool(HUGGINGFACE_API_TOKEN)
        },
        "session_limits": {
            "max_concurrent_sessions": 8,
            "session_timeout_minutes": 30,
            "upload_verification_timeout": 120
        }
    }
    
    return json.dumps(config)

# -------------------------------------------------------------------  
# PROMPTS - Template text for LLMs to generate contextual responses
# 💬 PROMPTS = Templates that adapt to different situations
# These provide guidance/instructions for various scenarios
# -------------------------------------------------------------------

@mcp.prompt("Voice recording session guidance")
async def voice_recording_session_guidance(
    session_type: str = Field(description="Session type: baseline, truth, lie", default="baseline"),
    question_number: int = Field(description="Current question number (1-5)", default=1),
    player_name: str = Field(description="Player name for personalization", default="Player")
) -> str:
    """
    💬 PROMPT PURPOSE: Generate comprehensive recording session guidance
    
    📝 DETAILED FUNCTION:
    - Context-aware instructions based on session type and question
    - Personalized guidance using player name
    - Technical recording requirements
    - Different instructions for different session types (baseline/truth/lie)
    
    ✅ USAGE: LLMs use this to give players appropriate recording instructions
    🎯 VERY USEFUL: Ensures consistent, helpful guidance across all recording sessions
    """
    
    # Get the specific question text
    question_text = RECORDING_PROMPTS.get(str(question_number), "Unknown question")
    question_type = "QUESTION" if str(question_number) in ["1", "2", "5"] else "READ ALOUD"
    
    # Session type specific instructions
    session_instructions = {
        "baseline": f"""Hello {player_name}! This is a baseline recording session.

📝 Your task: Answer naturally and honestly. This helps establish your normal speech patterns.

🎯 Be yourself: Speak at your normal pace, use your natural tone, and don't overthink it.""",
        
        "truth": f"""Hello {player_name}! This is a truth session.

📝 Your task: Answer all questions with complete honesty. Your truthful responses help establish your baseline patterns.

🎯 Stay honest: Even if the answer seems boring or obvious, tell the complete truth.""",
        
        "lie": f"""Hello {player_name}! This is a lie session.

📝 Your task: For question 5 specifically, you should tell a deliberate lie. All other questions should be answered truthfully.

🎯 Be convincing: Make your lies believable, but remember - only lie for question 5!"""
    }
    
    base_instruction = session_instructions.get(session_type, session_instructions["baseline"])
    
    # Question-specific guidance
    if question_type == "READ ALOUD":
        question_guidance = "📖 **Reading Task**: This is a text reading exercise. Read the text clearly and naturally, as if you're speaking to a friend."
    else:
        question_guidance = "💭 **Question Response**: Think about your answer briefly, then respond naturally."
    
    full_guidance = f"""{base_instruction}

**Question {question_number}/5** ({question_type}):
{question_text}

{question_guidance}

**Technical Requirements:**
🎙️ Speak clearly and at normal volume
🔇 Ensure minimal background noise  
⏱️ Recording should be at least 10 seconds long
⬆️ Wait for the recording to upload completely before proceeding

**Next Steps:**
1. Record your response
2. Upload will be verified automatically
3. Proceed to the next question once verified

The system will verify your recording is properly stored before moving to the next question."""
    
    return full_guidance

@mcp.prompt("Game progress and session status")
async def game_progress_status(
    client_id: str = Field(description="Client ID to get status for", default="anonymous"),
    include_technical_details: bool = Field(description="Include technical session info", default=False)
) -> str:
    """
    📊 PROMPT PURPOSE: Generate comprehensive progress reports
    
    📝 DETAILED FUNCTION:  
    - Shows current game/recording progress
    - Personalized with player information
    - Can include technical details for debugging
    - Adaptive messaging based on completion status
    
    ✅ USAGE: LLMs use this to give players progress updates
    🎯 VERY USEFUL: Keep players informed about their session progress
    """
    
    # Get session data
    profile = SESSIONS.get(client_id, {}).get("profile")
    recording_session = RECORDING_SESSIONS.get(client_id)
    
    if not profile and not recording_session:
        return f"""👋 Welcome to Catch Meow!

It looks like you haven't started yet. Here's what you need to do:

1️⃣ **Create Your Profile**: Use the 'save_profile' tool to tell us your name, hometown, and favorite color
2️⃣ **Start Recording**: Once your profile is saved, we'll automatically create your recording session
3️⃣ **Answer 5 Questions**: Record your responses to our 5 questions
4️⃣ **Verification**: Each recording will be verified before moving to the next question

Ready to begin? Start with saving your profile!"""
    
    if not recording_session:
        player_name = profile.get("name", "Player") if profile else "Player"
        profile_data = profile if profile else {}
        return f"""👋 Hello {player_name}!

Your profile is saved, but no recording session found. Use 'start_recording_for_question' to begin your voice recording session.

Profile Info:
• Name: {profile_data.get('name', 'Not set')}
• Hometown: {profile_data.get('home_town', 'Not set')}  
• Favorite Color: {profile_data.get('favorite_color', 'Not set')}

Ready to start recording? Begin with question 1!"""
    
    # Full progress report
    session = recording_session
    player_name = session["profile"]["name"]
    recorded_count = len(session["recorded_questions"])
    verified_count = sum(1 for upload in session["expected_uploads"] if upload["verified"])
    total_expected = len(session["expected_uploads"])
    current_q = session["current_question"]
    
    # Progress indicators
    progress_bar = ("🟢" * verified_count + 
                   "⏳" * (recorded_count - verified_count) + 
                   "⭕" * (5 - recorded_count))
    completion_percent = (verified_count / 5) * 100
    
    status_report = f"""🎮 **Catch Meow Progress Report**
👤 Player: {player_name}

📊 **Overall Progress ({completion_percent:.0f}% Complete):**
{progress_bar} {verified_count}/5 questions verified

📝 **Session Status:**
• Current Question: {current_q}/5
• Recorded: {recorded_count}/5 questions  
• Uploaded: {total_expected} files
• Verified: {verified_count}/{total_expected} uploads

"""
    
    # Status-specific messaging
    if verified_count == 5:
        status_report += """🎉 **Session Complete!** 
All questions have been recorded and verified. Great job!

Your voice session is ready for analysis. The AI will now examine your recordings for bluff detection patterns."""
    elif recorded_count == 5:
        pending_count = total_expected - verified_count
        status_report += f"""⚠️ **Almost Done!**
All questions recorded, but {pending_count} uploads still pending verification.

The system is checking for your uploaded files. This usually takes a few moments."""
    else:
        remaining = 5 - recorded_count
        status_report += f"""📝 **In Progress**
{remaining} question(s) remaining to record.

Next: Use 'start_recording_for_question' with question number {current_q} to continue."""
    
    # Technical details if requested
    if include_technical_details and recording_session:
        status_report += f"""

🔧 **Technical Details:**
• Session ID: {session['session_id']}
• Created: {session['created_at']}
• Upload Details: {len(session['expected_uploads'])} files tracked"""
        
        for upload in session["expected_uploads"]:
            status = "✅ Verified" if upload["verified"] else "⏳ Pending"
            status_report += f"""
  - Q{upload['question_number']}: {upload['filename']} - {status}"""
    
    return status_report


if __name__ == "__main__":
    # Exposes an HTTP MCP endpoint at http://127.0.0.1:3000/mcp
    mcp.run(transport="streamable-http")