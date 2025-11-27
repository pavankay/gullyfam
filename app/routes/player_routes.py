"""
Player Routes

Routes for player-facing pages: onboarding, play, settings, propose.
All routes render server-side templates with form submissions.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from app.services import game_service

bp = Blueprint('player', __name__)


# =============================================================================
# Onboarding
# =============================================================================

@bp.route('/', methods=['GET', 'POST'])
def onboard():
    """
    Onboarding page - enter name and selfie to join the game.

    GET: Show onboarding form
    POST: Create participant and redirect to play page
    """
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            if not name:
                return render_template('onboard.html', error='Name is required')

            selfie_file = request.files.get('selfie')
            participant = game_service.create_participant(name, selfie_file)

            return redirect(url_for('player.play', player_id=participant['id']))

        except Exception as e:
            import traceback
            return render_template('onboard.html', error=str(e), traceback=traceback.format_exc())

    return render_template('onboard.html')


# =============================================================================
# Play - Answer Questions
# =============================================================================

@bp.route('/play/<player_id>', methods=['GET', 'POST'])
def play(player_id):
    """
    Play page - answer the current question.

    GET: Show current question and answer form
    POST: Submit answer
    """
    # Get participant
    participant = game_service.get_participant(player_id)
    if not participant:
        return redirect(url_for('player.onboard'))

    # Get current active question
    question = game_service.get_active_question()

    # Get all participants for dropdown
    all_participants = game_service.get_all_participants()

    # Check if already answered
    already_answered = False
    if question:
        existing_answer = game_service.get_answer(question['id'], player_id)
        already_answered = existing_answer is not None

    message = None

    if request.method == 'POST' and question:
        try:
            answer = request.form.get('answer')
            if not answer:
                message = 'Please select an answer'
            else:
                result = game_service.submit_answer(question['id'], player_id, answer)
                if result:
                    message = 'Answer submitted!'
                    already_answered = True
                else:
                    message = 'You already answered this question'
                    already_answered = True

        except Exception as e:
            import traceback
            return render_template(
                'play.html',
                participant=participant,
                question=question,
                all_participants=all_participants,
                already_answered=already_answered,
                error=str(e),
                traceback=traceback.format_exc()
            )

    return render_template(
        'play.html',
        participant=participant,
        question=question,
        all_participants=all_participants,
        already_answered=already_answered,
        message=message
    )


# =============================================================================
# Settings - Edit Profile
# =============================================================================

@bp.route('/player/<player_id>', methods=['GET', 'POST'])
def settings(player_id):
    """
    Settings page - edit name and selfie.

    GET: Show settings form
    POST: Update settings
    """
    participant = game_service.get_participant(player_id)
    if not participant:
        return redirect(url_for('player.onboard'))

    message = None

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            selfie_file = request.files.get('selfie')

            game_service.update_participant(
                player_id,
                name=name if name else None,
                selfie_file=selfie_file if selfie_file and selfie_file.filename else None
            )

            # Refresh participant data
            participant = game_service.get_participant(player_id)
            message = 'Settings saved!'

        except Exception as e:
            import traceback
            return render_template(
                'player.html',
                participant=participant,
                error=str(e),
                traceback=traceback.format_exc()
            )

    return render_template('player.html', participant=participant, message=message)


# =============================================================================
# Propose - Submit Question Ideas
# =============================================================================

@bp.route('/propose/<player_id>', methods=['GET', 'POST'])
def propose(player_id):
    """
    Propose page - suggest a new question.

    GET: Show propose form
    POST: Submit proposed question
    """
    participant = game_service.get_participant(player_id)
    if not participant:
        return redirect(url_for('player.onboard'))

    message = None

    if request.method == 'POST':
        try:
            text = request.form.get('text', '').strip()
            question_type = request.form.get('type', 'vote')

            if not text:
                message = 'Please enter a question'
            else:
                game_service.create_question(
                    text=text,
                    question_type=question_type,
                    proposed_by=player_id
                )
                message = 'Question submitted! The game host will review it.'

        except Exception as e:
            import traceback
            return render_template(
                'propose.html',
                participant=participant,
                error=str(e),
                traceback=traceback.format_exc()
            )

    return render_template('propose.html', participant=participant, message=message)
