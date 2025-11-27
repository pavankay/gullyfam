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

def create_question(text, question_type, correct_answer=None, proposed_by=None, image_file=None):
    """
    Create a new question.

    Args:
        text: Question text
        question_type: 'trivia' or 'vote'
        correct_answer: participant_id for trivia questions
        proposed_by: participant_id who proposed it
        image_file: Optional image file

    Returns:
        dict: Created question data with id
    """
    image_url = None

    if image_file and image_file.filename:
        import uuid
        gcs_path, _, _ = storage_service.upload_file(
            f"questions/{str(uuid.uuid4())[:8]}",
            image_file,
            image_file.filename
        )
        # Store full public URL
        image_url = f"https://storage.googleapis.com/{Config.FIREBASE_STORAGE_BUCKET}/{gcs_path}"

    question_data = {
        'text': text,
        'type': question_type,
        'image_url': image_url,
        'correct_answer': correct_answer,
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


def activate_question(question_id):
    """Set a question as active (deactivate any other active question first)."""
    # Deactivate current active question
    current_active = get_active_question()
    if current_active:
        firebase_service.update_doc(
            Config.Collections.QUESTIONS,
            current_active['id'],
            {'status': 'closed'}
        )

    # Activate the new question
    firebase_service.update_doc(
        Config.Collections.QUESTIONS,
        question_id,
        {'status': 'active'}
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
        correct_answer = question.get('correct_answer')
        for answer in answers:
            if answer['answer'] == correct_answer:
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

    # Mark question as closed
    firebase_service.update_doc(
        Config.Collections.QUESTIONS,
        question_id,
        {'status': 'closed'}
    )


def delete_question(question_id):
    """Delete a question."""
    firebase_service.delete_doc(Config.Collections.QUESTIONS, question_id)


def update_question(question_id, text=None, correct_answer=None):
    """Update question fields."""
    updates = {}
    if text:
        updates['text'] = text
    if correct_answer is not None:
        updates['correct_answer'] = correct_answer
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
