from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..models import ChatSession, ChatMessage, db
from datetime import datetime

bp = Blueprint('chat', __name__)

@bp.route('/start', methods=['POST'])
@login_required
def start_chat():
    # Create a new chat session
    session = ChatSession(
        user_id=current_user.id,
        started_at=datetime.utcnow(),
        preferred_language=current_user.preferred_language
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'session_id': session.id,
        'started_at': session.started_at.isoformat(),
        'user_role': current_user.role,
        'preferred_language': session.preferred_language
    })

@bp.route('/message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    session_id = data.get('session_id')
    content = data.get('content')
    
    if not session_id or not content:
        return jsonify({'error': 'Missing session_id or content'}), 400
        
    # Get the chat session
    session = ChatSession.query.get(session_id)
    if not session or session.user_id != current_user.id:
        return jsonify({'error': 'Invalid session'}), 404
        
    # Add user message
    user_message = ChatMessage(
        session_id=session_id,
        role='user',
        content=content,
        language=current_user.preferred_language
    )
    db.session.add(user_message)
    
    # Generate response based on user role
    response_content = generate_role_based_response(current_user.role, content)
    
    # Add system response
    system_message = ChatMessage(
        session_id=session_id,
        role='assistant',
        content=response_content,
        language=current_user.preferred_language
    )
    db.session.add(system_message)
    
    try:
        db.session.commit()
        return jsonify({
            'messages': [
                {
                    'role': user_message.role,
                    'content': user_message.content,
                    'timestamp': user_message.timestamp.isoformat()
                },
                {
                    'role': system_message.role,
                    'content': system_message.content,
                    'timestamp': system_message.timestamp.isoformat()
                }
            ]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def generate_role_based_response(role, message):
    """Generate different responses based on user role"""
    if role == 'patient':
        # Limited responses for patients
        # Add your logic here to limit responses for patients
        return "I can help you with basic health inquiries. For detailed medical advice, please consult with a doctor."
    elif role == 'doctor':
        # More detailed responses for doctors
        # Add your logic here to provide more detailed responses for doctors
        return "Here's a detailed medical analysis based on the provided information..."
    else:
        return "I can assist you with general health information. How may I help you?"

@bp.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
        
    session = ChatSession.query.get(session_id)
    if not session or session.user_id != current_user.id:
        return jsonify({'error': 'Invalid session'}), 404
        
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    return jsonify({
        'messages': [{
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages]
    })
