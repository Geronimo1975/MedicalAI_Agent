from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from .models import User, Appointment, MedicalRecord, Prescription, MedicalDocument, ChatSession, ChatMessage, db
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from .chatbot import ChatbotService

api_bp = Blueprint('api', __name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = Path("uploads/medical_documents")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Appointments
@api_bp.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    if current_user.role == 'patient':
        appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    elif current_user.role == 'doctor':
        appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
    else:
        appointments = Appointment.query.all()
        
    return jsonify([{
        'id': a.id,
        'patient_id': a.patient_id,
        'doctor_id': a.doctor_id,
        'date_time': a.date_time.isoformat(),
        'status': a.status,
        'notes': a.notes,
        'video_room_id': a.video_room_id
    } for a in appointments])

@api_bp.route('/appointments', methods=['POST'])
@login_required
def create_appointment():
    data = request.get_json()
    
    appointment = Appointment(
        patient_id=current_user.id if current_user.role == 'patient' else data['patient_id'],
        doctor_id=data['doctor_id'],
        date_time=datetime.fromisoformat(data['date_time']),
        status='scheduled',
        notes=data.get('notes'),
        video_room_id=data.get('video_room_id')
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'doctor_id': appointment.doctor_id,
        'date_time': appointment.date_time.isoformat(),
        'status': appointment.status,
        'notes': appointment.notes,
        'video_room_id': appointment.video_room_id
    })

@api_bp.route('/appointments/<int:id>', methods=['PUT'])
@login_required
def update_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        appointment.status = data['status']
    if 'notes' in data:
        appointment.notes = data['notes']
    if 'video_room_id' in data:
        appointment.video_room_id = data['video_room_id']
    
    db.session.commit()
    
    return jsonify({
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'doctor_id': appointment.doctor_id,
        'date_time': appointment.date_time.isoformat(),
        'status': appointment.status,
        'notes': appointment.notes,
        'video_room_id': appointment.video_room_id
    })

# Medical Records
@api_bp.route('/medical-records/<int:patient_id>', methods=['GET'])
@login_required
def get_medical_records(patient_id):
    if current_user.role == 'patient' and current_user.id != patient_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    
    return jsonify([{
        'id': r.id,
        'patient_id': r.patient_id,
        'doctor_id': r.doctor_id,
        'date': r.date.isoformat(),
        'diagnosis': r.diagnosis,
        'prescription': r.prescription,
        'notes': r.notes
    } for r in records])

@api_bp.route('/medical-records', methods=['POST'])
@login_required
def create_medical_record():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Only doctors can create medical records'}), 403
        
    data = request.get_json()
    
    record = MedicalRecord(
        patient_id=data['patient_id'],
        doctor_id=current_user.id,
        diagnosis=data['diagnosis'],
        prescription=data.get('prescription'),
        notes=data.get('notes')
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'id': record.id,
        'patient_id': record.patient_id,
        'doctor_id': record.doctor_id,
        'date': record.date.isoformat(),
        'diagnosis': record.diagnosis,
        'prescription': record.prescription,
        'notes': record.notes
    })

# Prescriptions
@api_bp.route('/prescriptions', methods=['GET'])
@login_required
def get_prescriptions():
    if current_user.role == 'patient':
        prescriptions = Prescription.query.filter_by(patient_id=current_user.id).all()
    elif current_user.role == 'doctor':
        prescriptions = Prescription.query.filter_by(doctor_id=current_user.id).all()
    else:
        prescriptions = Prescription.query.all()

    return jsonify([{
        'id': p.id,
        'patient_id': p.patient_id,
        'doctor_id': p.doctor_id,
        'medication': p.medication,
        'dosage': p.dosage,
        'frequency': p.frequency,
        'start_date': p.start_date.isoformat(),
        'end_date': p.end_date.isoformat(),
        'status': p.status,
        'notes': p.notes,
        'created_at': p.created_at.isoformat(),
        'patient_name': p.patient.name,
        'doctor_name': p.doctor.name
    } for p in prescriptions])

@api_bp.route('/prescriptions/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_prescriptions(patient_id):
    if current_user.role == 'patient' and current_user.id != patient_id:
        return jsonify({'error': 'Unauthorized'}), 403

    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()

    return jsonify([{
        'id': p.id,
        'patient_id': p.patient_id,
        'doctor_id': p.doctor_id,
        'medication': p.medication,
        'dosage': p.dosage,
        'frequency': p.frequency,
        'start_date': p.start_date.isoformat(),
        'end_date': p.end_date.isoformat(),
        'status': p.status,
        'notes': p.notes,
        'created_at': p.created_at.isoformat(),
        'patient_name': p.patient.name,
        'doctor_name': p.doctor.name
    } for p in prescriptions])

@api_bp.route('/prescriptions', methods=['POST'])
@login_required
def create_prescription():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Only doctors can create prescriptions'}), 403

    data = request.get_json()

    try:
        prescription = Prescription(
            patient_id=data['patient_id'],
            doctor_id=current_user.id,
            medication=data['medication'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            status='active',
            notes=data.get('notes')
        )

        db.session.add(prescription)
        db.session.commit()

        return jsonify({
            'id': prescription.id,
            'patient_id': prescription.patient_id,
            'doctor_id': prescription.doctor_id,
            'medication': prescription.medication,
            'dosage': prescription.dosage,
            'frequency': prescription.frequency,
            'start_date': prescription.start_date.isoformat(),
            'end_date': prescription.end_date.isoformat(),
            'status': prescription.status,
            'notes': prescription.notes,
            'created_at': prescription.created_at.isoformat(),
            'patient_name': prescription.patient.name,
            'doctor_name': prescription.doctor.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/prescriptions/<int:id>', methods=['PUT'])
@login_required
def update_prescription(id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Only doctors can update prescriptions'}), 403

    prescription = Prescription.query.get_or_404(id)
    if prescription.doctor_id != current_user.id:
        return jsonify({'error': 'You can only update your own prescriptions'}), 403

    data = request.get_json()

    try:
        if 'status' in data:
            prescription.status = data['status']
        if 'notes' in data:
            prescription.notes = data['notes']
        if 'end_date' in data:
            prescription.end_date = datetime.fromisoformat(data['end_date'])

        db.session.commit()

        return jsonify({
            'id': prescription.id,
            'patient_id': prescription.patient_id,
            'doctor_id': prescription.doctor_id,
            'medication': prescription.medication,
            'dosage': prescription.dosage,
            'frequency': prescription.frequency,
            'start_date': prescription.start_date.isoformat(),
            'end_date': prescription.end_date.isoformat(),
            'status': prescription.status,
            'notes': prescription.notes,
            'created_at': prescription.created_at.isoformat(),
            'patient_name': prescription.patient.name,
            'doctor_name': prescription.doctor.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Medical Documents
@api_bp.route('/documents', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        data = request.form
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOAD_FOLDER / unique_filename

        file.save(file_path)

        document = MedicalDocument(
            title=data.get('title', filename),
            file_path=str(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            shared_by_id=current_user.id,
            shared_with_id=data['shared_with_id'],
            description=data.get('description'),
            category=data.get('category')
        )

        db.session.add(document)
        db.session.commit()

        return jsonify({
            'id': document.id,
            'title': document.title,
            'file_type': document.file_type,
            'shared_by_id': document.shared_by_id,
            'shared_with_id': document.shared_with_id,
            'created_at': document.created_at.isoformat(),
            'description': document.description,
            'category': document.category
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/documents', methods=['GET'])
@login_required
def get_documents():
    try:
        # Get documents shared by or with the current user
        documents = MedicalDocument.query.filter(
            db.or_(
                MedicalDocument.shared_by_id == current_user.id,
                MedicalDocument.shared_with_id == current_user.id
            )
        ).all()

        return jsonify([{
            'id': doc.id,
            'title': doc.title,
            'file_type': doc.file_type,
            'shared_by_id': doc.shared_by_id,
            'shared_with_id': doc.shared_with_id,
            'created_at': doc.created_at.isoformat(),
            'description': doc.description,
            'category': doc.category,
            'is_archived': doc.is_archived,
            'shared_by_name': doc.shared_by.name,
            'shared_with_name': doc.shared_with.name
        } for doc in documents])

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/documents/<int:id>/download', methods=['GET'])
@login_required
def download_document(id):
    document = MedicalDocument.query.get_or_404(id)

    # Check if user has access to the document
    if current_user.id not in [document.shared_by_id, document.shared_with_id]:
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=f"{document.title}.{document.file_type}"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/documents/<int:id>/archive', methods=['PUT'])
@login_required
def archive_document(id):
    document = MedicalDocument.query.get_or_404(id)

    # Only the person who shared the document can archive it
    if current_user.id != document.shared_by_id:
        return jsonify({'error': 'Unauthorized action'}), 403

    try:
        document.is_archived = not document.is_archived
        db.session.commit()

        return jsonify({
            'id': document.id,
            'is_archived': document.is_archived
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Chatbot endpoints
@api_bp.route('/chat/session', methods=['POST'])
@login_required
def create_chat_session():
    try:
        session = ChatbotService.create_session(current_user.id)
        return jsonify({
            'session_id': session.id,
            'started_at': session.started_at.isoformat(),
            'message': "Hello! I'm here to help assess your symptoms. Please describe what's bothering you."
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/chat/sessions', methods=['GET'])
@login_required
def get_chat_sessions():
    try:
        sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.started_at.desc()).all()
        return jsonify([{
            'id': session.id,
            'started_at': session.started_at.isoformat(),
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'summary': session.summary,
            'triage_level': session.triage_level
        } for session in sessions])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/chat/session/<int:session_id>', methods=['GET'])
@login_required
def get_chat_history(session_id):
    try:
        session = ChatSession.query.get_or_404(session_id)
        if session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403

        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
        return jsonify({
            'session_id': session_id,
            'started_at': session.started_at.isoformat(),
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'triage_level': session.triage_level,
            'summary': session.summary,
            'messages': [{
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/chat/session/<int:session_id>/message', methods=['POST'])
@login_required
def send_message(session_id):
    try:
        session = ChatSession.query.get_or_404(session_id)
        if session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403

        if session.ended_at:
            return jsonify({'error': 'This chat session has ended'}), 400

        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        response = ChatbotService.get_response(session_id, data['message'])

        return jsonify({
            'response': response,
            'triage_level': session.triage_level
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/chat/session/<int:session_id>/end', methods=['POST'])
@login_required
def end_chat_session(session_id):
    try:
        session = ChatSession.query.get_or_404(session_id)
        if session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403

        if session.ended_at:
            return jsonify({'error': 'Session already ended'}), 400

        summary = ChatbotService.end_session(session_id)

        return jsonify({
            'summary': summary,
            'ended_at': session.ended_at.isoformat(),
            'triage_level': session.triage_level
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400