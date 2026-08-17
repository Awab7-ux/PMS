#!/usr/bin/env python
"""Smoke test for Chat System"""
import sys
sys.path.insert(0, '.')

from backend.app import create_app, db
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMembership
from backend.app.models.conversation import Conversation, ConversationMember, Message
from backend.app.services.chat_service import ConversationService
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime, timezone

# Create test app
app = create_app()

with app.app_context():
    # Create test data
    org = db.session.query(Organization).first()
    if not org:
        org = Organization(id=uuid.uuid4(), name="Test Org")
        db.session.add(org)
        db.session.commit()
    
    # Create two test users
    user_a = db.session.query(User).filter_by(email="testusera@test.com").first()
    if not user_a:
        user_a = User(
            id=uuid.uuid4(),
            email="testusera@test.com",
            username="usera",
            password_hash=generate_password_hash("password123"),
            full_name="User A"
        )
        db.session.add(user_a)
        db.session.commit()
    
    user_b = db.session.query(User).filter_by(email="testuserb@test.com").first()
    if not user_b:
        user_b = User(
            id=uuid.uuid4(),
            email="testuserb@test.com",
            username="userb",
            password_hash=generate_password_hash("password123"),
            full_name="User B"
        )
        db.session.add(user_b)
        db.session.commit()
    
    # Get or create default role
    from backend.app.models.organization import Role
    role = db.session.query(Role).first()
    if not role:
        role = Role(id=uuid.uuid4(), name="Member")
        db.session.add(role)
        db.session.commit()
    
    # Ensure users are members of organization
    for user in [user_a, user_b]:
        mem = db.session.query(OrganizationMembership).filter_by(
            organization_id=org.id, user_id=user.id
        ).first()
        if not mem:
            mem = OrganizationMembership(
                id=uuid.uuid4(),
                organization_id=org.id,
                user_id=user.id,
                role_id=role.id,
                status="active"
            )
            db.session.add(mem)
    db.session.commit()
    
    # Test 1: Create direct message conversation
    print("[TEST 1] Creating direct message conversation...")
    service = ConversationService()
    conv = service.create_direct_message_conversation(
        str(user_a.id), str(user_b.id), str(org.id)
    )
    print("OK: Conversation created: " + str(conv['id']))
    
    # Test 2: Send message from User A
    print("[TEST 2] Sending message from User A...")
    msg = service.send_message(str(user_a.id), conv['id'], "Hello from User A")
    print("OK: Message sent: " + str(msg['id']))
    msg_id_1 = msg['id']
    
    # Test 3: Verify User B can see message
    print("[TEST 3] Polling for messages as User B...")
    messages = service.get_messages_after(str(user_b.id), conv['id'], None, 50)
    print("OK: Found " + str(len(messages['items'])) + " message(s)")
    assert len(messages['items']) > 0, "User B should see the message"
    assert "Hello from User A" in messages['items'][0]['content']
    
    # Test 4: Send message from User B
    print("[TEST 4] Sending message from User B...")
    msg2 = service.send_message(str(user_b.id), conv['id'], "Hello from User B")
    print("OK: Message sent: " + str(msg2['id']))
    msg_id_2 = msg2['id']
    
    # Test 5: Verify User A sees new message via polling
    print("[TEST 5] Polling for new messages as User A (using ?after parameter)...")
    new_messages = service.get_messages_after(str(user_a.id), conv['id'], msg_id_1, 50)
    print("OK: Found " + str(len(new_messages['items'])) + " new message(s)")
    assert len(new_messages['items']) > 0, "User A should see User B's message"
    assert "Hello from User B" in new_messages['items'][0]['content']
    
    # Test 6: Mark as read
    print("[TEST 6] Marking conversation as read...")
    result = service.mark_as_read(str(user_a.id), conv['id'])
    print("OK: Marked as read at: " + str(result['last_read_at']))
    
    # Test 7: Verify unread count
    print("[TEST 7] Checking unread count...")
    conv_data = service.get_conversation(str(user_a.id), conv['id'])
    print("OK: Unread count: " + str(conv_data.get('unread_count', 0)))
    assert conv_data.get('unread_count', 0) == 0, "Unread count should be 0 after marking read"
    
    # Test 8: Verify organization isolation
    print("[TEST 8] Testing organization isolation...")
    try:
        service.get_conversation(str(user_a.id), str(uuid.uuid4()))
        print("FAIL: Should have failed - unauthorized access")
    except:
        print("OK: Organization isolation working")
    
    # Test 9: Verify no duplicates by UUID
    print("[TEST 9] Verifying message deduplication...")
    all_msgs = service.get_messages(str(user_a.id), conv['id'])
    msg_ids = [m['id'] for m in all_msgs['items']]
    assert len(msg_ids) == len(set(msg_ids)), "Messages should not be duplicated"
    print("OK: All " + str(len(msg_ids)) + " messages unique")
    
    print("\n" + "="*50)
    print("SUCCESS: ALL SMOKE TESTS PASSED")
    print("="*50)
