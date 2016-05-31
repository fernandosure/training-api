from app import db
from app.exceptions import ValidationError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func


class AuditMixin(object):
    created_at = db.Column(db.DateTime(timezone=True), nullable=True, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now())


class Provider(AuditMixin, db.Model):
    __tablename__ = 'providers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String)
    branches = db.relationship('ProviderBranch', backref='provider', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'branches': [branch.to_json() for branch in self.branches],
            'branches_count': self.branches.count()
        }

    def __repr__(self):
        return '<Provider %s>' % (self.name)


class ProviderBranch(AuditMixin, db.Model):
    __tablename__ = 'provider_branches'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey(Provider.id))
    name = db.Column(db.String)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    employees = db.relationship('ProviderBranchEmployee', backref='branch', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'employees': self.employees.count()
        }

    def __repr__(self):
        return '<ProviderBranch %s>' % self.name


class ProviderBranchEmployee(AuditMixin, db.Model):
    __tablename__ = 'provider_branch_employees'
    id = db.Column(db.Integer, primary_key=True)
    provider_branch_id = db.Column(db.Integer, db.ForeignKey(ProviderBranch.id), nullable=False)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)
    title = db.Column(db.String)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'title': self.title
        }

    def __repr__(self):
        return '<ProviderBranchEmployee %s>' % (self.name)

    @staticmethod
    def from_json(json):
        name = json.get('name')
        phone = json.get('phone')
        title = json.get('title')

        if name is None or name == '':
            raise ValidationError('Name cannot be empty')

        return ProviderBranchEmployee(name=name, phone=phone, title=title)


class User(AuditMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)

    def to_json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

    def __repr__(self):
        return '<User %s %s>' % (self.first_name, self.last_name)


class TrainingBatch (AuditMixin, db.Model):
    __tablename__ = 'training_batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    # relationships
    sessions = db.relationship('TrainingSession', backref='batch', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'sessions': self.sessions.count()
        }

    @staticmethod
    def from_json(json):
        name = json.get('name')

        if name is None or name == '':
            raise ValidationError('Name cannot be empty')

        return TrainingBatch(name=name)

    def __repr__(self):
        return '<TrainingBatch %s>' % (self.name)


class TrainingSession(AuditMixin, db.Model):
    __tablename__ = 'training_sessions'
    id = db.Column(db.Integer, primary_key=True)

    teacher_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    training_batch_id = db.Column(db.Integer, db.ForeignKey(TrainingBatch.id), nullable=False)
    provider_branch_id = db.Column(db.Integer, db.ForeignKey(ProviderBranch.id), nullable=False)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    comments = db.Column(db.String(512))
    signature_url = db.Column(db.String)

    # computed properties
    # @aggregated('assistants', db.Column(db.Integer))
    # def avg_score(self):
    #     return func.avg(TrainingSessionAssistant.score)
    @hybrid_property
    def avg_score(self):
        # return func.avg(TrainingSessionAssistant.score)
        return db.session.query(func.avg(TrainingSessionAssistant.score)).filter(TrainingSessionAssistant.training_session_id == self.id).scalar()

    # relations
    teacher = db.relationship('User', backref='training_sessions')
    provider_branch = db.relationship('ProviderBranch', backref='training_sessions')
    assistants = db.relationship('TrainingSessionAssistant', backref='session', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'comments': self.comments,
            'signature_url': self.signature_url,
            'teacher': self.teacher.to_json(),
            'avg_score': self.avg_score,
            'assistants': [assistant.to_json() for assistant in self.assistants]
        }

    @staticmethod
    def from_json(json):
        provider_branch_id = json.get('provider_branch_id')
        teacher_id = json.get('teacher_id')
        latitude = json.get('latitude')
        longitude = json.get('longitude')

        if provider_branch_id is None:
            raise ValidationError('provider_branch_id cannot be empty')

        if teacher_id is None:
            raise ValidationError('teacher_id cannot be empty')

        if latitude is None:
            raise ValidationError('latitude cannot be empty')

        if longitude is None:
            raise ValidationError('longitude cannot be empty')

        return TrainingSession(provider_branch_id=provider_branch_id, teacher_id=teacher_id, latitude=latitude, longitude=longitude)

    def __repr__(self):
        return '<TrainingSession %s %s >' % (self.teacher.first_name, self.teacher.last_name)


class TrainingSessionAssistant(AuditMixin, db.Model):
    __tablename__ = 'training_session_assistants'
    id = db.Column(db.Integer, primary_key=True, nullable=False)

    training_session_id = db.Column(db.Integer, db.ForeignKey(TrainingSession.id), nullable=False)
    provider_branch_employee_id = db.Column(db.Integer, db.ForeignKey(ProviderBranchEmployee.id), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    employee = db.relationship('ProviderBranchEmployee')
    # training_session = db.relationship('TrainingSession', backref='assistants')

    def to_json(self):
        return {
            'id': self.id,
            'training_session_id': self.training_session_id,
            'provider_branch_employee_id': self.provider_branch_employee_id,
            'employee': self.employee.to_json(),
            'score': self.score
        }

    def __repr__(self):
        return '<TrainingSessionAssistant %s %s>' % self.employee.name
