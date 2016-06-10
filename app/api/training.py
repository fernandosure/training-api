from flask import jsonify, request, g, current_app, url_for
from . import api
from .. import db
from ..models import ProviderBranchEmployee, TrainingBatch, TrainingSession, TrainingSessionAssistant, TrainingScenario, TrainingSessionAssistantScore
from ..logger import log
from ..exceptions import ValidationError
from ..s3 import upload_to_s3
import base64


#############################
# GET ALL TRAINING SCENARIOS
#############################
@api.route('/training/scenarios')
def get_scenarios():
    log.info('get_scenarios')

    scenarios = TrainingScenario.query.order_by(TrainingScenario.description)

    return jsonify({
        'content': [scenario.to_json() for scenario in scenarios],
        'total_elements': scenarios.count()
    })


#############################
# GET ALL TRAINING BATCHES
#############################
@api.route('/training/batches')
def get_batches():
    log.info('get_batches')

    batches = TrainingBatch.query.order_by(TrainingBatch.name.asc())

    return jsonify({
        'content': [batch.to_json() for batch in batches],
        'total_elements': batches.count()
    })


#############################
# CREATE A NEW TRAINING BATCH
#############################
@api.route('/training/batches', methods=['POST'])
def new_batch():
    log.info('new_batch')

    batch = TrainingBatch.from_json(request.json)

    db.session.add(batch)
    db.session.commit()

    return jsonify(batch.to_json()), 201


#############################
# GET ALL SESSIONS BY BATCH
#############################
@api.route('/training/batches/<int:batch_id>/sessions')
def get_training_sessions_by_batch(batch_id):
    log.info('get_training_sessions_by_batch: batch_id %s ' % batch_id)

    sessions = TrainingSession.query.filter(TrainingSession.training_batch_id == batch_id)

    return jsonify({
        'content': [session.to_json() for session in sessions],
        'total_elements': sessions.count()
    })


#############################
# GET A SINGLE SESSION BY ID
#############################
@api.route('/training/batches/<int:batch_id>/sessions/<int:session_id>', methods=['GET'])
def get_training_session(batch_id, session_id):

    log.info('get_training_session: batch_id %s session_id: %s' % (batch_id, session_id))

    session = TrainingSession.query.filter(TrainingSession.training_batch_id == batch_id) \
                                   .filter(TrainingSession.id == session_id).first_or_404()

    return jsonify(session.to_json())


#############################
# START/CREATE A NEW SESSION
#############################
@api.route('/training/batches/<int:batch_id>/sessions', methods=['POST'])
def new_training_session(batch_id):

    log.info('new_training_session: batch_id %s' % batch_id)
    log.info('request: %s' % request.json)

    batch = TrainingBatch.query.filter(TrainingBatch.id == batch_id).first_or_404()

    session = TrainingSession.from_json(request.json)
    session.batch = batch

    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_json()), 201


######################################
# ADD ASSISTANTS TO EXISTING SESSION
######################################
@api.route('/training/batches/<int:batch_id>/sessions/<int:session_id>', methods=['PATCH'])
def add_assistants_to_training_session(batch_id, session_id):

    log.info('add_assistants_to_training_session: batch_id %s session_id: %s' % (batch_id, session_id))
    log.info('request: %s' % request.json)

    session = TrainingSession.query.filter(TrainingSession.training_batch_id == batch_id) \
                                   .filter(TrainingSession.id == session_id).first_or_404()
    # constraints
    if session.signature_url is not None:
        raise ValidationError('Training session is already completed, you cannot add new assistants to it')

    # check body to find assistant field
    assistants = request.get_json().get('assistants')
    if assistants is None:
        raise ValidationError('assistants cannot be null')

    log.info('assistants: %s' % len(assistants))

    for i, assistant in enumerate(assistants):

        employee = session.provider_branch.employees.filter(ProviderBranchEmployee.id == assistant['employee_id']).first()
        if employee is None:
            raise ValidationError('Employee %s does not exist' % assistant['employee_id'])

        if assistant['results'] is None:
            raise ValidationError('scores array on assistant #%s' % assistant['employee_id'])


        session_assistant = TrainingSessionAssistant()
        session_assistant.employee = employee
        session_assistant.session = session

        log.info('Training session id: %s employee: %s', (session.id, employee.name))

        for x, result in enumerate(assistant['results']):

            if result['scenario_id'] is None:
                raise ValidationError('scenario_id is null in result [%s] of assistant #%s' % (x + 1, assistant['employee_id']))

            scenario = TrainingScenario.query.filter(TrainingScenario.id == result['scenario_id']).first()
            if scenario is None:
                raise ValidationError('scenario in result [%s] of assistant #%s does not exist' % (x + 1, assistant['employee_id']))

            if result['score'] is None:
                raise ValidationError('score in result [%s] of assistant #%s is null' % (x + 1, assistant['employee_id']))

            if result['score'] < 0 or result['score'] > 100:
                raise ValidationError('score in result [%s] of assistant #%s is outside of permitted scope [0-100]' % (x + 1, assistant['employee_id']))

            scenario_score = TrainingSessionAssistantScore(score=result['score'])
            scenario_score.scenario = scenario
            session_assistant.scores.append(scenario_score)

            log.info('Training session id: %s employee: %s scenario: %s score %s', (session.id, employee.name, scenario.description, scenario_score.score))

        db.session.add(session_assistant)

    db.session.commit()
    return jsonify(session.to_json()), 201


######################################
# FINISH A SESSION AND UPLOAD SIGNATURE
######################################
@api.route('/training/batches/<int:batch_id>/sessions/<int:session_id>/finish', methods=['POST'])
def finish_training_session(batch_id, session_id):
    log.info('finish_training_session: batch_id %s session_id: %s' % (batch_id, session_id))
    # log.info('request: %s' % request.json)

    session = TrainingSession.query.filter(TrainingSession.training_batch_id == batch_id) \
                                   .filter(TrainingSession.id == session_id).first_or_404()

    log.info('signature_url %s' % session.signature_url)

    if session.signature_url is not None:
        raise ValidationError('Training session is already completed')

    json = request.json

    # validate comments field
    comments = json.get('comments')
    if comments is None:
        raise ValidationError('comments cannot be empty')

    if json.get('signature_base64') is None:
        raise ValidationError('Signature cannot be null')

    file = base64.b64decode(json.get('signature_base64'))
    result_url = upload_to_s3(file, '/training/signatures/' + str(session.id) + ".jpg")

    # save the url from the uploaded image
    session.comments = comments
    session.signature_url = result_url
    db.session.commit()
    return jsonify(session.to_json()), 201
