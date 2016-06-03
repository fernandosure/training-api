from flask import jsonify, request, g, current_app, url_for
from . import api
from .. import db
from ..models import Provider, ProviderBranch, ProviderBranchEmployee
from ..logger import log


@api.route('/training/providers')
def get_providers(): 

    providers = Provider.query.order_by(Provider.name.asc())
    return jsonify({
        'content': [provider.to_json() for provider in providers],
        'total_elements': providers.count()
    })


@api.route('/training/providers/<string:slug>/branches')
def get_branches(slug):

    provider = Provider.query.filter(Provider.slug == slug).first_or_404()

    return jsonify({
        'content': [provider_branch.to_json() for provider_branch in provider.branches],
        'total_elements': provider.branches.count()
    })


@api.route('/training/providers/<string:slug>/branches/<int:branch_id>/employees', methods=['GET'])
def get_employees(slug, branch_id):

    log.info('get_employees: slug %s branch_id: %s' % (slug, branch_id))

    branch = ProviderBranch.query.filter(ProviderBranch.provider.has(slug=slug)) \
                                 .filter(ProviderBranch.id == branch_id).first_or_404()

    return jsonify({
        'content': [employee.to_json() for employee in branch.employees],
        'total_elements': branch.employees.count()
    })


@api.route('/training/providers/<string:slug>/branches/<int:branch_id>/employees', methods=['POST'])
def new_employee(slug, branch_id):

    log.info('new_employee: slug %s branch_id: %s' % (slug, branch_id))
    log.info('request: %s' % request.json)

    branch = ProviderBranch.query.filter(ProviderBranch.provider.has(slug=slug)) \
                                 .filter(ProviderBranch.id == branch_id).first_or_404()

    employee = ProviderBranchEmployee.from_json(request.json)
    employee.branch = branch
    db.session.add(employee)
    db.session.commit()
    return jsonify(employee.to_json()), 201
