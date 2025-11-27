"""
Player Routes

Routes for player-facing pages: onboarding, play, settings, propose.
All routes render server-side templates with form submissions.
"""

import traceback
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


# =============================================================================
# Add Vote Question
# =============================================================================

@bp.route('/add-vote', methods=['GET', 'POST'])
@bp.route('/add-vote/<player_id>', methods=['GET', 'POST'])
def add_vote(player_id=None):
    """
    Add vote question page.

    GET: Show form
    POST: Create vote question
    """
    participant = None
    if player_id:
        participant = game_service.get_participant(player_id)
        if not participant:
            return redirect(url_for('player.onboard'))

    if request.method == 'POST':
        try:
            text = request.form.get('text', '').strip()
            if not text:
                return render_template(
                    'add_vote.html',
                    participant=participant,
                    error='Please enter a question'
                )

            image_file = request.files.get('image')

            game_service.create_question(
                text=text,
                question_type='vote',
                proposed_by=player_id,
                image_file=image_file if image_file and image_file.filename else None
            )

            # Redirect back appropriately
            if participant:
                return redirect(url_for('player.propose', player_id=player_id))
            else:
                return redirect(url_for('admin.questions', key=request.args.get('key', '')))

        except Exception as e:
            import traceback
            return render_template(
                'add_vote.html',
                participant=participant,
                error=str(e),
                traceback=traceback.format_exc()
            )

    return render_template('add_vote.html', participant=participant)


# =============================================================================
# Add Trivia Question
# =============================================================================

@bp.route('/add-trivia', methods=['GET', 'POST'])
@bp.route('/add-trivia/<player_id>', methods=['GET', 'POST'])
def add_trivia(player_id=None):
    """
    Add trivia question page.

    GET: Show form
    POST: Create trivia question
    """
    participant = None
    if player_id:
        participant = game_service.get_participant(player_id)
        if not participant:
            return redirect(url_for('player.onboard'))

    # Need all participants for correct answer dropdown
    all_participants = game_service.get_all_participants()

    if request.method == 'POST':
        try:
            text = request.form.get('text', '').strip()
            correct_answer = request.form.get('correct_answer')

            if not text:
                return render_template(
                    'add_trivia.html',
                    participant=participant,
                    participants=all_participants,
                    error='Please enter a question'
                )

            if not correct_answer:
                return render_template(
                    'add_trivia.html',
                    participant=participant,
                    participants=all_participants,
                    error='Please select the correct answer'
                )

            image_file = request.files.get('image')
            answer_image_file = request.files.get('answer_image')

            game_service.create_question(
                text=text,
                question_type='trivia',
                correct_answer=correct_answer,
                proposed_by=player_id,
                image_file=image_file if image_file and image_file.filename else None,
                answer_image_file=answer_image_file if answer_image_file and answer_image_file.filename else None
            )

            # Redirect back appropriately
            if participant:
                return redirect(url_for('player.propose', player_id=player_id))
            else:
                return redirect(url_for('admin.questions', key=request.args.get('key', '')))

        except Exception as e:
            import traceback
            return render_template(
                'add_trivia.html',
                participant=participant,
                participants=all_participants,
                error=str(e),
                traceback=traceback.format_exc()
            )

    return render_template('add_trivia.html', participant=participant, participants=all_participants)
