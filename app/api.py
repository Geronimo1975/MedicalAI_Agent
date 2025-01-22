from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models import User, Appointment, MedicalRecord, db
from datetime import datetime

api_bp = Blueprint('api', __name__)

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
