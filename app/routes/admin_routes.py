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
    TV display page - auto-cycles through states based on question timing.
    No authentication required (public view for TV).

    States (auto-determined):
    - waiting: No active question, results expired → show QR + join/propose
    - question: Active question → show question + countdown timer
    - results: Question just closed → show answer + leaderboard
    """
    # Get all participants for leaderboard and count
    leaderboard = game_service.get_all_participants()
    participant_count = len(leaderboard)
    participant_lookup = {p['id']: p for p in leaderboard}

    # Get active question
    active_question = game_service.get_active_question()

    # AUTO-CLOSE: If active question has expired, close it
    if active_question:
        time_remaining = game_service.get_question_time_remaining(active_question)
        if time_remaining <= 0:
            game_service.close_question(active_question['id'])
            active_question = None  # Now closed, will show results

    # Get last closed question for results
    closed_question = game_service.get_last_closed_question()

    # Determine display mode based on state
    if active_question:
        # QUESTION MODE: Show question with countdown timer
        time_remaining = game_service.get_question_time_remaining(active_question)
        answers = game_service.get_answers_for_question(active_question['id'])
        answer_count = len(answers)

        return render_template(
            'tv.html',
            tv_display_mode='question',
            question=active_question,
            show_results=False,
            answer_count=answer_count,
            time_remaining=time_remaining,
            results_time=0,
            results=[],
            correct_participant=None,
            leaderboard=leaderboard,
            participant_count=participant_count,
            refresh_seconds=3
        )

    elif closed_question:
        results_time = game_service.get_results_time_remaining(closed_question)

        if results_time > 0:
            # RESULTS MODE: Show answer reveal + leaderboard
            results = game_service.get_vote_results(closed_question['id'])
            answers = game_service.get_answers_for_question(closed_question['id'])
            answer_count = len(answers)
            correct_participant = None
            if closed_question.get('correct_answer'):
                correct_participant = participant_lookup.get(closed_question['correct_answer'])

            return render_template(
                'tv.html',
                tv_display_mode='results',
                question=closed_question,
                show_results=True,
                answer_count=answer_count,
                time_remaining=0,
                results_time=results_time,
                results=results,
                correct_participant=correct_participant,
                leaderboard=leaderboard,
                participant_count=participant_count,
                refresh_seconds=5
            )

    # WAITING MODE: No active question, results expired
    return render_template(
        'tv.html',
        tv_display_mode='waiting',
        question=None,
        show_results=False,
        answer_count=0,
        time_remaining=0,
        results_time=0,
        results=[],
        correct_participant=None,
        leaderboard=leaderboard,
        participant_count=participant_count,
        refresh_seconds=10
    )


# =============================================================================
# Admin Panel
# =============================================================================

@bp.route('/admin')
def admin():
    """Redirect to questions page."""
    if not check_admin_key():
        return render_template('admin_login.html'), 401
    return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))


@bp.route('/admin/questions')
def questions():
    """Admin panel - manage questions."""
    if not check_admin_key():
        return render_template('admin_login.html'), 401

    questions = game_service.get_all_questions()
    participants = game_service.get_all_participants()
    participant_lookup = {p['id']: p for p in participants}

    return render_template(
        'admin_questions.html',
        questions=questions,
        participants=participants,
        participant_lookup=participant_lookup,
        admin_key=Config.ADMIN_SECRET
    )


@bp.route('/admin/participants')
def participants():
    """Admin panel - manage participants."""
    if not check_admin_key():
        return render_template('admin_login.html'), 401

    participants = game_service.get_all_participants()

    return render_template(
        'admin_participants.html',
        participants=participants,
        admin_key=Config.ADMIN_SECRET
    )


@bp.route('/admin/tv-control')
def tv_control():
    """Admin panel - control TV display."""
    if not check_admin_key():
        return render_template('admin_login.html'), 401

    participants = game_service.get_all_participants()
    tv_mode = game_service.get_tv_mode()

    return render_template(
        'admin_tv.html',
        participants=participants,
        tv_mode=tv_mode,
        admin_key=Config.ADMIN_SECRET
    )


@bp.route('/admin/set-tv-mode', methods=['POST'])
def set_tv_mode():
    """Set TV display mode."""
    if not check_admin_key():
        return "Unauthorized", 401

    mode = request.form.get('mode', 'auto')
    game_service.set_tv_mode(mode)

    return redirect(url_for('admin.tv_control', key=Config.ADMIN_SECRET))


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
        answer_image_file = request.files.get('answer_image')

        if not text:
            return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET, error='Question text required'))

        game_service.create_question(
            text=text,
            question_type=question_type,
            correct_answer=correct_answer if correct_answer else None,
            image_file=image_file if image_file and image_file.filename else None,
            answer_image_file=answer_image_file if answer_image_file and answer_image_file.filename else None
        )

        return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))

    except Exception as e:
        return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET, error=str(e)))


@bp.route('/admin/activate', methods=['POST'])
def activate_question():
    """Activate a question."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.activate_question(question_id)

    return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))


@bp.route('/admin/close', methods=['POST'])
def close_question():
    """Close a question and calculate scores."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.close_question(question_id)

    return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))


@bp.route('/admin/delete_question', methods=['POST'])
def delete_question():
    """Delete a question."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    if question_id:
        game_service.delete_question(question_id)

    return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))


@bp.route('/admin/update_question', methods=['POST'])
def update_question():
    """Update question (e.g., set correct answer for trivia)."""
    if not check_admin_key():
        return "Unauthorized", 401

    question_id = request.form.get('question_id')
    correct_answer = request.form.get('correct_answer')

    if question_id:
        game_service.update_question(question_id, correct_answer=correct_answer)

    return redirect(url_for('admin.questions', key=Config.ADMIN_SECRET))


@bp.route('/admin/reset', methods=['POST'])
def reset_scores():
    """Reset all participant scores to 0."""
    if not check_admin_key():
        return "Unauthorized", 401

    game_service.reset_all_scores()

    return redirect(url_for('admin.participants', key=Config.ADMIN_SECRET))


@bp.route('/admin/delete_participant', methods=['POST'])
def delete_participant():
    """Delete a participant."""
    if not check_admin_key():
        return "Unauthorized", 401

    participant_id = request.form.get('participant_id')
    if participant_id:
        game_service.delete_participant(participant_id)

    return redirect(url_for('admin.participants', key=Config.ADMIN_SECRET))
