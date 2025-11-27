"""
Game Service

All game logic for the Gullyfam Thanksgiving party game.
Handles participants, questions, answers, and scoring.
"""

from datetime import datetime
from app.services import firebase_service, storage_service
from app.config import Config


# =============================================================================
# Participant Functions
# =============================================================================

def create_participant(name, selfie_file=None):
    """
    Create a new participant with optional selfie.

    Args:
        name: Participant name
        selfie_file: Optional file object for selfie

    Returns:
        dict: Created participant data with id
    """
    selfie_url = None

    # Upload selfie if provided
    if selfie_file and selfie_file.filename:
        import uuid
        temp_id = str(uuid.uuid4())[:8]
        gcs_path, _, _ = storage_service.upload_file(
            f"participants/{temp_id}",
            selfie_file,
            selfie_file.filename
        )
        # Store full public URL
        selfie_url = f"https://storage.googleapis.com/{Config.FIREBASE_STORAGE_BUCKET}/{gcs_path}"

    participant_data = {
        'name': name,
        'selfie_url': selfie_url,
        'score': 0,
        'created_at': datetime.utcnow().isoformat()
    }

    return firebase_service.create_doc(Config.Collections.PARTICIPANTS, participant_data)


def get_participant(participant_id):
    """Get participant by ID."""
    return firebase_service.get_doc(Config.Collections.PARTICIPANTS, participant_id)


def get_all_participants():
    """Get all participants sorted by score (descending)."""
    participants = firebase_service.query_docs(
        Config.Collections.PARTICIPANTS,
        order_by=('score', 'DESCENDING')
    )
    return participants


def update_participant(participant_id, name=None, selfie_file=None):
    """Update participant name and/or selfie."""
    updates = {}

    if name:
        updates['name'] = name

    if selfie_file and selfie_file.filename:
        gcs_path, _, _ = storage_service.upload_file(
            f"participants/{participant_id}",
            selfie_file,
            selfie_file.filename
        )
        # Store full public URL
        updates['selfie_url'] = f"https://storage.googleapis.com/{Config.FIREBASE_STORAGE_BUCKET}/{gcs_path}"

    if updates:
        firebase_service.update_doc(Config.Collections.PARTICIPANTS, participant_id, updates)

    return get_participant(participant_id)


def delete_participant(participant_id):
    """Delete a participant."""
    firebase_service.delete_doc(Config.Collections.PARTICIPANTS, participant_id)


def add_score(participant_id, points):
    """Add points to participant's score."""
    participant = get_participant(participant_id)
    if participant:
        new_score = participant.get('score', 0) + points
        firebase_service.update_doc(
            Config.Collections.PARTICIPANTS,
            participant_id,
            {'score': new_score}
        )


def reset_all_scores():
    """Reset all participant scores to 0."""
    participants = get_all_participants()
    for p in participants:
        firebase_service.update_doc(
            Config.Collections.PARTICIPANTS,
            p['id'],
            {'score': 0}
        )


# =============================================================================
# Question Functions
# =============================================================================

def create_question(text, question_type, proposed_by=None, image_file=None, answer_image_file=None, options=None, correct_option=None):
    """
    Create a new question.

    Args:
        text: Question text
        question_type: 'trivia' or 'vote'
        proposed_by: participant_id who proposed it
        image_file: Optional question image (e.g., silhouette)
        answer_image_file: Optional answer/reveal image (for trivia)
        options: List of 4 answer options (for trivia)
        correct_option: Index of correct option 0-3 (for trivia)

    Returns:
        dict: Created question data with id
    """
    import uuid

    image_url = None
    answer_image_url = None

    if image_file and image_file.filename:
        gcs_path, _, _ = storage_service.upload_file(
            f"questions/{str(uuid.uuid4())[:8]}",
            image_file,
            image_file.filename
        )
        image_url = f"https://storage.googleapis.com/{Config.FIREBASE_STORAGE_BUCKET}/{gcs_path}"

    if answer_image_file and answer_image_file.filename:
        gcs_path, _, _ = storage_service.upload_file(
            f"questions/{str(uuid.uuid4())[:8]}_answer",
            answer_image_file,
            answer_image_file.filename
        )
        answer_image_url = f"https://storage.googleapis.com/{Config.FIREBASE_STORAGE_BUCKET}/{gcs_path}"

    question_data = {
        'text': text,
        'type': question_type,
        'image_url': image_url,
        'answer_image_url': answer_image_url,
        'options': options,  # List of 4 options for trivia
        'correct_option': correct_option,  # Index 0-3 for trivia
        'status': 'pending',
        'proposed_by': proposed_by,
        'created_at': datetime.utcnow().isoformat()
    }

    return firebase_service.create_doc(Config.Collections.QUESTIONS, question_data)


def get_question(question_id):
    """Get question by ID."""
    return firebase_service.get_doc(Config.Collections.QUESTIONS, question_id)


def get_all_questions():
    """Get all questions."""
    return firebase_service.query_docs(
        Config.Collections.QUESTIONS,
        order_by=('created_at', 'DESCENDING')
    )


def get_pending_questions():
    """Get pending (proposed) questions."""
    return firebase_service.query_docs(
        Config.Collections.QUESTIONS,
        filters=[('status', '==', 'pending')]
    )


def get_active_question():
    """Get the currently active question."""
    return firebase_service.query_one(
        Config.Collections.QUESTIONS,
        filters=[('status', '==', 'active')]
    )


def get_last_closed_question():
    """Get the most recently closed question (for showing results)."""
    results = firebase_service.query_docs(
        Config.Collections.QUESTIONS,
        filters=[('status', '==', 'closed')],
        order_by=('created_at', 'DESCENDING'),
        limit=1
    )
    return results[0] if results else None


def activate_question(question_id):
    """Set a question as active (deactivate any other active question first)."""
    # Deactivate current active question
    current_active = get_active_question()
    if current_active:
        firebase_service.update_doc(
            Config.Collections.QUESTIONS,
            current_active['id'],
            {
                'status': 'closed',
                'closed_at': datetime.utcnow().isoformat()
            }
        )

    # Activate the new question with timestamp
    firebase_service.update_doc(
        Config.Collections.QUESTIONS,
        question_id,
        {
            'status': 'active',
            'activated_at': datetime.utcnow().isoformat()
        }
    )


def close_question(question_id):
    """Close a question and calculate scores."""
    question = get_question(question_id)
    if not question:
        return

    # Get all answers for this question
    answers = get_answers_for_question(question_id)

    if question['type'] == 'trivia':
        # Award 1 point for correct answers
        correct_option = question.get('correct_option')
        for answer in answers:
            # Compare as strings since form data comes as string
            if str(answer['answer']) == str(correct_option):
                add_score(answer['participant_id'], 1)
                # Update answer record
                firebase_service.update_doc(
                    Config.Collections.ANSWERS,
                    answer['id'],
                    {'points_awarded': 1}
                )
    else:
        # Vote question: 1 point for participation
        for answer in answers:
            add_score(answer['participant_id'], 1)
            firebase_service.update_doc(
                Config.Collections.ANSWERS,
                answer['id'],
                {'points_awarded': 1}
            )

    # Mark question as closed with timestamp
    firebase_service.update_doc(
        Config.Collections.QUESTIONS,
        question_id,
        {
            'status': 'closed',
            'closed_at': datetime.utcnow().isoformat()
        }
    )


def delete_question(question_id):
    """Delete a question."""
    firebase_service.delete_doc(Config.Collections.QUESTIONS, question_id)


def update_question(question_id, text=None, options=None, correct_option=None):
    """Update question fields."""
    updates = {}
    if text:
        updates['text'] = text
    if options is not None:
        updates['options'] = options
    if correct_option is not None:
        updates['correct_option'] = correct_option
    if updates:
        firebase_service.update_doc(Config.Collections.QUESTIONS, question_id, updates)


# =============================================================================
# Answer Functions
# =============================================================================

def submit_answer(question_id, participant_id, answer):
    """
    Submit an answer to a question.

    Uses composite key to prevent duplicate answers.

    Args:
        question_id: Question being answered
        participant_id: Who is answering
        answer: The answer (participant_id they selected)

    Returns:
        dict: Answer data or None if already answered
    """
    # Check if already answered (using composite key)
    doc_id = f"{question_id}_{participant_id}"
    existing = firebase_service.get_doc(Config.Collections.ANSWERS, doc_id)
    if existing:
        return None  # Already answered

    answer_data = {
        'id': doc_id,
        'question_id': question_id,
        'participant_id': participant_id,
        'answer': answer,
        'points_awarded': 0,
        'created_at': datetime.utcnow().isoformat()
    }

    # Use set with specific ID
    db = firebase_service.get_firestore_client()
    db.collection(Config.Collections.ANSWERS).document(doc_id).set(answer_data)

    return answer_data


def get_answer(question_id, participant_id):
    """Check if participant already answered a question."""
    doc_id = f"{question_id}_{participant_id}"
    return firebase_service.get_doc(Config.Collections.ANSWERS, doc_id)


def get_answers_for_question(question_id):
    """Get all answers for a question."""
    return firebase_service.query_docs(
        Config.Collections.ANSWERS,
        filters=[('question_id', '==', question_id)]
    )


def get_vote_results(question_id):
    """
    Get vote results for a question.

    Returns:
        list: List of dicts with participant info and vote count, sorted by votes
    """
    answers = get_answers_for_question(question_id)
    participants = {p['id']: p for p in get_all_participants()}

    # Count votes per answer
    vote_counts = {}
    for answer in answers:
        voted_for = answer['answer']
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

    # Build results with participant info
    results = []
    for participant_id, count in vote_counts.items():
        participant = participants.get(participant_id, {})
        results.append({
            'participant_id': participant_id,
            'name': participant.get('name', 'Unknown'),
            'selfie_url': participant.get('selfie_url'),
            'votes': count
        })

    # Sort by votes descending
    results.sort(key=lambda x: x['votes'], reverse=True)
    return results


# =============================================================================
# Image URL Helper
# =============================================================================

def get_public_url(gcs_path):
    """Get public URL for an image (bucket must be public)."""
    if not gcs_path:
        return None
    bucket = Config.FIREBASE_STORAGE_BUCKET
    return f"https://storage.googleapis.com/{bucket}/{gcs_path}"


# =============================================================================
# Timing Constants
# =============================================================================

QUESTION_DURATION_SECONDS = 60
RESULTS_DURATION_SECONDS = 60


# =============================================================================
# TV Mode Functions
# =============================================================================

TV_MODE_DOC_ID = 'tv_mode'
VALID_TV_MODES = ['auto', 'question', 'results', 'onboard', 'propose']


def get_tv_mode():
    """Get current TV display mode. Defaults to 'auto'."""
    doc = firebase_service.get_doc(Config.Collections.SETTINGS, TV_MODE_DOC_ID)
    if doc:
        return doc.get('mode', 'auto')
    return 'auto'


def set_tv_mode(mode):
    """Set TV display mode."""
    if mode not in VALID_TV_MODES:
        raise ValueError(f"Invalid TV mode: {mode}. Must be one of {VALID_TV_MODES}")

    db = firebase_service.get_firestore_client()
    db.collection(Config.Collections.SETTINGS).document(TV_MODE_DOC_ID).set({
        'mode': mode,
        'updated_at': datetime.utcnow().isoformat()
    })


# =============================================================================
# Time Remaining Helpers
# =============================================================================

def get_question_time_remaining(question):
    """Get seconds remaining for active question. Returns 0 if expired."""
    if not question or question.get('status') != 'active':
        return 0
    activated_at = question.get('activated_at')
    if not activated_at:
        return QUESTION_DURATION_SECONDS  # No timestamp, assume just started

    activated = datetime.fromisoformat(activated_at)
    elapsed = (datetime.utcnow() - activated).total_seconds()
    remaining = QUESTION_DURATION_SECONDS - elapsed
    return max(0, int(remaining))


def get_results_time_remaining(question):
    """Get seconds remaining to show results. Returns 0 if expired."""
    if not question or question.get('status') != 'closed':
        return 0
    closed_at = question.get('closed_at')
    if not closed_at:
        return RESULTS_DURATION_SECONDS  # No timestamp, assume just closed

    closed = datetime.fromisoformat(closed_at)
    elapsed = (datetime.utcnow() - closed).total_seconds()
    remaining = RESULTS_DURATION_SECONDS - elapsed
    return max(0, int(remaining))
