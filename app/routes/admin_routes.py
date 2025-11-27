"""
Admin Routes

Routes for admin panel and TV display.
Admin routes require ?key=ADMIN_SECRET in URL.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from app.services import game_service
from app.config import Config

bp = Blueprint('admin', __name__)


def check_admin_key():
    """Check if admin key is valid."""
    key = request.args.get('key')
    return key == Config.ADMIN_SECRET


# =============================================================================
# TV Display
# =============================================================================

@bp.route('/tv')
def tv():
    """
    TV display page - shows current question, results, and leaderboard.
    No authentication required (public view for TV).
    """
    # Get current question
    question = game_service.get_active_question()

    # Get results if there's a question
    results = []
    answer_count = 0
    if question:
        results = game_service.get_vote_results(question['id'])
        answers = game_service.get_answers_for_question(question['id'])
        answer_count = len(answers)

    # Get leaderboard (all participants sorted by score)
    leaderboard = game_service.get_all_participants()

    # Get participant count
    participant_count = len(leaderboard)

    return render_template(
        'tv.html',
        question=question,
        results=results,
        answer_count=answer_count,
        leaderboard=leaderboard,
        participant_count=participant_count
    )


# =============================================================================
# Admin Panel
# =============================================================================

@bp.route('/admin')
def admin():
    """
    Admin panel - manage questions and see participants.
    Requires ?key=ADMIN_SECRET in URL.
    """
    if not check_admin_key():
        return render_template('admin_login.html'), 401

    # Get all questions
    questions = game_service.get_all_questions()

    # Get all participants
    participants = game_service.get_all_participants()

    # Build participant lookup for displaying names
    participant_lookup = {p['id']: p for p in participants}

    return render_template(
        'admin.html',
        questions=questions,
        participants=participants,
        participant_lookup=participant_lookup,
        admin_key=Config.ADMIN_SECRET
    )


@bp.route('/admin/question', methods=['POST'])
def create_question():
    """Create a new question."""
    if not check_admin_key():
        return "Unauthorized", 401

    try:
        text = request.form.get('text', '').strip()
        question_type = request.form.get('type', 'vote')
        correct_answer = request.form.get('correct_answer')
        image_file = request.files.get('image')

        if not text:
            return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET, error='Question text required'))

        game_service.create_question(
            text=text,
            question_type=question_type,
            correct_answer=correct_answer if correct_answer else None,
            image_file=image_file if image_file and image_file.filename else None
        )

        return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))

    except Exception as e:
        return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET, error=str(e)))


@bp.route('/admin/activate', methods=['POST'])
def activate_question():
    """Activate a question."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.activate_question(question_id)

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))


@bp.route('/admin/close', methods=['POST'])
def close_question():
    """Close a question and calculate scores."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.close_question(question_id)

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))


@bp.route('/admin/delete_question', methods=['POST'])
def delete_question():
    """Delete a question."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.delete_question(question_id)

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))


@bp.route('/admin/update_question', methods=['POST'])
def update_question():
    """Update question (e.g., set correct answer for trivia)."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    correct_answer = request.form.get('correct_answer')

    if question_id:
        game_service.update_question(question_id, correct_answer=correct_answer)

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))


@bp.route('/admin/reset', methods=['POST'])
def reset_scores():
    """Reset all participant scores to 0."""
    if not check_admin_key():
        return "Unauthorized", 401

    game_service.reset_all_scores()

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))


@bp.route('/admin/delete_participant', methods=['POST'])
def delete_participant():
    """Delete a participant."""
    if not check_admin_key():
        return "Unauthorized", 401

    participant_id = request.form.get('participant_id')
    if participant_id:
        game_service.delete_participant(participant_id)

    return redirect(url_for('admin.admin', key=Config.ADMIN_SECRET))
