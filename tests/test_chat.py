import pytest
import uuid
from datetime import datetime, timezone

from backend.app import create_app, db
from backend.app.models.conversation import Conversation, ConversationMember, Message
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMembership, Role
from backend.app.services.chat_service import ConversationService
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app, client):
    """Create a test user and return auth headers."""
    with app.app_context():
        # Create organization
        org = Organization(
            name="Test Org",
            slug="test-org",
            description="Test organization",
            is_active=True,
        )
        db.session.add(org)
        db.session.flush()

        # Create role
        role = Role(
            organization_id=org.id,
            name="Test Role",
            description="Test role",
            is_system_default=True,
        )
        db.session.add(role)
        db.session.flush()

        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash=generate_password_hash("TestPassword123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        # Create membership
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role_id=role.id,
            status="active",
            is_owner=True,
        )
        db.session.add(membership)
        db.session.commit()

        # Login and get token
        response = client.post(
            '/api/v1/auth/login',
            json={'email': 'test@example.com', 'password': 'TestPassword123!'},
        )
        data = response.get_json()
        token = data['data']['access_token']

        return {
            'Authorization': f'Bearer {token}',
            'user_id': str(user.id),
            'organization_id': str(org.id),
            'Content-Type': 'application/json',
        }


@pytest.fixture
def second_user(app, auth_headers):
    """Create a second test user."""
    with app.app_context():
        org_id = uuid.UUID(auth_headers['organization_id'])
        user = User(
            email="test2@example.com",
            username="testuser2",
            full_name="Test User 2",
            password_hash=generate_password_hash("TestPassword123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        role = db.session.query(Role).filter_by(organization_id=org_id).first()
        membership = OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role_id=role.id,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        return {'id': str(user.id), 'email': 'test2@example.com'}


class TestConversationAPI:
    """Test conversation API endpoints."""

    def test_list_conversations_empty(self, client, auth_headers):
        """Test listing conversations when none exist."""
        response = client.get(
            f'/api/v1/conversations?organization_id={auth_headers["organization_id"]}',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 0
        assert data['meta']['pagination']['total'] == 0

    def test_create_direct_message_conversation(self, client, auth_headers, second_user, app):
        """Test creating a direct message conversation."""
        response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['type'] == 'direct'
        assert data['data']['organization_id'] == auth_headers['organization_id']

    def test_create_direct_message_with_self_fails(self, client, auth_headers):
        """Test creating a direct message with self fails."""
        response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': auth_headers['user_id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_create_group_conversation(self, client, auth_headers):
        """Test creating a group conversation."""
        response = client.post(
            '/api/v1/conversations/group',
            headers=auth_headers,
            json={
                'name': 'Test Group',
                'organization_id': auth_headers['organization_id'],
                'member_ids': [],
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['type'] == 'group'
        assert data['data']['name'] == 'Test Group'

    def test_send_message(self, client, auth_headers, second_user):
        """Test sending a message."""
        # Create conversation first
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message
        response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Hello, world!'},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['content'] == 'Hello, world!'
        assert data['data']['sender_id'] == auth_headers['user_id']

    def test_get_messages(self, client, auth_headers, second_user):
        """Test retrieving messages from a conversation."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message
        client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Test message'},
        )

        # Get messages
        response = client.get(
            f'/api/v1/conversations/{conv_id}/messages?limit=50&offset=0',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['content'] == 'Test message'

    def test_get_messages_with_polling(self, client, auth_headers, second_user):
        """Test polling for new messages."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send first message
        msg1_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Message 1'},
        )
        msg1_id = msg1_response.get_json()['data']['id']

        # Poll for new messages after msg1
        response = client.get(
            f'/api/v1/conversations/{conv_id}/messages?after={msg1_id}&limit=50',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 0  # No new messages after msg1

        # Send second message
        msg2_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Message 2'},
        )

        # Poll again
        response = client.get(
            f'/api/v1/conversations/{conv_id}/messages?after={msg1_id}&limit=50',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['content'] == 'Message 2'

    def test_edit_message(self, client, auth_headers, second_user):
        """Test editing a message."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message
        msg_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Original message'},
        )
        msg_id = msg_response.get_json()['data']['id']

        # Edit message
        response = client.patch(
            f'/api/v1/conversations?message_id={msg_id}',
            headers=auth_headers,
            json={'content': 'Edited message'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['content'] == 'Edited message'

    def test_delete_message(self, client, auth_headers, second_user):
        """Test deleting a message."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message
        msg_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'To be deleted'},
        )
        msg_id = msg_response.get_json()['data']['id']

        # Delete message
        response = client.delete(
            f'/api/v1/conversations?message_id={msg_id}',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_unauthorized_access_conversation(self, app, client):
        """Test accessing a conversation without authorization."""
        response = client.get('/api/v1/conversations/invalid-id')
        assert response.status_code == 401

    def test_mark_as_read(self, client, auth_headers, second_user):
        """Test marking a conversation as read."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message
        client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Test message'},
        )

        # Mark as read
        response = client.post(
            f'/api/v1/conversations/{conv_id}/read',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['last_read_at'] is not None

    def test_direct_conversation_idempotency(self, client, auth_headers, second_user):
        """Test that creating the same direct conversation twice returns the same conversation."""
        # Create first time
        response1 = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id_1 = response1.get_json()['data']['id']

        # Create second time
        response2 = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id_2 = response2.get_json()['data']['id']

        # Should be the same conversation
        assert conv_id_1 == conv_id_2

    def test_unread_count(self, client, auth_headers, second_user, app):
        """Test unread message count."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message from first user
        client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Message from user 1'},
        )

        # Get auth headers for second user
        with app.app_context():
            user = db.session.query(User).filter_by(email='test2@example.com').first()
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test2@example.com', 'password': 'TestPassword123!'},
            )
            second_user_headers = {
                'Authorization': f'Bearer {response.get_json()["data"]["access_token"]}',
                'user_id': str(user.id),
                'organization_id': auth_headers['organization_id'],
                'Content-Type': 'application/json',
            }

        # List conversations for second user - should show unread count
        response = client.get(
            f'/api/v1/conversations?organization_id={auth_headers["organization_id"]}',
            headers=second_user_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['unread_count'] == 1

        # Mark as read
        client.post(
            f'/api/v1/conversations/{conv_id}/read',
            headers=second_user_headers,
        )

        # Unread count should now be 0
        response = client.get(
            f'/api/v1/conversations?organization_id={auth_headers["organization_id"]}',
            headers=second_user_headers,
        )
        data = response.get_json()
        assert data['data'][0]['unread_count'] == 0

    def test_cannot_edit_others_messages(self, client, auth_headers, second_user, app):
        """Test that user cannot edit another user's message."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message from first user
        msg_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Message from user 1'},
        )
        msg_id = msg_response.get_json()['data']['id']

        # Get second user headers
        with app.app_context():
            user = db.session.query(User).filter_by(email='test2@example.com').first()
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test2@example.com', 'password': 'TestPassword123!'},
            )
            second_user_headers = {
                'Authorization': f'Bearer {response.get_json()["data"]["access_token"]}',
                'user_id': str(user.id),
                'organization_id': auth_headers['organization_id'],
                'Content-Type': 'application/json',
            }

        # Try to edit first user's message as second user
        response = client.patch(
            f'/api/v1/conversations?message_id={msg_id}',
            headers=second_user_headers,
            json={'content': 'Edited by someone else'},
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False

    def test_cannot_delete_others_messages(self, client, auth_headers, second_user, app):
        """Test that user cannot delete another user's message."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Send message from first user
        msg_response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': 'Message from user 1'},
        )
        msg_id = msg_response.get_json()['data']['id']

        # Get second user headers
        with app.app_context():
            user = db.session.query(User).filter_by(email='test2@example.com').first()
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test2@example.com', 'password': 'TestPassword123!'},
            )
            second_user_headers = {
                'Authorization': f'Bearer {response.get_json()["data"]["access_token"]}',
                'user_id': str(user.id),
                'organization_id': auth_headers['organization_id'],
                'Content-Type': 'application/json',
            }

        # Try to delete first user's message as second user
        response = client.delete(
            f'/api/v1/conversations?message_id={msg_id}',
            headers=second_user_headers,
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False

    def test_group_conversation_with_members(self, client, auth_headers, second_user, app):
        """Test creating a group conversation with multiple members."""
        # Get third user
        with app.app_context():
            org_id = uuid.UUID(auth_headers['organization_id'])
            user3 = User(
                email="test3@example.com",
                username="testuser3",
                full_name="Test User 3",
                password_hash=generate_password_hash("TestPassword123!"),
                is_active=True,
            )
            db.session.add(user3)
            db.session.flush()

            role = db.session.query(Role).filter_by(organization_id=org_id).first()
            membership = OrganizationMembership(
                organization_id=org_id,
                user_id=user3.id,
                role_id=role.id,
                status="active",
            )
            db.session.add(membership)
            db.session.commit()
            third_user_id = str(user3.id)

        # Create group with members
        response = client.post(
            '/api/v1/conversations/group',
            headers=auth_headers,
            json={
                'name': 'Test Group',
                'organization_id': auth_headers['organization_id'],
                'member_ids': [second_user['id'], third_user_id],
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        conv_id = data['data']['id']

        # Get members
        response = client.get(
            f'/api/v1/conversations/{conv_id}/members',
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 3  # creator + 2 members

    def test_conversation_membership_required(self, client, auth_headers, second_user, app):
        """Test that non-members cannot access conversations."""
        # Create a group conversation
        response = client.post(
            '/api/v1/conversations/group',
            headers=auth_headers,
            json={
                'name': 'Private Group',
                'organization_id': auth_headers['organization_id'],
                'member_ids': [],
            },
        )
        conv_id = response.get_json()['data']['id']

        # Get second user headers
        with app.app_context():
            user = db.session.query(User).filter_by(email='test2@example.com').first()
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test2@example.com', 'password': 'TestPassword123!'},
            )
            second_user_headers = {
                'Authorization': f'Bearer {response.get_json()["data"]["access_token"]}',
                'user_id': str(user.id),
                'organization_id': auth_headers['organization_id'],
                'Content-Type': 'application/json',
            }

        # Try to access as non-member
        response = client.get(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=second_user_headers,
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False

    def test_max_message_length(self, client, auth_headers, second_user):
        """Test that messages longer than max length are rejected."""
        # Create conversation
        create_response = client.post(
            '/api/v1/conversations/direct',
            headers=auth_headers,
            json={
                'other_user_id': second_user['id'],
                'organization_id': auth_headers['organization_id'],
            },
        )
        conv_id = create_response.get_json()['data']['id']

        # Try to send a very long message
        long_message = 'x' * 10001
        response = client.post(
            f'/api/v1/conversations/{conv_id}/messages',
            headers=auth_headers,
            json={'content': long_message},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
